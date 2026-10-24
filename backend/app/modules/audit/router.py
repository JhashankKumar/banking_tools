from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select

from app.api.dependencies import Audit, DbSession, require
from app.api.pagination import Page, count_rows, paged
from app.api.responses import PageResponse, page_of
from app.core.permissions import Permission
from app.modules.audit.models import AuditEvent
from app.modules.audit.schemas import AuditEventOut
from app.modules.users.models import User

router = APIRouter(prefix="/audit-logs", tags=["audit"])
AuditReader = Annotated[User, Depends(require(Permission.AUDIT_READ))]


@router.get("")
def list_audit_events(
    user: AuditReader,
    session: DbSession,
    trail: Audit,
    page: Page,
    action: Annotated[str | None, Query(max_length=64)] = None,
) -> PageResponse[AuditEventOut]:
    query = select(AuditEvent)
    if action is not None:
        query = query.where(AuditEvent.action == action)
    total = count_rows(session, query)
    rows = session.execute(
        paged(
            query.add_columns(User.username)
            .outerjoin(User, User.id == AuditEvent.actor_user_id)
            .order_by(AuditEvent.id.desc()),
            page,
        )
    ).all()
    items = [
        AuditEventOut.model_validate(event).model_copy(update={"actor_username": username})
        for event, username in rows
    ]
    page_out = page_of(items, total, page)
    trail.success("audit.viewed", resource_type="audit_log")
    return page_out
