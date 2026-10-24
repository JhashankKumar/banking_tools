import uuid
from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, StringConstraints

from app.modules.copilot.answer import CopilotAnswer

Question = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1000)]


class QuestionIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    chat_id: uuid.UUID | None = None
    question: Question


class ChatSummaryOut(BaseModel):
    id: uuid.UUID
    title: str
    author_username: str
    updated_at: datetime
    message_count: int
    is_own: bool


class MessageOut(BaseModel):
    id: uuid.UUID
    role: Literal["user", "assistant"]
    question: str | None
    answer: CopilotAnswer | None
    created_at: datetime


class ChatOut(BaseModel):
    id: uuid.UUID
    title: str
    author_username: str
    is_own: bool
    messages: list[MessageOut]


class AskOut(BaseModel):
    chat: ChatSummaryOut
    message: MessageOut
