import json
from decimal import Decimal
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.modules.audit.models import AuditEvent
from app.modules.copilot.models import CopilotRun, RunOutcome
from app.modules.copilot.provider import (
    FakeModelProvider,
    ModelReply,
    Usage,
    fake_text,
    fake_tool_call,
    get_model_provider,
)
from app.modules.users.models import Role, User
from app.seed import seed
from tests.factories import assert_error, signed_in

ASK = "/api/v1/cases/FR-10482/copilot/questions"
CHATS = "/api/v1/cases/FR-10482/chats"
ANSWER = json.dumps(
    {
        "kind": "answer",
        "records": [{"text": "TX-1001 moved ₹48,500.00.", "citations": ["EV-10482-TX-1001"]}],
        "not_established": ["Ownership of ACC-C."],
    }
)


@pytest.fixture(autouse=True)
def seeded(db_session: Session) -> None:
    seed(db_session, demo_password="seed-password-for-tests")
    db_session.commit()


@pytest.fixture
def script(app: FastAPI) -> Any:
    """Installs a fake model for the request; returns it so tests can inspect its calls."""

    def install(*replies: ModelReply) -> FakeModelProvider:
        provider = FakeModelProvider(replies)
        app.dependency_overrides[get_model_provider] = lambda: provider
        return provider

    return install


@pytest.fixture
def analyst(client: TestClient, db_session: Session) -> dict[str, str]:
    return signed_in(client, db_session, Role.ANALYST)


def ask(client: TestClient, headers: dict[str, str], question: str, chat_id: str | None = None):
    return client.post(ASK, json={"chat_id": chat_id, "question": question}, headers=headers)


def money_answer(script: Any) -> FakeModelProvider:
    return script(fake_tool_call("find_money_paths", {}), fake_text(ANSWER, "0.0005"))


def test_ask_creates_chat_and_cited_answer(
    client: TestClient, db_session: Session, analyst: dict[str, str], script: Any
) -> None:
    money_answer(script)

    response = ask(client, analyst, "Where did the money go after ACC-001?")

    assert response.status_code == 200, response.text
    body = response.json()["data"]
    assert body["chat"]["title"] == "Where did the money go after ACC-001?"
    assert body["chat"]["is_own"] is True
    answer = body["message"]["answer"]
    assert answer["records"][0]["citations"] == ["EV-10482-TX-1001"]
    assert answer["steps"] == ["Found money paths (24 h, 3 hops)"]
    event = db_session.scalars(select(AuditEvent).where(AuditEvent.action == "copilot.asked")).one()
    assert event.details["tools"] == "find_money_paths"
    assert event.details["cost_usd"] == "0.000500"
    assert "where did the money go" not in json.dumps(event.details).lower()
    assert "48,500" not in json.dumps(event.details)


def test_chat_title_is_first_60_characters(
    client: TestClient, analyst: dict[str, str], script: Any
) -> None:
    money_answer(script)
    question = "Where did the money go? " * 5

    title = ask(client, analyst, question).json()["data"]["chat"]["title"]

    assert title == question.strip()[:60]


def test_follow_up_sends_history(client: TestClient, analyst: dict[str, str], script: Any) -> None:
    money_answer(script)
    chat_id = ask(client, analyst, "Where did the money go?").json()["data"]["chat"]["id"]
    provider = script(fake_text(json.dumps({"kind": "answer", "not_established": ["Intent."]})))

    response = ask(client, analyst, "And what is not established?", chat_id)

    assert response.status_code == 200, response.text
    sent = [m.content or "" for m in provider.calls[0][0]]
    assert "Where did the money go?" in sent
    assert any("EV-10482-TX-1001" in m for m in sent)
    assert sent[-1] == "And what is not established?"


def test_customer_info_question_declined_without_model_call(
    client: TestClient, db_session: Session, analyst: dict[str, str], script: Any
) -> None:
    provider = script()

    response = ask(client, analyst, "What is the phone number of the person behind ACC-001?")

    assert response.status_code == 200
    assert response.json()["data"]["message"]["answer"]["kind"] == "decline"
    assert provider.calls == []
    assert db_session.scalars(
        select(AuditEvent.action).where(AuditEvent.action == "copilot.declined")
    ).one()
    assert db_session.scalars(select(CopilotRun.outcome)).one() == RunOutcome.DECLINED


