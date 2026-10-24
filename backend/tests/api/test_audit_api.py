from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.modules.users.models import Role
from tests.factories import DEFAULT_PASSWORD, auth_header, make_user

AUDIT_URL = "/api/v1/audit-logs"


def test_auditor_reads_audit_logs(client: TestClient, db_session: Session) -> None:
    make_user(db_session, username="auditor.one", role=Role.AUDITOR)
    headers = auth_header(client, "auditor.one")

    response = client.get(AUDIT_URL, headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["data"][0]["action"] == "auth.login.succeeded"
    assert body["page"]["total"] >= 1


def test_audit_logs_filter_by_action(client: TestClient, db_session: Session) -> None:
    make_user(db_session, username="auditor.one", role=Role.AUDITOR)
    client.post("/api/v1/auth/token", data={"username": "auditor.one", "password": "wrong-pass"})
    headers = auth_header(client, "auditor.one")

    response = client.get(AUDIT_URL, params={"action": "auth.login.failed"}, headers=headers)

    assert [item["action"] for item in response.json()["data"]] == ["auth.login.failed"]


def test_analyst_cannot_read_audit_logs(client: TestClient, db_session: Session) -> None:
    make_user(db_session, username="analyst.one", role=Role.ANALYST)

    response = client.get(AUDIT_URL, headers=auth_header(client, "analyst.one"))

    assert response.status_code == 403


def test_audit_view_is_itself_audited(client: TestClient, db_session: Session) -> None:
    make_user(db_session, username="auditor.one", role=Role.AUDITOR)
    headers = auth_header(client, "auditor.one")
    client.get(AUDIT_URL, headers=headers)

    response = client.get(AUDIT_URL, params={"action": "audit.viewed"}, headers=headers)

    assert len(response.json()["data"]) == 1


def test_audit_entries_contain_no_secrets(client: TestClient, db_session: Session) -> None:
    make_user(db_session, username="auditor.one", role=Role.AUDITOR)
    make_user(db_session, username="supervisor.one", role=Role.SUPERVISOR)
    supervisor = auth_header(client, "supervisor.one")
    client.post(
        "/api/v1/users",
        json={"username": "new.analyst", "password": "brand-new-password-1", "role": "analyst"},
        headers=supervisor,
    )
    auditor = auth_header(client, "auditor.one")

    response = client.get(AUDIT_URL, headers=auditor)

    for secret in (DEFAULT_PASSWORD, "brand-new-password-1", "$argon2", "Bearer", "eyJ"):
        assert secret not in response.text


def test_audit_entries_include_actor_username(client: TestClient, db_session: Session) -> None:
    make_user(db_session, username="auditor.one", role=Role.AUDITOR)
    client.post("/api/v1/auth/token", data={"username": "auditor.one", "password": "wrong-pass"})
    headers = auth_header(client, "auditor.one")

    items = client.get(AUDIT_URL, headers=headers).json()["data"]

    by_action = {i["action"]: i for i in items}
    assert by_action["auth.login.succeeded"]["actor_username"] == "auditor.one"
    assert by_action["auth.login.failed"]["actor_username"] is None
