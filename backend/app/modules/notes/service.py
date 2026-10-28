"""Case notes, supervisor review, and case status changes.

Notes are case records (any case reader sees them; only the author edits or submits). A case has
at most one note awaiting review. Status moves only through `next_case_status`: submission is
the one automatic change (Open → In review); every other change is a supervisor's decision.
"""

import re
import uuid
from datetime import UTC, datetime
from typing import Literal

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.dependencies import AuditTrail
from app.api.pagination import PageParams, count_rows, paged
from app.core.errors import AppError, NotFoundError
from app.core.permissions import Permission, has_permission
from app.modules.cases.models import Case, CaseStatus, case_transactions
from app.modules.cases.service import CaseNotFoundError
from app.modules.copilot.models import CopilotChat, CopilotMessage, MessageRole
from app.modules.evidence.models import Evidence
from app.modules.graph import service as graph
from app.modules.notes.models import (
    CaseNote,
    CaseNoteVersion,
    CaseStatusChange,
    NoteOrigin,
    NoteReview,
    NoteStatus,
    ReviewDecision,
)
from app.modules.notes.schemas import (
    CloseIn,
    NoteCreate,
    NoteOut,
    NoteUpdate,
    ReviewIn,
    ReviewOut,
    ReviewQueueItem,
    StatusChangeOut,
    VersionOut,
)
from app.modules.users.models import User

StatusEvent = Literal[
    "submit", "return", "approve_keep_open", "approve_escalate", "approve_close", "close"
]
_CITED = re.compile(r"\b(?:EV-[A-Z0-9-]+|TX-\d+)\b")
_EDITABLE = (NoteStatus.DRAFT, NoteStatus.RETURNED)


class CaseStatusConflictError(AppError):
    status = 409
    code = "CASE_STATUS_CONFLICT"
    message = "That action is not possible for the case's current status."


class NoteNotFoundError(NotFoundError):
    code = "NOTE_NOT_FOUND"
    message = "Note not found"


class NoteForbiddenError(AppError):
    status = 403
    code = "NOTE_FORBIDDEN"
    message = "Only the note's author can change or submit it."


class NoteStatusConflictError(AppError):
    status = 409
    code = "NOTE_STATUS_CONFLICT"
    message = "That action is not possible for the note's current status."


class NoteReviewPendingError(AppError):
    status = 409
    code = "NOTE_REVIEW_PENDING"
    message = "Another note on this case is already awaiting review."


class NoteSelfReviewError(AppError):
    status = 409
    code = "NOTE_SELF_REVIEW"
    message = "You can't review your own note. Another supervisor must review it."


class NoteCitationInvalidError(AppError):
    status = 422
    code = "NOTE_CITATION_INVALID"
    message = "The note cites records that are not part of this case."

    def __init__(self, unknown: list[str]) -> None:
        super().__init__(self.message)
        self.details = [{"field": "body", "message": f"Unknown citation {i}"} for i in unknown]


class NoteSourceInvalidError(AppError):
    status = 422
    code = "VALIDATION_FAILED"
    message = "Request validation failed"
    details = ({"field": "body.source_message_id", "message": "Not one of your copilot answers"},)


_ALLOWED: dict[tuple[CaseStatus, StatusEvent], CaseStatus] = {
    (CaseStatus.OPEN, "submit"): CaseStatus.IN_REVIEW,
    (CaseStatus.ESCALATED, "submit"): CaseStatus.ESCALATED,
    (CaseStatus.IN_REVIEW, "return"): CaseStatus.OPEN,
    (CaseStatus.ESCALATED, "return"): CaseStatus.ESCALATED,
    (CaseStatus.IN_REVIEW, "approve_keep_open"): CaseStatus.OPEN,
    (CaseStatus.ESCALATED, "approve_keep_open"): CaseStatus.ESCALATED,
    (CaseStatus.IN_REVIEW, "approve_escalate"): CaseStatus.ESCALATED,
    (CaseStatus.ESCALATED, "approve_escalate"): CaseStatus.ESCALATED,
    (CaseStatus.IN_REVIEW, "approve_close"): CaseStatus.CLOSED,
    (CaseStatus.ESCALATED, "approve_close"): CaseStatus.CLOSED,
    (CaseStatus.ESCALATED, "close"): CaseStatus.CLOSED,
}


