from collections.abc import Callable, Sequence
from typing import Any

import pytest
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.modules.safety.contract import SafetyCheck
from app.modules.safety.registry import CATALOGUE
from app.modules.safety.runner import run_catalogue
from app.modules.safety.schemas import SafetyRunOut
from app.seed import seed

Run = Callable[..., SafetyRunOut]


@pytest.fixture
def casebook(db_session: Session) -> None:
    seed(db_session, demo_password="seed-password-for-tests")
    db_session.commit()


@pytest.fixture
def run(db_session: Session) -> Run:
    """Runs checks on the test transaction's connection, as the route does on its own."""

    def _run(checks: Sequence[SafetyCheck] = CATALOGUE, **kwargs: Any) -> SafetyRunOut:
        return run_catalogue(db_session.connection(), get_settings(), checks, **kwargs)

    return _run
