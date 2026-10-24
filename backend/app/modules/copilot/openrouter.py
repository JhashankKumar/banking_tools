"""OpenRouter chat-completions adapter (OpenAI-compatible API, open-weight models only)."""

import logging
from collections.abc import Sequence
from decimal import Decimal, InvalidOperation
from typing import Any

import httpx
from pydantic import SecretStr

from app.modules.copilot.provider import (
    ChatMessage,
    ModelReply,
    ModelUnavailableError,
    ToolCall,
    ToolSpec,
    Usage,
)

URL = "https://openrouter.ai/api/v1/chat/completions"
logger = logging.getLogger(__name__)


def _message(m: ChatMessage) -> dict[str, Any]:
    out: dict[str, Any] = {"role": m.role, "content": m.content}
    if m.tool_call_id is not None:
        out["tool_call_id"] = m.tool_call_id
    if m.tool_calls:
        out["tool_calls"] = [
            {"id": c.id, "type": "function", "function": {"name": c.name, "arguments": c.arguments}}
            for c in m.tool_calls
        ]
    return out


def _tool(t: ToolSpec) -> dict[str, Any]:
    return {
        "type": "function",
        "function": {"name": t.name, "description": t.description, "parameters": t.parameters},
    }


class OpenRouterModelProvider:
    def __init__(
        self,
        api_key: SecretStr,
        model: str,
        *,
        timeout_s: float = 30.0,
        fallback_cost_per_1k: Decimal = Decimal("0.002"),
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._timeout_s = timeout_s
        self._fallback_cost_per_1k = fallback_cost_per_1k
        self._transport = transport

    def complete(self, messages: Sequence[ChatMessage], tools: Sequence[ToolSpec]) -> ModelReply:
        body: dict[str, Any] = {
            "model": self._model,
            "messages": [_message(m) for m in messages],
            "tools": [_tool(t) for t in tools],
            "usage": {"include": True},
            # Route only to endpoints that do not retain or train on request data.
            "provider": {"data_collection": "deny"},
        }
        headers = {"Authorization": f"Bearer {self._api_key.get_secret_value()}"}
        try:
            with httpx.Client(timeout=self._timeout_s, transport=self._transport) as client:
                response = client.post(URL, json=body, headers=headers)
        except httpx.HTTPError as error:
            # Type only: the request (and its Authorization header) is never logged.
            logger.warning("Model request failed: %s", type(error).__name__)
            raise ModelUnavailableError("The model could not be reached") from None
        if response.status_code != 200:
            logger.warning("Model returned HTTP %s", response.status_code)
            raise ModelUnavailableError(f"The model returned HTTP {response.status_code}")
        return self._parse(response)

    def _parse(self, response: httpx.Response) -> ModelReply:
        try:
            payload: dict[str, Any] = response.json()
            message: dict[str, Any] = payload["choices"][0]["message"]
            raw_calls: list[dict[str, Any]] = message.get("tool_calls") or []
            calls = [
                ToolCall(
                    id=str(c["id"]),
                    name=str(c["function"]["name"]),
                    arguments=str(c["function"].get("arguments") or "{}"),
                )
                for c in raw_calls
            ]
            usage: dict[str, Any] = payload.get("usage") or {}
            prompt = int(usage.get("prompt_tokens") or 0)
            completion = int(usage.get("completion_tokens") or 0)
        except (ValueError, KeyError, IndexError, TypeError):
            raise ModelUnavailableError("The model returned an unreadable response") from None
        return ModelReply(
            content=message.get("content"),
            tool_calls=calls,
            usage=Usage(prompt, completion, self._cost(usage.get("cost"), prompt + completion)),
            model=str(payload.get("model") or self._model),
        )

    def _cost(self, reported: object, tokens: int) -> Decimal:
        if reported is not None:
            try:
                return Decimal(str(reported))
            except InvalidOperation:
                pass
        return self._fallback_cost_per_1k * tokens / 1000
