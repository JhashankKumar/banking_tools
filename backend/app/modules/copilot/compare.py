"""Manual model comparison and smoke check against the seeded local database.

    uv run python -m app.modules.copilot.compare --models a/x,b/y --cap-usd 1.00

Asks each model a fixed set of questions through the real harness (same tools, prompt and
grounding checks as the app) and prints one row per answer. Stops once the cumulative cost
reaches the cap. Needs OPENROUTER_API_KEY; never prints it. Reads only: nothing is committed.
"""

import argparse
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from decimal import Decimal

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

import app.db.models  # noqa: F401  # pyright: ignore[reportUnusedImport]  (registers every table)
from app.core.config import Settings, get_settings
from app.db.session import get_engine
from app.modules.copilot.harness import CopilotUnavailableError, run_copilot
from app.modules.copilot.openrouter import OpenRouterModelProvider
from app.modules.copilot.provider import ChatMessage, ModelProvider, ModelReply, ToolSpec
from app.modules.copilot.tools import ToolContext
from app.modules.users.models import Role, User

QUESTIONS: list[tuple[str, str]] = [
    ("FR-10482", "Where did the money go after ACC-001?"),
    ("FR-10482", "Why did the alert fire?"),
    ("FR-10482", "What is not established?"),
    ("FR-10486", "What does TX-2001 show?"),
]
MODELS_URL = "https://openrouter.ai/api/v1/models"


@dataclass(frozen=True)
class Row:
    model: str
    case_id: str
    question: str
    outcome: str  # "answered" or "failed"
    tool_calls: int
    cost_usd: Decimal
    latency_ms: int


class _Metered:
    """Wraps a provider and adds up every call's cost, including calls of failed runs."""

    def __init__(self, inner: ModelProvider) -> None:
        self._inner = inner
        self.cost = Decimal("0")

    def complete(self, messages: Sequence[ChatMessage], tools: Sequence[ToolSpec]) -> ModelReply:
        reply = self._inner.complete(messages, tools)
        self.cost += reply.usage.cost_usd
        return reply


def run_comparison(
    session: Session,
    user: User,
    *,
    models: Sequence[str],
    provider_for: Callable[[str], ModelProvider],
    settings: Settings,
    cap_usd: Decimal,
) -> list[Row]:
    """One row per (model, question) until the cumulative cost reaches `cap_usd`."""
    rows: list[Row] = []
    spent = Decimal("0")
    for model in models:
        for case_id, question in QUESTIONS:
            if spent >= cap_usd:
                return rows
            provider = _Metered(provider_for(model))
            ctx = ToolContext(session=session, case_id=case_id, user=user)
            try:
                result = run_copilot(
                    provider, ctx, question=question, history=[], settings=settings
                )
                outcome, tools, latency = "answered", len(result.tool_names), result.latency_ms
            except CopilotUnavailableError:
                outcome, tools, latency = "failed", 0, 0
            spent += provider.cost
            rows.append(Row(model, case_id, question, outcome, tools, provider.cost, latency))
    return rows


def _known_models(names: Sequence[str]) -> list[str]:
    """Drops IDs OpenRouter does not list (the listing needs no key)."""
    try:
        listed = {m["id"] for m in httpx.get(MODELS_URL, timeout=20).json()["data"]}
    except (httpx.HTTPError, KeyError, ValueError):
        print("Could not fetch the model list; trying all models.", file=sys.stderr)
        return list(names)
    for name in names:
        if name not in listed:
            print(f"Skipping {name}: not listed by OpenRouter.", file=sys.stderr)
    return [n for n in names if n in listed]


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--models", required=True, help="Comma-separated OpenRouter model IDs")
    parser.add_argument("--cap-usd", type=Decimal, default=Decimal("1.00"))
    args = parser.parse_args(argv)
    settings = get_settings()
    if settings.openrouter_api_key is None:
        print("Set OPENROUTER_API_KEY in the repo-root .env first.", file=sys.stderr)
        raise SystemExit(2)
    key = settings.openrouter_api_key
    models = _known_models([m.strip() for m in args.models.split(",") if m.strip()])

    with Session(get_engine()) as session:
        user = session.scalars(
            select(User).where(User.role == Role.ANALYST, User.is_active).limit(1)
        ).first()
        if user is None:
            print("No active analyst user; run `python -m app.seed` first.", file=sys.stderr)
            raise SystemExit(2)
        rows = run_comparison(
            session,
            user,
            models=models,
            provider_for=lambda model: OpenRouterModelProvider(
                key, model, fallback_cost_per_1k=settings.copilot_fallback_cost_per_1k_tokens
            ),
            settings=settings,
            cap_usd=args.cap_usd,
        )
        session.rollback()  # Read-only: tools never write, but leave nothing behind.

    print(
        f"{'model':40} {'case':9} {'outcome':9} {'tools':>5} {'cost USD':>10} {'ms':>6}  question"
    )
    for r in rows:
        print(
            f"{r.model:40} {r.case_id:9} {r.outcome:9} {r.tool_calls:>5} "
            f"{r.cost_usd:>10.6f} {r.latency_ms:>6}  {r.question}"
        )
    total = sum((r.cost_usd for r in rows), Decimal("0"))
    print(f"Total cost: US${total:.6f} (cap US${args.cap_usd})")


if __name__ == "__main__":
    main()
