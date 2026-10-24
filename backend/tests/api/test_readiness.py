import re

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine

from app.db.session import get_engine

UUID_PATTERN = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$")


def test_ready_ok_when_database_reachable(client: TestClient) -> None:
    response = client.get("/api/v1/health/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_503_when_database_unreachable(app: FastAPI) -> None:
    unreachable = create_engine(
        "postgresql+psycopg://nobody:unused@127.0.0.1:1/none",
        connect_args={"connect_timeout": 1},
    )
    app.dependency_overrides[get_engine] = lambda: unreachable

    response = TestClient(app).get("/api/v1/health/ready")

    assert response.status_code == 503
    assert response.json() == {"status": "unavailable"}
    assert "psycopg" not in response.text
    assert "unused" not in response.text


def test_request_id_generated_and_echoed(client: TestClient) -> None:
    generated = client.get("/api/v1/health")
    supplied = client.get("/api/v1/health", headers={"X-Request-ID": "abc-123"})

    assert UUID_PATTERN.match(generated.headers["X-Request-ID"])
    assert supplied.headers["X-Request-ID"] == "abc-123"


def test_request_id_rejects_malformed_header(client: TestClient) -> None:
    response = client.get("/api/v1/health", headers={"X-Request-ID": "bad id;drop"})

    assert UUID_PATTERN.match(response.headers["X-Request-ID"])