def next_case_status(current: CaseStatus, event: StatusEvent) -> CaseStatus:
    """The case status after `event`; a review never silently undoes an escalation."""
    try:
        return _ALLOWED[(current, event)]
    except KeyError:
        raise CaseStatusConflictError from None


def extract_cited_ids(body: str) -> list[str]:
    return list(dict.fromkeys(_CITED.findall(body)))


def _now() -> datetime:
    # Python time, not now(): rows written in one transaction must keep their real order.
    return datetime.now(UTC)


def _case(session: Session, case_id: str, *, lock: bool = False) -> Case:
    # lock: row lock until commit, so concurrent reviews or closes cannot interleave.
    case = session.get(Case, case_id, with_for_update=lock, populate_existing=lock)
    if case is None:
        raise CaseNotFoundError
    return case


def _validated_citations(session: Session, case_id: str, body: str) -> list[str]:
    cited = extract_cited_ids(body)
    evidence = set(
        session.scalars(
            select(Evidence.id).where(
                Evidence.case_id == case_id,
                Evidence.id.in_([c for c in cited if c.startswith("EV-")]),
            )
        )
    )
    transactions: set[str] = set()
    if any(c.startswith("TX-") for c in cited):
        # This case's transactions plus those around it that the copilot can show (widest window).
        neighbourhood = {
            e.transaction_id for e in graph.get_case_graph(session, case_id, window_hours=168).edges
        }
        in_case = session.scalars(
            select(case_transactions.c.transaction_id).where(case_transactions.c.case_id == case_id)
        )
        transactions = set(in_case) | neighbourhood
    unknown = [c for c in cited if c not in evidence | transactions]
    if unknown:
        raise NoteCitationInvalidError(unknown)
    return cited


def _username(session: Session, user_id: uuid.UUID) -> str:
    return session.get_one(User, user_id).username


def note_out(session: Session, note: CaseNote, user: User) -> NoteOut:
    versions = list(
        session.scalars(
            select(CaseNoteVersion)
            .where(CaseNoteVersion.note_id == note.id)
            .order_by(CaseNoteVersion.version)
        )
    )
    reviews = list(
        session.scalars(
            select(NoteReview).where(NoteReview.note_id == note.id).order_by(NoteReview.created_at)
        )
    )
    current = versions[-1]
    return NoteOut(
        id=note.id,
        case_id=note.case_id,
        status=note.status,
        origin=note.origin,
        author_username=_username(session, note.author_id),
        current_version=note.current_version,
        body=current.body,
        cited_ids=current.cited_ids,
        created_at=note.created_at,
        updated_at=note.updated_at,
        can_edit=note.author_id == user.id and note.status in _EDITABLE,
        can_review=(
            note.status == NoteStatus.AWAITING_REVIEW
            and note.author_id != user.id
            and has_permission(user.role, Permission.CASE_TRANSITION)
        ),
        reviews=[
            ReviewOut(
                decision=r.decision,
                version=r.version,
                reviewer_username=_username(session, r.reviewer_id),
                comment=r.comment,
                reason=r.reason,
                created_at=r.created_at,
            )
            for r in reviews
        ],
        versions=[
            VersionOut(
                version=v.version,
                edited_by_username=_username(session, v.edited_by),
                created_at=v.created_at,
            )
            for v in versions
        ],
    )


def list_notes(
    session: Session, case_id: str, user: User, page: PageParams
) -> tuple[list[NoteOut], int]:
    _case(session, case_id)
    query = select(CaseNote).where(CaseNote.case_id == case_id)
    notes = session.scalars(paged(query.order_by(CaseNote.created_at.desc()), page))
    return [note_out(session, n, user) for n in notes], count_rows(session, query)


def _load_note(
    session: Session, case_id: str, note_id: uuid.UUID, *, lock: bool = False
) -> CaseNote:
    note = session.get(CaseNote, note_id, with_for_update=lock, populate_existing=lock)
    if note is None or note.case_id != case_id:
        raise NoteNotFoundError
    return note


