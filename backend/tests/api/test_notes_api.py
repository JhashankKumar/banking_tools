import json
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import Engine, event, select
from sqlalchemy.orm import Session

from app.modules.audit.models import AuditEvent
from app.modules.cases.models import Case, CaseStatus
from app.modules.copilot.provider import (
    FakeModelProvider,
    fake_text,
    get_model_provider,
)
from app.modules.users.models import Role
from app.seed import seed
from tests.factories import assert_error, signed_in

CASE = "/api/v1/cases/FR-10482"
NOTES = f"{CASE}/notes"
BODY = "What the records show\n- TX-1001 moved INR 48500.00 [EV-10482-TX-1001]"


@pytest.fixture(autouse=True)
def seeded(db_session: Session) -> None:
    seed(db_session, demo_password="seed-password-for-tests")
    db_session.commit()


@pytest.fixture
def analyst(client: TestClient, db_session: Session) -> dict[str, str]:
    return signed_in(client, db_session, Role.ANALYST)


@pytest.fixture
def supervisor(client: TestClient, db_session: Session) -> dict[str, str]:
    return signed_in(client, db_session, Role.SUPERVISOR)


def create(client: TestClient, headers: dict[str, str], body: str = BODY, **extra: Any) -> Any:
    response = client.post(NOTES, json={"body": body, **extra}, headers=headers)
    assert response.status_code == 201, response.text
    return response.json()["data"]


def submit(client: TestClient, headers: dict[str, str], note_id: str) -> Any:
    return client.post(f"{NOTES}/{note_id}/submit", headers=headers)


def review(client: TestClient, headers: dict[str, str], note_id: str, **body: Any) -> Any:
    return client.post(f"{NOTES}/{note_id}/review", json=body, headers=headers)


def case_status(db_session: Session) -> CaseStatus:
    db_session.expire_all()
    return db_session.get_one(Case, "FR-10482").status


def actions(db_session: Session) -> list[str]:
    return list(db_session.scalars(select(AuditEvent.action).order_by(AuditEvent.id)))


def submitted(client: TestClient, analyst: dict[str, str]) -> str:
    note_id: str = create(client, analyst)["id"]
    assert submit(client, analyst, note_id).status_code == 200
    return note_id


def test_analyst_saves_ai_drafted_note_with_valid_citations(
    app: FastAPI, client: TestClient, db_session: Session, analyst: dict[str, str]
) -> None:
    answer = {
        "kind": "answer",
        "records": [{"text": "TX-1001.", "citations": ["EV-10482-TX-1001"]}],
    }
    app.dependency_overrides[get_model_provider] = lambda: FakeModelProvider(
        [fake_text(json.dumps(answer))]
    )
    asked = client.post(
        f"{CASE}/copilot/questions", json={"question": "Draft a case note"}, headers=analyst
    ).json()["data"]

    note = create(client, analyst, source_message_id=asked["message"]["id"])

    assert note["status"] == "draft"
    assert note["origin"] == "ai_drafted"
    assert note["author_username"] == "analyst.one"
    assert note["cited_ids"] == ["TX-1001", "EV-10482-TX-1001"]
    assert note["current_version"] == 1
    assert note["can_edit"] is True
    assert "note.saved" in actions(db_session)


def test_written_note_has_written_origin(client: TestClient, analyst: dict[str, str]) -> None:
    assert create(client, analyst)["origin"] == "written"


def test_invalid_citation_rejected(client: TestClient, analyst: dict[str, str]) -> None:
    response = client.post(NOTES, json={"body": "Wrong case [EV-10483-TX-3001]"}, headers=analyst)

    assert_error(response, 422, "NOTE_CITATION_INVALID")
    assert response.json()["error"]["details"] == [
        {"field": "body", "message": "Unknown citation EV-10483-TX-3001"}
    ]


def test_unknown_transaction_citation_rejected(client: TestClient, analyst: dict[str, str]) -> None:
    response = client.post(NOTES, json={"body": "Ghost TX-9999"}, headers=analyst)

    assert_error(response, 422, "NOTE_CITATION_INVALID")


def test_source_message_must_be_own_assistant_message(
    client: TestClient, analyst: dict[str, str]
) -> None:
    response = client.post(
        NOTES,
        json={"body": BODY, "source_message_id": "00000000-0000-4000-8000-000000000000"},
        headers=analyst,
    )

    assert_error(response, 422, "VALIDATION_FAILED")


def test_submit_moves_open_case_to_in_review_and_audits(
    client: TestClient, db_session: Session, analyst: dict[str, str]
) -> None:
    note_id = create(client, analyst)["id"]

    response = submit(client, analyst, note_id)

    assert response.status_code == 200
    assert response.json()["data"]["status"] == "awaiting_review"
    assert case_status(db_session) == CaseStatus.IN_REVIEW
    assert {"note.submitted", "case.status_changed"} <= set(actions(db_session))
    history = client.get(f"{CASE}/status-changes", headers=analyst).json()["data"]
    assert [
        (h["from_status"], h["to_status"], h["reason"], h["actor_username"]) for h in history
    ] == [("open", "in_review", "note_submitted", "analyst.one")]


