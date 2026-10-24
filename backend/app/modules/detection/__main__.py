"""Run detection on OFI_DATABASE_URL: `uv run python -m app.modules.detection`."""

from collections.abc import Callable
from contextlib import AbstractContextManager

from sqlalchemy.orm import Session

from app.db.session import get_engine
from app.modules.detection.service import run_detection


def _open_session() -> AbstractContextManager[Session]:
    return Session(get_engine())


def main(open_session: Callable[[], AbstractContextManager[Session]] = _open_session) -> None:
    with open_session() as session:
        summary = run_detection(session)
        session.commit()
    for rule_id, hits in summary.items():
        print(f"{rule_id}: {hits}")


if __name__ == "__main__":
    main()
