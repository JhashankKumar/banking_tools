"""Test helpers for creating synthetic users and authenticating as them."""

from fastapi.testclient import TestClient
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