def test_second_submission_conflicts(client: TestClient, analyst: dict[str, str]) -> None:
    submitted(client, analyst)
    second = create(client, analyst)["id"]

    assert_error(submit(client, analyst, second), 409, "NOTE_REVIEW_PENDING")


def test_self_review_conflicts(client: TestClient, supervisor: dict[str, str]) -> None:
    note_id = submitted(client, supervisor)

    response = review(client, supervisor, note_id, decision="approve_keep_open")

    assert_error(response, 409, "NOTE_SELF_REVIEW")


def test_return_requires_comment_and_reopens_case(
    client: TestClient, db_session: Session, analyst: dict[str, str], supervisor: dict[str, str]
) -> None:
    note_id = submitted(client, analyst)

    assert_error(review(client, supervisor, note_id, decision="return"), 422, "VALIDATION_FAILED")
    response = review(client, supervisor, note_id, decision="return", comment="Cite TX-1002 too.")

    assert response.status_code == 200
    note = response.json()["data"]
    assert note["status"] == "returned"
    assert note["reviews"][0]["comment"] == "Cite TX-1002 too."
    assert case_status(db_session) == CaseStatus.OPEN
    assert "note.returned" in actions(db_session)


def test_returned_note_revised_and_resubmitted(
    client: TestClient, analyst: dict[str, str], supervisor: dict[str, str]
) -> None:
    note_id = submitted(client, analyst)
    review(client, supervisor, note_id, decision="return", comment="Add the onward hop.")

    edited = client.patch(
        f"{NOTES}/{note_id}",
        json={"body": BODY + "\n- TX-1002 [EV-10482-TX-1002]"},
        headers=analyst,
    )

    assert edited.status_code == 200
    assert edited.json()["data"]["current_version"] == 2
    assert [v["version"] for v in edited.json()["data"]["versions"]] == [1, 2]
    assert submit(client, analyst, note_id).status_code == 200


def test_approve_close_requires_listed_reason(
    client: TestClient, db_session: Session, analyst: dict[str, str], supervisor: dict[str, str]
) -> None:
    note_id = submitted(client, analyst)

    bad = review(
        client, supervisor, note_id, decision="approve_close", reason="Because", comment="x"
    )
    good = review(
        client,
        supervisor,
        note_id,
        decision="approve_close",
        reason="No further action",
        comment="Benign after review.",
    )

    assert_error(bad, 422, "VALIDATION_FAILED")
    assert good.status_code == 200
    assert good.json()["data"]["status"] == "approved"
    assert case_status(db_session) == CaseStatus.CLOSED
    assert "note.approved" in actions(db_session)


def test_approve_escalate_then_close_escalated_case(
    client: TestClient, db_session: Session, analyst: dict[str, str], supervisor: dict[str, str]
) -> None:
    note_id = submitted(client, analyst)

    escalated = review(
        client, supervisor, note_id, decision="approve_escalate", reason="Refer to fraud operations"
    )
    closed = client.post(
        f"{CASE}/close",
        json={"reason": "Referred externally", "comment": "Handed over."},
        headers=supervisor,
    )

    assert escalated.status_code == 200
    assert closed.status_code == 200
    assert case_status(db_session) == CaseStatus.CLOSED
    history = client.get(f"{CASE}/status-changes", headers=supervisor).json()["data"]
    assert [(h["from_status"], h["to_status"]) for h in history] == [
        ("open", "in_review"),
        ("in_review", "escalated"),
        ("escalated", "closed"),
    ]


def test_review_on_escalated_case_keeps_it_escalated(
    client: TestClient, db_session: Session, analyst: dict[str, str], supervisor: dict[str, str]
) -> None:
    first = submitted(client, analyst)
    review(client, supervisor, first, decision="approve_escalate", reason="Refer")
    second = submitted(client, analyst)

    review(client, supervisor, second, decision="return", comment="More detail.")

    assert case_status(db_session) == CaseStatus.ESCALATED


def test_close_only_from_escalated(client: TestClient, supervisor: dict[str, str]) -> None:
    response = client.post(
        f"{CASE}/close", json={"reason": "No further action", "comment": "x"}, headers=supervisor
    )

    assert_error(response, 409, "CASE_STATUS_CONFLICT")


def test_closed_case_rejects_submit(
    client: TestClient, analyst: dict[str, str], supervisor: dict[str, str]
) -> None:
    note_id = submitted(client, analyst)
    review(
        client,
        supervisor,
        note_id,
        decision="approve_close",
        reason="No further action",
        comment="x",
    )
    later = create(client, analyst)["id"]

    assert_error(submit(client, analyst, later), 409, "CASE_STATUS_CONFLICT")


