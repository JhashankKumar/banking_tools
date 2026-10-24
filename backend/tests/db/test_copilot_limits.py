from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import Engine, text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.modules.cases.models import Case, CaseStatus
from app.modules.copilot.limits import (
    CopilotLimitError,
    check_limits,
    lock_questions,
    question_lock_key,
)
from app.modules.copilot.models import CopilotRun, RunOutcome
from app.modules.users.models import Role, User
from tests.factories import make_user

NOW = datetime(2026, 10, 24, 6, 0, tzinfo=UTC)


@pytest.fixture
def users(db_session: Session) -> tuple[User, User]:
    db_session.add(
        Case(
            id="FR-L1",
            title="Limits",
            status=CaseStatus.OPEN,
            opened_at=NOW,
            scenario_id="test-limits",
        )
    )
    db_session.flush()
    return (
        make_user(db_session, username="limit.one", role=Role.ANALYST),
        make_user(db_session, username="limit.two", role=Role.ANALYST),
    )


def _runs(session: Session, user: User, n: int, *, cost: str = "0", at: datetime = NOW) -> None:
    for i in range(n):
        session.add(
            CopilotRun(
                user_id=user.id,
                case_id="FR-L1",
                model="fake/model",
                outcome=RunOutcome.ANSWERED,
                cost_usd=Decimal(cost),
                created_at=at - timedelta(minutes=i + 1),
            )
        )
    session.flush()


def test_hourly_limit_per_user(db_session: Session, users: tuple[User, User]) -> None:
    first, second = users
    _runs(db_session, first, 20)
    settings = get_settings().model_copy(update={"copilot_questions_per_hour": 20})

    with pytest.raises(CopilotLimitError) as raised:
        check_limits(db_session, first.id, NOW, settings)
    check_limits(db_session, second.id, NOW, settings)

    assert raised.value.message == "You've reached the limit of 20 copilot questions per hour."


def test_old_runs_do_not_count(db_session: Session, users: tuple[User, User]) -> None:
    first, _ = users
    _runs(db_session, first, 20, at=NOW - timedelta(hours=2))

    check_limits(db_session, first.id, NOW, get_settings())


def test_daily_budget_blocks_all_users(db_session: Session, users: tuple[User, User]) -> None:
    first, second = users
    _runs(db_session, first, 4, cost="0.50")
    settings = get_settings().model_copy(update={"copilot_daily_budget_usd": Decimal("2.00")})

    with pytest.raises(CopilotLimitError):
        check_limits(db_session, second.id, NOW, settings)


def test_limit_error_has_retry_after_header(db_session: Session, users: tuple[User, User]) -> None:
    first, _ = users
    _runs(db_session, first, 4, cost="0.50")

    with pytest.raises(CopilotLimitError) as raised:
        check_limits(db_session, first.id, NOW, get_settings())

    assert raised.value.status == 429
    assert raised.value.code == "COPILOT_LIMIT_REACHED"
    # Budget resets at the next UTC midnight: 18 hours after 06:00 UTC.
    assert raised.value.headers == {"Retry-After": str(18 * 3600)}


def test_question_lock_serialises_one_users_parallel_questions(
    engine: Engine, users: tuple[User, User]
) -> None:
    first, second = users
    with Session(engine) as holder, Session(engine) as other:
        lock_questions(holder, first.id)

        same_user = other.scalar(
            text("SELECT pg_try_advisory_xact_lock(:k)"), {"k": question_lock_key(first.id)}
        )
        other_user = other.scalar(
            text("SELECT pg_try_advisory_xact_lock(:k)"), {"k": question_lock_key(second.id)}
        )
        holder.rollback()
        other.rollback()

    assert same_user is False
    assert other_user is True
