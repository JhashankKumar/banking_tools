from collections.abc import Iterator
from functools import lru_cache
from typing import Any

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session

from app.core.config import get_settings


def _use_utc(dbapi_connection: Any, _record: Any) -> None:
    # Runs on every new connection, after libpq applies any client PGTZ, so timestamptz values
    # always come back in UTC whatever the server or client time zone (ADR 0001 #6).
    with dbapi_connection.cursor() as cursor:
        cursor.execute("SET TIME ZONE 'UTC'")
    dbapi_connection.commit()


def build_engine(url: str) -> Engine:
    engine = create_engine(url, pool_pre_ping=True)
    event.listen(engine, "connect", _use_utc)
    return engine


@lru_cache
def get_engine() -> Engine:
    return build_engine(get_settings().database_url)


def get_session() -> Iterator[Session]:
    """FastAPI dependency: one session per request, committed on success, rolled back on error."""
    with Session(get_engine()) as session:
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
