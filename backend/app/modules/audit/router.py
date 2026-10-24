from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import func, select

from app.api.dependencies import DbSession, request_id_of, require
from app.api.pagination import Page
from app.api.responses import PageResponse, page_of
from app.core.permissions import Permission
from app.modules.audit import service as audit
from app.modules.audit.models import AuditEvent, Outcome
from app.modules.audit.schemas import AuditEventOut
from app.modules.users.models import User

router = APIRouter(prefix="/audit-logs", tags=["audit"])
AuditReader = Annotated[User, Depends(require(Permission.AUDIT_READ))]


@router.get("")
def list_audit_events(
    user: AuditReader,
    session: DbSession,
    request: Request,
    page: Page,
    action: Annotated[str | None, Query(max_length=64)] = None,
) -> PageResponse[AuditEventOut]:
    query = select(AuditEvent)
    if action is not None:
        query = query.where(AuditEvent.action == action)
    total = session.scalar(select(func.count()).select_from(query.subquery())) or 0
    rows = session.execute(
        query.add_columns(User.username)
        .outerjoin(User, User.id == AuditEvent.actor_user_id)
        .order_by(AuditEvent.id.desc())
        .limit(page.limit)
        .offset(page.offset)
    ).all()
    items = [
        AuditEventOut.model_validate(event).model_copy(update={"actor_username": username})
        for event, username in rows
    ]
    page_out = page_of(items, total, page)
    audit.record(
        session,
        action="audit.viewed",
        outcome=Outcome.SUCCESS,
        actor_user_id=user.id,
        request_id=request_id_of(request),
        resource_type="audit_log",
    )
    return page_out
