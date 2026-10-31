import pytest
from sqlalchemy import Engine, func, select, text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.base import Base
from app.modules.safety.context import CheckContext
from app.modules.safety.contract import CATEGORY_ORDER, CheckOutcome, SafetyCheck
from app.modules.safety.registry import CATALOGUE
from app.modules.safety.runner import SAFETY_LOCK_KEY, SafetyRunInProgressError, run_catalogue
from tests.security.conftest import Run

INJ_01 = next(c for c in CATALOGUE if c.id == "INJ-01")


def _boom(_ctx: CheckContext) -> CheckOutcome:
    raise KeyError("internal detail")


BOOM = SafetyCheck(id="ZZZ-99", category="Grounding", attack="Raises.", defence="None.", run=_boom)


def _counts(session: Session) -> dict[str, int]:
    return {
        t.name: session.scalar(select(func.count()).select_from(t)) or 0
        for t in Base.metadata.sorted_tables
    }


def test_run_leaves_every_table_unchanged(db_session: Session, casebook: None, run: Run) -> None:
    before = _counts(db_session)

    result = run()

    assert result.counts.passed >= 1
    assert _counts(db_session) == before


def test_checks_skip_without_casebook(run: Run) -> None:
    [result] = run([INJ_01]).results

    assert result.status == "skipped"
    assert result.observed == "Needs the seeded casebook (python -m app.seed)"


def test_erroring_check_fails_alone(casebook: None, run: Run) -> None:
    boom, inj = run([BOOM, INJ_01]).results

    assert (boom.status, boom.observed) == ("failed", "The check itself errored (KeyError)")
    assert inj.status == "passed", inj.observed


def test_second_concurrent_run_conflicts(engine: Engine, run: Run) -> None:
    with engine.connect() as other:
        other.execute(text("SELECT pg_advisory_lock(:k)"), {"k": SAFETY_LOCK_KEY})
        try:
            with pytest.raises(SafetyRunInProgressError):
                run([INJ_01])
        finally:
            other.execute(text("SELECT pg_advisory_unlock(:k)"), {"k": SAFETY_LOCK_KEY})


def test_lock_released_after_error(casebook: None, run: Run) -> None:
    run([BOOM])

    assert run([INJ_01]).results[0].status == "passed"


def _end_the_transaction(ctx: CheckContext) -> CheckOutcome:
    ctx.session.connection().exec_driver_sql("ROLLBACK")  # Code under test misbehaving.
    return CheckOutcome("passed", "")


BREAKS_TRANSACTION = SafetyCheck(
    id="ZZZ-98", category="Grounding", attack="Ends it.", defence="None.", run=_end_the_transaction
)


def _lock_is_free(engine: Engine) -> bool:
    with engine.connect() as probe:
        free = bool(probe.scalar(text("SELECT pg_try_advisory_lock(:k)"), {"k": SAFETY_LOCK_KEY}))
        if free:
            probe.execute(text("SELECT pg_advisory_unlock(:k)"), {"k": SAFETY_LOCK_KEY})
        return free


def test_lock_never_outlives_a_run_that_broke_its_transaction(engine: Engine) -> None:
    """On its own connection (as the route runs it), a run whose cleanup fails still frees the
    lock; a held lock would answer 409 to every later run until the API restarted."""
    with engine.connect() as connection:
        try:
            run_catalogue(connection, get_settings(), [BREAKS_TRANSACTION])
        except Exception:  # noqa: BLE001, S110  (the run may fail; only the lock matters here)
            pass

        assert _lock_is_free(engine)


def test_catalogue_ids_unique_and_ordered() -> None:
    ids = [c.id for c in CATALOGUE]
    assert len(ids) == len(set(ids))
    order = [(CATEGORY_ORDER.index(c.category), c.id) for c in CATALOGUE]
    assert order == sorted(order)
