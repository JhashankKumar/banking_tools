from collections.abc import Callable

import pytest
from sqlalchemy.orm import Session

from app.modules.copilot.tools import ToolContext
from app.modules.users.models import Role, User
from app.seed import seed
from tests.factories import make_user


@pytest.fixture
def analyst(db_session: Session) -> User:
    seed(db_session, demo_password="demo-password-for-tests")
    return make_user(db_session, username="copilot.analyst", role=Role.ANALYST)


@pytest.fixture
def ctx_for(db_session: Session, analyst: User) -> Callable[[str], ToolContext]:
    """Tool context for one seeded case, acting as an analyst."""
    return lambda case_id: ToolContext(session=db_session, case_id=case_id, user=analyst)
