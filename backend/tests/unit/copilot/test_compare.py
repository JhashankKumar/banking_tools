import json
from collections.abc import Callable
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.modules.copilot import compare
from app.modules.copilot.provider import (
    FakeModelProvider,
    ModelProvider,
    ModelReply,
    ToolCall,
    Usage,
    fake_text,
)
from app.modules.copilot.tools import ToolContext

Ctx = Callable[[str], ToolContext]
PLAIN = json.dumps(
    {"kind": "answer", "records": [{"text": "On the case.", "citations": ["EV-10482-TX-1001"]}]}
)


def _always(reply_cost: str) -> Callable[[str], ModelProvider]:
    return lambda _model: FakeModelProvider([fake_text(PLAIN, reply_cost)] * 20)


def test_comparison_stops_at_cost_cap(db_session: Session, ctx_for: Ctx) -> None:
    user = ctx_for("FR-10482").user

    rows = compare.run_comparison(
        db_session,
        user,
        models=["a/one", "b/two"],
        provider_for=_always("0.40"),
        settings=get_settings(),
        cap_usd=Decimal("1.00"),
    )

    assert [r.model for r in rows] == ["a/one", "a/one", "a/one"]
    assert all(r.outcome == "answered" for r in rows)
    assert sum((r.cost_usd for r in rows), Decimal("0")) == Decimal("1.20")


def test_failed_runs_still_count_their_cost(db_session: Session, ctx_for: Ctx) -> None:
    user = ctx_for("FR-10482").user

    def flaky(_model: str) -> ModelProvider:
        # One paid tool round, then the model goes away: the run fails but was not free.
        paid_tool_round = ModelReply(
            content=None,
            tool_calls=[ToolCall(id="c1", name="get_case_summary", arguments="{}")],
            usage=Usage(10, 5, Decimal("0.30")),
            model="fake/model",
        )
        return FakeModelProvider([paid_tool_round])

    rows = compare.run_comparison(
        db_session,
        user,
        models=["a/one"],
        provider_for=flaky,
        settings=get_settings(),
        cap_usd=Decimal("0.50"),
    )

    assert [r.outcome for r in rows] == ["failed", "failed"]
    assert [r.cost_usd for r in rows] == [Decimal("0.30"), Decimal("0.30")]


def test_main_refuses_without_key(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(
        compare,
        "get_settings",
        lambda: get_settings().model_copy(update={"openrouter_api_key": None}),
    )

    with pytest.raises(SystemExit) as exited:
        compare.main(["--models", "a/one"])

    assert exited.value.code == 2
    assert "OPENROUTER_API_KEY" in capsys.readouterr().err
