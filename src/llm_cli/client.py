"""模型调用封装：OpenAI 兼容协议的同步非流式对话。"""

from __future__ import annotations

from dataclasses import dataclass, field

import httpx


@dataclass(frozen=True)
class Message:
    role: str
    content: str


@dataclass(frozen=True)
class Usage:
    """token 用量统计。"""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    reasoning_tokens: int = 0


@dataclass(frozen=True)
class ChatResult:
    """一次对话的解析结果。"""

    content: str
    model: str
    finish_reason: str | None
    usage: Usage
    raw: dict = field(default_factory=dict)


class LLMClient:
    """OpenAI 兼容协议客户端（非流式）。"""

    def __init__(self, api_key: str | None, base_url: str, model: str, timeout: float):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    def chat(self, messages: list[Message]) -> ChatResult:
        """发起一次对话请求，返回解析后的结构化结果。"""
        if not self.api_key:
            raise RuntimeError("缺少 API Key，无法调用模型")

        payload = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
        }

        try:
            response = httpx.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise RuntimeError(f"模型请求超时（{self.timeout}s）") from exc
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(
                f"模型接口返回 {exc.response.status_code}：{exc.response.text}"
            ) from exc
        except httpx.HTTPError as exc:
            raise RuntimeError(f"模型请求失败：{exc}") from exc

        try:
            data = response.json()
            return self._parse(data)
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise RuntimeError(f"模型响应格式异常：{response.text}") from exc

    @staticmethod
    def _parse(data: dict) -> ChatResult:
        """从 Chat Completions 响应中提取回复正文与用量。"""
        choice = data["choices"][0]
        message = choice["message"]
        content = message.get("content") or ""

        usage_raw = data.get("usage") or {}
        completion_details = usage_raw.get("completion_tokens_details") or {}
        usage = Usage(
            prompt_tokens=int(usage_raw.get("prompt_tokens", 0)),
            completion_tokens=int(usage_raw.get("completion_tokens", 0)),
            total_tokens=int(usage_raw.get("total_tokens", 0)),
            reasoning_tokens=int(completion_details.get("reasoning_tokens", 0)),
        )

        return ChatResult(
            content=content,
            model=data.get("model", ""),
            finish_reason=choice.get("finish_reason"),
            usage=usage,
            raw=data,
        )
