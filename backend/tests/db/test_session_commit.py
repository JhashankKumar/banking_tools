"""The request's transaction must commit before the response is sent (review finding M1-I1)."""

from collections.abc import Iterator

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.modules.users.models import Role
from tests.factories import signed_in


def test_commit_failure_returns_500_instead_of_success(
    app: FastAPI, client: TestClient, db_session: Session
) -> None:
    headers = signed_in(client, db_session, Role.SUPERVISOR)

    def session_whose_commit_fails() -> Iterator[Session]:
        yield db_session
        raise RuntimeError("simulated commit failure")

    app.dependency_overrides[get_session] = session_whose_commit_fails
    response = TestClient(app, raise_server_exceptions=False).post(
        "/api/v1/users",
        json={"username": "new.analyst", "password": "a-long-password-123", "role": "analyst"},
        headers=headers,
    )

    assert response.status_code == 500
