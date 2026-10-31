"""Shared test fixtures.

Tests run against a dedicated PostgreSQL test database (``OFI_TEST_DATABASE_URL``),
never the development database. Each test runs inside a transaction that is rolled back.
"""

import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import Engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.core.config import ENV_FILE, get_settings
from app.db.session import build_engine, get_engine, get_session
from app.main import create_app
from app.modules.safety.router import get_safety_connection

API_ROOT = Path(__file__).resolve().parents[1]
TEST_JWT_SECRET = "test-only-jwt-secret-not-for-real-use-0123456789"


class _TestDatabaseSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="OFI_", env_file=ENV_FILE, extra="ignore")

    test_database_url: str


def _test_database_url() -> str:
    url = _TestDatabaseSettings().test_database_url  # pyright: ignore[reportCallIssue]
    database = make_url(url).database or ""
    if not database.endswith("_test"):
        raise RuntimeError("OFI_TEST_DATABASE_URL must name a database ending in _test")
    return url


TEST_DATABASE_URL = _test_database_url()
# Environment variables take precedence over .env, so the app under test can only see the test DB.
os.environ["OFI_DATABASE_URL"] = TEST_DATABASE_URL
os.environ["OFI_JWT_SECRET"] = TEST_JWT_SECRET
os.environ["OFI_APP_ENV"] = "test"
os.environ["OFI_DOCS_ENABLED"] = "false"


@pytest.fixture(autouse=True)
def fresh_settings() -> Iterator[None]:
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def alembic_config(url: str) -> Config:
    config = Config(str(API_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(API_ROOT / "migrations"))
    config.set_main_option("sqlalchemy.url", url.replace("%", "%%"))
    return config


@pytest.fixture(scope="session")
def engine() -> Iterator[Engine]:
    command.upgrade(alembic_config(TEST_DATABASE_URL), "head")
    test_engine = build_engine(TEST_DATABASE_URL)
    yield test_engine
    test_engine.dispose()


@pytest.fixture
def db_session(engine: Engine) -> Iterator[Session]:
    connection = engine.connect()
    outer = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    try:
        yield session
    finally:
        session.close()
        outer.rollback()
        connection.close()


@pytest.fixture
def app(engine: Engine, db_session: Session) -> FastAPI:
    application = create_app()

    def _session() -> Iterator[Session]:
        # Same commit/rollback semantics as app.db.session.get_session, inside the test savepoint.
        try:
            yield db_session
            db_session.commit()
        except Exception:
            db_session.rollback()
            raise

    application.dependency_overrides[get_session] = _session
    application.dependency_overrides[get_engine] = lambda: engine
    # The safety run sees the test's uncommitted data and is rolled back inside its transaction.
    application.dependency_overrides[get_safety_connection] = lambda: db_session.connection()
    return application


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    return TestClient(app)
