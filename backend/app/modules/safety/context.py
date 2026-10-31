"""What a check gets: a session inside the run's rolled-back transaction, and helpers."""

import secrets
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

from sqlalchemy import select, update
from sqlalchemy.orm import Session
from starlette.requests import Request

from app.api.dependencies import AuditTrail
from app.core.config import Settings
from app.core.security import hash_password
from app.modules.audit.models import AuditEvent
from app.modules.cases.models import Case, CaseStatus
from app.modules.copilot import service as copilot
from app.modules.copilot.provider import ModelProvider
from app.modules.copilot.schemas import AskOut, QuestionIn
from app.modules.notes.models import CaseNote, NoteStatus
from app.modules.safety.contract import CasebookMissingError
from app.modules.users.models import Role, User


def run_settings(settings: Settings) -> Settings:
    """Generous limits, so real usage by other people cannot fail a check that is not about it."""
    return settings.model_copy(
        update={"copilot_questions_per_hour": 10_000, "copilot_daily_budget_usd": Decimal("1000")}
    )


@dataclass
class CheckContext:
    session: Session
    settings: Settings
    now: datetime
    run_id: uuid.UUID = field(default_factory=uuid.uuid4)
    _users: dict[str, User] = field(default_factory=lambda: {})

    def user(self, role: Role, suffix: str = "") -> User:
        """A throw-away user, created once per run; gone when the run is rolled back."""
        username = f"safety.check.{role.value}{suffix}"
        if username not in self._users:
            user = User(
                username=username,
                password_hash=hash_password(secrets.token_urlsafe(24)),
                role=role,
                is_active=True,
            )
            self.session.add(user)
            self.session.flush()
            self._users[username] = user
        return self._users[username]

    def require_case(self, case_id: str) -> None:
        if self.session.get(Case, case_id) is None:
            raise CasebookMissingError(case_id)

    def fresh_case(self, case_id: str) -> None:
        """Puts a seeded case back to Open with no note under review, whatever earlier demo use
        left behind (rolled back with the run)."""
        self.require_case(case_id)
        self.session.execute(
            update(CaseNote)
            .where(CaseNote.case_id == case_id, CaseNote.status == NoteStatus.AWAITING_REVIEW)
            .values(status=NoteStatus.RETURNED)
        )
        self.session.get_one(Case, case_id).status = CaseStatus.OPEN
        self.session.flush()

    def request(self, path: str = "/safety") -> Request:
        request = Request({"type": "http", "method": "POST", "path": path, "headers": []})
        request.state.request_id = f"safety-{self.run_id}"
        return request

    def trail(self, user: User) -> AuditTrail:
        return AuditTrail(self.session, self.request(), user)

    def ask(
        self,
        user: User,
        case_id: str,
        question: str,
        provider: ModelProvider | None,
        *,
        chat_id: uuid.UUID | None = None,
        settings: Settings | None = None,
    ) -> AskOut:
        """Asks through the production service, exactly as the API route does."""
        return copilot.ask(
            self.session,
            provider,
            case_id,
            user,
            QuestionIn(chat_id=chat_id, question=question),
            trail=self.trail(user),
            settings=settings or self.settings,
        )

    def audit_rows(self, action: str | None = None) -> list[AuditEvent]:
        """This run's audit rows, all or for one action; earlier checks' rows were rolled back."""
        query = select(AuditEvent).where(AuditEvent.request_id == f"safety-{self.run_id}")
        if action is not None:
            query = query.where(AuditEvent.action == action)
        return list(self.session.scalars(query.order_by(AuditEvent.id)))
