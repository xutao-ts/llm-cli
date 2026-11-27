"""模型调用封装：OpenAI 兼容协议的同步 / 异步非流式对话。"""

from __future__ import annotations

import asyncio
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


def _build_payload(model: str, messages: list[Message]) -> dict:
    return {
        "model": model,
        "messages": [{"role": m.role, "content": m.content} for m in messages],
    }


def _parse_response(data: dict) -> ChatResult:
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


class LLMClient:
    """OpenAI 兼容协议客户端（非流式，支持同步与异步）。"""

    def __init__(self, api_key: str | None, base_url: str, model: str, timeout: float):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    def _ensure_key(self) -> None:
        if not self.api_key:
            raise RuntimeError("缺少 API Key，无法调用模型")

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}"}

    def chat(self, messages: list[Message]) -> ChatResult:
        """发起一次同步对话请求，返回解析后的结构化结果。"""
        self._ensure_key()

        try:
            response = httpx.post(
                f"{self.base_url}/chat/completions",
                headers=self._headers(),
                json=_build_payload(self.model, messages),
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
            return _parse_response(response.json())
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise RuntimeError(f"模型响应格式异常：{response.text}") from exc

    async def async_chat(self, messages: list[Message]) -> ChatResult:
        """发起一次异步对话请求，供 asyncio 并发场景调用。"""
        self._ensure_key()

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self._headers(),
                    json=_build_payload(self.model, messages),
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
            return _parse_response(response.json())
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise RuntimeError(f"模型响应格式异常：{response.text}") from exc

    @staticmethod
    async def gather_chats(
        client: LLMClient,
        items: list[tuple[str, list[Message]]],
    ) -> list[tuple[str, ChatResult | RuntimeError]]:
        """并发执行多条对话，按入参顺序返回结果。

        Args:
            client: 复用同一个客户端实例。
            items: 每项为 ``(请求标识, messages)``，标识用于结果归属。

        Returns:
            与入参同序的列表；成功项为 ``(标识, ChatResult)``，
            失败项为 ``(标识, RuntimeError)``，不抛出未捕获异常。
        """
        labels = [label for label, _ in items]
        coros = [client.async_chat(messages) for _, messages in items]
        results = await asyncio.gather(*coros, return_exceptions=True)

        output: list[tuple[str, ChatResult | RuntimeError]] = []
        for label, result in zip(labels, results, strict=False):
            if isinstance(result, Exception):
                output.append((label, RuntimeError(str(result))))
            else:
                output.append((label, result))
        return output