def test_analyst_cannot_review_or_close(
    client: TestClient, db_session: Session, analyst: dict[str, str]
) -> None:
    other = signed_in(client, db_session, Role.ANALYST, "analyst.two")
    note_id = submitted(client, analyst)

    assert_error(
        review(client, other, note_id, decision="approve_keep_open"), 403, "AUTH_FORBIDDEN"
    )
    assert_error(
        client.post(
            f"{CASE}/close", json={"reason": "No further action", "comment": "x"}, headers=other
        ),
        403,
        "AUTH_FORBIDDEN",
    )
    assert case_status(db_session) == CaseStatus.IN_REVIEW
    assert actions(db_session).count("access.denied") == 2


def test_only_author_edits_and_submits(
    client: TestClient, db_session: Session, analyst: dict[str, str]
) -> None:
    note_id = create(client, analyst)["id"]
    other = signed_in(client, db_session, Role.ANALYST, "analyst.two")

    assert_error(
        client.patch(f"{NOTES}/{note_id}", json={"body": "Mine now"}, headers=other),
        403,
        "NOTE_FORBIDDEN",
    )
    assert_error(submit(client, other, note_id), 403, "NOTE_FORBIDDEN")


def test_awaiting_note_cannot_be_edited(client: TestClient, analyst: dict[str, str]) -> None:
    note_id = submitted(client, analyst)

    response = client.patch(f"{NOTES}/{note_id}", json={"body": BODY}, headers=analyst)

    assert_error(response, 409, "NOTE_STATUS_CONFLICT")


def test_notes_visible_to_other_analyst(
    client: TestClient, db_session: Session, analyst: dict[str, str]
) -> None:
    create(client, analyst)
    other = signed_in(client, db_session, Role.ANALYST, "analyst.two")

    notes = client.get(NOTES, headers=other).json()["data"]

    assert [(n["author_username"], n["can_edit"], n["can_review"]) for n in notes] == [
        ("analyst.one", False, False)
    ]


def test_awaiting_review_queue_excludes_own_notes(
    client: TestClient, db_session: Session, analyst: dict[str, str], supervisor: dict[str, str]
) -> None:
    submitted(client, analyst)
    own = create(client, supervisor, body="Supervisor note on FR-10482")["id"]
    other_case = client.post(
        "/api/v1/cases/FR-10483/notes",
        json={"body": "Benign [EV-10483-TX-3001]"},
        headers=supervisor,
    ).json()["data"]["id"]
    client.post(f"/api/v1/cases/FR-10483/notes/{other_case}/submit", headers=supervisor)

    queue = client.get("/api/v1/notes/awaiting-review", headers=supervisor).json()["data"]

    assert [(q["case_id"], q["author_username"]) for q in queue] == [("FR-10482", "analyst.one")]
    assert own not in {q["note_id"] for q in queue}


def test_auditor_forbidden_on_notes(client: TestClient, db_session: Session) -> None:
    auditor = signed_in(client, db_session, Role.AUDITOR)

    assert_error(client.get(NOTES, headers=auditor), 403, "AUTH_FORBIDDEN")
    assert_error(
        client.get("/api/v1/notes/awaiting-review", headers=auditor), 403, "AUTH_FORBIDDEN"
    )


def test_review_locks_note_and_case_rows(
    client: TestClient, engine: Engine, analyst: dict[str, str], supervisor: dict[str, str]
) -> None:
    note_id = submitted(client, analyst)
    statements: list[str] = []

    def capture(_conn: Any, _cursor: Any, statement: str, *_args: Any) -> None:
        statements.append(statement)

    event.listen(engine, "before_cursor_execute", capture)
    try:
        review(client, supervisor, note_id, decision="approve_keep_open")
    finally:
        event.remove(engine, "before_cursor_execute", capture)

    locked = [s for s in statements if "FOR UPDATE" in s]
    assert any("FROM case_notes" in s for s in locked)
    assert any("FROM cases" in s for s in locked)


def test_close_blocked_while_a_note_awaits_review(
    client: TestClient, analyst: dict[str, str], supervisor: dict[str, str]
) -> None:
    first = submitted(client, analyst)
    review(client, supervisor, first, decision="approve_escalate", reason="Refer")
    submitted(client, analyst)  # Pending on the escalated case.

    response = client.post(
        f"{CASE}/close", json={"reason": "No further action", "comment": "x"}, headers=supervisor
    )

    assert_error(response, 409, "NOTE_REVIEW_PENDING")


def test_note_cannot_cite_another_cases_transaction(
    client: TestClient, analyst: dict[str, str]
) -> None:
    response = client.post(NOTES, json={"body": "Unrelated TX-3001"}, headers=analyst)

    assert_error(response, 422, "NOTE_CITATION_INVALID")
