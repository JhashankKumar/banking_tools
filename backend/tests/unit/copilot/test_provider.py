from decimal import Decimal

import pytest

from app.modules.copilot.provider import (
    ChatMessage,
    FakeModelProvider,
    ModelUnavailableError,
    ToolSpec,
    fake_text,
    fake_tool_call,
)

TOOLS = [ToolSpec(name="get_case_summary", description="Case summary", parameters={})]


def test_fake_provider_returns_replies_in_order_and_records_calls() -> None:
    provider = FakeModelProvider([fake_tool_call("get_case_summary", {}), fake_text("{}", "0.01")])
    messages = [ChatMessage(role="user", content="Why did the alert fire?")]

    first = provider.complete(messages, TOOLS)
    second = provider.complete(messages, TOOLS)

    assert [c.name for c in first.tool_calls] == ["get_case_summary"]
    assert first.content is None
    assert second.content == "{}"
    assert second.usage.cost_usd == Decimal("0.01")
    assert len(provider.calls) == 2
    assert provider.calls[0][0][0].content == "Why did the alert fire?"
    assert [t.name for t in provider.calls[0][1]] == ["get_case_summary"]


def test_fake_provider_exhausted_raises_unavailable() -> None:
    provider = FakeModelProvider([])

    with pytest.raises(ModelUnavailableError):
        provider.complete([ChatMessage(role="user", content="hi")], TOOLS)
