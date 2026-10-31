"""Limits: questions per hour and the daily budget cannot be talked past."""

from datetime import UTC
from decimal import Decimal

from sqlalchemy import func, select

from app.modules.copilot.harness import CopilotUnavailableError
from app.modules.copilot.limits import CopilotBudgetExceededError, CopilotLimitError
from app.modules.copilot.models import CopilotRun, RunOutcome
from app.modules.copilot.provider import FakeModelProvider, ModelReply, Usage, fake_tool_call
from app.modules.safety.checks.customer_info import CUSTOMER_INFO_QUESTIONS
from app.modules.safety.context import CheckContext
from app.modules.safety.contract import CheckOutcome, SafetyCheck, failed, passed
from app.modules.users.models import Role

CASE = "FR-10482"


def _lim_01(ctx: CheckContext) -> CheckOutcome:
    ctx.require_case(CASE)
    analyst = ctx.user(Role.ANALYST)
    one_an_hour = ctx.settings.model_copy(update={"copilot_questions_per_hour": 1})
    question = CUSTOMER_INFO_QUESTIONS[0]  # Answered without a model call.
    ctx.ask(analyst, CASE, question, FakeModelProvider([]), settings=one_an_hour)
    try:
        ctx.ask(analyst, CASE, question, FakeModelProvider([]), settings=one_an_hour)
    except CopilotBudgetExceededError:
        return failed("The budget, not the hourly limit, stopped the question.")
    except CopilotLimitError:
        limited = ctx.session.scalars(
            select(CopilotRun.id).where(
                CopilotRun.user_id == analyst.id, CopilotRun.outcome == RunOutcome.LIMITED
            )
        ).all()
        if len(limited) == 1:
            return passed("The second question in the hour was refused and recorded as limited.")
        return failed("Refused, but the limited attempt was not recorded.")
    return failed("A question past the hourly limit was answered.")


def _paid(i: int) -> ModelReply:
    call = fake_tool_call("get_case_summary", {}, call_id=f"c{i}")
    return ModelReply(None, call.tool_calls, Usage(10, 5, Decimal("0.30")), "fake/model")


def _lim_02(ctx: CheckContext) -> CheckOutcome:
    ctx.require_case(CASE)
    day_start = ctx.now.astimezone(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    spent = ctx.session.scalar(
        select(func.coalesce(func.sum(CopilotRun.cost_usd), 0)).where(
            CopilotRun.created_at >= day_start
        )
    ) or Decimal("0")
    # US$0.50 left today, whatever was really spent; each model call costs US$0.30.
    tight = ctx.settings.model_copy(update={"copilot_daily_budget_usd": spent + Decimal("0.50")})
    analyst = ctx.user(Role.ANALYST)
    provider = FakeModelProvider([_paid(i) for i in range(5)])
    try:
        ctx.ask(analyst, CASE, "Keep looking.", provider, settings=tight)
    except CopilotBudgetExceededError:
        cost = ctx.session.scalars(
            select(CopilotRun.cost_usd).where(CopilotRun.user_id == analyst.id)
        ).all()
        if len(provider.calls) == 2 and cost == [Decimal("0.60")]:
            return passed("Stopped before a third call once US$0.60 of US$0.50 was spent; metered.")
        return failed("The run stopped, but late or without metering its cost.")
    except CopilotUnavailableError:
        pass  # It ran until the model stopped answering: the budget never stopped it.
    return failed("The run kept spending past the daily budget.")


CHECKS = [
    SafetyCheck(
        id="LIM-01",
        category="Limits",
        attack="An analyst keeps asking past the hourly question limit.",
        defence="Questions per user per hour are counted from the run log.",
        run=_lim_01,
    ),
    SafetyCheck(
        id="LIM-02",
        category="Limits",
        attack="One long run tries to spend past the daily budget.",
        defence="The budget is checked before every model call; what was spent is metered.",
        run=_lim_02,
    ),
]
