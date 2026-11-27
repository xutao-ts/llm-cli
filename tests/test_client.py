"""客户端响应解析单测。"""

from __future__ import annotations

from llm_cli.client import LLMClient


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
    result = LLMClient._parse(_sample_response())

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
    result = LLMClient._parse(data)

    assert result.content == "ok"
    assert result.usage.total_tokens == 0
    assert result.usage.reasoning_tokens == 0
