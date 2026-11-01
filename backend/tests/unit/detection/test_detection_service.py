from contextlib import nullcontext
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.audit.models import AuditEvent, Outcome
from app.modules.cases.models import Alert, Case, CaseStatus, PartyType, case_transactions
from app.modules.detection.__main__ import main
from app.modules.detection.service import run_detection
from app.modules.evidence.models import Evidence
from app.modules.parties.models import Account, AccountStatus, Beneficiary, IdentifierType
from app.modules.transactions.models import Transaction, TransactionStatus
from app.seed import seed

SCENARIO = "test-detection"


@pytest.fixture(autouse=True)
def seeded(db_session: Session) -> None:
    seed(db_session, demo_password="seed-password-for-tests")
    db_session.commit()


def alerts_for_case(session: Session, case_id: str) -> list[str]:
    return list(session.scalars(select(Alert.id).where(Alert.case_id == case_id)).all())


def test_fr_10482_alert_created_from_rule(db_session: Session) -> None:
    alert = db_session.get_one(Alert, "AL-ROT-TX-1002")

    assert (alert.rule_id, alert.rule_version, alert.rule_code) == (
        "RAPID_ONWARD_TRANSFER",
        "2",
        "ROT",
    )
    assert alert.case_id == "FR-10482"
    assert (alert.entity_type, alert.entity_id) == (PartyType.BENEFICIARY, "BEN-B")
    assert alert.trigger_transaction_id == "TX-1002"
    assert alert.transaction_ids == ["TX-1001", "TX-1002"]
    assert alert.metrics["elapsed_seconds"] == "328"
    assert alert.triggered_at == datetime(2026, 9, 15, 4, 37, 42, tzinfo=UTC)
    assert alert.is_synthetic
    assert alert.scenario_id == "fr-10482"
    assert db_session.get(Evidence, "EV-10482-AL-ROT-TX-1002") is not None


def test_benign_high_value_payment_raises_no_alert(db_session: Session) -> None:
    assert alerts_for_case(db_session, "FR-10483") == []


def test_reversed_incoming_raises_no_alert_end_to_end(db_session: Session) -> None:
    assert db_session.get_one(Transaction, "TX-5002").reversal_of_transaction_id == "TX-5001"
    assert alerts_for_case(db_session, "FR-10485") == []


def test_prompt_injection_case_raises_no_alert(db_session: Session) -> None:
    assert alerts_for_case(db_session, "FR-10486") == []


def test_detection_is_idempotent(db_session: Session) -> None:
    def snapshot() -> tuple[list[tuple[str, str | None]], int]:
        alerts = db_session.execute(select(Alert.id, Alert.case_id).order_by(Alert.id)).all()
        evidence = db_session.scalar(select(func.count()).select_from(Evidence)) or 0
        return [(a, c) for a, c in alerts], evidence

    before = snapshot()
    summary = run_detection(db_session)

    assert summary == {  # one per seeded alert
        "RAPID_ONWARD_TRANSFER": 6,
        "FAN_OUT_SPLIT": 2,
        "FAN_IN_COLLECT": 1,
        "CIRCULAR_FLOW": 1,
    }
    assert snapshot() == before


def _rapid_pair(session: Session, prefix: str) -> str:
    """Insert a pass-through pattern outside any seeded case; return the trigger transaction ID."""
    session.add_all(
        [
            Account(
                id=f"ACC-{prefix}1",
                status=AccountStatus.ACTIVE,
                currency="INR",
                scenario_id=SCENARIO,
            ),
            Beneficiary(
                id=f"BEN-{prefix}",
                display_label="Test",
                identifier_type=IdentifierType.VPA,
                scenario_id=SCENARIO,
            ),
            Account(
                id=f"ACC-{prefix}2",
                status=AccountStatus.ACTIVE,
                currency="INR",
                scenario_id=SCENARIO,
            ),
        ]
    )
    session.flush()
    for tx_id, src, dst, amount, minute in [
        (
            f"TX-{prefix}1",
            ("source_account_id", f"ACC-{prefix}1"),
            ("destination_beneficiary_id", f"BEN-{prefix}"),
            "20000.00",
            0,
        ),
        (
            f"TX-{prefix}2",
            ("source_beneficiary_id", f"BEN-{prefix}"),
            ("destination_account_id", f"ACC-{prefix}2"),
            "19000.00",
            3,
        ),
    ]:
        session.add(
            Transaction(
                id=tx_id,
                **{src[0]: src[1], dst[0]: dst[1]},
                amount=Decimal(amount),
                currency="INR",
                occurred_at=datetime(2026, 10, 1, 6, minute, 0, tzinfo=UTC),
                status=TransactionStatus.SETTLED,
                source_status="SUCCESS",
                scenario_id=SCENARIO,
            )
        )
        session.flush()
    return f"TX-{prefix}2"


