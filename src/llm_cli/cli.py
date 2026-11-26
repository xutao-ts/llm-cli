"""命令行入口。

用法：
    python -m llm_cli "你的问题"
"""

from __future__ import annotations

import argparse

from .config import Settings
from .logger import setup_logger


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="llm-cli", description="LLM 命令行问答工具")
    parser.add_argument("question", nargs="?", help="提问内容；不填则进入交互模式（后续实现）")
    parser.add_argument("--model", help="覆盖默认模型")
    parser.add_argument("--debug", action="store_true", help="开启 DEBUG 日志")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    settings = Settings.load()
    logger = setup_logger("DEBUG" if args.debug else settings.log_level)

    if not args.question:
        logger.info("交互模式尚未实现，请传入问题文本。")
        return 0

    if not settings.api_key:
        logger.warning("未配置 LLM_API_KEY，模型调用暂不可用；请先在环境变量或本地配置中填写。")

    logger.info("已接收问题：%s", args.question)
    logger.info("默认模型：%s", args.model or settings.model)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
