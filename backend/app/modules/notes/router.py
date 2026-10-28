import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.dependencies import Audit, DbSession, require
from app.api.pagination import Page, PageParams
from app.api.responses import DataResponse, PageResponse, page_of
from app.core.permissions import Permission
from app.modules.notes import service
from app.modules.notes.schemas import (
    CloseIn,
    NoteCreate,
    NoteOut,
    NoteUpdate,
    ReviewIn,
    ReviewQueueItem,
    StatusChangeOut,
)
from app.modules.users.models import User

router = APIRouter(prefix="/cases", tags=["notes"])
queue_router = APIRouter(prefix="/notes", tags=["notes"])

CaseReader = Annotated[User, Depends(require(Permission.CASE_READ))]
# Reviewing notes and changing case status are supervisor powers.
Reviewer = Annotated[User, Depends(require(Permission.CASE_TRANSITION))]
_ALL = PageParams(limit=100, offset=0)


@router.get("/{case_id}/notes")
def list_notes(
    case_id: str, user: CaseReader, session: DbSession, page: Page
) -> PageResponse[NoteOut]:
    items, total = service.list_notes(session, case_id, user, page)
    return page_of(items, total, page)


@router.post("/{case_id}/notes", status_code=status.HTTP_201_CREATED)
def create_note(
    case_id: str, data: NoteCreate, user: CaseReader, session: DbSession, trail: Audit
) -> DataResponse[NoteOut]:
    return DataResponse(data=service.create_note(session, case_id, user, data, trail))


@router.patch("/{case_id}/notes/{note_id}")
def update_note(
    case_id: str,
    note_id: uuid.UUID,
    data: NoteUpdate,
    user: CaseReader,
    session: DbSession,
    trail: Audit,
) -> DataResponse[NoteOut]:
    return DataResponse(data=service.update_note(session, case_id, note_id, user, data, trail))


@router.post("/{case_id}/notes/{note_id}/submit")
def submit_note(
    case_id: str, note_id: uuid.UUID, user: CaseReader, session: DbSession, trail: Audit
) -> DataResponse[NoteOut]:
    return DataResponse(data=service.submit_note(session, case_id, note_id, user, trail))


@router.post("/{case_id}/notes/{note_id}/review")
def review_note(
    case_id: str,
    note_id: uuid.UUID,
    data: ReviewIn,
    user: Reviewer,
    session: DbSession,
    trail: Audit,
) -> DataResponse[NoteOut]:
    return DataResponse(data=service.review_note(session, case_id, note_id, user, data, trail))


@router.post("/{case_id}/close")
def close_case(
    case_id: str, data: CloseIn, user: Reviewer, session: DbSession, trail: Audit
) -> DataResponse[list[StatusChangeOut]]:
    service.close_case(session, case_id, user, data, trail)
    items, _total = service.list_status_changes(session, case_id, _ALL)
    return DataResponse(data=items)


@router.get("/{case_id}/status-changes")
def list_status_changes(
    case_id: str, user: CaseReader, session: DbSession, page: Page
) -> PageResponse[StatusChangeOut]:
    items, total = service.list_status_changes(session, case_id, page)
    return page_of(items, total, page)


@queue_router.get("/awaiting-review")
def awaiting_review(
    user: Reviewer, session: DbSession, page: Page
) -> PageResponse[ReviewQueueItem]:
    items, total = service.review_queue(session, user, page)
    return page_of(items, total, page)
