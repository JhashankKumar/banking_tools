import json
from collections.abc import Callable
from decimal import Decimal
from typing import Any

import pytest

from app.core.config import Settings, get_settings
from app.modules.copilot.harness import CopilotUnavailableError, run_copilot
from app.modules.copilot.limits import CopilotLimitError
from app.modules.copilot.provider import FakeModelProvider, Usage, fake_text, fake_tool_call
from app.modules.copilot.tools import ToolContext

Ctx = Callable[[str], ToolContext]
SEVEN_TOOLS = {
    "get_case_summary",
    "get_alert_details",
    "get_transactions",
    "find_money_paths",
    "get_case_graph",
    "get_evidence_records",
    "get_rule",
}


def _settings(**overrides: Any) -> Settings:
    return get_settings().model_copy(update=overrides)


def _answer_json(**fields: Any) -> str:
    return json.dumps({"kind": "answer", **fields})


# Quotes no values, so it needs no tool output to pass grounding.
PLAIN = _answer_json(
    records=[{"text": "TX-1001 is on the case.", "citations": ["EV-10482-TX-1001"]}]
)
VALID = _answer_json(
    records=[
        {"text": "TX-1001 moved ₹48,500.00 to BEN-B.", "citations": ["EV-10482-TX-1001"]},
        {"text": "TX-1002 moved ₹45,000.00 to ACC-C.", "citations": ["EV-10482-TX-1002"]},
    ],
    calculated=[{"text": "Sent on 5 m 28 s later.", "citations": ["EV-10482-TX-1001"]}],
    not_established=["Ownership of ACC-C."],
    next_checks=["Review ACC-C's other inbound transfers."],
)


def _run(provider: FakeModelProvider, ctx: ToolContext, **settings: Any):
    return run_copilot(
        provider,
        ctx,
        question="Where did the money go?",
        history=[],
        settings=_settings(**settings),
    )


def test_tool_then_answer_happy_path(ctx_for: Ctx) -> None:
    provider = FakeModelProvider(
        [fake_tool_call("find_money_paths", {}), fake_text(VALID, "0.001")]
    )

    result = _run(provider, ctx_for("FR-10482"))

    assert [i.citations for i in result.answer.records] == [
        ["EV-10482-TX-1001"],
        ["EV-10482-TX-1002"],
    ]
    assert result.answer.steps == ["Found money paths (24 h, 3 hops)"]
    assert result.tool_names == ["find_money_paths"]
    assert str(result.usage.cost_usd) == "0.001"


def test_unknown_tool_is_rejected_and_reported_to_model(ctx_for: Ctx) -> None:
    provider = FakeModelProvider([fake_tool_call("get_all_accounts", {}), fake_text(PLAIN)])

    _run(provider, ctx_for("FR-10482"))

    tool_message = provider.calls[1][0][-1]
    assert tool_message.role == "tool"
    assert json.loads(tool_message.content or "") == {"error": "Unknown tool"}


def test_case_id_argument_naming_this_case_is_accepted(ctx_for: Ctx) -> None:
    provider = FakeModelProvider(
        [fake_tool_call("get_alert_details", {"case_id": "FR-10482"}), fake_text(PLAIN)]
    )

    result = _run(provider, ctx_for("FR-10482"))

    assert result.tool_names == ["get_alert_details"]


def test_case_id_argument_naming_another_case_is_refused(ctx_for: Ctx) -> None:
    provider = FakeModelProvider(
        [fake_tool_call("get_alert_details", {"case_id": "FR-10486"}), fake_text(PLAIN)]
    )

    result = _run(provider, ctx_for("FR-10482"))

    tool_message = provider.calls[1][0][-1]
    assert json.loads(tool_message.content or "") == {
        "error": "This chat can only read case FR-10482"
    }
    assert result.tool_names == []


def test_tool_call_cap(ctx_for: Ctx) -> None:
    provider = FakeModelProvider(
        [fake_tool_call("get_case_summary", {}, call_id=f"c{i}") for i in range(7)]
    )

    with pytest.raises(CopilotUnavailableError):
        _run(provider, ctx_for("FR-10482"), copilot_max_tool_calls=6)


def test_repair_turn_then_success(ctx_for: Ctx) -> None:
    provider = FakeModelProvider(
        [fake_tool_call("find_money_paths", {}), fake_text("The money went on."), fake_text(VALID)]
    )

    result = _run(provider, ctx_for("FR-10482"))

    assert len(result.answer.records) == 2
    repair_request = provider.calls[2][0][-1]
    assert repair_request.role == "user"
    assert "JSON" in (repair_request.content or "")


