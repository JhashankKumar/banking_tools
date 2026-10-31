"""Request-level negatives the in-app safety run cannot reach: every route, every role."""

import re
import uuid
from collections.abc import Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx2 import Response
from sqlalchemy.orm import Session

from app.modules.users.models import Role
from app.seed import seed
from tests.factories import assert_error, signed_in

PUBLIC = {"/api/v1/health", "/api/v1/health/ready", "/api/v1/auth/token"}
CASE_DATA = ("/api/v1/cases", "/api/v1/alerts", "/api/v1/notes", "/api/v1/rules")
SUPERVISOR_ONLY = ("/api/v1/safety", "/api/v1/users")
LEAKS = re.compile(r"Traceback|sqlalchemy|psycopg|File \"|/app/|\.py\b", re.IGNORECASE)


def _routes(app: FastAPI) -> Iterator[tuple[str, str]]:
    for path, operations in app.openapi()["paths"].items():
        for method in operations:
            filled = re.sub(r"\{case_id\}", "FR-10482", path)
            yield method.upper(), re.sub(r"\{[a-z_]+\}", str(uuid.uuid4()), filled)


def _call(client: TestClient, method: str, url: str, headers: dict[str, str]) -> Response:
    body: dict[str, str] | None = {} if method in {"POST", "PATCH"} else None
    return client.request(method, url, json=body, headers=headers)


@pytest.fixture(autouse=True)
def seeded(db_session: Session) -> None:
    seed(db_session, demo_password="seed-password-for-tests")
    db_session.commit()


def test_route_list_is_not_empty(app: FastAPI) -> None:
    assert len(list(_routes(app))) >= 25


def test_every_api_route_requires_a_token(app: FastAPI, client: TestClient) -> None:
    for method, url in _routes(app):
        if url in PUBLIC:
            continue
        response = _call(client, method, url, {})
        assert response.status_code == 401, (method, url, response.status_code)
        assert response.json()["error"]["code"] == "AUTH_NOT_AUTHENTICATED"


def test_auditor_is_refused_case_routes(
    app: FastAPI, client: TestClient, db_session: Session
) -> None:
    auditor = signed_in(client, db_session, Role.AUDITOR)
    for method, url in _routes(app):
        if url.startswith(CASE_DATA):
            assert_error(_call(client, method, url, auditor), 403, "AUTH_FORBIDDEN")


def test_analyst_is_refused_safety_and_users(
    app: FastAPI, client: TestClient, db_session: Session
) -> None:
    analyst = signed_in(client, db_session, Role.ANALYST)
    for method, url in _routes(app):
        if url.startswith(SUPERVISOR_ONLY):
            assert_error(_call(client, method, url, analyst), 403, "AUTH_FORBIDDEN")


def test_error_bodies_hide_internals(app: FastAPI, client: TestClient, db_session: Session) -> None:
    analyst = signed_in(client, db_session, Role.ANALYST)
    seen: set[int] = set()
    for method, url in _routes(app):
        for headers in ({}, analyst):
            response = _call(client, method, url, headers)
            if response.status_code < 400:
                continue
            seen.add(response.status_code)
            body = response.json()
            assert set(body) == {"error"}, (method, url)
            assert set(body["error"]) == {"code", "message", "details", "request_id"}
            assert not LEAKS.search(response.text), (method, url, response.text)
    assert {401, 403, 404, 422} <= seen
