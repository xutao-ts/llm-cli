"""客户端响应解析单测。"""

from __future__ import annotations

import asyncio

from llm_cli import client as client_module
from llm_cli.client import (
    LLMClient,
    Message,
    _build_payload,
    _parse_response,
    _parse_stream_line,
)


def _sample_response() -> dict:
    return {
        "choices": [
            {
                "finish_reason": "stop",
                "index": 0,
                "message": {
                    "content": "你好！很高兴见到你。",
                    "reasoning_content": "用户用中文打招呼，应中文回复。",
                    "role": "assistant",
                },
            }
        ],
        "created": 1795750138,
        "id": "resp-123",
        "model": "deepseek-v4-flash",
        "object": "chat.completion",
        "usage": {
            "completion_tokens": 60,
            "prompt_tokens": 31,
            "total_tokens": 91,
            "completion_tokens_details": {"reasoning_tokens": 23},
        },
    }


def test_parse_extracts_content_and_usage():
    result = _parse_response(_sample_response())

    assert result.content == "你好！很高兴见到你。"
    assert result.model == "deepseek-v4-flash"
    assert result.finish_reason == "stop"
    assert result.usage.prompt_tokens == 31
    assert result.usage.completion_tokens == 60
    assert result.usage.total_tokens == 91
    assert result.usage.reasoning_tokens == 23
    assert result.raw["id"] == "resp-123"


def test_parse_missing_usage_defaults_to_zero():
    data = {"choices": [{"message": {"content": "ok"}, "finish_reason": "stop"}]}
    result = _parse_response(data)

    assert result.content == "ok"
    assert result.usage.total_tokens == 0
    assert result.usage.reasoning_tokens == 0
    assert result.reasoning == ""


def test_parse_extracts_reasoning_content():
    result = _parse_response(_sample_response())

    assert result.reasoning == "用户用中文打招呼，应中文回复。"


def test_build_payload_only_adds_thinking_when_given():
    messages = [Message(role="user", content="hi")]

    assert "thinking" not in _build_payload("m", messages)
    assert _build_payload("m", messages, "disabled")["thinking"] == {"type": "disabled"}
    assert _build_payload("m", messages, "auto")["thinking"] == {"type": "auto"}


def test_gather_chats_returns_results_in_order_without_raising(monkeypatch):
    from llm_cli.client import ChatResult, Usage

    client = LLMClient(api_key="sk-test", base_url="https://example.com/v1", model="m", timeout=5.0)

    def _result(content: str) -> ChatResult:
        return ChatResult(content=content, model="m", finish_reason="stop", usage=Usage(), raw={})

    async def mixed(messages: list[Message]):
        if messages[0].content == "第二题":
            raise RuntimeError("boom")
        return _result(messages[0].content)

    monkeypatch.setattr(client, "async_chat", mixed)
    items = [
        ("a", [Message(role="user", content="第一题")]),
        ("b", [Message(role="user", content="第二题")]),
    ]

    results = asyncio.run(LLMClient.gather_chats(client, items))

    assert [label for label, _ in results] == ["a", "b"]
    assert results[0][1].content == "第一题"
    assert isinstance(results[1][1], RuntimeError)
    assert "boom" in str(results[1][1])


def test_parse_stream_line_ignores_non_data_lines():
    assert _parse_stream_line("") is None
    assert _parse_stream_line(": keep-alive") is None
    assert _parse_stream_line("event: message") is None
    assert _parse_stream_line('data: {"id": "abc"}') == {"id": "abc"}


def test_chat_stream_yields_deltas_and_usage(monkeypatch):
    lines = [
        'data: {"model": "m", "choices": [{"delta": {"content": "你"}}]}',
        "",
        'data: {"model": "m", "choices": [{"delta": {"content": "好"}, "finish_reason": "stop"}]}',
        'data: {"model": "m", "choices": [], "usage": {'
        '"prompt_tokens": 3, "completion_tokens": 2, "total_tokens": 5}}',
        "data: [DONE]",
    ]

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def raise_for_status(self):
            pass

        def iter_lines(self):
            return iter(lines)

    monkeypatch.setattr(client_module.httpx, "stream", lambda *a, **kw: FakeResponse())
    client = LLMClient(api_key="sk-test", base_url="https://example.com/v1", model="m", timeout=5.0)

    chunks = list(client.chat_stream([Message(role="user", content="你好")]))

    assert "".join(c.delta for c in chunks) == "你好"
    assert chunks[-2].finish_reason == "stop"
    assert chunks[-1].usage.total_tokens == 5
