"""The model provider contract (docs/project/AI_AGENT_AND_SECURITY.md "Model provider").

The application depends on `ModelProvider` only; OpenRouter is one implementation and
`FakeModelProvider` replays scripted replies so tests need no key, network, or spend.
"""

import json
from collections.abc import Sequence
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Literal, Protocol


@dataclass(frozen=True)
class ToolCall:
    id: str
    name: str
    arguments: str  # Raw JSON text from the model; parsed and validated by the harness.


@dataclass(frozen=True)
class ChatMessage:
    role: Literal["system", "user", "assistant", "tool"]
    content: str | None
    tool_call_id: str | None = None
    tool_calls: list[ToolCall] = field(default_factory=lambda: [])


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    parameters: dict[str, Any]  # JSON Schema of the arguments.


@dataclass(frozen=True)
class Usage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost_usd: Decimal = Decimal("0")


@dataclass(frozen=True)
class ModelReply:
    content: str | None
    tool_calls: list[ToolCall]
    usage: Usage
    model: str


class ModelUnavailableError(Exception):
    """The model could not be reached or answered unusably. The message never contains secrets."""


class ModelProvider(Protocol):
    def complete(
        self, messages: Sequence[ChatMessage], tools: Sequence[ToolSpec]
    ) -> ModelReply: ...


class FakeModelProvider:
    """Replays scripted replies in order and records what it was sent."""

    def __init__(self, replies: Sequence[ModelReply]) -> None:
        self._replies = list(replies)
        self.calls: list[tuple[list[ChatMessage], list[ToolSpec]]] = []

    def complete(self, messages: Sequence[ChatMessage], tools: Sequence[ToolSpec]) -> ModelReply:
        self.calls.append((list(messages), list(tools)))
        if not self._replies:
            raise ModelUnavailableError("No scripted reply left")
        return self._replies.pop(0)


def fake_text(content: str, cost: str = "0") -> ModelReply:
    return ModelReply(
        content=content, tool_calls=[], usage=Usage(10, 10, Decimal(cost)), model="fake/model"
    )


def fake_tool_call(name: str, args: dict[str, Any], call_id: str = "call_1") -> ModelReply:
    return ModelReply(
        content=None,
        tool_calls=[ToolCall(id=call_id, name=name, arguments=json.dumps(args))],
        usage=Usage(10, 5, Decimal("0")),
        model="fake/model",
    )


def get_model_provider() -> ModelProvider | None:
    """FastAPI dependency: the configured OpenRouter provider, or None without a key (the
    copilot then answers 503 while declines and chat history keep working). Tests override it.
    """
    from app.core.config import get_settings
    from app.modules.copilot.openrouter import OpenRouterModelProvider

    settings = get_settings()
    if settings.openrouter_api_key is None:
        return None
    return OpenRouterModelProvider(
        settings.openrouter_api_key,
        settings.openrouter_model,
        fallback_cost_per_1k=settings.copilot_fallback_cost_per_1k_tokens,
    )
