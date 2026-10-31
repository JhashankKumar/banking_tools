from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.audit.models import AuditEvent
from app.modules.users.models import Role
from app.seed import seed
from tests.factories import assert_error, signed_in

CHECKS = "/api/v1/safety/checks"
RUNS = "/api/v1/safety/runs"


def test_supervisor_and_auditor_list_and_run(client: TestClient, db_session: Session) -> None:
    seed(db_session, demo_password="seed-password-for-tests")
    db_session.commit()
    for role in (Role.SUPERVISOR, Role.AUDITOR):
        headers = signed_in(client, db_session, role)

        checks = client.get(CHECKS, headers=headers)
        run = client.post(RUNS, headers=headers)

        assert checks.status_code == 200, checks.text
        assert {"id", "category", "attack", "defence"} <= set(checks.json()["data"][0])
        assert run.status_code == 200, run.text
        body = run.json()["data"]
        assert set(body["counts"]) == {"passed", "failed", "skipped"}
        assert body["counts"]["failed"] == 0, body["results"]
        assert len(body["results"]) == len(checks.json()["data"])


def test_analyst_forbidden(client: TestClient, db_session: Session) -> None:
    analyst = signed_in(client, db_session, Role.ANALYST)

    assert_error(client.get(CHECKS, headers=analyst), 403, "AUTH_FORBIDDEN")
    assert_error(client.post(RUNS, headers=analyst), 403, "AUTH_FORBIDDEN")


def test_requires_token(client: TestClient) -> None:
    assert_error(client.post(RUNS), 401, "AUTH_NOT_AUTHENTICATED")


def test_run_is_audited_with_counts_only(client: TestClient, db_session: Session) -> None:
    supervisor = signed_in(client, db_session, Role.SUPERVISOR)

    client.post(RUNS, headers=supervisor)

    [event] = db_session.scalars(
        select(AuditEvent).where(AuditEvent.action == "safety.checks.run")
    ).all()
    assert set(event.details) == {"passed", "failed", "skipped"}
