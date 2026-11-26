"""模型调用封装（预留）。

阶段 0 先定义接口与数据结构，具体 HTTP 调用在后续周次接入。
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Message:
    role: str
    content: str


class LLMClient:
    """OpenAI 兼容协议客户端的占位实现。"""

    def __init__(self, api_key: str | None, base_url: str, model: str, timeout: float):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    def chat(self, _messages: list[Message]) -> str:
        """同步对话接口，后续接入真实请求。"""
        raise NotImplementedError("模型调用将在后续周次实现")
