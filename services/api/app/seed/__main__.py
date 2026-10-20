"""Seed the database named by OFI_DATABASE_URL: `uv run python -m app.seed`."""

import sys

from sqlalchemy.orm import Session

import app.db.models  # noqa: F401  # pyright: ignore[reportUnusedImport]  (registers every table for the summary)
from app.core.config import Settings, get_settings
from app.db.session import get_engine
from app.seed import seed

MIN_DEMO_PASSWORD_LENGTH = 12


def main(settings: Settings | None = None) -> None:
    settings = settings or get_settings()
    if settings.app_env == "production":
        print(
            "Refusing to seed demo users and synthetic data when OFI_APP_ENV=production.",
            file=sys.stderr,
        )
        raise SystemExit(2)
    password = settings.demo_password.get_secret_value() if settings.demo_password else ""
    if len(password) < MIN_DEMO_PASSWORD_LENGTH:
        print(
            f"OFI_DEMO_PASSWORD must be set (at least {MIN_DEMO_PASSWORD_LENGTH} characters).",
            file=sys.stderr,
        )
        raise SystemExit(2)
    with Session(get_engine()) as session:
        summary = seed(session, demo_password=password)
        session.commit()
    for table, count in summary.items():
        print(f"{table}: {count}")


if __name__ == "__main__":
    main()
