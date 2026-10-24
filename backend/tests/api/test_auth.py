from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.modules.audit.models import AuditEvent, Outcome
from app.modules.users.models import Role, User
from tests.factories import DEFAULT_PASSWORD, auth_header, make_user, signed_in

TOKEN_URL = "/api/v1/auth/token"
ME_URL = "/api/v1/auth/me"
GENERIC_LOGIN_ERROR = ("AUTH_INVALID_CREDENTIALS", "Invalid username or password")


def post_login(client: TestClient, username: str, password: str) -> dict[str, object]:
    response = client.post(TOKEN_URL, data={"username": username, "password": password})
    error = response.json()["error"]
    return {"status": response.status_code, "body": (error["code"], error["message"])}


def test_login_success_returns_bearer_token(client: TestClient, db_session: Session) -> None:
    make_user(db_session, username="analyst.one", role=Role.ANALYST)

    response = client.post(
        TOKEN_URL, data={"username": "analyst.one", "password": DEFAULT_PASSWORD}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["expires_in"] == 1800
    assert isinstance(body["access_token"], str)


def test_login_wrong_password_401_generic_message(client: TestClient, db_session: Session) -> None:
    make_user(db_session, username="analyst.one", role=Role.ANALYST)

    assert post_login(client, "analyst.one", "wrong-password") == {
        "status": 401,
        "body": GENERIC_LOGIN_ERROR,
    }


def test_login_unknown_user_401_same_message(client: TestClient) -> None:
    assert post_login(client, "nobody.here", "whatever-password") == {
        "status": 401,
        "body": GENERIC_LOGIN_ERROR,
    }


def test_login_inactive_user_401_same_message(client: TestClient, db_session: Session) -> None:
    make_user(db_session, username="former.analyst", role=Role.ANALYST, is_active=False)

    assert post_login(client, "former.analyst", DEFAULT_PASSWORD) == {
        "status": 401,
        "body": GENERIC_LOGIN_ERROR,
    }


def test_login_audits_success_and_failure(client: TestClient, db_session: Session) -> None:
    user = make_user(db_session, username="analyst.one", role=Role.ANALYST)
    client.post(TOKEN_URL, data={"username": "analyst.one", "password": "wrong-password"})
    token = client.post(
        TOKEN_URL, data={"username": "analyst.one", "password": DEFAULT_PASSWORD}
    ).json()["access_token"]

    events = db_session.scalars(select(AuditEvent).order_by(AuditEvent.id)).all()

    assert [(e.action, e.outcome) for e in events] == [
        ("auth.login.failed", Outcome.FAILURE),
        ("auth.login.succeeded", Outcome.SUCCESS),
    ]
    assert events[1].actor_user_id == user.id
    for event in events:
        assert event.request_id
        serialized = str(event.details)
        assert DEFAULT_PASSWORD not in serialized
        assert "wrong-password" not in serialized
        assert token not in serialized


def test_me_requires_token(client: TestClient) -> None:
    response = client.get(ME_URL)

    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"


def test_me_returns_role_and_permissions(client: TestClient, db_session: Session) -> None:
    user = make_user(db_session, username="auditor.one", role=Role.AUDITOR)

    response = client.get(ME_URL, headers=auth_header(client, "auditor.one"))

    assert response.status_code == 200
    assert response.json()["data"] == {
        "id": str(user.id),
        "username": "auditor.one",
        "role": "auditor",
        "permissions": ["audit:read"],
    }


def test_expired_token_rejected(client: TestClient, db_session: Session) -> None:
    user = make_user(db_session, username="analyst.one", role=Role.ANALYST)
    token = create_access_token(user.id, now=datetime.now(UTC) - timedelta(minutes=31))

    response = client.get(ME_URL, headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401


def test_tampered_token_rejected(client: TestClient, db_session: Session) -> None:
    token = signed_in(client, db_session, Role.ANALYST)["Authorization"]
    tampered = token[:-2] + ("A" if token[-2] != "A" else "B") + token[-1]

    response = client.get(ME_URL, headers={"Authorization": tampered})

    assert response.status_code == 401


def test_deactivated_user_token_rejected(client: TestClient, db_session: Session) -> None:
    user = make_user(db_session, username="analyst.one", role=Role.ANALYST)
    headers = auth_header(client, "analyst.one")
    user.is_active = False
    db_session.commit()

    response = client.get(ME_URL, headers=headers)

    assert response.status_code == 401


def test_password_hash_is_argon2_and_not_plaintext(db_session: Session) -> None:
    make_user(db_session, username="analyst.one", role=Role.ANALYST)

    stored = db_session.scalars(select(User.password_hash)).one()

    assert stored.startswith("$argon2id$")
    assert DEFAULT_PASSWORD not in stored


def test_token_tolerates_small_clock_skew(client: TestClient, db_session: Session) -> None:
    """A token issued a few seconds 'in the future' (clock stepped back, e.g. WSL2/NTP) is valid."""
    user = make_user(db_session, username="analyst.one", role=Role.ANALYST)
    token = create_access_token(user.id, now=datetime.now(UTC) + timedelta(seconds=5))

    response = client.get(ME_URL, headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200


def test_token_from_far_future_rejected(client: TestClient, db_session: Session) -> None:
    user = make_user(db_session, username="analyst.one", role=Role.ANALYST)
    token = create_access_token(user.id, now=datetime.now(UTC) + timedelta(minutes=5))

    response = client.get(ME_URL, headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401
