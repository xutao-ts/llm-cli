"""CLI 入口单测。"""

from __future__ import annotations

from llm_cli import cli
from llm_cli.client import ChatResult, Usage
from llm_cli.config import Settings


def _settings(api_key: str | None) -> Settings:
    return Settings(
        api_key=api_key,
        base_url="https://example.com/v1",
        model="test-model",
        timeout=30.0,
        log_level="INFO",
    )


def _stub_load(api_key: str | None):
    def load(cls, *args, **kwargs):
        return _settings(api_key)

    return classmethod(load)


def test_cli_with_question_without_api_key(capsys, monkeypatch):
    monkeypatch.setattr(cli.Settings, "load", _stub_load(None))
    exit_code = cli.main(["你好"])
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "LLM_API_KEY" in captured.err + captured.out


def test_cli_with_question_prints_reply(capsys, monkeypatch):
    stub_result = ChatResult(
        content="你好，我是模型",
        model="test-model",
        finish_reason="stop",
        usage=Usage(prompt_tokens=31, completion_tokens=60, total_tokens=91, reasoning_tokens=23),
        raw={},
    )
    monkeypatch.setattr(cli.Settings, "load", _stub_load("sk-test"))
    monkeypatch.setattr(cli.LLMClient, "chat", lambda self, messages: stub_result)
    exit_code = cli.main(["你好"])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "你好，我是模型" in captured.out
    assert "test-model" in captured.out
    assert "输入 31" in captured.out
    assert "推理 23" in captured.out


def test_cli_raw_output(capsys, monkeypatch):
    stub_result = ChatResult(
        content="hi",
        model="m",
        finish_reason="stop",
        usage=Usage(),
        raw={"id": "xyz", "model": "m"},
    )
    monkeypatch.setattr(cli.Settings, "load", _stub_load("sk-test"))
    monkeypatch.setattr(cli.LLMClient, "chat", lambda self, messages: stub_result)
    exit_code = cli.main(["你好", "--raw"])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert '"id": "xyz"' in captured.out


def test_cli_without_question(capsys):
    exit_code = cli.main([])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "交互模式" in captured.err + captured.out
