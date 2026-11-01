import random
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.modules.detection.facts import Conversion, PartyKey, TransactionFact
from app.modules.detection.rules.fan_out_split import FanOutSplit
from app.modules.transactions.models import TransactionStatus
from tests.unit.detection.factories import fact

PAYER: PartyKey = ("account", "ACC-901")
SPLITTER: PartyKey = ("beneficiary", "BEN-S90")
T0 = datetime(2026, 9, 22, 8, 30, tzinfo=UTC)  # 14:00 IST
SENTENCE = "Signal for analyst review; not a finding of fraud."

FR_10490_OUTS = [
    ("39000.00", 180),
    ("38500.00", 330),
    ("40000.00", 480),
    ("39500.00", 615),
    ("38000.00", 750),
]


def payee(n: int) -> PartyKey:
    return ("account", f"ACC-9{n:02d}")


def incoming(amount: str = "200000.00", **kw: object) -> TransactionFact:
    return fact("TX-9001", PAYER, SPLITTER, amount, T0, **kw)  # pyright: ignore[reportArgumentType]


def outs(spec: list[tuple[str, int]], first_id: int = 2) -> list[TransactionFact]:
    return [
        fact(f"TX-90{first_id + i:02d}", SPLITTER, payee(i + 2), amount, T0 + timedelta(seconds=s))
        for i, (amount, s) in enumerate(spec)
    ]


def test_fr_10490_shape_fires_at_fifth_transfer() -> None:
    hits = FanOutSplit().evaluate([incoming(), *outs(FR_10490_OUTS)])

    assert len(hits) == 1
    hit = hits[0]
    assert hit.rule_id == "FAN_OUT_SPLIT"
    assert hit.rule_code == "FOS"
    assert hit.entity == SPLITTER
    assert hit.trigger_transaction_id == "TX-9006"
    assert hit.transaction_ids == ("TX-9001", "TX-9002", "TX-9003", "TX-9004", "TX-9005", "TX-9006")
    assert hit.triggered_at == T0 + timedelta(seconds=750)
    assert hit.metrics == {
        "incoming_transaction_id": "TX-9001",
        "incoming_amount": "200000.00",
        "currency": "INR",
        "outgoing_count": "5",
        "outgoing_total": "195000.00",
        "onward_share": "0.97",
        "elapsed_seconds": "750",
        "window_seconds": "1800",
        "min_transfers": "3",
        "min_onward_share": "0.80",
    }
    assert hit.explanation == (
        "BEN-S90 received INR 200000.00 in TX-9001 and sent INR 195000.00 (97%) onward in "
        f"5 transfers within 12 minutes 30 seconds. {SENTENCE}"
    )


def test_below_min_incoming_no_hit() -> None:
    spec = [("16666.67", 60), ("16666.66", 120), ("16666.66", 180)]
    assert FanOutSplit().evaluate([incoming("49999.99"), *outs(spec)]) == []


def test_exactly_at_thresholds_fires() -> None:
    spec = [("15000.00", 60), ("15000.00", 120), ("10000.00", 180)]
    [hit] = FanOutSplit().evaluate([incoming("50000.00"), *outs(spec)])
    assert hit.trigger_transaction_id == "TX-9004"
    assert hit.metrics["onward_share"] == "0.80"


def test_just_under_share_no_hit() -> None:
    spec = [("15000.00", 60), ("15000.00", 120), ("9999.99", 180)]
    assert FanOutSplit().evaluate([incoming("50000.00"), *outs(spec)]) == []


def test_two_transfers_enough_money_no_hit() -> None:
    spec = [("100000.00", 60), ("100000.00", 120)]
    assert FanOutSplit().evaluate([incoming(), *outs(spec)]) == []


def test_outside_window_not_counted() -> None:
    spec = [("80000.00", 60), ("80000.00", 120), ("40000.00", 1801)]
    assert FanOutSplit().evaluate([incoming(), *outs(spec)]) == []


