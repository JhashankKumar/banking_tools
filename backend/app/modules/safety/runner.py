"""Runs the catalogue inside one transaction that is always rolled back.

Production code under test commits (a failed question is kept, a 403 keeps its audit row). Each
check gets a connection-level savepoint and a fresh session that joins it with
`create_savepoint`, so the code's commits only release inner savepoints; rolling the check's
savepoint back undoes everything it did, and one check cannot leave the next a broken session.
"""

import time
import uuid
from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy import Connection, text
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.errors import AppError
from app.modules.safety.context import CheckContext, run_settings
from app.modules.safety.contract import (
    CASEBOOK_MISSING,
    CasebookMissingError,
    CheckOutcome,
    SafetyCheck,
    failed,
    skipped,
)
from app.modules.safety.registry import CATALOGUE
from app.modules.safety.schemas import SafetyCounts, SafetyResultOut, SafetyRunOut

SAFETY_LOCK_KEY = 0x5AFE7  # One run at a time, across all API processes.


class SafetyRunInProgressError(AppError):
    status = 409
    code = "SAFETY_RUN_IN_PROGRESS"
    message = "A safety run is already in progress."


def _run_one(
    connection: Connection, check: SafetyCheck, settings: Settings, now: datetime, run_id: uuid.UUID
) -> CheckOutcome:
    savepoint = connection.begin_nested()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    ctx = CheckContext(session=session, settings=settings, now=now, run_id=run_id)
    try:
        return check.run(ctx)
    except CasebookMissingError:
        return skipped(CASEBOOK_MISSING)
    except Exception as error:  # A bug in a check must not hide the other checks.
        return failed(f"The check itself errored ({type(error).__name__})")
    finally:
        session.close()
        savepoint.rollback()


def run_catalogue(
    connection: Connection,
    settings: Settings,
    checks: Sequence[SafetyCheck] = CATALOGUE,
    *,
    now: datetime | None = None,
) -> SafetyRunOut:
    started_at = now or datetime.now(UTC)
    started = time.monotonic()
    transaction = connection.begin_nested() if connection.in_transaction() else connection.begin()
    # Transaction-scoped: Postgres frees it when the run's transaction ends, however it ends,
    # so a failed cleanup can never leave every later run answering 409.
    locked = connection.scalar(text("SELECT pg_try_advisory_xact_lock(:k)"), {"k": SAFETY_LOCK_KEY})
    if not locked:
        transaction.rollback()
        raise SafetyRunInProgressError
    generous, run_id = run_settings(settings), uuid.uuid4()
    results: list[SafetyResultOut] = []
    try:
        for check in checks:
            check_started = time.monotonic()
            outcome = _run_one(connection, check, generous, started_at, run_id)
            results.append(
                SafetyResultOut(
                    id=check.id,
                    category=check.category,
                    attack=check.attack,
                    defence=check.defence,
                    status=outcome.status,
                    observed=outcome.observed,
                    duration_ms=int((time.monotonic() - check_started) * 1000),
                )
            )
    finally:
        transaction.rollback()
    return SafetyRunOut(
        ran_at=started_at,
        duration_ms=int((time.monotonic() - started) * 1000),
        counts=SafetyCounts(
            passed=sum(r.status == "passed" for r in results),
            failed=sum(r.status == "failed" for r in results),
            skipped=sum(r.status == "skipped" for r in results),
        ),
        results=results,
    )
