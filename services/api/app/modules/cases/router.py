from typing import Annotated

from fastapi import APIRouter, Depends, Request

from app.api.dependencies import DbSession, request_id_of, require
from app.api.pagination import Page
from app.api.responses import DataResponse, PageResponse, page_of
from app.core.permissions import Permission
from app.modules.audit import service as audit
from app.modules.audit.models import Outcome
from app.modules.cases import service
from app.modules.cases.schemas import CaseOut
from app.modules.transactions import service as transactions
from app.modules.transactions.schemas import TransactionOut
from app.modules.users.models import User

router = APIRouter(prefix="/cases", tags=["cases"])

# The permission dependency runs before any lookup, so a denied role learns nothing about
# whether a case exists.
CaseReader = Annotated[User, Depends(require(Permission.CASE_READ))]
TransactionReader = Annotated[User, Depends(require(Permission.TRANSACTION_READ))]


@router.get("/{case_id}")
def get_case(
    case_id: str, user: CaseReader, session: DbSession, request: Request
) -> DataResponse[CaseOut]:
    case = service.get_case(session, case_id)
    audit.record(
        session,
        action="case.viewed",
        outcome=Outcome.SUCCESS,
        actor_user_id=user.id,
        request_id=request_id_of(request),
        resource_type="case",
        resource_id=case_id,
    )
    return DataResponse(data=case)


@router.get("/{case_id}/transactions")
def list_case_transactions(
    case_id: str, user: TransactionReader, session: DbSession, request: Request, page: Page
) -> PageResponse[TransactionOut]:
    service.ensure_case_exists(session, case_id)
    items, total = transactions.list_case_transactions(session, case_id, page)
    audit.record(
        session,
        action="case.transactions.viewed",
        outcome=Outcome.SUCCESS,
        actor_user_id=user.id,
        request_id=request_id_of(request),
        resource_type="case",
        resource_id=case_id,
    )
    return page_of(items, total, page)
