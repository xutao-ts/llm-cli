"""CLI 入口单测。"""

from __future__ import annotations

import re

from llm_cli import cli
from llm_cli.client import ChatResult, Message, StreamChunk, Usage
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
    monkeypatch.setattr(cli.LLMClient, "chat", lambda self, messages, thinking=None: stub_result)
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
    monkeypatch.setattr(cli.LLMClient, "chat", lambda self, messages, thinking=None: stub_result)
    exit_code = cli.main(["你好", "--raw"])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert '"id": "xyz"' in captured.out


def test_cli_without_question_enters_chat_mode(capsys, monkeypatch):
    monkeypatch.setattr(cli.Settings, "load", _stub_load("sk-test"))

    def fake_input(prompt=""):
        raise EOFError

    monkeypatch.setattr("builtins.input", fake_input)

    exit_code = cli.main([])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "交互模式" in captured.err + captured.out


def test_cli_chat_mode_keeps_history(capsys, monkeypatch):
    calls: list[list[Message]] = []
    replies = iter(["第一轮回复", "第二轮回复"])

    def fake_chat(self, messages, thinking=None):
        calls.append(list(messages))
        return ChatResult(
            content=next(replies),
            model="m",
            finish_reason="stop",
            usage=Usage(),
            raw={},
        )

    inputs = iter(["第一问", "第二问", "/exit"])
    monkeypatch.setattr(cli.Settings, "load", _stub_load("sk-test"))
    monkeypatch.setattr(cli.LLMClient, "chat", fake_chat)
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

    assert cli.main([]) == 0

    assert len(calls) == 2
    assert [(m.role, m.content) for m in calls[1]] == [
        ("user", "第一问"),
        ("assistant", "第一轮回复"),
        ("user", "第二问"),
    ]
    out = capsys.readouterr().out
    assert "第一轮回复" in out
    assert "第二轮回复" in out


def test_cli_chat_mode_clear_resets_history(capsys, monkeypatch):
    calls: list[list[Message]] = []

    def fake_chat(self, messages, thinking=None):
        calls.append(list(messages))
        return ChatResult(content="ok", model="m", finish_reason="stop", usage=Usage(), raw={})

    inputs = iter(["问一", "/clear", "问二", "/exit"])
    monkeypatch.setattr(cli.Settings, "load", _stub_load("sk-test"))
    monkeypatch.setattr(cli.LLMClient, "chat", fake_chat)
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

    assert cli.main([]) == 0
    assert [(m.role, m.content) for m in calls[1]] == [("user", "问二")]
    assert "已清空对话上下文。" in capsys.readouterr().out


def test_cli_chat_mode_failed_turn_not_added_to_history(capsys, monkeypatch):
    calls: list[list[Message]] = []
    responses = iter([RuntimeError("boom"), "ok"])

    def fake_chat(self, messages, thinking=None):
        calls.append(list(messages))
        item = next(responses)
        if isinstance(item, Exception):
            raise item
        return ChatResult(content=item, model="m", finish_reason="stop", usage=Usage(), raw={})

    inputs = iter(["失败的问题", "重试的问题", "/exit"])
    monkeypatch.setattr(cli.Settings, "load", _stub_load("sk-test"))
    monkeypatch.setattr(cli.LLMClient, "chat", fake_chat)
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

    assert cli.main([]) == 0
    assert [(m.role, m.content) for m in calls[1]] == [("user", "重试的问题")]


def test_cli_chat_mode_stream(capsys, monkeypatch):
    chunks = [StreamChunk(delta="流式回复", model="m")]
    inputs = iter(["你好", "/exit"])
    monkeypatch.setattr(cli.Settings, "load", _stub_load("sk-test"))
    monkeypatch.setattr(
        cli.LLMClient,
        "chat_stream",
        lambda self, messages, thinking=None: iter(chunks),
    )
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

    assert cli.main(["--stream"]) == 0
    out = capsys.readouterr().out
    assert "流式回复" in out
    assert "已退出交互模式。" in out


def test_cli_logs_carry_request_id(monkeypatch):
    stub_result = ChatResult(
        content="hi",
        model="m",
        finish_reason="stop",
        usage=Usage(),
        raw={},
    )
    records: list[str] = []

    class RecordingLogger:
        def info(self, msg: str, *args):
            records.append(msg % args)

        def error(self, msg: str, *args):
            records.append(msg % args)

    monkeypatch.setattr(cli.Settings, "load", _stub_load("sk-test"))
    monkeypatch.setattr(cli.LLMClient, "chat", lambda self, messages, thinking=None: stub_result)
    monkeypatch.setattr(cli, "setup_logger", lambda *_a, **_k: RecordingLogger())

    cli.main(["你好"])
    joined = "\n".join(records)
    # 日志中应出现形如 [7d1c18af] 的 8 位十六进制请求标识
    assert re.search(r"\[[0-9a-f]{8}\]", joined)


