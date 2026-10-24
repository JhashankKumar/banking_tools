import uuid
from collections.abc import Mapping

from sqlalchemy.orm import Session

from app.modules.audit.models import AuditEvent, Outcome


def record(
    session: Session,
    *,
    action: str,
    outcome: Outcome,
    actor_user_id: uuid.UUID | None,
    request_id: str | None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    details: Mapping[str, str] | None = None,
) -> None:
    """Add an audit event to the session. Callers must never pass passwords, hashes, or tokens."""
    session.add(
        AuditEvent(
            action=action,
            outcome=outcome,
            actor_user_id=actor_user_id,
            request_id=request_id,
            resource_type=resource_type,
            resource_id=resource_id,
            details=dict(details or {}),
        )
    )
    session.flush()