def _case(session: Session, case_id: str, transaction_id: str) -> None:
    session.add(
        Case(
            id=case_id,
            title="Test",
            status=CaseStatus.OPEN,
            opened_at=datetime(2026, 10, 1, tzinfo=UTC),
            scenario_id=SCENARIO,
        )
    )
    session.flush()
    session.execute(
        case_transactions.insert().values(case_id=case_id, transaction_id=transaction_id)
    )


def test_alert_case_link_only_when_unambiguous(db_session: Session) -> None:
    no_case_trigger = _rapid_pair(db_session, "N")
    two_case_trigger = _rapid_pair(db_session, "T")
    _case(db_session, "FR-T0001", two_case_trigger)
    _case(db_session, "FR-T0002", two_case_trigger)

    run_detection(db_session)

    for trigger in (no_case_trigger, two_case_trigger):
        alert = db_session.get_one(Alert, f"AL-ROT-{trigger}")
        assert alert.case_id is None
        evidence = db_session.scalar(
            select(func.count()).select_from(Evidence).where(Evidence.source_record_id == alert.id)
        )
        assert evidence == 0


def test_detection_cli_prints_summary(
    db_session: Session, capsys: pytest.CaptureFixture[str]
) -> None:
    main(open_session=lambda: nullcontext(db_session))

    assert "RAPID_ONWARD_TRANSFER: 6" in capsys.readouterr().out


def test_detection_run_is_audited(db_session: Session) -> None:
    run_detection(db_session)

    event = db_session.scalars(
        select(AuditEvent)
        .where(AuditEvent.action == "detection.run")
        .order_by(AuditEvent.id.desc())
    ).first()

    assert event is not None
    assert event.outcome == Outcome.SUCCESS
    assert event.actor_user_id is None
    assert event.details == {
        "RAPID_ONWARD_TRANSFER": "6",
        "FAN_OUT_SPLIT": "2",
        "FAN_IN_COLLECT": "1",
        "CIRCULAR_FLOW": "1",
        "rule_versions": (
            "RAPID_ONWARD_TRANSFER:2,FAN_OUT_SPLIT:1,FAN_IN_COLLECT:1,CIRCULAR_FLOW:1"
        ),
        "new_alerts": "0",
    }


@pytest.mark.parametrize(
    ("alert_id", "rule_id", "case_id", "transaction_ids"),
    [
        ("AL-FOS-TX-9006", "FAN_OUT_SPLIT", "FR-10490", [f"TX-900{i}" for i in range(1, 7)]),
        ("AL-FOS-TX-9406", "FAN_OUT_SPLIT", "FR-10494", [f"TX-940{i}" for i in range(1, 7)]),
        ("AL-FIC-TX-8906", "FAN_IN_COLLECT", "FR-10489", [f"TX-890{i}" for i in range(1, 7)]),
        ("AL-CIR-TX-4003", "CIRCULAR_FLOW", "FR-10484", ["TX-4001", "TX-4002", "TX-4003"]),
    ],
)
def test_new_rules_raise_expected_seeded_alerts(
    db_session: Session, alert_id: str, rule_id: str, case_id: str, transaction_ids: list[str]
) -> None:
    alert = db_session.get_one(Alert, alert_id)
    assert (alert.rule_id, alert.case_id, list(alert.transaction_ids)) == (
        rule_id,
        case_id,
        transaction_ids,
    )
    assert alert.explanation.endswith("Signal for analyst review; not a finding of fraud.")
    assert db_session.get(Evidence, f"EV-{case_id.removeprefix('FR-')}-{alert_id}") is not None


def test_payroll_look_alike_metrics(db_session: Session) -> None:
    metrics = db_session.get_one(Alert, "AL-FOS-TX-9406").metrics
    assert (metrics["outgoing_count"], metrics["onward_share"], metrics["elapsed_seconds"]) == (
        "5",
        "0.80",
        "1200",
    )


def test_merchant_look_alike_raises_no_alert(db_session: Session) -> None:
    assert alerts_for_case(db_session, "FR-10495") == []
