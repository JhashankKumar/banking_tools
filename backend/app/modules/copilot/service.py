"""Chats and questions. Chats are private to their author; supervisors may read any chat."""

import json
import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.dependencies import AuditTrail
from app.api.pagination import PageParams, count_rows, paged
from app.core.config import Settings
from app.core.errors import AppError, NotFoundError
from app.core.permissions import Permission, has_permission
from app.modules.cases.service import ensure_case_exists
from app.modules.copilot.answer import (
    CopilotAnswer,
    decline_answer,
    is_customer_info_request,
)
from app.modules.copilot.harness import CopilotUnavailableError, run_copilot
from app.modules.copilot.limits import (
    CopilotBudgetExceededError,
    CopilotLimitError,
    check_limits,
    lock_questions,
    record_run,
)
from app.modules.copilot.models import CopilotChat, CopilotMessage, MessageRole, RunOutcome
from app.modules.copilot.provider import ChatMessage, ModelProvider
from app.modules.copilot.schemas import (
    AskOut,
    ChatOut,
    ChatSummaryOut,
    MessageOut,
    QuestionIn,
)
from app.modules.copilot.tools import ToolContext
from app.modules.users.models import User

TITLE_LENGTH = 60


class ChatNotFoundError(NotFoundError):
    code = "COPILOT_CHAT_NOT_FOUND"
    message = "Chat not found"


class ChatReadOnlyError(AppError):
    status = 403
    code = "COPILOT_CHAT_READ_ONLY"
    message = "This chat belongs to another user. Start your own chat to ask questions."


def _is_supervisor(user: User) -> bool:
    return has_permission(user.role, Permission.CASE_TRANSITION)


def _message_count():
    return (
        select(func.count(CopilotMessage.id))
        .where(CopilotMessage.chat_id == CopilotChat.id)
        .correlate(CopilotChat)
        .scalar_subquery()
    )


def _summaries_query(case_id: str, user: User):
    query = (
        select(CopilotChat, User.username, _message_count())
        .join(User, User.id == CopilotChat.author_id)
        .where(CopilotChat.case_id == case_id)
    )
    if not _is_supervisor(user):
        query = query.where(CopilotChat.author_id == user.id)
    return query


def _summary(chat: CopilotChat, author: str, count: int, user: User) -> ChatSummaryOut:
    return ChatSummaryOut(
        id=chat.id,
        title=chat.title,
        author_username=author,
        updated_at=chat.updated_at,
        message_count=count,
        is_own=chat.author_id == user.id,
    )


def list_chats(
    session: Session, case_id: str, user: User, page: PageParams
) -> tuple[list[ChatSummaryOut], int]:
    ensure_case_exists(session, case_id)
    query = _summaries_query(case_id, user)
    rows = session.execute(
        paged(
            query.order_by(
                (CopilotChat.author_id == user.id).desc(), CopilotChat.updated_at.desc()
            ),
            page,
        )
    ).all()
    return [_summary(c, a, n, user) for c, a, n in rows], count_rows(session, query)


def _load_chat(session: Session, case_id: str, chat_id: uuid.UUID, user: User) -> CopilotChat:
    chat = session.get(CopilotChat, chat_id)
    if chat is None or chat.case_id != case_id:
        raise ChatNotFoundError
    if chat.author_id != user.id and not _is_supervisor(user):
        raise ChatNotFoundError  # Never reveal that another analyst's chat exists.
    return chat


def _messages(session: Session, chat_id: uuid.UUID) -> list[CopilotMessage]:
    return list(
        session.scalars(
            select(CopilotMessage)
            .where(CopilotMessage.chat_id == chat_id)
            .order_by(CopilotMessage.created_at, CopilotMessage.role)
        )
    )


def _message_out(m: CopilotMessage) -> MessageOut:
    return MessageOut(
        id=m.id,
        role=m.role.value,
        question=m.question,
        answer=CopilotAnswer.model_validate(m.answer) if m.answer is not None else None,
        created_at=m.created_at,
    )


def get_chat(session: Session, case_id: str, chat_id: uuid.UUID, user: User) -> ChatOut:
    ensure_case_exists(session, case_id)
    chat = _load_chat(session, case_id, chat_id, user)
    author = session.get_one(User, chat.author_id)
    return ChatOut(
        id=chat.id,
        title=chat.title,
        author_username=author.username,
        is_own=chat.author_id == user.id,
        messages=[_message_out(m) for m in _messages(session, chat.id)],
    )


def _history(session: Session, chat_id: uuid.UUID, limit: int) -> list[ChatMessage]:
    """Earlier turns as model context: questions verbatim, answers as their JSON."""
    if limit == 0:
        return []
    out: list[ChatMessage] = []
    for m in _messages(session, chat_id)[-limit:]:
        if m.role == MessageRole.USER:
            out.append(ChatMessage("user", m.question))
        elif m.answer is not None:
            prior = {k: v for k, v in m.answer.items() if k != "steps"}
            out.append(ChatMessage("assistant", json.dumps(prior, ensure_ascii=False)))
    return out


