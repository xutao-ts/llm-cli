"""asyncio 并发调用示例（W02）。

运行前请先在 .env 或环境变量中配置 LLM_API_KEY 等。

用法（在项目根目录、激活 .venv 后）：
    python examples/async_batch.py
"""

from __future__ import annotations

import asyncio
import time

from llm_cli.client import LLMClient, Message
from llm_cli.config import Settings
from llm_cli.logger import setup_logger

QUESTIONS = [
    ("q1", "用一句话解释什么是向量数据库。"),
    ("q2", "列出 RAG 流程的三个主要阶段。"),
    ("q3", "温度参数调高和调低分别有什么表现？"),
    ("q4", "什么是上下文窗口？超出会怎样？"),
    ("q5", "Token 和单词是一回事吗？"),
]


async def main() -> int:
    settings = Settings.load()
    logger = setup_logger(settings.log_level)

    if not settings.api_key:
        logger.error("未配置 LLM_API_KEY，无法调用模型。")
        return 1

    client = LLMClient(
        api_key=settings.api_key,
        base_url=settings.base_url,
        model=settings.model,
        timeout=settings.timeout,
    )

    items = [(label, [Message(role="user", content=question)]) for label, question in QUESTIONS]

    started = time.perf_counter()
    results = await LLMClient.gather_chats(client, items)
    elapsed = time.perf_counter() - started

    print(f"\n并发 {len(items)} 个请求，总耗时 {elapsed:.2f}s\n")
    for label, result in results:
        question = dict(QUESTIONS)[label]
        print(f"[{label}] 问题：{question}")
        if isinstance(result, RuntimeError):
            print(f"    失败：{result}\n")
            continue
        usage = result.usage
        print(f"    回复：{result.content}")
        print(
            f"    模型：{result.model} | 用量 输入 {usage.prompt_tokens} / "
            f"输出 {usage.completion_tokens} / 合计 {usage.total_tokens}\n"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
