import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Request, status

from app.api.dependencies import DbSession, request_id_of, require
from app.api.pagination import Page
from app.api.responses import DataResponse, PageResponse, page_of
from app.core.permissions import Permission
from app.modules.users import service
from app.modules.users.models import User
from app.modules.users.schemas import UserCreate, UserOut, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])
Supervisor = Annotated[User, Depends(require(Permission.USER_MANAGE))]


@router.get("")
def list_users(actor: Supervisor, session: DbSession, page: Page) -> PageResponse[UserOut]:
    users, total = service.list_users(session, page)
    return page_of([UserOut.model_validate(u) for u in users], total, page)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_user(
    data: UserCreate, actor: Supervisor, session: DbSession, request: Request
) -> DataResponse[UserOut]:
    user = service.create_user(session, actor=actor, data=data, request_id=request_id_of(request))
    return DataResponse(data=UserOut.model_validate(user))


@router.patch("/{user_id}")
def update_user(
    user_id: uuid.UUID, data: UserUpdate, actor: Supervisor, session: DbSession, request: Request
) -> DataResponse[UserOut]:
    user = service.update_user(
        session, actor=actor, user_id=user_id, data=data, request_id=request_id_of(request)
    )
    return DataResponse(data=UserOut.model_validate(user))
