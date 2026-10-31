"""Access control: roles, chat privacy and the four-eyes rule hold whatever is asked."""

import json
from datetime import UTC, datetime

from app.api.dependencies import get_current_user, require
from app.core.errors import ForbiddenError, NotAuthenticatedError
from app.core.permissions import Permission
from app.core.security import create_access_token
from app.modules.copilot import service as copilot
from app.modules.copilot.harness import run_copilot
from app.modules.copilot.provider import FakeModelProvider, fake_text, fake_tool_call
from app.modules.copilot.tools import ToolContext
from app.modules.notes import service as notes
from app.modules.notes.models import ReviewDecision
from app.modules.notes.schemas import NoteCreate, ReviewIn
from app.modules.safety.checks.customer_info import CUSTOMER_INFO_QUESTIONS
from app.modules.safety.context import CheckContext
from app.modules.safety.contract import CheckOutcome, SafetyCheck, failed, passed
from app.modules.users.models import Role, User

CASE = "FR-10482"
NOTE_BODY = "What the records show\n- TX-1001 moved INR 48500.00 [EV-10482-TX-1001]"
_DECLINED = CUSTOMER_INFO_QUESTIONS[0]  # Opens a chat without any model call.


def _chat_of(ctx: CheckContext, user: User):
    return ctx.ask(user, CASE, _DECLINED, FakeModelProvider([])).chat.id


def _acc_01(ctx: CheckContext) -> CheckOutcome:
    ctx.require_case(CASE)
    chat_id = _chat_of(ctx, ctx.user(Role.ANALYST))
    try:
        copilot.get_chat(ctx.session, CASE, chat_id, ctx.user(Role.ANALYST, "2"))
    except copilot.ChatNotFoundError:
        return passed("Reported as not found; the other analyst's chat was not revealed.")
    return failed("Another analyst's chat was readable.")


def _acc_02(ctx: CheckContext) -> CheckOutcome:
    ctx.require_case(CASE)
    chat_id = _chat_of(ctx, ctx.user(Role.ANALYST))
    try:
        ctx.ask(
            ctx.user(Role.SUPERVISOR), CASE, "Add this.", FakeModelProvider([]), chat_id=chat_id
        )
    except copilot.ChatReadOnlyError:
        return passed("The supervisor could read the chat but not post into it.")
    return failed("A supervisor posted into an analyst's chat.")


def _acc_03(ctx: CheckContext) -> CheckOutcome:
    ctx.require_case(CASE)
    provider = FakeModelProvider(
        [
            fake_tool_call("get_transactions", {}),
            fake_text(json.dumps({"kind": "answer", "not_established": ["Anything."]})),
        ]
    )
    run_copilot(
        provider,
        ToolContext(session=ctx.session, case_id=CASE, user=ctx.user(Role.AUDITOR)),
        question="List the transactions.",
        history=[],
        settings=ctx.settings,
    )
    [reply] = [m.content or "" for m in provider.calls[-1][0] if m.role == "tool"]
    if json.loads(reply) != {"error": "Not permitted for your role"}:
        return failed("A tool returned case data to a role without case access.")
    return passed(
        "Defence in depth: even past a missing route check, the tool refused the auditor."
    )


def _note(ctx: CheckContext, author: User, *, submit: bool = True):
    note = notes.create_note(
        ctx.session, CASE, author, NoteCreate(body=NOTE_BODY), ctx.trail(author)
    )
    if submit:
        note = notes.submit_note(ctx.session, CASE, note.id, author, ctx.trail(author))
    return note


def _acc_04(ctx: CheckContext) -> CheckOutcome:
    ctx.fresh_case(CASE)
    analyst = ctx.user(Role.ANALYST)
    try:
        require(Permission.CASE_TRANSITION)(analyst, ctx.session, ctx.request())
        return failed("An analyst passed the reviewer permission check.")
    except ForbiddenError:
        pass
    supervisor = ctx.user(Role.SUPERVISOR)
    note = _note(ctx, supervisor)
    approve = ReviewIn(decision=ReviewDecision.APPROVE_KEEP_OPEN)
    try:
        notes.review_note(ctx.session, CASE, note.id, supervisor, approve, ctx.trail(supervisor))
    except notes.NoteSelfReviewError:
        return passed("Analysts cannot review; a supervisor cannot approve their own note.")
    return failed("A supervisor approved their own note.")


def _acc_05(ctx: CheckContext) -> CheckOutcome:
    analyst = ctx.user(Role.ANALYST)
    try:
        require(Permission.USER_MANAGE)(analyst, ctx.session, ctx.request("/api/v1/users"))
    except ForbiddenError:
        if len(ctx.audit_rows("access.denied")) == 1:
            return passed("Refused with 403, and the refusal was audited as access.denied.")
        return failed("Refused, but no access.denied audit row was written.")
    return failed("An analyst passed the user-management permission check.")


def _acc_06(ctx: CheckContext) -> CheckOutcome:
    user = ctx.user(Role.ANALYST)
    token = create_access_token(user.id, datetime.now(UTC))
    if get_current_user(ctx.session, token).id != user.id:
        return failed("A valid token was not accepted, so nothing was tested.")
    user.is_active = False
    ctx.session.flush()
    try:
        get_current_user(ctx.session, token)
    except NotAuthenticatedError:
        return passed("The same token was refused as soon as the user was deactivated.")
    return failed("A deactivated user's token was still accepted.")


def _acc_07(ctx: CheckContext) -> CheckOutcome:
    ctx.fresh_case(CASE)
    analyst = ctx.user(Role.ANALYST)
    _note(ctx, analyst)
    second = _note(ctx, analyst, submit=False)
    try:
        notes.submit_note(ctx.session, CASE, second.id, analyst, ctx.trail(analyst))
    except notes.NoteReviewPendingError:
        return passed("The second submission was refused while the first awaits review.")
    return failed("Two notes were awaiting review on one case.")


CHECKS = [
    SafetyCheck(
        id="ACC-01",
        category="Access control",
        attack="An analyst opens another analyst's copilot chat.",
        defence="Chats are private to their author; others get not-found.",
        run=_acc_01,
    ),
    SafetyCheck(
        id="ACC-02",
        category="Access control",
        attack="A supervisor asks a question inside an analyst's chat.",
        defence="Supervisors may read other people's chats, never post into them.",
        run=_acc_02,
    ),
    SafetyCheck(
        id="ACC-03",
        category="Access control",
        attack="The copilot runs for an auditor and asks for case transactions.",
        defence="Every tool call re-checks the user's role.",
        run=_acc_03,
    ),
    SafetyCheck(
        id="ACC-04",
        category="Access control",
        attack="An analyst reviews a note, and a supervisor approves their own note.",
        defence="Only supervisors review, and never their own note (four-eyes rule).",
        run=_acc_04,
    ),
    SafetyCheck(
        id="ACC-05",
        category="Access control",
        attack="An analyst tries to create or change users.",
        defence="User management needs the supervisor role; refusals are audited.",
        run=_acc_05,
    ),
    SafetyCheck(
        id="ACC-06",
        category="Access control",
        attack="A deactivated user keeps using a token issued before deactivation.",
        defence="Every request re-reads the user and refuses inactive accounts.",
        run=_acc_06,
    ),
    SafetyCheck(
        id="ACC-07",
        category="Access control",
        attack="A second note is submitted while another awaits review on the same case.",
        defence="One note under review per case, enforced in the service and the database.",
        run=_acc_07,
    ),
]
