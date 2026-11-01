import random
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from app.modules.detection.facts import Conversion, PartyKey, TransactionFact
from app.modules.detection.rules.rapid_onward_transfer import RapidOnwardTransfer, describe_elapsed
from app.modules.transactions.models import TransactionStatus

ACC_001: PartyKey = ("account", "ACC-001")
BEN_B: PartyKey = ("beneficiary", "BEN-B")
ACC_C: PartyKey = ("account", "ACC-C")
T0 = datetime(2026, 9, 15, 4, 32, 14, tzinfo=UTC)  # 10:02:14 IST


def fact(
    tx_id: str,
    source: PartyKey,
    destination: PartyKey,
    amount: str,
    at: datetime,
    *,
    currency: str = "INR",
    status: TransactionStatus = TransactionStatus.SETTLED,
    reversed_by: tuple[str, ...] = (),
    reverses: str | None = None,
    converted: Conversion | None = None,
) -> TransactionFact:
    return TransactionFact(
        id=tx_id,
        source=source,
        destination=destination,
        amount=Decimal(amount),
        currency=currency,
        occurred_at=at,
        status=status,
        reversed_by=reversed_by,
        reverses=reverses,
        converted=converted,
    )


def incoming(**overrides: object) -> TransactionFact:
    values: dict[str, object] = {
        "tx_id": "TX-1001",
        "source": ACC_001,
        "destination": BEN_B,
        "amount": "48500.00",
        "at": T0,
    }
    values.update(overrides)
    return fact(**values)  # pyright: ignore[reportArgumentType]


def outgoing(**overrides: object) -> TransactionFact:
    values: dict[str, object] = {
        "tx_id": "TX-1002",
        "source": BEN_B,
        "destination": ACC_C,
        "amount": "45000.00",
        "at": T0 + timedelta(seconds=328),
    }
    values.update(overrides)
    return fact(**values)  # pyright: ignore[reportArgumentType]


def hits(*facts: TransactionFact) -> list[str]:
    return [h.trigger_transaction_id for h in RapidOnwardTransfer().evaluate(list(facts))]


def test_fr_10482_triggers_with_exact_metrics_and_explanation() -> None:
    [hit] = RapidOnwardTransfer().evaluate([incoming(), outgoing()])

    assert hit.rule_id == "RAPID_ONWARD_TRANSFER"
    assert hit.rule_version == "2"
    assert hit.rule_code == "ROT"
    assert hit.entity == BEN_B
    assert hit.trigger_transaction_id == "TX-1002"
    assert hit.transaction_ids == ("TX-1001", "TX-1002")
    assert hit.triggered_at == T0 + timedelta(seconds=328)
    assert dict(hit.metrics) == {
        "elapsed_seconds": "328",
        "incoming_transaction_id": "TX-1001",
        "incoming_amount": "48500.00",
        "outgoing_transaction_id": "TX-1002",
        "outgoing_amount": "45000.00",
        "currency": "INR",
        "window_seconds": "1800",
        "min_onward_ratio": "0.50",
    }
    assert hit.explanation == (
        "BEN-B received INR 48500.00 in TX-1001 and sent INR 45000.00 in TX-1002 "
        "5 minutes 28 seconds later. Signal for analyst review; not a finding of fraud."
    )


def test_onward_outside_window_does_not_trigger() -> None:
    assert hits(incoming(), outgoing(at=T0 + timedelta(minutes=31))) == []


def test_onward_exactly_at_window_triggers() -> None:
    assert hits(incoming(), outgoing(at=T0 + timedelta(minutes=30))) == ["TX-1002"]


def test_pending_incoming_does_not_trigger() -> None:
    assert hits(incoming(status=TransactionStatus.PENDING), outgoing()) == []


def test_failed_outgoing_does_not_trigger() -> None:
    assert hits(incoming(), outgoing(status=TransactionStatus.FAILED)) == []


def test_reversed_incoming_does_not_trigger() -> None:
    assert hits(incoming(status=TransactionStatus.REVERSED), outgoing()) == []


def test_incoming_with_reversal_record_does_not_trigger() -> None:
    assert hits(incoming(reversed_by=("TX-R1",)), outgoing()) == []


def test_different_currencies_without_a_recorded_rate_do_not_trigger() -> None:
    assert hits(incoming(), outgoing(currency="USD")) == []


def usd_out(amount_inr: str, rate: str = "83.45") -> TransactionFact:
    """BEN-B sends USD 500.00; the record states what that cost in INR at the rate applied."""
    return outgoing(
        amount="500.00",
        currency="USD",
        converted=Conversion(Decimal(amount_inr), "INR", Decimal(rate)),
    )


def test_onward_in_another_currency_triggers_on_its_recorded_conversion() -> None:
    [hit] = RapidOnwardTransfer().evaluate([incoming(), usd_out("41725.00")])

    assert hit.transaction_ids == ("TX-1001", "TX-1002")
    assert dict(hit.metrics) == {
        "elapsed_seconds": "328",
        "incoming_transaction_id": "TX-1001",
        "incoming_amount": "48500.00",
        "incoming_currency": "INR",
        "outgoing_transaction_id": "TX-1002",
        "outgoing_amount": "500.00",
        "outgoing_currency": "USD",
        "currency": "INR",
        "converted_transaction_id": "TX-1002",
        "converted_amount": "41725.00",
        "fx_rate": "83.45",
        "window_seconds": "1800",
        "min_onward_ratio": "0.50",
    }
    assert hit.explanation == (
        "BEN-B received INR 48500.00 in TX-1001 and sent USD 500.00 (INR 41725.00 at the "
        "recorded rate 83.45) in TX-1002 5 minutes 28 seconds later. "
        "Signal for analyst review; not a finding of fraud."
    )


