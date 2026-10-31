"""Audit and secrets: records say what happened without leaking what was asked or keys."""

import json
import re
from collections.abc import Sequence

from app.modules.copilot.harness import CopilotUnavailableError
from app.modules.copilot.provider import (
    ChatMessage,
    FakeModelProvider,
    ModelReply,
    ModelUnavailableError,
    ToolSpec,
    fake_text,
    fake_tool_call,
)
from app.modules.safety.context import CheckContext
from app.modules.safety.contract import CheckOutcome, SafetyCheck, failed, passed
from app.modules.users.models import Role

CASE = "FR-10482"
QUESTION = "Where did the money go after ACC-001?"
ANSWER = json.dumps(
    {
        "kind": "answer",
        "records": [{"text": "TX-1001 moved ₹48,500.00.", "citations": ["EV-10482-TX-1001"]}],
    }
)
ALLOWED_KEYS = {"chat_id", "tools", "prompt_tokens", "completion_tokens", "cost_usd", "latency_ms"}
FAKE_KEY = "sk-or-v1-0000safetycheck0000"  # Shaped like an OpenRouter key; not a real one.
_KEY_LIKE = re.compile(r"sk-or-", re.IGNORECASE)


def _aud_01(ctx: CheckContext) -> CheckOutcome:
    ctx.require_case(CASE)
    provider = FakeModelProvider([fake_tool_call("find_money_paths", {}), fake_text(ANSWER)])
    ctx.ask(ctx.user(Role.ANALYST), CASE, QUESTION, provider)
    [row] = ctx.audit_rows("copilot.asked")
    text = json.dumps(row.details, ensure_ascii=False).lower()
    if not set(row.details) <= ALLOWED_KEYS:
        return failed("The audit row holds fields beyond counts, tools and cost.")
    if "where did the money" in text or "48,500" in text or "48500" in text:
        return failed("The audit row repeats the question or an amount.")
    return passed("Audited with tool names, token counts and cost only.")


class _LeakyProvider:
    """A provider whose failure message carries a key-like string."""

    def complete(self, messages: Sequence[ChatMessage], tools: Sequence[ToolSpec]) -> ModelReply:
        raise ModelUnavailableError(f"upstream rejected key {FAKE_KEY}")


def _aud_02(ctx: CheckContext) -> CheckOutcome:
    ctx.require_case(CASE)
    try:
        ctx.ask(ctx.user(Role.ANALYST), CASE, QUESTION, _LeakyProvider())
    except CopilotUnavailableError as error:
        rows = ctx.audit_rows()
        surfaced = " ".join(
            [
                str(error),
                error.message,
                json.dumps(list(error.details)),
                json.dumps([r.details for r in rows]),
            ]
        )
        if _KEY_LIKE.search(surfaced):
            return failed("A key-like string reached the error or the audit log.")
        return passed("Only the generic “unavailable” message surfaced; nothing key-like.")
    return failed("The provider failure did not surface as unavailable.")


CHECKS = [
    SafetyCheck(
        id="AUD-01",
        category="Audit and secrets",
        attack="Someone reads the audit log hoping to see what analysts asked.",
        defence="Copilot audit rows hold tool names, counts and cost, never questions or amounts.",
        run=_aud_01,
    ),
    SafetyCheck(
        id="AUD-02",
        category="Audit and secrets",
        attack="The model provider fails with an error message that contains a key.",
        defence="Provider errors become a generic message; nothing key-like is stored or shown.",
        run=_aud_02,
    ),
]
