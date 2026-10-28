import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.config import Settings, get_settings
from app.main import create_app


@pytest.fixture
def plain_client() -> TestClient:
    """App without database overrides; health endpoints must not need the database."""
    return TestClient(create_app())


def test_health_returns_ok(plain_client: TestClient) -> None:
    response = plain_client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_unknown_api_route_returns_json_404(plain_client: TestClient) -> None:
    response = plain_client.get("/api/v1/does-not-exist")

    assert response.status_code == 404
    assert response.headers["content-type"].startswith("application/json")
    assert "Traceback" not in response.text


def test_settings_load_from_environment_without_env_file() -> None:
    settings = Settings(_env_file=None)  # pyright: ignore[reportCallIssue]

    assert settings.database_url.startswith("postgresql")
    assert settings.access_token_minutes == 30


def test_settings_require_secrets(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OFI_JWT_SECRET")

    with pytest.raises(ValidationError):
        Settings(_env_file=None)  # pyright: ignore[reportCallIssue]


def test_jwt_secret_min_length(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OFI_JWT_SECRET", "x" * 31)

    with pytest.raises(ValidationError):
        Settings(_env_file=None)  # pyright: ignore[reportCallIssue]


def test_api_docs_disabled_by_default(plain_client: TestClient) -> None:
    for path in ("/docs", "/redoc", "/openapi.json"):
        assert plain_client.get(path).status_code == 404


def test_api_docs_enabled_when_opted_in(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OFI_DOCS_ENABLED", "true")
    get_settings.cache_clear()

    client = TestClient(create_app())

    assert client.get("/openapi.json").status_code == 200