def test_transfer_before_incoming_not_counted() -> None:
    early = fact("TX-9000", SPLITTER, payee(9), "80000.00", T0 - timedelta(seconds=1))
    spec = [("80000.00", 60), ("80000.00", 120)]
    assert FanOutSplit().evaluate([early, incoming(), *outs(spec)]) == []


def test_non_completed_and_reversed_ignored() -> None:
    spec = [("60000.00", 60), ("60000.00", 120), ("60000.00", 180)]
    pending, failed, reversed_out = outs(spec)
    facts = [
        incoming(),
        fact(
            pending.id,
            pending.source,
            pending.destination,
            "60000.00",
            pending.occurred_at,
            status=TransactionStatus.PENDING,
        ),
        fact(
            failed.id,
            failed.source,
            failed.destination,
            "60000.00",
            failed.occurred_at,
            status=TransactionStatus.FAILED,
        ),
        fact(
            reversed_out.id,
            reversed_out.source,
            reversed_out.destination,
            "60000.00",
            reversed_out.occurred_at,
            reversed_by=("TX-9099",),
        ),
    ]
    assert FanOutSplit().evaluate(facts) == []


def test_reversed_incoming_no_hit() -> None:
    assert FanOutSplit().evaluate([incoming(reversed_by=("TX-9099",)), *outs(FR_10490_OUTS)]) == []


def test_reversal_record_is_not_incoming_money() -> None:
    assert FanOutSplit().evaluate([incoming(reverses="TX-8000"), *outs(FR_10490_OUTS)]) == []


def test_transfer_back_to_payer_not_counted() -> None:
    back = fact("TX-9002", SPLITTER, PAYER, "60000.00", T0 + timedelta(seconds=60))
    rest = outs([("60000.00", 120), ("60000.00", 180)], first_id=3)
    assert FanOutSplit().evaluate([incoming(), back, *rest]) == []


def test_other_currency_without_conversion_not_counted() -> None:
    usd = fact(
        "TX-9004", SPLITTER, payee(4), "2000.00", T0 + timedelta(seconds=180), currency="USD"
    )
    spec = [("80000.00", 60), ("80000.00", 120)]
    assert FanOutSplit().evaluate([incoming(), *outs(spec), usd]) == []


def test_recorded_conversion_counted() -> None:
    usd = fact(
        "TX-9004",
        SPLITTER,
        payee(4),
        "500.00",
        T0 + timedelta(seconds=180),
        currency="USD",
        converted=Conversion(Decimal("41725.00"), "INR", Decimal("83.45")),
    )
    spec = [("60000.00", 60), ("60000.00", 120)]
    [hit] = FanOutSplit().evaluate([incoming(), *outs(spec), usd])
    assert hit.trigger_transaction_id == "TX-9004"
    assert hit.metrics["outgoing_total"] == "161725.00"


def test_same_trigger_from_two_incomings_one_hit() -> None:
    second = fact(
        "TX-9001B", ("account", "ACC-999"), SPLITTER, "200000.00", T0 + timedelta(seconds=10)
    )
    hits = FanOutSplit().evaluate([incoming(), second, *outs(FR_10490_OUTS)])
    assert [h.transaction_ids[0] for h in hits] == ["TX-9001"]
    assert [h.trigger_transaction_id for h in hits] == ["TX-9006"]


def test_shuffled_input_same_hits() -> None:
    facts = [incoming(), *outs(FR_10490_OUTS)]
    expected = FanOutSplit().evaluate(facts)
    for seed in range(5):
        shuffled = facts[:]
        random.Random(seed).shuffle(shuffled)
        assert FanOutSplit().evaluate(shuffled) == expected


def test_parameters() -> None:
    assert FanOutSplit().parameters == {
        "window_seconds": "1800",
        "min_incoming_amount": "INR:50000.00",
        "min_transfers": "3",
        "min_onward_share": "0.80",
    }
