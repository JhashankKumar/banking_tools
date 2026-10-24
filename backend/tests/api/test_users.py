import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.audit.models import AuditEvent, Outcome
from app.modules.users.models import Role, User
from tests.factories import DEFAULT_PASSWORD, assert_error, auth_header, make_user

USERS_URL = "/api/v1/users"
NEW_PASSWORD = "a-new-long-password-123"
USER_OUT_KEYS = {"id", "username", "role", "is_active", "created_at", "updated_at"}


@pytest.fixture
def supervisor(db_session: Session) -> User:
    return make_user(db_session, username="supervisor.one", role=Role.SUPERVISOR)


@pytest.fixture
def supervisor_headers(client: TestClient, supervisor: User) -> dict[str, str]:
    return auth_header(client, supervisor.username)


def create(client: TestClient, headers: dict[str, str], **body: object) -> dict[str, object]:
    payload = {"username": "new.analyst", "password": NEW_PASSWORD, "role": "analyst"} | body
    response = client.post(USERS_URL, json=payload, headers=headers)
    return {"status": response.status_code, "body": response.json()}


def test_supervisor_creates_user(client: TestClient, supervisor_headers: dict[str, str]) -> None:
    result = create(client, supervisor_headers)

    assert result["status"] == 201
    body = result["body"]
    assert isinstance(body, dict)
    body = body["data"]  # pyright: ignore[reportUnknownVariableType]
    assert isinstance(body, dict)
    assert body["username"] == "new.analyst"
    assert body["role"] == "analyst"
    assert body["is_active"] is True


def test_created_user_can_log_in(client: TestClient, supervisor_headers: dict[str, str]) -> None:
    create(client, supervisor_headers)

    assert auth_header(client, "new.analyst", NEW_PASSWORD)


def test_create_duplicate_username_409(
    client: TestClient, supervisor_headers: dict[str, str]
) -> None:
    create(client, supervisor_headers)

    assert create(client, supervisor_headers)["status"] == 409


def test_password_too_short_422(client: TestClient, supervisor_headers: dict[str, str]) -> None:
    assert create(client, supervisor_headers, password="short")["status"] == 422


def test_invalid_username_422(client: TestClient, supervisor_headers: dict[str, str]) -> None:
    assert create(client, supervisor_headers, username="Not Valid!")["status"] == 422


def test_user_out_never_contains_password_hash(
    client: TestClient, supervisor_headers: dict[str, str]
) -> None:
    created = client.post(
        USERS_URL,
        json={"username": "new.analyst", "password": NEW_PASSWORD, "role": "analyst"},
        headers=supervisor_headers,
    )
    listed = client.get(USERS_URL, headers=supervisor_headers)
    patched = client.patch(
        f"{USERS_URL}/{created.json()['data']['id']}",
        json={"role": "auditor"},
        headers=supervisor_headers,
    )

    assert set(created.json()["data"]) == USER_OUT_KEYS
    assert all(set(item) == USER_OUT_KEYS for item in listed.json()["data"])
    assert set(patched.json()["data"]) == USER_OUT_KEYS
    for response in (created, listed, patched):
        assert "$argon2" not in response.text
        assert NEW_PASSWORD not in response.text


@pytest.mark.parametrize("role", [Role.ANALYST, Role.AUDITOR])
def test_analyst_and_auditor_cannot_manage_users(
    client: TestClient, db_session: Session, role: Role
) -> None:
    make_user(db_session, username="not.supervisor", role=role)
    headers = auth_header(client, "not.supervisor")

    assert client.get(USERS_URL, headers=headers).status_code == 403
    assert create(client, headers)["status"] == 403
    denied = db_session.scalars(
        select(AuditEvent).where(AuditEvent.action == "access.denied")
    ).all()
    assert len(denied) == 2
    assert all(event.outcome == Outcome.DENIED for event in denied)


def test_supervisor_deactivates_user_then_user_cannot_login(
    client: TestClient, db_session: Session, supervisor_headers: dict[str, str]
) -> None:
    target = make_user(db_session, username="leaving.analyst", role=Role.ANALYST)

    response = client.patch(
        f"{USERS_URL}/{target.id}", json={"is_active": False}, headers=supervisor_headers
    )
    login = client.post(
        "/api/v1/auth/token", data={"username": "leaving.analyst", "password": DEFAULT_PASSWORD}
    )

    assert response.status_code == 200
    assert response.json()["data"]["is_active"] is False
    assert login.status_code == 401


def test_supervisor_resets_password(
    client: TestClient, db_session: Session, supervisor_headers: dict[str, str]
) -> None:
    target = make_user(db_session, username="forgetful.analyst", role=Role.ANALYST)

    client.patch(
        f"{USERS_URL}/{target.id}", json={"password": NEW_PASSWORD}, headers=supervisor_headers
    )

    assert auth_header(client, "forgetful.analyst", NEW_PASSWORD)


@pytest.mark.parametrize("change", [{"is_active": False}, {"role": "analyst"}])
def test_supervisor_cannot_deactivate_or_demote_self(
    client: TestClient,
    supervisor: User,
    supervisor_headers: dict[str, str],
    change: dict[str, object],
) -> None:
    response = client.patch(f"{USERS_URL}/{supervisor.id}", json=change, headers=supervisor_headers)

    assert_error(response, 409, "USER_SELF_LOCKOUT")
    assert response.json()["error"]["message"] == (
        "Supervisors cannot deactivate or change the role of their own account"
    )


def test_patch_unknown_user_404(client: TestClient, supervisor_headers: dict[str, str]) -> None:
    response = client.patch(
        f"{USERS_URL}/00000000-0000-4000-8000-000000000000",
        json={"is_active": False},
        headers=supervisor_headers,
    )

    assert response.status_code == 404


def test_user_changes_are_audited_without_secrets(
    client: TestClient, db_session: Session, supervisor: User, supervisor_headers: dict[str, str]
) -> None:
    created_id: str = client.post(
        USERS_URL,
        json={"username": "new.analyst", "password": NEW_PASSWORD, "role": "analyst"},
        headers=supervisor_headers,
    ).json()["data"]["id"]
    client.patch(
        f"{USERS_URL}/{created_id}",
        json={"role": "auditor", "password": "another-long-password-9"},
        headers=supervisor_headers,
    )

    events = db_session.scalars(
        select(AuditEvent)
        .where(AuditEvent.action.in_(["user.created", "user.updated"]))
        .order_by(AuditEvent.id)
    ).all()

    assert [e.action for e in events] == ["user.created", "user.updated"]
    assert all(e.actor_user_id == supervisor.id for e in events)
    assert all(e.resource_id == created_id for e in events)
    assert events[1].details == {"fields": "password,role"}
    for event in events:
        assert NEW_PASSWORD not in str(event.details)
        assert "another-long-password-9" not in str(event.details)


def test_list_users_limit_capped(client: TestClient, supervisor_headers: dict[str, str]) -> None:
    assert (
        client.get(USERS_URL, params={"limit": 101}, headers=supervisor_headers).status_code == 422
    )
    assert (
        client.get(USERS_URL, params={"offset": -1}, headers=supervisor_headers).status_code == 422
    )


def test_list_users_paginates(client: TestClient, supervisor_headers: dict[str, str]) -> None:
    create(client, supervisor_headers)

    response = client.get(USERS_URL, params={"limit": 1}, headers=supervisor_headers)

    assert response.status_code == 200
    assert len(response.json()["data"]) == 1
    assert response.json()["page"]["total"] == 2