def test_cli_stream_prints_incrementally(capsys, monkeypatch):
    chunks = [
        StreamChunk(delta="你好", model="test-model"),
        StreamChunk(delta="，世界", model="test-model"),
        StreamChunk(
            finish_reason="stop",
            model="test-model",
            usage=Usage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
        ),
    ]
    monkeypatch.setattr(cli.Settings, "load", _stub_load("sk-test"))
    monkeypatch.setattr(
        cli.LLMClient, "chat_stream", lambda self, messages, thinking=None: iter(chunks)
    )

    exit_code = cli.main(["你好", "--stream"])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "你好，世界" in captured.out
    assert "输入 10" in captured.out
    assert "合计 15" in captured.out


def test_cli_stream_raw_output(capsys, monkeypatch):
    chunks = [StreamChunk(delta="hi", model="m", raw={"id": "xyz"})]
    monkeypatch.setattr(cli.Settings, "load", _stub_load("sk-test"))
    monkeypatch.setattr(
        cli.LLMClient, "chat_stream", lambda self, messages, thinking=None: iter(chunks)
    )

    exit_code = cli.main(["你好", "--stream", "--raw"])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert '"id": "xyz"' in captured.out


def test_cli_stream_error_returns_nonzero(capsys, monkeypatch):
    def _broken(self, messages, thinking=None):
        raise RuntimeError("boom")

    monkeypatch.setattr(cli.Settings, "load", _stub_load("sk-test"))
    monkeypatch.setattr(cli.LLMClient, "chat_stream", _broken)

    exit_code = cli.main(["你好", "--stream"])
    assert exit_code == 1


def test_cli_passes_thinking_option(capsys, monkeypatch):
    seen: dict = {}
    stub_result = ChatResult(content="hi", model="m", finish_reason="stop", usage=Usage(), raw={})

    def fake_chat(self, messages, thinking=None):
        seen["thinking"] = thinking
        return stub_result

    def fake_stream(self, messages, thinking=None):
        seen["thinking"] = thinking
        return iter([StreamChunk(delta="hi", model="m")])

    monkeypatch.setattr(cli.Settings, "load", _stub_load("sk-test"))
    monkeypatch.setattr(cli.LLMClient, "chat", fake_chat)
    monkeypatch.setattr(cli.LLMClient, "chat_stream", fake_stream)

    assert cli.main(["你好", "--thinking", "disabled"]) == 0
    assert seen["thinking"] == "disabled"

    assert cli.main(["你好", "--stream", "--thinking", "enabled"]) == 0
    assert seen["thinking"] == "enabled"


def test_cli_show_reasoning_non_stream(capsys, monkeypatch):
    stub_result = ChatResult(
        content="答案是 2",
        model="m",
        finish_reason="stop",
        usage=Usage(reasoning_tokens=5),
        reasoning="先算 1+1。",
        raw={},
    )
    monkeypatch.setattr(cli.Settings, "load", _stub_load("sk-test"))
    monkeypatch.setattr(cli.LLMClient, "chat", lambda self, messages, thinking=None: stub_result)

    assert cli.main(["1+1", "--show-reasoning"]) == 0
    out = capsys.readouterr().out
    assert "[思考]" in out
    assert "先算 1+1。" in out

    assert cli.main(["1+1"]) == 0
    assert "先算 1+1。" not in capsys.readouterr().out


def test_cli_stream_show_reasoning(capsys, monkeypatch):
    chunks = [
        StreamChunk(reasoning="想一想", model="m"),
        StreamChunk(delta="答案", model="m"),
        StreamChunk(finish_reason="stop", model="m"),
    ]
    monkeypatch.setattr(cli.Settings, "load", _stub_load("sk-test"))
    monkeypatch.setattr(
        cli.LLMClient,
        "chat_stream",
        lambda self, messages, thinking=None: iter(chunks),
    )

    assert cli.main(["你好", "--stream", "--show-reasoning"]) == 0
    out = capsys.readouterr().out
    assert "[思考] 想一想" in out
    assert "答案" in out


def test_cli_help_lists_all_options(capsys):
    parser = cli.build_parser()
    help_text = parser.format_help()
    for option in (
        "--model",
        "--stream",
        "--thinking",
        "--show-reasoning",
        "--debug",
        "--raw",
        "question",
    ):
        assert option in help_text