def test_converted_onward_below_ratio_does_not_trigger() -> None:
    assert hits(incoming(), usd_out("24249.99")) == []


def test_incoming_in_another_currency_triggers_on_its_recorded_conversion() -> None:
    usd_in = incoming(
        amount="600.00",
        currency="USD",
        converted=Conversion(Decimal("50070.00"), "INR", Decimal("83.45")),
    )

    [hit] = RapidOnwardTransfer().evaluate([usd_in, outgoing()])

    assert hit.metrics["converted_transaction_id"] == "TX-1001"
    assert hit.metrics["currency"] == "INR"
    assert "received USD 600.00 (INR 50070.00 at the recorded rate 83.45) in TX-1001" in (
        hit.explanation
    )


def test_converted_incoming_below_threshold_does_not_trigger() -> None:
    usd_in = incoming(
        amount="100.00",
        currency="USD",
        converted=Conversion(Decimal("8345.00"), "INR", Decimal("83.45")),
    )

    assert hits(usd_in, outgoing(amount="8000.00")) == []


def test_conversion_into_a_third_currency_does_not_trigger() -> None:
    eur_out = outgoing(
        amount="500.00",
        currency="USD",
        converted=Conversion(Decimal("460.00"), "EUR", Decimal("0.92")),
    )

    assert hits(incoming(), eur_out) == []


def test_currency_without_threshold_does_not_trigger() -> None:
    assert hits(incoming(currency="USD"), outgoing(currency="USD")) == []


def test_incoming_below_threshold_does_not_trigger() -> None:
    assert hits(incoming(amount="9999.99"), outgoing(amount="9000.00")) == []


def test_onward_below_ratio_does_not_trigger() -> None:
    assert hits(incoming(), outgoing(amount="24249.99")) == []


def test_onward_exactly_at_ratio_triggers() -> None:
    assert hits(incoming(), outgoing(amount="24250.00")) == ["TX-1002"]


def test_return_to_original_sender_does_not_trigger() -> None:
    assert hits(incoming(), outgoing(destination=ACC_001)) == []


def test_outgoing_before_incoming_does_not_trigger() -> None:
    assert hits(incoming(at=T0 + timedelta(minutes=10)), outgoing(at=T0)) == []


def test_pairs_with_most_recent_incoming() -> None:
    out_at = T0 + timedelta(minutes=30)
    older = incoming(tx_id="TX-0901", at=out_at - timedelta(minutes=20))
    newer = incoming(tx_id="TX-0902", at=out_at - timedelta(minutes=5))

    [hit] = RapidOnwardTransfer().evaluate([older, newer, outgoing(at=out_at)])

    assert hit.metrics["incoming_transaction_id"] == "TX-0902"
    assert hit.transaction_ids == ("TX-0902", "TX-1002")


def test_one_hit_per_outgoing_and_deterministic_order() -> None:
    facts = [
        incoming(),
        outgoing(),
        incoming(
            tx_id="TX-1003",
            destination=ACC_C,
            source=("account", "ACC-009"),
            at=T0 + timedelta(minutes=1),
        ),
        outgoing(
            tx_id="TX-1004",
            source=ACC_C,
            destination=("account", "ACC-010"),
            at=T0 + timedelta(minutes=12),
        ),
    ]
    expected = [h.trigger_transaction_id for h in RapidOnwardTransfer().evaluate(facts)]

    shuffled = facts.copy()
    random.Random(7).shuffle(shuffled)

    assert expected == ["TX-1002", "TX-1004"]
    assert [h.trigger_transaction_id for h in RapidOnwardTransfer().evaluate(shuffled)] == expected


@pytest.mark.parametrize(
    ("seconds", "wording"),
    [
        (45, "45 seconds"),
        (1, "1 second"),
        (61, "1 minute 1 second"),
        (328, "5 minutes 28 seconds"),
        (1800, "30 minutes"),
        (0, "0 seconds"),
    ],
)
def test_elapsed_wording(seconds: int, wording: str) -> None:
    assert describe_elapsed(seconds) == wording


def test_refund_to_sender_with_other_recent_incoming_does_not_trigger() -> None:
    other_sender: PartyKey = ("account", "ACC-OTHER")
    facts = [
        fact("TX-1", other_sender, BEN_B, "20000.00", T0),
        fact("TX-2", ACC_001, BEN_B, "20000.00", T0 + timedelta(minutes=5)),
        fact("TX-3", BEN_B, ACC_001, "20000.00", T0 + timedelta(minutes=10)),
    ]

    assert hits(*facts) == []


def test_settled_reversal_record_is_not_incoming() -> None:
    account_d: PartyKey = ("account", "ACC-D")
    facts = [
        fact("TX-1", BEN_B, ACC_001, "20000.00", T0, reversed_by=("TX-2",)),
        fact("TX-2", ACC_001, BEN_B, "20000.00", T0 + timedelta(minutes=1), reverses="TX-1"),
        fact("TX-3", BEN_B, account_d, "15000.00", T0 + timedelta(minutes=6)),
    ]

    assert hits(*facts) == []
