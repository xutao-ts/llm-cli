"""命令行入口。

用法：
    python -m llm_cli "你的问题"
"""

from __future__ import annotations

import argparse
import json

from .client import ChatResult, LLMClient, Message
from .config import Settings
from .logger import setup_logger


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="llm-cli", description="LLM 命令行问答工具")
    parser.add_argument("question", nargs="?", help="提问内容；不填则进入交互模式（后续实现）")
    parser.add_argument("--model", help="覆盖默认模型")
    parser.add_argument("--debug", action="store_true", help="开启 DEBUG 日志")
    parser.add_argument("--raw", action="store_true", help="输出模型返回的原始 JSON")
    return parser


def format_result(result: ChatResult) -> str:
    """把结构化结果渲染成易读的终端文本。"""
    usage = result.usage
    usage_line = (
        f"Token 用量：输入 {usage.prompt_tokens} / 输出 {usage.completion_tokens} "
        f"/ 合计 {usage.total_tokens}"
    )
    if usage.reasoning_tokens:
        usage_line += f"（其中推理 {usage.reasoning_tokens}）"

    lines = [
        "=" * 60,
        f"回复：{result.content}",
        "-" * 60,
        f"模型：{result.model or '未知'}",
        f"结束原因：{result.finish_reason or '未知'}",
        usage_line,
        "=" * 60,
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    settings = Settings.load()
    logger = setup_logger("DEBUG" if args.debug else settings.log_level)

    if not args.question:
        logger.info("交互模式尚未实现，请传入问题文本。")
        return 0

    if not settings.api_key:
        logger.error("未配置 LLM_API_KEY，无法调用模型；请在环境变量或 .env 中填写。")
        return 1

    client = LLMClient(
        api_key=settings.api_key,
        base_url=settings.base_url,
        model=args.model or settings.model,
        timeout=settings.timeout,
    )

    logger.info("已接收问题：%s", args.question)
    try:
        result = client.chat([Message(role="user", content=args.question)])
    except RuntimeError as exc:
        logger.error("%s", exc)
        return 1

    if args.raw:
        print(json.dumps(result.raw, ensure_ascii=False, indent=2))
    else:
        print(format_result(result))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
