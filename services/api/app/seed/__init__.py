"""Deterministic synthetic seed data. Safe to run repeatedly."""

from sqlalchemy import Table, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.base import Base
from app.modules.cases.models import case_transactions
from app.modules.users.models import Role, User
from app.seed.scenarios import all_scenarios

DEMO_USERS: dict[str, Role] = {
    "analyst.demo": Role.ANALYST,
    "supervisor.demo": Role.SUPERVISOR,
    "auditor.demo": Role.AUDITOR,
}

SeedSummary = dict[str, int]


def seed(session: Session, *, demo_password: str) -> SeedSummary:
    """Upsert every scenario by primary key and create missing demo users. Flushes, never commits.

    Existing demo users are left untouched (their password is not reset).
    """
    for scenario in all_scenarios():
        for record in scenario.records:
            session.merge(record)
        session.flush()
        if scenario.case_links:
            session.execute(
                insert(case_transactions)
                .values([{"case_id": c, "transaction_id": t} for c, t in scenario.case_links])
                .on_conflict_do_nothing()
            )

    existing = set(session.scalars(select(User.username).where(User.username.in_(DEMO_USERS))))
    for username, role in DEMO_USERS.items():
        if username not in existing:
            session.add(
                User(username=username, password_hash=hash_password(demo_password), role=role)
            )
    session.flush()
    return _row_counts(session)


def _row_counts(session: Session) -> SeedSummary:
    tables: list[Table] = sorted(Base.metadata.tables.values(), key=lambda t: t.name)
    return {t.name: session.scalar(select(func.count()).select_from(t)) or 0 for t in tables}
