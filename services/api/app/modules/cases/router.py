from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request

from app.api.dependencies import DbSession, request_id_of, require
from app.api.pagination import Page
from app.api.responses import DataResponse, PageResponse, page_of
from app.core.permissions import Permission
from app.modules.audit import service as audit
from app.modules.audit.models import Outcome
from app.modules.cases import service
from app.modules.cases.schemas import CaseOut
from app.modules.graph import service as graph
from app.modules.graph.schemas import CaseGraphOut, MoneyPathsOut
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


@router.get("/{case_id}/money-paths")
def get_money_paths(
    case_id: str,
    user: TransactionReader,
    session: DbSession,
    request: Request,
    max_hops: Annotated[int, Query(ge=1, le=5)] = 3,
    window_hours: Annotated[int, Query(ge=1, le=168)] = 24,
) -> DataResponse[MoneyPathsOut]:
    result = graph.get_money_paths(session, case_id, max_hops=max_hops, window_hours=window_hours)
    audit.record(
        session,
        action="case.money_paths.viewed",
        outcome=Outcome.SUCCESS,
        actor_user_id=user.id,
        request_id=request_id_of(request),
        resource_type="case",
        resource_id=case_id,
        details={
            "max_hops": str(max_hops),
            "window_hours": str(window_hours),
            "paths": str(len(result.paths)),
            "truncated": str(result.truncated).lower(),
        },
    )
    return DataResponse(data=result)


@router.get("/{case_id}/graph")
def get_case_graph(
    case_id: str,
    user: TransactionReader,
    session: DbSession,
    request: Request,
    window_hours: Annotated[int, Query(ge=1, le=168)] = 24,
) -> DataResponse[CaseGraphOut]:
    result = graph.get_case_graph(session, case_id, window_hours=window_hours)
    audit.record(
        session,
        action="case.graph.viewed",
        outcome=Outcome.SUCCESS,
        actor_user_id=user.id,
        request_id=request_id_of(request),
        resource_type="case",
        resource_id=case_id,
        details={
            "window_hours": str(window_hours),
            "nodes": str(len(result.nodes)),
            "edges": str(len(result.edges)),
            "truncated": str(result.truncated).lower(),
        },
    )
    return DataResponse(data=result)
