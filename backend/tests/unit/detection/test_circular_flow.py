import random
from datetime import UTC, datetime, timedelta

from app.modules.detection.facts import PartyKey, TransactionFact
from app.modules.detection.rules.circular_flow import CircularFlow
from app.modules.transactions.models import TransactionStatus
from tests.unit.detection.factories import fact

A: PartyKey = ("account", "ACC-401")
B: PartyKey = ("beneficiary", "BEN-402")
C: PartyKey = ("account", "ACC-403")
T0 = datetime(2026, 9, 19, 4, 0, tzinfo=UTC)
HOUR = timedelta(hours=1)
SENTENCE = "Signal for analyst review; not a finding of fraud."


def cycle(
    start: str = "30000.00",
    middle: str = "29000.00",
    back: str = "28000.00",
    close_at: timedelta = 5 * HOUR,
    **close_kw: object,
) -> list[TransactionFact]:
    return [
        fact("TX-4001", A, B, start, T0),
        fact("TX-4002", B, C, middle, T0 + 2 * HOUR),
        fact("TX-4003", C, A, back, T0 + close_at, **close_kw),  # pyright: ignore[reportArgumentType]
    ]


def test_fr_10484_shape_fires() -> None:
    hits = CircularFlow().evaluate(cycle())

    assert len(hits) == 1
    hit = hits[0]
    assert hit.rule_id == "CIRCULAR_FLOW"
    assert hit.rule_code == "CIR"
    assert hit.entity == A
    assert hit.trigger_transaction_id == "TX-4003"
    assert hit.transaction_ids == ("TX-4001", "TX-4002", "TX-4003")
    assert hit.triggered_at == T0 + 5 * HOUR
    assert hit.metrics == {
        "hops": "3",
        "start_transaction_id": "TX-4001",
        "start_amount": "30000.00",
        "returned_amount": "28000.00",
        "currency": "INR",
        "return_ratio": "0.93",
        "elapsed_seconds": "18000",
        "window_seconds": "86400",
        "min_return_ratio": "0.50",
    }
    assert hit.explanation == (
        "ACC-401 sent INR 30000.00 in TX-4001 and INR 28000.00 came back in TX-4003 5 hours "
        f"later, via BEN-402 and ACC-403. {SENTENCE}"
    )


def test_longer_than_window_no_hit() -> None:
    assert CircularFlow().evaluate(cycle(close_at=24 * HOUR + timedelta(seconds=1))) == []


def test_exactly_24h_fires() -> None:
    [hit] = CircularFlow().evaluate(cycle(close_at=24 * HOUR))
    assert hit.metrics["elapsed_seconds"] == "86400"


def test_start_below_threshold_no_hit() -> None:
    assert CircularFlow().evaluate(cycle("9999.99", "9000.00", "8000.00")) == []


def test_returned_below_ratio_no_hit() -> None:
    assert CircularFlow().evaluate(cycle(back="14999.99")) == []


def test_returned_exactly_half_fires() -> None:
    [hit] = CircularFlow().evaluate(cycle(back="15000.00"))
    assert hit.metrics["return_ratio"] == "0.50"


def test_two_hop_round_trip_no_hit() -> None:
    facts = [fact("TX-1", A, B, "30000.00", T0), fact("TX-2", B, A, "29000.00", T0 + HOUR)]
    assert CircularFlow().evaluate(facts) == []


def test_out_of_order_hops_no_hit() -> None:
    facts = [
        fact("TX-4002", B, C, "29000.00", T0),
        fact("TX-4001", A, B, "30000.00", T0 + HOUR),
        fact("TX-4003", C, A, "28000.00", T0 + 2 * HOUR),
    ]
    assert CircularFlow().evaluate(facts) == []


def test_non_completed_hop_no_hit() -> None:
    assert CircularFlow().evaluate(cycle(status=TransactionStatus.PENDING)) == []


def test_reversed_hop_no_hit() -> None:
    assert CircularFlow().evaluate(cycle(reversed_by=("TX-4099",))) == []


def test_reversal_record_hop_no_hit() -> None:
    assert CircularFlow().evaluate(cycle(reverses="TX-4000")) == []


def test_mixed_currency_cycle_no_hit() -> None:
    assert CircularFlow().evaluate(cycle(back="340.00", currency="USD")) == []


def test_picks_latest_start_when_several() -> None:
    earlier_start = fact("TX-4000", A, B, "30000.00", T0 - HOUR)
    [hit] = CircularFlow().evaluate([earlier_start, *cycle()])
    assert hit.transaction_ids == ("TX-4001", "TX-4002", "TX-4003")


def test_shuffled_input_same_hits() -> None:
    facts = [fact("TX-4000", A, B, "30000.00", T0 - HOUR), *cycle()]
    expected = CircularFlow().evaluate(facts)
    for seed in range(5):
        shuffled = facts[:]
        random.Random(seed).shuffle(shuffled)
        assert CircularFlow().evaluate(shuffled) == expected


def test_parameters() -> None:
    assert CircularFlow().parameters == {
        "window_seconds": "86400",
        "min_start_amount": "INR:10000.00",
        "min_return_ratio": "0.50",
        "hops": "3",
    }


def test_round_trip_closed_by_self_transfer_no_hit() -> None:
    # A -> B -> A then A -> A is a refund plus a self-transfer, not a three-party cycle.
    facts = [
        fact("TX-1", A, B, "30000.00", T0),
        fact("TX-2", B, A, "29000.00", T0 + HOUR),
        fact("TX-3", A, A, "28000.00", T0 + 2 * HOUR),
    ]
    assert CircularFlow().evaluate(facts) == []
