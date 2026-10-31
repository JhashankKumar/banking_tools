"""Reproducible benchmark on generated synthetic scenarios.

    cd backend && uv run python -m app.benchmark --seed 20261101 --variants 50

Writes results.json and RESULTS.md (default: docs/evaluation/results). Uses no database and no
model. `--live` also asks real models through the copilot harness (needs OPENROUTER_API_KEY
and the seeded database; spends at most --cap-usd).
"""

import argparse
import sys
from collections.abc import Sequence
from decimal import Decimal
from pathlib import Path
from typing import Any

from app.benchmark.report import build_report, write_report

DEFAULT_OUT = Path(__file__).resolve().parents[3] / "docs" / "evaluation" / "results"


def _positive(value: str) -> int:
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("must be 1 or more")
    return number


def _live(models: Sequence[str], cap_usd: Decimal) -> dict[str, Any]:
    from sqlalchemy import select
    from sqlalchemy.orm import Session

    import app.db.models  # noqa: F401  # pyright: ignore[reportUnusedImport]  (registers every table)
    from app.core.config import get_settings
    from app.db.session import get_engine
    from app.modules.copilot.compare import run_comparison
    from app.modules.copilot.openrouter import OpenRouterModelProvider
    from app.modules.users.models import Role, User

    settings = get_settings()
    key = settings.openrouter_api_key
    if key is None:  # main() checked already; kept for the type checker.
        raise SystemExit(2)
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
            cap_usd=cap_usd,
        )
        session.rollback()
    summary: dict[str, Any] = {}
    for model in models:
        mine = [r for r in rows if r.model == model]
        answered = [r for r in mine if r.outcome == "answered"]
        summary[model] = {
            "questions": len(mine),
            "answered": len(answered),
            "failed": len(mine) - len(answered),
            "cost_usd": f"{sum((r.cost_usd for r in mine), Decimal('0')):.6f}",
            "mean_latency_ms": (
                round(sum(r.latency_ms for r in answered) / len(answered)) if answered else None
            ),
        }
    return {"models": summary, "cap_usd": f"{cap_usd:.2f}"}


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=20261101)
    parser.add_argument("--variants", type=_positive, default=50, help="Variants per family")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--live", action="store_true", help="Also ask real models (costs money)")
    parser.add_argument("--models", default="", help="Comma-separated OpenRouter model IDs")
    parser.add_argument("--cap-usd", type=Decimal, default=Decimal("1.00"))
    args = parser.parse_args(argv)

    if args.out.exists() and not args.out.is_dir():
        parser.error(f"--out is not a directory: {args.out}")
    blocked = next((p for p in args.out.parents if p.exists() and not p.is_dir()), None)
    if blocked is not None:
        parser.error(f"--out is inside a file: {blocked}")

    live = None
    if args.live:
        from app.core.config import get_settings

        key = get_settings().openrouter_api_key
        if key is None or not key.get_secret_value():
            print("OPENROUTER_API_KEY is not set; --live needs it.", file=sys.stderr)
            raise SystemExit(2)
        models = [m.strip() for m in args.models.split(",") if m.strip()]
        if not models:
            parser.error("--live needs --models")
        live = _live(models, args.cap_usd)

    report = build_report(args.seed, args.variants, live=live)
    try:
        write_report(report, args.out)
    except OSError as error:
        print(f"Could not write to {args.out}: {error.strerror}", file=sys.stderr)
        raise SystemExit(2) from None
    print(f"Wrote {args.out / 'results.json'} and {args.out / 'RESULTS.md'}")


if __name__ == "__main__":
    main()
