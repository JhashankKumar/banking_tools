"""Test helpers for creating synthetic users and authenticating as them."""

from fastapi.testclient import TestClient
from httpx2 import Response
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.modules.users.models import Role, User

DEFAULT_PASSWORD = "correct-horse-battery"


def make_user(
    session: Session,
    *,
    username: str,
    role: Role,
    password: str = DEFAULT_PASSWORD,
    is_active: bool = True,
) -> User:
    user = User(
        username=username, password_hash=hash_password(password), role=role, is_active=is_active
    )
    session.add(user)
    # Commit (releases the test savepoint) so a later request rollback cannot undo test setup.
    session.commit()
    return user


def login(client: TestClient, username: str, password: str = DEFAULT_PASSWORD) -> str:
    response = client.post("/api/v1/auth/token", data={"username": username, "password": password})
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def auth_header(
    client: TestClient, username: str, password: str = DEFAULT_PASSWORD
) -> dict[str, str]:
    return {"Authorization": f"Bearer {login(client, username, password)}"}


def signed_in(
    client: TestClient, session: Session, role: Role, username: str | None = None
) -> dict[str, str]:
    """Creates an active user with `role` (default username e.g. "analyst.one") and signs in."""
    name = username or f"{role.value}.one"
    make_user(session, username=name, role=role)
    return auth_header(client, name)


def assert_error(response: Response, status: int, code: str) -> None:
    """The response is the API error envelope with this status and registry code."""
    assert response.status_code == status, response.text
    assert response.json()["error"]["code"] == code
