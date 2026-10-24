"""Usage limits from the run log, so they hold across processes and restarts.

Per user: `copilot_questions_per_hour`. Across everyone: `copilot_daily_budget_usd` per UTC day.
"""

import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.errors import AppError
from app.modules.copilot.models import CopilotRun, RunOutcome
from app.modules.copilot.provider import Usage


class CopilotLimitError(AppError):
    status = 429
    code = "COPILOT_LIMIT_REACHED"

    def __init__(self, message: str, retry_after_s: int) -> None:
        super().__init__(message)
        self.message = message
        self.headers = {"Retry-After": str(max(retry_after_s, 1))}


def question_lock_key(user_id: uuid.UUID) -> int:
    """A stable signed 64-bit advisory-lock key per user."""
    return int.from_bytes(user_id.bytes[:8], "big") & 0x7FFF_FFFF_FFFF_FFFF


def lock_questions(session: Session, user_id: uuid.UUID) -> None:
    """Serialises one user's questions until the transaction ends, so parallel requests cannot
    all pass the hourly limit before any of them is recorded."""
    session.execute(select(func.pg_advisory_xact_lock(question_lock_key(user_id))))


def _seconds_to_midnight(now: datetime) -> int:
    day_start = now.astimezone(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    return int((day_start + timedelta(days=1) - now).total_seconds())


class CopilotBudgetExceededError(CopilotLimitError):
    """Raised mid-run when the run itself reaches the remaining daily budget."""

    def __init__(self, now: datetime, *, usage: Usage, tool_calls: int) -> None:
        super().__init__(BUDGET_MESSAGE, _seconds_to_midnight(now))
        self.usage = usage
        self.tool_calls = tool_calls


BUDGET_MESSAGE = "The copilot's daily budget is used up. It resets at 00:00 UTC (05:30 IST)."


def check_limits(
    session: Session, user_id: uuid.UUID, now: datetime, settings: Settings
) -> Decimal:
    """Raises when a limit is reached; otherwise returns the budget left for today (USD)."""
    hour_ago = now - timedelta(hours=1)
    recent = session.scalars(
        select(CopilotRun.created_at)
        .where(
            CopilotRun.user_id == user_id,
            CopilotRun.created_at > hour_ago,
            CopilotRun.outcome != RunOutcome.LIMITED,
        )
        .order_by(CopilotRun.created_at)
    ).all()
    if len(recent) >= settings.copilot_questions_per_hour:
        raise CopilotLimitError(
            f"You've reached the limit of {settings.copilot_questions_per_hour} copilot "
            "questions per hour.",
            int((recent[0] + timedelta(hours=1) - now).total_seconds()),
        )

    day_start = now.astimezone(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    spent = session.scalar(
        select(func.coalesce(func.sum(CopilotRun.cost_usd), 0)).where(
            CopilotRun.created_at >= day_start
        )
    ) or Decimal("0")
    if spent >= settings.copilot_daily_budget_usd:
        raise CopilotLimitError(BUDGET_MESSAGE, _seconds_to_midnight(now))
    return settings.copilot_daily_budget_usd - spent


def record_run(
    session: Session,
    *,
    user_id: uuid.UUID,
    case_id: str,
    chat_id: uuid.UUID | None,
    outcome: RunOutcome,
    model: str,
    tool_calls: int = 0,
    usage: Usage | None = None,
    latency_ms: int = 0,
) -> CopilotRun:
    usage = usage or Usage()
    run = CopilotRun(
        user_id=user_id,
        case_id=case_id,
        chat_id=chat_id,
        outcome=outcome,
        model=model,
        tool_calls=tool_calls,
        prompt_tokens=usage.prompt_tokens,
        completion_tokens=usage.completion_tokens,
        cost_usd=usage.cost_usd,
        latency_ms=latency_ms,
    )
    session.add(run)
    session.flush()
    return run