def _add_version(session: Session, note: CaseNote, body: str, cited: list[str], user: User) -> None:
    session.add(
        CaseNoteVersion(
            note_id=note.id,
            version=note.current_version,
            body=body,
            cited_ids=cited,
            edited_by=user.id,
            created_at=_now(),
        )
    )
    session.flush()


def _audit_note(trail: AuditTrail, action: str, note: CaseNote, **details: str) -> None:
    trail.success(
        action,
        resource_type="case_note",
        resource_id=str(note.id),
        details={"case_id": note.case_id, "version": str(note.current_version), **details},
    )


def create_note(
    session: Session, case_id: str, user: User, data: NoteCreate, trail: AuditTrail
) -> NoteOut:
    _case(session, case_id)
    if data.source_message_id is not None:
        source = session.execute(
            select(CopilotMessage)
            .join(CopilotChat, CopilotChat.id == CopilotMessage.chat_id)
            .where(
                CopilotMessage.id == data.source_message_id,
                CopilotMessage.role == MessageRole.ASSISTANT,
                CopilotChat.case_id == case_id,
                CopilotChat.author_id == user.id,
            )
        ).scalar_one_or_none()
        if source is None:
            raise NoteSourceInvalidError
    cited = _validated_citations(session, case_id, data.body)
    now = _now()
    note = CaseNote(
        case_id=case_id,
        author_id=user.id,
        status=NoteStatus.DRAFT,
        origin=NoteOrigin.AI_DRAFTED if data.source_message_id else NoteOrigin.WRITTEN,
        source_message_id=data.source_message_id,
        current_version=1,
        created_at=now,
        updated_at=now,
    )
    session.add(note)
    session.flush()
    _add_version(session, note, data.body, cited, user)
    _audit_note(trail, "note.saved", note)
    return note_out(session, note, user)


def _authored(note: CaseNote, user: User) -> None:
    if note.author_id != user.id:
        raise NoteForbiddenError
    if note.status not in _EDITABLE:
        raise NoteStatusConflictError


def update_note(
    session: Session,
    case_id: str,
    note_id: uuid.UUID,
    user: User,
    data: NoteUpdate,
    trail: AuditTrail,
) -> NoteOut:
    note = _load_note(session, case_id, note_id)
    _authored(note, user)
    cited = _validated_citations(session, case_id, data.body)
    note.current_version += 1
    note.updated_at = _now()
    _add_version(session, note, data.body, cited, user)
    _audit_note(trail, "note.saved", note)
    return note_out(session, note, user)


def change_case_status(
    session: Session,
    case: Case,
    to: CaseStatus,
    *,
    actor: User,
    reason: str,
    comment: str | None,
    note_id: uuid.UUID | None,
    trail: AuditTrail,
) -> None:
    """The only place a case status changes; every change is recorded and audited."""
    if to == case.status:
        return
    session.add(
        CaseStatusChange(
            case_id=case.id,
            from_status=case.status,
            to_status=to,
            actor_id=actor.id,
            reason=reason,
            comment=comment,
            note_id=note_id,
            created_at=_now(),
        )
    )
    trail.success(
        "case.status_changed",
        resource_type="case",
        resource_id=case.id,
        details={"from": case.status.value, "to": to.value, "reason": reason},
    )
    case.status = to
    session.flush()


def submit_note(
    session: Session, case_id: str, note_id: uuid.UUID, user: User, trail: AuditTrail
) -> NoteOut:
    _case(session, case_id, lock=True)  # Case first, then note: one lock order everywhere.
    note = _load_note(session, case_id, note_id, lock=True)
    _authored(note, user)
    pending = session.scalar(
        select(CaseNote.id).where(
            CaseNote.case_id == case_id, CaseNote.status == NoteStatus.AWAITING_REVIEW
        )
    )
    if pending is not None:  # Checked first: it explains why the case is In review.
        raise NoteReviewPendingError
    case = _case(session, case_id)
    target = next_case_status(case.status, "submit")
    note.status = NoteStatus.AWAITING_REVIEW
    note.updated_at = _now()
    try:
        with session.begin_nested():  # The partial unique index settles concurrent submissions.
            session.flush()
    except IntegrityError:
        raise NoteReviewPendingError from None
    change_case_status(
        session,
        case,
        target,
        actor=user,
        reason="note_submitted",
        comment=None,
        note_id=note.id,
        trail=trail,
    )
    _audit_note(trail, "note.submitted", note)
    return note_out(session, note, user)


