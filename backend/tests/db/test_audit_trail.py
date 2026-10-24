from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette.requests import Request

from app.api.dependencies import AuditTrail
from app.modules.audit.models import AuditEvent, Outcome
from app.modules.users.models import Role
from tests.factories import make_user


def test_success_fills_actor_request_id_and_outcome(db_session: Session) -> None:
    user = make_user(db_session, username="analyst.one", role=Role.ANALYST)
    request = Request({"type": "http", "state": {"request_id": "req-1"}})

    AuditTrail(db_session, request, user).success(
        "case.viewed", resource_type="case", resource_id="FR-1", details={"k": "v"}
    )

    event = db_session.scalars(select(AuditEvent).where(AuditEvent.action == "case.viewed")).one()
    assert event.outcome == Outcome.SUCCESS
    assert event.actor_user_id == user.id
    assert event.request_id == "req-1"
    assert (event.resource_type, event.resource_id) == ("case", "FR-1")
    assert event.details == {"k": "v"}