def test_analyst_sees_only_own_chats(
    client: TestClient, db_session: Session, analyst: dict[str, str], script: Any
) -> None:
    money_answer(script)
    ask(client, analyst, "Where did the money go?")
    other = signed_in(client, db_session, Role.ANALYST, "analyst.two")

    response = client.get(CHATS, headers=other)

    assert response.status_code == 200
    assert response.json()["data"] == []


def test_supervisor_reads_analyst_chat_read_only(
    client: TestClient, db_session: Session, analyst: dict[str, str], script: Any
) -> None:
    money_answer(script)
    chat_id = ask(client, analyst, "Where did the money go?").json()["data"]["chat"]["id"]
    supervisor = signed_in(client, db_session, Role.SUPERVISOR)

    listed = client.get(CHATS, headers=supervisor).json()["data"]
    chat = client.get(f"{CHATS}/{chat_id}", headers=supervisor).json()["data"]

    assert [(c["id"], c["is_own"], c["author_username"]) for c in listed] == [
        (chat_id, False, "analyst.one")
    ]
    assert chat["is_own"] is False
    assert [m["role"] for m in chat["messages"]] == ["user", "assistant"]


def test_supervisor_cannot_post_into_others_chat(
    client: TestClient, db_session: Session, analyst: dict[str, str], script: Any
) -> None:
    money_answer(script)
    chat_id = ask(client, analyst, "Where did the money go?").json()["data"]["chat"]["id"]
    supervisor = signed_in(client, db_session, Role.SUPERVISOR)
    provider = script(fake_text(ANSWER))

    response = ask(client, supervisor, "Anything else?", chat_id)

    assert_error(response, 403, "COPILOT_CHAT_READ_ONLY")
    assert provider.calls == []


def test_other_analysts_chat_is_not_found(
    client: TestClient, db_session: Session, analyst: dict[str, str], script: Any
) -> None:
    money_answer(script)
    chat_id = ask(client, analyst, "Where did the money go?").json()["data"]["chat"]["id"]
    other = signed_in(client, db_session, Role.ANALYST, "analyst.two")

    assert_error(client.get(f"{CHATS}/{chat_id}", headers=other), 404, "COPILOT_CHAT_NOT_FOUND")
    assert_error(ask(client, other, "Hi?", chat_id), 404, "COPILOT_CHAT_NOT_FOUND")


def test_chat_from_other_case_404(client: TestClient, analyst: dict[str, str], script: Any) -> None:
    money_answer(script)
    chat_id = ask(client, analyst, "Where did the money go?").json()["data"]["chat"]["id"]

    response = client.get(f"/api/v1/cases/FR-10483/chats/{chat_id}", headers=analyst)

    assert_error(response, 404, "COPILOT_CHAT_NOT_FOUND")


def test_auditor_forbidden(client: TestClient, db_session: Session, script: Any) -> None:
    provider = script(fake_text(ANSWER))
    auditor = signed_in(client, db_session, Role.AUDITOR)

    assert_error(client.get(CHATS, headers=auditor), 403, "AUTH_FORBIDDEN")
    assert_error(ask(client, auditor, "Where did the money go?"), 403, "AUTH_FORBIDDEN")
    assert provider.calls == []


@pytest.mark.parametrize("question", ["", "   ", "x" * 1001])
def test_question_length_validated(
    client: TestClient, analyst: dict[str, str], question: str
) -> None:
    assert_error(ask(client, analyst, question), 422, "VALIDATION_FAILED")


def test_unknown_case_404(client: TestClient, analyst: dict[str, str], script: Any) -> None:
    script(fake_text(ANSWER))

    response = client.post(
        "/api/v1/cases/FR-99999/copilot/questions",
        json={"question": "Why?"},
        headers=analyst,
    )

    assert_error(response, 404, "CASE_NOT_FOUND")


