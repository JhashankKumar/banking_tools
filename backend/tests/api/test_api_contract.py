"""Wire contract: docs/project/API_AND_CODE_CONVENTIONS.md §1 (envelope, errors, request IDs)."""

import logging
from typing import Any

import pytest
from fastapi import APIRouter, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.modules.users.models import Role
from tests.factories import make_user, signed_in


@pytest.fixture
def supervisor_headers(client: TestClient, db_session: Session) -> dict[str, str]:
    return signed_in(client, db_session, Role.SUPERVISOR)


def assert_error(response_json: Any, code: str, request_id: str) -> dict[str, Any]:
    assert set(response_json) == {"error"}
    error: dict[str, Any] = response_json["error"]
    assert set(error) == {"code", "message", "details", "request_id"}
    assert error["code"] == code
    assert error["request_id"] == request_id
    return error


def test_unknown_route_uses_error_envelope(client: TestClient) -> None:
    response = client.get("/api/v1/does-not-exist")

    assert response.status_code == 404
    assert_error(response.json(), "NOT_FOUND", response.headers["X-Request-ID"])


def test_wrong_method_uses_error_envelope(client: TestClient) -> None:
    response = client.delete("/api/v1/health")

    assert response.status_code == 405
    assert_error(response.json(), "METHOD_NOT_ALLOWED", response.headers["X-Request-ID"])


def test_unauthenticated_uses_error_envelope(client: TestClient) -> None:
    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"
    assert_error(response.json(), "AUTH_NOT_AUTHENTICATED", response.headers["X-Request-ID"])


def test_validation_error_lists_fields_without_echoing_input(
    client: TestClient, supervisor_headers: dict[str, str]
) -> None:
    secret_attempt = "tiny-pw"
    response = client.post(
        "/api/v1/users",
        json={"username": "new.analyst", "password": secret_attempt, "role": "analyst"},
        headers=supervisor_headers,
    )

    assert response.status_code == 422
    error = assert_error(response.json(), "VALIDATION_FAILED", response.headers["X-Request-ID"])
    details: list[dict[str, str]] = error["details"]
    assert [d["field"] for d in details] == ["body.password"]
    assert secret_attempt not in response.text


def test_unknown_request_fields_rejected(
    client: TestClient, supervisor_headers: dict[str, str]
) -> None:
    response = client.post(
        "/api/v1/users",
        json={
            "username": "new.analyst",
            "password": "a-long-password-123",
            "role": "analyst",
            "is_superuser": True,
        },
        headers=supervisor_headers,
    )

    assert response.status_code == 422
    error = assert_error(response.json(), "VALIDATION_FAILED", response.headers["X-Request-ID"])
    assert error["details"] == [
        {"field": "body.is_superuser", "message": "Extra inputs are not permitted"}
    ]


def test_unexpected_error_is_generic_500_with_request_id(
    app: FastAPI, caplog: pytest.LogCaptureFixture
) -> None:
    boom = APIRouter()

    @boom.get("/api/v1/test-only/boom")
    def explode() -> None:
        raise RuntimeError("database password is hunter2")

    app.include_router(boom)

    with caplog.at_level(logging.ERROR):
        response = TestClient(app).get("/api/v1/test-only/boom")

    assert response.status_code == 500
    request_id = response.headers["X-Request-ID"]
    error = assert_error(response.json(), "INTERNAL_ERROR", request_id)
    assert error["message"] == "Something went wrong"
    assert "hunter2" not in response.text
    [record] = [r for r in caplog.records if r.levelno == logging.ERROR]
    assert getattr(record, "request_id", None) == request_id


def test_success_single_resource_uses_data_envelope(
    client: TestClient, supervisor_headers: dict[str, str]
) -> None:
    response = client.get("/api/v1/auth/me", headers=supervisor_headers)

    assert set(response.json()) == {"data"}
    assert response.json()["data"]["role"] == "supervisor"


def test_success_list_uses_data_and_page(
    client: TestClient, supervisor_headers: dict[str, str]
) -> None:
    response = client.get("/api/v1/users", params={"limit": 10}, headers=supervisor_headers)

    body = response.json()
    assert set(body) == {"data", "page"}
    assert body["page"] == {"total": 1, "limit": 10, "offset": 0}
    assert [u["username"] for u in body["data"]] == ["supervisor.one"]


def test_login_logs_never_contain_password(
    client: TestClient, db_session: Session, caplog: pytest.LogCaptureFixture
) -> None:
    make_user(db_session, username="analyst.one", role=Role.ANALYST)

    with caplog.at_level(logging.DEBUG):
        client.post(
            "/api/v1/auth/token", data={"username": "analyst.one", "password": "nope-wrong-1"}
        )

    assert "nope-wrong-1" not in caplog.text
