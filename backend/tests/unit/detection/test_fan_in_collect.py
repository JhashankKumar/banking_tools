import random
from datetime import UTC, datetime, timedelta

from app.modules.detection.facts import PartyKey, TransactionFact
from app.modules.detection.rules.fan_in_collect import FanInCollect
from app.modules.transactions.models import TransactionStatus
from tests.unit.detection.factories import fact

COLLECTOR: PartyKey = ("beneficiary", "BEN-M89")
ONWARD: PartyKey = ("account", "ACC-X89")
T0 = datetime(2026, 9, 21, 5, 30, tzinfo=UTC)  # 11:00 IST
SENTENCE = "Signal for analyst review; not a finding of fraud."

FR_10489_IN = [
    ("12000.00", 0),
    ("15500.00", 250),
    ("11000.00", 570),
    ("18000.00", 785),
    ("14500.00", 1060),
]


def payer(n: int) -> PartyKey:
    return ("account", f"ACC-89{n}")


def ins(spec: list[tuple[str, int]], payers: list[int] | None = None) -> list[TransactionFact]:
    numbers = payers or list(range(1, len(spec) + 1))
    return [
        fact(f"TX-890{i + 1}", payer(numbers[i]), COLLECTOR, amount, T0 + timedelta(seconds=s))
        for i, (amount, s) in enumerate(spec)
    ]


def onward(amount: str = "68000.00", at: int = 1452, **kw: object) -> TransactionFact:
    return fact("TX-8906", COLLECTOR, ONWARD, amount, T0 + timedelta(seconds=at), **kw)  # pyright: ignore[reportArgumentType]


def test_fr_10489_shape_links_all_five_payers() -> None:
    hits = FanInCollect().evaluate([*ins(FR_10489_IN), onward()])

    assert len(hits) == 1
    hit = hits[0]
    assert hit.rule_id == "FAN_IN_COLLECT"
    assert hit.rule_code == "FIC"
    assert hit.entity == COLLECTOR
    assert hit.trigger_transaction_id == "TX-8906"
    assert hit.transaction_ids == ("TX-8901", "TX-8902", "TX-8903", "TX-8904", "TX-8905", "TX-8906")
    assert hit.metrics == {
        "payer_count": "5",
        "incoming_count": "5",
        "incoming_total": "71000.00",
        "outgoing_transaction_id": "TX-8906",
        "outgoing_amount": "68000.00",
        "currency": "INR",
        "onward_share": "0.95",
        "elapsed_seconds": "1452",
        "window_seconds": "1800",
        "min_payers": "3",
        "min_onward_ratio": "0.50",
    }
    assert hit.explanation == (
        "BEN-M89 received INR 71000.00 from 5 payers in 5 transfers and sent INR 68000.00 in "
        f"TX-8906 24 minutes 12 seconds after the first of them. {SENTENCE}"
    )


def test_two_payers_no_hit() -> None:
    spec = [("20000.00", 0), ("20000.00", 60)]
    assert FanInCollect().evaluate([*ins(spec), onward("30000.00", 120)]) == []


def test_same_payer_three_times_counts_once() -> None:
    spec = [("10000.00", 0), ("10000.00", 60), ("10000.00", 120)]
    assert FanInCollect().evaluate([*ins(spec, payers=[1, 1, 1]), onward("20000.00", 180)]) == []


def test_total_below_threshold_no_hit() -> None:
    spec = [("8333.33", 0), ("8333.33", 60), ("8333.33", 120)]
    assert FanInCollect().evaluate([*ins(spec), onward("20000.00", 180)]) == []


def test_exactly_at_thresholds_fires() -> None:
    spec = [("10000.00", 0), ("10000.00", 60), ("5000.00", 120)]
    [hit] = FanInCollect().evaluate([*ins(spec), onward("12500.00", 180)])
    assert hit.metrics["incoming_total"] == "25000.00"
    assert hit.metrics["onward_share"] == "0.50"


def test_onward_just_under_ratio_no_hit() -> None:
    spec = [("10000.00", 0), ("10000.00", 60), ("5000.00", 120)]
    assert FanInCollect().evaluate([*ins(spec), onward("12499.99", 180)]) == []


def test_incoming_older_than_window_not_counted() -> None:
    spec = [("10000.00", 0), ("10000.00", 600), ("10000.00", 1200)]
    # The first payment is 30 min 1 s before the onward transfer: two payers remain.
    assert FanInCollect().evaluate([*ins(spec), onward("20000.00", 1801)]) == []


def test_onward_after_hours_no_hit() -> None:
    spec = [
        ("4500.00", 0),
        ("6200.00", 240),
        ("3800.00", 540),
        ("5500.00", 900),
        ("7000.00", 1200),
        ("4000.00", 1500),
    ]
    assert FanInCollect().evaluate([*ins(spec), onward("30200.00", 12600)]) == []


def test_out_to_a_payer_is_skipped() -> None:
    back = fact("TX-8906", COLLECTOR, payer(2), "68000.00", T0 + timedelta(seconds=1452))
    assert FanInCollect().evaluate([*ins(FR_10489_IN), back]) == []


def test_non_completed_and_reversal_records_ignored() -> None:
    a, b, c = ins([("10000.00", 0), ("10000.00", 60), ("10000.00", 120)])
    facts = [
        a,
        fact(
            b.id,
            b.source,
            b.destination,
            "10000.00",
            b.occurred_at,
            status=TransactionStatus.PENDING,
        ),
        fact(c.id, c.source, c.destination, "10000.00", c.occurred_at, reverses="TX-0001"),
        fact(
            "TX-8907",
            payer(4),
            COLLECTOR,
            "10000.00",
            T0 + timedelta(seconds=150),
            reversed_by=("TX-0002",),
        ),
        onward("20000.00", 180),
    ]
    assert FanInCollect().evaluate(facts) == []


def test_reversal_record_outgoing_is_not_onward() -> None:
    assert FanInCollect().evaluate([*ins(FR_10489_IN), onward(reverses="TX-0003")]) == []


def test_other_currency_without_conversion_not_counted() -> None:
    spec = [("12000.00", 0), ("15500.00", 250)]
    usd = fact(
        "TX-8909", payer(9), COLLECTOR, "200.00", T0 + timedelta(seconds=300), currency="USD"
    )
    assert FanInCollect().evaluate([*ins(spec), usd, onward("20000.00", 600)]) == []


def test_shuffled_input_same_hits() -> None:
    facts = [*ins(FR_10489_IN), onward()]
    expected = FanInCollect().evaluate(facts)
    for seed in range(5):
        shuffled = facts[:]
        random.Random(seed).shuffle(shuffled)
        assert FanInCollect().evaluate(shuffled) == expected


def test_parameters() -> None:
    assert FanInCollect().parameters == {
        "window_seconds": "1800",
        "min_payers": "3",
        "min_total_incoming": "INR:25000.00",
        "min_onward_ratio": "0.50",
    }
