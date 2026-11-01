"""Database-level invariants. These hold even if application code has a bug."""

from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest
from alembic import command
from sqlalchemy import Engine, inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.cases.models import Alert, Case, CaseStatus, PartyType
from app.modules.evidence.models import Evidence, EvidenceLabel, EvidenceType
from app.modules.notes.models import CaseNote, NoteOrigin, NoteStatus
from app.modules.parties.models import Account, AccountStatus, Beneficiary, IdentifierType
from app.modules.transactions.models import Transaction, TransactionStatus
from app.modules.users.models import Role, User
from tests.conftest import TEST_DATABASE_URL, alembic_config

SCENARIO = "test-schema"


@pytest.fixture
def parties(db_session: Session) -> tuple[Account, Beneficiary]:
    account = Account(
        id="ACC-T1", status=AccountStatus.ACTIVE, currency="INR", scenario_id=SCENARIO
    )
    beneficiary = Beneficiary(
        id="BEN-T1",
        display_label="Test Beneficiary",
        identifier_type=IdentifierType.ACCOUNT,
        scenario_id=SCENARIO,
    )
    db_session.add_all([account, beneficiary])
    db_session.flush()
    return account, beneficiary


def make_transaction(**overrides: object) -> Transaction:
    values: dict[str, object] = {
        "id": "TX-T1",
        "source_account_id": "ACC-T1",
        "destination_beneficiary_id": "BEN-T1",
        "amount": Decimal("48500.00"),
        "currency": "INR",
        "occurred_at": datetime(2026, 9, 15, 4, 32, 14, tzinfo=UTC),
        "status": TransactionStatus.SETTLED,
        "source_status": "SUCCESS",
        "scenario_id": SCENARIO,
    }
    values.update(overrides)
    return Transaction(**values)


def assert_rejected(session: Session, row: object) -> None:
    session.add(row)
    with pytest.raises(IntegrityError):
        session.flush()
    session.rollback()


@pytest.mark.usefixtures("parties")
def test_transaction_requires_exactly_one_source(db_session: Session) -> None:
    assert_rejected(db_session, make_transaction(source_account_id=None))
    assert_rejected(db_session, make_transaction(source_beneficiary_id="BEN-T1"))


@pytest.mark.usefixtures("parties")
def test_transaction_requires_exactly_one_destination(db_session: Session) -> None:
    assert_rejected(db_session, make_transaction(destination_beneficiary_id=None))
    assert_rejected(db_session, make_transaction(destination_account_id="ACC-T1"))


@pytest.mark.usefixtures("parties")
def test_transaction_amount_must_be_positive(db_session: Session) -> None:
    assert_rejected(db_session, make_transaction(amount=Decimal("0.00")))


@pytest.mark.usefixtures("parties")
def test_transaction_currency_must_be_three_uppercase_letters(db_session: Session) -> None:
    assert_rejected(db_session, make_transaction(currency="inr"))


@pytest.mark.usefixtures("parties")
def test_transaction_conversion_is_all_or_nothing(db_session: Session) -> None:
    usd = {"amount": Decimal("500.00"), "currency": "USD"}
    assert_rejected(db_session, make_transaction(**usd, fx_rate=Decimal("83.45")))
    assert_rejected(
        db_session,
        make_transaction(**usd, converted_amount=Decimal("41725.00"), converted_currency="INR"),
    )


@pytest.mark.usefixtures("parties")
def test_transaction_conversion_must_be_into_another_currency(db_session: Session) -> None:
    assert_rejected(
        db_session,
        make_transaction(
            converted_amount=Decimal("48500.00"), converted_currency="INR", fx_rate=Decimal("1")
        ),
    )


@pytest.mark.usefixtures("parties")
def test_transaction_conversion_round_trips(db_session: Session) -> None:
    db_session.add(
        make_transaction(
            amount=Decimal("500.00"),
            currency="USD",
            converted_amount=Decimal("41725.00"),
            converted_currency="INR",
            fx_rate=Decimal("83.45"),
        )
    )
    db_session.flush()
    db_session.expire_all()

    tx = db_session.get_one(Transaction, "TX-T1")
    assert (tx.converted_amount, tx.converted_currency, tx.fx_rate) == (
        Decimal("41725.00"),
        "INR",
        Decimal("83.450000"),
    )


