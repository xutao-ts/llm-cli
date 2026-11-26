"""日志初始化：统一格式、级别可配置，输出到 stdout。"""

from __future__ import annotations

import logging
import sys


def setup_logger(level: str = "INFO") -> logging.Logger:
    """初始化 logger，避免重复添加 handler。"""
    logger = logging.getLogger("llm_cli")
    if logger.handlers:
        return logger

    handler = logging.StreamHandler(stream=sys.stderr)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    logger.addHandler(handler)
    logger.setLevel(level.upper())
    logger.propagate = False
    return logger
