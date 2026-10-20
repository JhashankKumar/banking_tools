from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request

from app.api.dependencies import DbSession, request_id_of, require
from app.api.pagination import Page
from app.api.responses import DataResponse, PageResponse, page_of
from app.core.permissions import Permission
from app.modules.alerts import service
from app.modules.alerts.schemas import AlertOut
from app.modules.audit import service as audit
from app.modules.audit.models import Outcome
from app.modules.users.models import User

router = APIRouter(prefix="/alerts", tags=["alerts"])
# Permission runs before any lookup: denied roles learn nothing about which alerts exist.
AlertReader = Annotated[User, Depends(require(Permission.ALERT_READ))]


@router.get("")
def list_alerts(
    user: AlertReader,
    session: DbSession,
    request: Request,
    page: Page,
    case_id: Annotated[str | None, Query(max_length=64)] = None,
    rule_id: Annotated[str | None, Query(max_length=64)] = None,
) -> PageResponse[AlertOut]:
    items, total = service.list_alerts(session, page, case_id=case_id, rule_id=rule_id)
    audit.record(
        session,
        action="alert.list.viewed",
        outcome=Outcome.SUCCESS,
        actor_user_id=user.id,
        request_id=request_id_of(request),
        resource_type="alert",
    )
    return page_of(items, total, page)


@router.get("/{alert_id}")
def get_alert(
    alert_id: str, user: AlertReader, session: DbSession, request: Request
) -> DataResponse[AlertOut]:
    alert = service.get_alert(session, alert_id)
    audit.record(
        session,
        action="alert.viewed",
        outcome=Outcome.SUCCESS,
        actor_user_id=user.id,
        request_id=request_id_of(request),
        resource_type="alert",
        resource_id=alert_id,
    )
    return DataResponse(data=alert)
