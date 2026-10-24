from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.pagination import PageParams, count_rows, paged
from app.modules.users.models import Role, User
from tests.factories import make_user


def test_count_rows_counts_the_filtered_query(db_session: Session) -> None:
    for name in ("a.one", "b.one", "c.one"):
        make_user(db_session, username=name, role=Role.ANALYST)
    make_user(db_session, username="d.one", role=Role.AUDITOR)

    assert count_rows(db_session, select(User).where(User.role == Role.ANALYST)) == 3
    assert count_rows(db_session, select(User).where(User.username == "nobody")) == 0


def test_paged_applies_limit_and_offset(db_session: Session) -> None:
    for name in ("a.one", "b.one", "c.one"):
        make_user(db_session, username=name, role=Role.ANALYST)

    query = paged(select(User.username).order_by(User.username), PageParams(limit=2, offset=1))

    assert list(db_session.scalars(query)) == ["b.one", "c.one"]
