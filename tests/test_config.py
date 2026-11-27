"""配置加载单测：默认值与环境变量覆盖。"""

from __future__ import annotations

from llm_cli import config
from llm_cli.config import Settings


def test_default_settings(monkeypatch):
    monkeypatch.setattr(config, "load_dotenv", lambda *args, **kwargs: False)
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.delenv("LLM_BASE_URL", raising=False)
    monkeypatch.delenv("LLM_MODEL", raising=False)

    settings = Settings.load()

    assert settings.api_key is None
    assert settings.base_url == "https://api.openai.com/v1"
    assert settings.model == "gpt-4o-mini"
    assert settings.timeout == 30.0
    assert settings.log_level == "INFO"


def test_env_overrides(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "sk-test")
    monkeypatch.setenv("LLM_BASE_URL", "https://example.com/v1")
    monkeypatch.setenv("LLM_MODEL", "qwen-test")
    monkeypatch.setenv("LLM_TIMEOUT", "60")

    settings = Settings.load()

    assert settings.api_key == "sk-test"
    assert settings.base_url == "https://example.com/v1"
    assert settings.model == "qwen-test"
    assert settings.timeout == 60.0