@pytest.mark.usefixtures("parties")
def test_amount_round_trips_as_decimal(db_session: Session) -> None:
    db_session.add(make_transaction())
    db_session.flush()
    db_session.expire_all()

    stored = db_session.get_one(Transaction, "TX-T1")

    assert type(stored.amount) is Decimal
    assert stored.amount == Decimal("48500.00")


@pytest.mark.usefixtures("parties")
def test_occurred_at_round_trips_as_utc(db_session: Session) -> None:
    ist = timezone(timedelta(hours=5, minutes=30))
    db_session.add(make_transaction(occurred_at=datetime(2026, 9, 15, 10, 2, 14, tzinfo=ist)))
    db_session.flush()
    db_session.expire_all()

    stored = db_session.get_one(Transaction, "TX-T1")

    assert stored.occurred_at.utcoffset() == timedelta(0)
    assert stored.occurred_at == datetime(2026, 9, 15, 4, 32, 14, tzinfo=UTC)


def test_evidence_id_format_enforced(db_session: Session) -> None:
    db_session.add(
        Case(
            id="FR-T1",
            title="Test case",
            status=CaseStatus.OPEN,
            opened_at=datetime(2026, 9, 15, tzinfo=UTC),
            scenario_id=SCENARIO,
        )
    )
    db_session.flush()

    assert_rejected(
        db_session,
        Evidence(
            id="not-an-evidence-id",
            case_id="FR-T1",
            evidence_type=EvidenceType.TRANSACTION,
            source_table="transactions",
            source_record_id="TX-T1",
            label=EvidenceLabel.OBSERVED_FACT,
            scenario_id=SCENARIO,
        ),
    )


def test_migration_downgrade_then_upgrade(engine: Engine) -> None:
    config = alembic_config(TEST_DATABASE_URL)

    command.downgrade(config, "base")
    command.upgrade(config, "head")


def make_alert(alert_id: str) -> Alert:
    return Alert(
        id=alert_id,
        rule_id="RAPID_ONWARD_TRANSFER",
        rule_version="1",
        rule_code="ROT",
        entity_type=PartyType.BENEFICIARY,
        entity_id="BEN-T1",
        trigger_transaction_id="TX-T1",
        transaction_ids=["TX-T0", "TX-T1"],
        triggered_at=datetime(2026, 9, 15, 4, 37, 42, tzinfo=UTC),
        explanation="Signal for analyst review; not a finding of fraud.",
        metrics={"elapsed_seconds": "328"},
        scenario_id=SCENARIO,
    )


@pytest.mark.usefixtures("parties")
def test_alert_unique_per_rule_and_trigger(db_session: Session) -> None:
    db_session.add(make_transaction())
    db_session.flush()
    db_session.add(make_alert("AL-ROT-TX-T1"))
    db_session.flush()

    assert_rejected(db_session, make_alert("AL-ROT-TX-T1-DUPLICATE"))


@pytest.mark.usefixtures("parties")
def test_alert_transaction_ids_and_metrics_round_trip(db_session: Session) -> None:
    db_session.add(make_transaction())
    db_session.flush()
    db_session.add(make_alert("AL-ROT-TX-T1"))
    db_session.flush()
    db_session.expire_all()

    stored = db_session.get_one(Alert, "AL-ROT-TX-T1")

    assert stored.transaction_ids == ["TX-T0", "TX-T1"]
    assert stored.metrics == {"elapsed_seconds": "328"}
    assert stored.entity_type == PartyType.BENEFICIARY


def test_migration_creates_copilot_and_notes_tables(engine: Engine) -> None:
    tables = set(inspect(engine).get_table_names())

    assert {
        "copilot_chats",
        "copilot_messages",
        "copilot_runs",
        "case_notes",
        "case_note_versions",
        "note_reviews",
        "case_status_changes",
    } <= tables


def test_one_pending_note_per_case_enforced_by_database(db_session: Session) -> None:
    case = Case(
        id="FR-T1",
        title="Schema test case",
        status=CaseStatus.OPEN,
        opened_at=datetime(2026, 9, 15, tzinfo=UTC),
        scenario_id=SCENARIO,
    )
    author = User(username="note.author", password_hash="x", role=Role.ANALYST)
    db_session.add_all([case, author])
    db_session.flush()
    for _ in range(2):
        db_session.add(
            CaseNote(
                case_id="FR-T1",
                author_id=author.id,
                status=NoteStatus.AWAITING_REVIEW,
                origin=NoteOrigin.WRITTEN,
                current_version=1,
            )
        )

    with pytest.raises(IntegrityError):
        db_session.flush()