_DECISION_EVENT: dict[ReviewDecision, StatusEvent] = {
    ReviewDecision.RETURN: "return",
    ReviewDecision.APPROVE_KEEP_OPEN: "approve_keep_open",
    ReviewDecision.APPROVE_ESCALATE: "approve_escalate",
    ReviewDecision.APPROVE_CLOSE: "approve_close",
}


def review_note(
    session: Session,
    case_id: str,
    note_id: uuid.UUID,
    user: User,
    data: ReviewIn,
    trail: AuditTrail,
) -> NoteOut:
    case = _case(session, case_id, lock=True)  # Case first, then note: one lock order everywhere.
    note = _load_note(session, case_id, note_id, lock=True)
    if note.status != NoteStatus.AWAITING_REVIEW:
        raise NoteStatusConflictError
    if note.author_id == user.id:
        raise NoteSelfReviewError
    target = next_case_status(case.status, _DECISION_EVENT[data.decision])
    returned = data.decision == ReviewDecision.RETURN
    note.status = NoteStatus.RETURNED if returned else NoteStatus.APPROVED
    note.updated_at = _now()
    session.add(
        NoteReview(
            note_id=note.id,
            version=note.current_version,
            reviewer_id=user.id,
            decision=data.decision,
            comment=data.comment,
            reason=data.reason,
            created_at=_now(),
        )
    )
    session.flush()
    change_case_status(
        session,
        case,
        target,
        actor=user,
        reason=data.reason or data.decision.value,
        comment=data.comment,
        note_id=note.id,
        trail=trail,
    )
    _audit_note(
        trail, "note.returned" if returned else "note.approved", note, decision=data.decision.value
    )
    return note_out(session, note, user)


def close_case(
    session: Session, case_id: str, user: User, data: CloseIn, trail: AuditTrail
) -> None:
    case = _case(session, case_id, lock=True)
    pending = session.scalar(
        select(CaseNote.id).where(
            CaseNote.case_id == case_id, CaseNote.status == NoteStatus.AWAITING_REVIEW
        )
    )
    if pending is not None:  # Review it first; otherwise it would be stranded on a closed case.
        raise NoteReviewPendingError
    target = next_case_status(case.status, "close")
    change_case_status(
        session,
        case,
        target,
        actor=user,
        reason=data.reason,
        comment=data.comment,
        note_id=None,
        trail=trail,
    )


def list_status_changes(
    session: Session, case_id: str, page: PageParams
) -> tuple[list[StatusChangeOut], int]:
    _case(session, case_id)
    query = select(CaseStatusChange).where(CaseStatusChange.case_id == case_id)
    rows = session.scalars(paged(query.order_by(CaseStatusChange.created_at), page))
    return [
        StatusChangeOut(
            from_status=r.from_status,
            to_status=r.to_status,
            actor_username=_username(session, r.actor_id),
            reason=r.reason,
            comment=r.comment,
            note_id=r.note_id,
            created_at=r.created_at,
        )
        for r in rows
    ], count_rows(session, query)


def review_queue(
    session: Session, user: User, page: PageParams
) -> tuple[list[ReviewQueueItem], int]:
    query = (
        select(CaseNote, Case.title, User.username)
        .join(Case, Case.id == CaseNote.case_id)
        .join(User, User.id == CaseNote.author_id)
        .where(CaseNote.status == NoteStatus.AWAITING_REVIEW, CaseNote.author_id != user.id)
    )
    rows = session.execute(paged(query.order_by(CaseNote.updated_at), page)).all()
    return [
        ReviewQueueItem(
            note_id=note.id,
            case_id=note.case_id,
            case_title=title,
            author_username=author,
            submitted_at=note.updated_at,
        )
        for note, title, author in rows
    ], count_rows(session, query)