def test_limit_reached_returns_429_with_retry_after(
    client: TestClient, db_session: Session, analyst: dict[str, str], script: Any
) -> None:
    provider = script(fake_text(ANSWER))
    user = db_session.scalars(select(User).where(User.username == "analyst.one")).one()
    db_session.add(
        CopilotRun(
            user_id=user.id,
            case_id="FR-10482",
            model="fake/model",
            outcome=RunOutcome.ANSWERED,
            cost_usd=get_settings().copilot_daily_budget_usd + Decimal("0.01"),
        )
    )
    db_session.commit()

    response = ask(client, analyst, "Where did the money go?")

    assert_error(response, 429, "COPILOT_LIMIT_REACHED")
    assert int(response.headers["Retry-After"]) > 0
    assert provider.calls == []


def test_model_unavailable_returns_503_and_keeps_question(
    client: TestClient, db_session: Session, analyst: dict[str, str], script: Any
) -> None:
    script()  # No replies: the model is unreachable.

    response = ask(client, analyst, "Where did the money go?")

    assert_error(response, 503, "COPILOT_UNAVAILABLE")
    chats = client.get(CHATS, headers=analyst).json()["data"]
    assert [c["message_count"] for c in chats] == [1]
    assert db_session.scalars(select(CopilotRun.outcome)).one() == RunOutcome.FAILED


def test_missing_key_returns_503_but_declines_still_work(
    app: FastAPI, client: TestClient, analyst: dict[str, str]
) -> None:
    app.dependency_overrides[get_model_provider] = lambda: None

    assert_error(ask(client, analyst, "Where did the money go?"), 503, "COPILOT_UNAVAILABLE")
    declined = ask(client, analyst, "What is the customer's address?")
    assert declined.json()["data"]["message"]["answer"]["kind"] == "decline"


def test_failed_run_records_its_cost(
    client: TestClient, db_session: Session, analyst: dict[str, str], script: Any
) -> None:
    paid = fake_tool_call("get_case_summary", {})
    script(paid.__class__(None, paid.tool_calls, Usage(10, 5, Decimal("0.25")), "fake/m"))

    assert_error(ask(client, analyst, "Where did the money go?"), 503, "COPILOT_UNAVAILABLE")

    run = db_session.scalars(select(CopilotRun)).one()
    assert (run.outcome, run.cost_usd, run.tool_calls) == (RunOutcome.FAILED, Decimal("0.25"), 1)


def test_model_decline_is_recorded_and_audited_as_declined(
    client: TestClient, db_session: Session, analyst: dict[str, str], script: Any
) -> None:
    script(fake_text(json.dumps({"kind": "decline", "suggestions": ["Draft a case note"]})))

    response = ask(client, analyst, "Where does the account holder live?")

    assert response.json()["data"]["message"]["answer"]["kind"] == "decline"
    assert db_session.scalars(select(CopilotRun.outcome)).one() == RunOutcome.DECLINED
    actions = db_session.scalars(select(AuditEvent.action)).all()
    assert "copilot.declined" in actions
    assert "copilot.asked" not in actions


def test_unavailable_error_names_the_chat_that_kept_the_question(
    client: TestClient, analyst: dict[str, str], script: Any
) -> None:
    script()  # No replies: the model is unreachable.

    response = ask(client, analyst, "Where did the money go?")

    chat_id = client.get(CHATS, headers=analyst).json()["data"][0]["id"]
    assert response.json()["error"]["details"] == [{"field": "chat_id", "message": chat_id}]


def test_history_sends_only_the_latest_messages(
    client: TestClient, analyst: dict[str, str], script: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("OFI_COPILOT_HISTORY_MESSAGES", "2")
    get_settings.cache_clear()
    chat_id: str | None = None
    for question in ("First question?", "Second question?"):
        money_answer(script)
        chat_id = ask(client, analyst, question, chat_id).json()["data"]["chat"]["id"]
    provider = money_answer(script)

    ask(client, analyst, "Third question?", chat_id)

    sent = [(m.role, m.content or "") for m in provider.calls[0][0]]
    assert [role for role, _ in sent] == ["system", "user", "assistant", "user"]
    assert sent[1][1] == "Second question?"
    assert sent[-1][1] == "Third question?"
