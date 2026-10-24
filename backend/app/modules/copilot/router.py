import uuid
from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import Audit, DbSession, require
from app.api.pagination import Page
from app.api.responses import DataResponse, PageResponse, page_of
from app.core.config import get_settings
from app.core.permissions import Permission
from app.modules.copilot import service
from app.modules.copilot.provider import ModelProvider, get_model_provider
from app.modules.copilot.schemas import AskOut, ChatOut, ChatSummaryOut, QuestionIn
from app.modules.users.models import User

router = APIRouter(prefix="/cases", tags=["copilot"])
CaseReader = Annotated[User, Depends(require(Permission.CASE_READ))]
Provider = Annotated[ModelProvider | None, Depends(get_model_provider)]


@router.get("/{case_id}/chats")
def list_chats(
    case_id: str, user: CaseReader, session: DbSession, page: Page
) -> PageResponse[ChatSummaryOut]:
    items, total = service.list_chats(session, case_id, user, page)
    return page_of(items, total, page)


@router.get("/{case_id}/chats/{chat_id}")
def get_chat(
    case_id: str, chat_id: uuid.UUID, user: CaseReader, session: DbSession
) -> DataResponse[ChatOut]:
    return DataResponse(data=service.get_chat(session, case_id, chat_id, user))


@router.post("/{case_id}/copilot/questions")
def ask(
    case_id: str,
    data: QuestionIn,
    user: CaseReader,
    session: DbSession,
    trail: Audit,
    provider: Provider,
) -> DataResponse[AskOut]:
    answer = service.ask(
        session, provider, case_id, user, data, trail=trail, settings=get_settings()
    )
    return DataResponse(data=answer)
