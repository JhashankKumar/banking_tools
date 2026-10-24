import json
from decimal import Decimal
from typing import Any

import httpx
import pytest
from pydantic import SecretStr

from app.core.config import Settings
from app.modules.copilot.openrouter import OpenRouterModelProvider
from app.modules.copilot.provider import ChatMessage, ModelUnavailableError, ToolSpec

KEY = SecretStr("test-key-not-real-0000")
TOOLS = [
    ToolSpec(
        name="find_money_paths",
        description="Money paths for the case",
        parameters={"type": "object", "properties": {"max_hops": {"type": "integer"}}},
    )
]
MESSAGES = [ChatMessage(role="user", content="Where did the money go?")]


def _provider(handler: Any) -> OpenRouterModelProvider:
    return OpenRouterModelProvider(KEY, "vendor/model", transport=httpx.MockTransport(handler))


def _reply(message: dict[str, Any], usage: dict[str, Any]) -> httpx.Response:
    return httpx.Response(
        200, json={"model": "vendor/model", "choices": [{"message": message}], "usage": usage}
    )


def test_openrouter_request_shape() -> None:
    seen: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["auth"] = request.headers["Authorization"]
        seen["body"] = json.loads(request.content)
        return _reply({"content": "{}"}, {"prompt_tokens": 1, "completion_tokens": 1})

    _provider(handler).complete(MESSAGES, TOOLS)

    assert seen["url"] == "https://openrouter.ai/api/v1/chat/completions"
    assert seen["auth"] == "Bearer test-key-not-real-0000"
    body = seen["body"]
    assert body["model"] == "vendor/model"
    assert body["messages"] == [{"role": "user", "content": "Where did the money go?"}]
    assert body["tools"] == [
        {
            "type": "function",
            "function": {
                "name": "find_money_paths",
                "description": "Money paths for the case",
                "parameters": TOOLS[0].parameters,
            },
        }
    ]
    assert body["usage"] == {"include": True}
    assert body["provider"] == {"data_collection": "deny"}


def test_openrouter_parses_tool_calls_and_usage() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return _reply(
            {
                "content": None,
                "tool_calls": [
                    {
                        "id": "call_1",
                        "type": "function",
                        "function": {"name": "find_money_paths", "arguments": '{"max_hops": 3}'},
                    }
                ],
            },
            {"prompt_tokens": 120, "completion_tokens": 30, "cost": 0.00042},
        )

    reply = _provider(handler).complete(MESSAGES, TOOLS)

    assert reply.content is None
    assert [(c.id, c.name, c.arguments) for c in reply.tool_calls] == [
        ("call_1", "find_money_paths", '{"max_hops": 3}')
    ]
    assert (reply.usage.prompt_tokens, reply.usage.completion_tokens) == (120, 30)
    assert reply.usage.cost_usd == Decimal("0.00042")
    assert reply.model == "vendor/model"


def test_openrouter_missing_cost_uses_fallback_rate() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return _reply({"content": "{}"}, {"prompt_tokens": 600, "completion_tokens": 400})

    reply = _provider(handler).complete(MESSAGES, TOOLS)

    # 1,000 tokens at the default fallback of 0.002 USD per 1k tokens.
    assert reply.usage.cost_usd == Decimal("0.002")


def test_openrouter_http_error_raises_unavailable_without_key_in_message() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"error": {"message": "upstream failed"}})

    with pytest.raises(ModelUnavailableError) as raised:
        _provider(handler).complete(MESSAGES, TOOLS)

    assert "test-key-not-real" not in str(raised.value)


def test_openrouter_timeout_raises_unavailable() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("slow", request=request)

    with pytest.raises(ModelUnavailableError):
        _provider(handler).complete(MESSAGES, TOOLS)


def test_settings_read_openrouter_names_without_prefix(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENROUTER_MODEL", "x/y")
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test-placeholder")

    settings = Settings()  # pyright: ignore[reportCallIssue]

    assert settings.openrouter_model == "x/y"
    assert settings.openrouter_api_key is not None
    assert settings.openrouter_api_key.get_secret_value() == "sk-test-placeholder"
    assert settings.copilot_daily_budget_usd == Decimal("2.00")
    assert settings.copilot_questions_per_hour == 20
    assert settings.copilot_max_tool_calls == 6