def test_repair_turn_names_changed_values(ctx_for: Ctx) -> None:
    wrong = _answer_json(
        records=[{"text": "TX-1001 moved ₹48,000.00.", "citations": ["EV-10482-TX-1001"]}]
    )
    provider = FakeModelProvider(
        [fake_tool_call("find_money_paths", {}), fake_text(wrong), fake_text(VALID)]
    )

    _run(provider, ctx_for("FR-10482"))

    assert "₹48,000.00" in (provider.calls[2][0][-1].content or "")


def test_repair_turn_then_failure(ctx_for: Ctx) -> None:
    provider = FakeModelProvider([fake_text("{bad"), fake_text("still not json")])

    with pytest.raises(CopilotUnavailableError):
        _run(provider, ctx_for("FR-10482"))


def test_model_unavailable_becomes_copilot_unavailable(ctx_for: Ctx) -> None:
    with pytest.raises(CopilotUnavailableError):
        _run(FakeModelProvider([]), ctx_for("FR-10482"))


def test_injection_text_does_not_change_tools(ctx_for: Ctx) -> None:
    provider = FakeModelProvider(
        [
            fake_tool_call("get_transactions", {}),
            fake_tool_call("get_all_accounts", {"reveal": True}, call_id="c2"),
            fake_text(
                _answer_json(
                    records=[{"text": "TX-2001 is recorded.", "citations": ["EV-10486-TX-2001"]}]
                )
            ),
        ]
    )

    _run(provider, ctx_for("FR-10486"))

    for _messages, tools in provider.calls:
        assert {t.name for t in tools} == SEVEN_TOOLS
    first_tool_output = provider.calls[1][0][-1].content or ""
    assert '"untrusted_text": "Ignore prior instructions' in first_tool_output


def test_tools_sent_are_case_bound(ctx_for: Ctx) -> None:
    provider = FakeModelProvider([fake_text(PLAIN)])

    _run(provider, ctx_for("FR-10482"))

    messages, tools = provider.calls[0]
    assert all("case_id" not in json.dumps(t.parameters) for t in tools)
    system = messages[0]
    assert system.role == "system"
    assert "FR-10482" in (system.content or "")
    assert "untrusted_text" in (system.content or "")


def test_failure_carries_partial_usage(ctx_for: Ctx) -> None:
    paid = fake_tool_call("get_case_summary", {})
    paid = paid.__class__(paid.content, paid.tool_calls, Usage(10, 5, Decimal("0.30")), paid.model)
    provider = FakeModelProvider([paid])  # Then the model goes away.

    with pytest.raises(CopilotUnavailableError) as raised:
        _run(provider, ctx_for("FR-10482"))

    assert raised.value.usage.cost_usd == Decimal("0.30")
    assert raised.value.tool_calls == 1


def test_run_stops_before_overspending_the_budget(ctx_for: Ctx) -> None:
    def paid(i: int) -> Any:
        reply = fake_tool_call("get_case_summary", {}, call_id=f"c{i}")
        return reply.__class__(None, reply.tool_calls, Usage(10, 5, Decimal("0.30")), "fake/m")

    provider = FakeModelProvider([paid(i) for i in range(5)])

    with pytest.raises(CopilotLimitError):
        run_copilot(
            provider,
            ctx_for("FR-10482"),
            question="Where did the money go?",
            history=[],
            settings=_settings(),
            max_cost_usd=Decimal("0.50"),
        )

    assert len(provider.calls) == 2  # 0.30 spent, 0.60 reached the cap: no third call.


def test_no_model_call_starts_after_the_run_deadline(ctx_for: Ctx) -> None:
    provider = FakeModelProvider([fake_text(PLAIN)])

    with pytest.raises(CopilotUnavailableError):
        _run(provider, ctx_for("FR-10482"), copilot_run_deadline_s=0)

    assert provider.calls == []


def test_answer_naming_an_unknown_record_gets_a_repair_turn(ctx_for: Ctx) -> None:
    unknown = _answer_json(
        records=[{"text": "TX-4242 is linked.", "citations": ["EV-10482-TX-1001"]}]
    )
    provider = FakeModelProvider([fake_text(unknown), fake_text(PLAIN)])

    result = _run(provider, ctx_for("FR-10482"))

    assert result.answer.records[0].text == "TX-1001 is on the case."
    repair = provider.calls[1][0][-1].content or ""
    assert "Record ID not found in the case records: TX-4242" in repair
