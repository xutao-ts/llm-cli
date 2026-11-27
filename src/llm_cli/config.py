"""配置加载：环境变量优先，其次外置配置文件；密钥不进代码库。"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - 依赖未装时的兜底

    def load_dotenv(*_args, **_kwargs) -> bool:
        return False


@dataclass(frozen=True)
class Settings:
    """运行配置。敏感字段只从环境变量读取。"""

    api_key: str | None
    base_url: str
    model: str
    timeout: float
    log_level: str

    @classmethod
    def load(cls, config_path: Path | None = None) -> Settings:
        # 从项目根目录的 .env 加载；已存在的环境变量优先，不覆盖
        load_dotenv(Path.cwd() / ".env")
        if config_path and config_path.exists():
            # 预留：后续可读取 TOML 配置；当前先以环境变量为主
            pass

        return cls(
            api_key=os.getenv("LLM_API_KEY"),
            base_url=os.getenv("LLM_BASE_URL", "https://api.openai.com/v1"),
            model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
            timeout=float(os.getenv("LLM_TIMEOUT", "30")),
            log_level=os.getenv("LLM_LOG_LEVEL", "INFO"),
        )