def _add_message(
    session: Session,
    chat: CopilotChat,
    role: MessageRole,
    *,
    question: str | None = None,
    answer: CopilotAnswer | None = None,
    run_id: uuid.UUID | None = None,
) -> CopilotMessage:
    message = CopilotMessage(
        chat_id=chat.id,
        role=role,
        question=question,
        answer=answer.model_dump(mode="json") if answer is not None else None,
        run_id=run_id,
        # Set here (not server now()): both messages of one request need distinct times.
        created_at=datetime.now(UTC),
    )
    session.add(message)
    chat.updated_at = message.created_at
    session.flush()
    return message


def _ask_out(session: Session, chat: CopilotChat, message: CopilotMessage, user: User) -> AskOut:
    count = session.scalar(
        select(func.count(CopilotMessage.id)).where(CopilotMessage.chat_id == chat.id)
    )
    return AskOut(
        chat=_summary(chat, user.username, count or 0, user),
        message=_message_out(message),
    )


def ask(
    session: Session,
    provider: ModelProvider | None,
    case_id: str,
    user: User,
    data: QuestionIn,
    *,
    trail: AuditTrail,
    settings: Settings,
) -> AskOut:
    ensure_case_exists(session, case_id)
    chat: CopilotChat | None = None
    if data.chat_id is not None:
        chat = _load_chat(session, case_id, data.chat_id, user)
        if chat.author_id != user.id:
            raise ChatReadOnlyError

    lock_questions(session, user.id)  # Held until this request's transaction ends.
    try:
        budget_left = check_limits(session, user.id, datetime.now(UTC), settings)
    except CopilotLimitError:
        record_run(
            session,
            user_id=user.id,
            case_id=case_id,
            chat_id=chat.id if chat else None,
            outcome=RunOutcome.LIMITED,
            model="none",
        )
        session.commit()  # Keep the record even though the request is about to fail.
        raise

    if chat is None:
        chat = CopilotChat(case_id=case_id, author_id=user.id, title=data.question[:TITLE_LENGTH])
        session.add(chat)
        session.flush()
    history = _history(session, chat.id, settings.copilot_history_messages)
    _add_message(session, chat, MessageRole.USER, question=data.question)

    if is_customer_info_request(data.question):
        run = record_run(
            session,
            user_id=user.id,
            case_id=case_id,
            chat_id=chat.id,
            outcome=RunOutcome.DECLINED,
            model="none",
        )
        reply = _add_message(
            session, chat, MessageRole.ASSISTANT, answer=decline_answer(), run_id=run.id
        )
        trail.success(
            "copilot.declined",
            resource_type="case",
            resource_id=case_id,
            details={"chat_id": str(chat.id)},
        )
        return _ask_out(session, chat, reply, user)

    try:
        if provider is None:
            raise CopilotUnavailableError
        result = run_copilot(
            provider,
            ToolContext(session=session, case_id=case_id, user=user),
            question=data.question,
            history=history,
            settings=settings,
            max_cost_usd=budget_left,
        )
    except (CopilotUnavailableError, CopilotBudgetExceededError) as error:
        record_run(
            session,
            user_id=user.id,
            case_id=case_id,
            chat_id=chat.id,
            outcome=RunOutcome.FAILED,
            model=settings.openrouter_model,
            tool_calls=error.tool_calls,
            usage=error.usage,  # What the failed run already cost counts against the limits.
        )
        session.commit()  # The question stays in the chat; the run is metered.
        raise

    declined = result.answer.kind == "decline"  # The model judged the question out of scope.
    run = record_run(
        session,
        user_id=user.id,
        case_id=case_id,
        chat_id=chat.id,
        outcome=RunOutcome.DECLINED if declined else RunOutcome.ANSWERED,
        model=result.model,
        tool_calls=len(result.tool_names),
        usage=result.usage,
        latency_ms=result.latency_ms,
    )
    reply = _add_message(session, chat, MessageRole.ASSISTANT, answer=result.answer, run_id=run.id)
    trail.success(
        "copilot.declined" if declined else "copilot.asked",
        resource_type="case",
        resource_id=case_id,
        details={
            "chat_id": str(chat.id),
            "tools": ",".join(result.tool_names),
            "prompt_tokens": str(result.usage.prompt_tokens),
            "completion_tokens": str(result.usage.completion_tokens),
            "cost_usd": f"{result.usage.cost_usd:.6f}",
            "latency_ms": str(result.latency_ms),
        },
    )
    return _ask_out(session, chat, reply, user)
