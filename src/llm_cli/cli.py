"""命令行入口。

用法：
    python -m llm_cli "你的问题"      # 单轮问答
    python -m llm_cli                 # 交互模式，多轮对话
"""

from __future__ import annotations

import argparse
import json
import uuid

from .client import ChatResult, LLMClient, Message, Usage
from .config import Settings
from .logger import setup_logger


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="llm-cli",
        description="LLM 命令行问答工具（OpenAI 兼容协议）",
    )
    parser.add_argument(
        "question",
        nargs="?",
        help="提问内容；不填则进入交互模式，可进行多轮对话",
    )
    parser.add_argument("--model", help="覆盖默认模型名称")
    parser.add_argument(
        "--stream",
        action="store_true",
        help="流式输出，边生成边打印",
    )
    parser.add_argument(
        "--thinking",
        choices=["auto", "enabled", "disabled"],
        help="思考/推理开关，透传给模型；不填则使用服务端默认",
    )
    parser.add_argument(
        "--show-reasoning",
        action="store_true",
        help="打印模型的思考过程（reasoning_content）",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="开启 DEBUG 级别日志",
    )
    parser.add_argument(
        "--raw",
        action="store_true",
        help="输出模型返回的原始 JSON，而非格式化结果",
    )
    return parser


def format_summary(result: ChatResult) -> str:
    """渲染模型信息与 token 用量等尾部摘要。"""
    usage = result.usage
    usage_line = (
        f"Token 用量：输入 {usage.prompt_tokens} / 输出 {usage.completion_tokens} "
        f"/ 合计 {usage.total_tokens}"
    )
    if usage.reasoning_tokens:
        usage_line += f"（其中推理 {usage.reasoning_tokens}）"

    return "\n".join(
        [
            "-" * 60,
            f"模型：{result.model or '未知'}",
            f"结束原因：{result.finish_reason or '未知'}",
            usage_line,
            "=" * 60,
        ]
    )


def format_result(result: ChatResult) -> str:
    """把结构化结果渲染成易读的终端文本。"""
    lines = [
        "=" * 60,
        f"回复：{result.content}",
        format_summary(result),
    ]
    return "\n".join(lines)


def stream_reply(
    client: LLMClient,
    messages: list[Message],
    raw: bool,
    thinking: str | None = None,
    show_reasoning: bool = False,
) -> ChatResult:
    """逐段打印流式回复，并聚合为一次完整结果。"""
    pieces: list[str] = []
    reasoning_pieces: list[str] = []
    raw_chunks: list[dict] = []
    model = ""
    finish_reason: str | None = None
    usage = Usage()
    reasoning_started = False
    content_started = False

    for chunk in client.chat_stream(messages, thinking=thinking):
        raw_chunks.append(chunk.raw)
        if chunk.delta:
            pieces.append(chunk.delta)
        if chunk.reasoning:
            reasoning_pieces.append(chunk.reasoning)
        if chunk.model:
            model = chunk.model
        if chunk.finish_reason:
            finish_reason = chunk.finish_reason
        if chunk.usage is not None:
            usage = chunk.usage

        if raw:
            print(json.dumps(chunk.raw, ensure_ascii=False))
            continue

        if show_reasoning and chunk.reasoning:
            if not reasoning_started:
                print("[思考] ", end="", flush=True)
                reasoning_started = True
            print(chunk.reasoning, end="", flush=True)

        if chunk.delta:
            if reasoning_started and not content_started:
                print()
            print(chunk.delta, end="", flush=True)
            content_started = True

    if not raw:
        print()

    return ChatResult(
        content="".join(pieces),
        model=model,
        finish_reason=finish_reason,
        usage=usage,
        reasoning="".join(reasoning_pieces),
        raw={"chunks": raw_chunks},
    )


def run_turn(
    client: LLMClient,
    messages: list[Message],
    args: argparse.Namespace,
    logger,
    request_id: str,
) -> ChatResult | None:
    """执行一轮请求并打印结果；请求失败返回 ``None``。"""
    try:
        if args.stream:
            result = stream_reply(
                client,
                messages,
                raw=args.raw,
                thinking=args.thinking,
                show_reasoning=args.show_reasoning,
            )
            if not args.raw:
                print(format_summary(result))
            return result

        result = client.chat(messages, thinking=args.thinking)
    except RuntimeError as exc:
        logger.error("[%s] %s", request_id, exc)
        return None

    if args.raw:
        print(json.dumps(result.raw, ensure_ascii=False, indent=2))
        return result

    if args.show_reasoning and result.reasoning:
        print("[思考]")
        print(result.reasoning)
        print()
    print(format_result(result))
    return result


def chat_loop(
    client: LLMClient,
    args: argparse.Namespace,
    logger,
    request_id: str,
) -> int:
    """交互模式：持续读取输入，保留完整上下文实现多轮对话。"""
    history: list[Message] = []
    turn = 0
    print("进入交互模式：直接输入问题，/clear 清空上下文，/exit 退出。")

    while True:
        try:
            text = input("你> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not text:
            continue
        if text in ("/exit", "/quit"):
            break
        if text == "/clear":
            history.clear()
            print("已清空对话上下文。")
            continue

        history.append(Message(role="user", content=text))
        turn += 1
        logger.info("[%s] 第 %d 轮提问：%s", request_id, turn, text)

        result = run_turn(client, history, args, logger, request_id)
        if result is None:
            # 失败的一轮不进入上下文，避免污染后续对话
            history.pop()
            continue
        history.append(Message(role="assistant", content=result.content))

    print("已退出交互模式。")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    settings = Settings.load()
    logger = setup_logger("DEBUG" if args.debug else settings.log_level)
    request_id = uuid.uuid4().hex[:8]

    if not settings.api_key:
        logger.error(
            "[%s] 未配置 LLM_API_KEY，无法调用模型；请在环境变量或 .env 中填写。",
            request_id,
        )
        return 1

    client = LLMClient(
        api_key=settings.api_key,
        base_url=settings.base_url,
        model=args.model or settings.model,
        timeout=settings.timeout,
    )

    if args.question is None:
        return chat_loop(client, args, logger, request_id)

    logger.info("[%s] 已接收问题：%s", request_id, args.question)
    result = run_turn(
        client,
        [Message(role="user", content=args.question)],
        args,
        logger,
        request_id,
    )
    return 0 if result is not None else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
