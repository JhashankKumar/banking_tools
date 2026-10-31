"""Every check in the catalogue passes against the real defences on the seeded casebook."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.modules.cases.models import Case, CaseStatus
from app.modules.copilot.models import CopilotRun, RunOutcome
from app.modules.notes.models import CaseNote, CaseNoteVersion, NoteOrigin, NoteStatus
from app.modules.safety.registry import CATALOGUE
from app.modules.users.models import Role
from tests.factories import make_user
from tests.security.conftest import Run

EXPECTED_IDS = {
    *(f"INJ-0{i}" for i in range(1, 6)),
    *(f"CUS-0{i}" for i in range(1, 10)),
    *(f"ACC-0{i}" for i in range(1, 8)),
    *(f"TOOL-0{i}" for i in range(1, 5)),
    *(f"GRD-0{i}" for i in range(1, 5)),
    "LIM-01",
    "LIM-02",
    "AUD-01",
    "AUD-02",
}


def test_catalogue_has_expected_checks() -> None:
    assert EXPECTED_IDS <= {c.id for c in CATALOGUE}


@pytest.mark.parametrize("check", CATALOGUE, ids=lambda c: c.id)
def test_every_check_passes(casebook: None, run: Run, check: object) -> None:
    [result] = run([check]).results

    assert result.status == "passed", result.observed


def test_checks_ignore_real_budget_usage(db_session: Session, casebook: None, run: Run) -> None:
    spender = make_user(db_session, username="real.spender", role=Role.ANALYST)
    db_session.add(
        CopilotRun(
            user_id=spender.id,
            case_id="FR-10482",
            outcome=RunOutcome.ANSWERED,
            model="fake/m",
            cost_usd=get_settings().copilot_daily_budget_usd + Decimal("1"),
            created_at=datetime.now(UTC),
        )
    )
    db_session.commit()

    results = [r for r in run().results if r.category != "Limits"]

    assert [r.id for r in results if r.status != "passed"] == []


NOTE_CHECKS = ("ACC-04", "ACC-07", "GRD-04")


@pytest.mark.parametrize("status", [CaseStatus.CLOSED, CaseStatus.IN_REVIEW])
def test_note_checks_pass_whatever_the_case_state(
    db_session: Session, casebook: None, run: Run, status: CaseStatus
) -> None:
    """A demo database that has been used (note pending, case closed) must not fail checks."""
    author = make_user(db_session, username="earlier.analyst", role=Role.ANALYST)
    note = CaseNote(
        case_id="FR-10482",
        author_id=author.id,
        status=NoteStatus.AWAITING_REVIEW,
        origin=NoteOrigin.WRITTEN,
        current_version=1,
    )
    db_session.add(note)
    db_session.flush()
    db_session.add(
        CaseNoteVersion(
            note_id=note.id, version=1, body="Earlier note", cited_ids=[], edited_by=author.id
        )
    )
    db_session.get_one(Case, "FR-10482").status = status
    db_session.commit()

    results = run([c for c in CATALOGUE if c.id in NOTE_CHECKS]).results

    assert [(r.id, r.status) for r in results if r.status != "passed"] == []
