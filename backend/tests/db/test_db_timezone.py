"""Timestamps must come back in UTC whatever the server or client time zone (ADR 0001 #6)."""

from collections.abc import Iterator

import pytest
from sqlalchemy import text

from app.db.session import get_engine


@pytest.fixture
def ist_client_environment(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.setenv("PGTZ", "Asia/Kolkata")  # libpq sends this as the session time zone
    get_engine.cache_clear()
    yield
    get_engine.cache_clear()


@pytest.mark.usefixtures("ist_client_environment")
def test_engine_sessions_use_utc() -> None:
    with get_engine().connect() as connection:
        zone = connection.execute(text("SHOW TimeZone")).scalar_one()
        offset = connection.execute(
            text("SELECT extract(timezone FROM TIMESTAMPTZ '2026-09-15 04:32:14+00')")
        ).scalar_one()

    assert zone == "UTC"
    assert offset == 0
