import random
import time
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.modules.detection.facts import PartyKey, TransactionFact
from app.modules.graph.paths import (
    BUDGET,
    MoneyPath,
    PathParams,
    PathResult,
    find_money_paths,
)
from app.modules.transactions.models import TransactionStatus

T0 = datetime(2026, 9, 15, 4, 32, 14, tzinfo=UTC)
L1 = (
    "Limited to records in this dataset. A path does not establish ownership, intent, "
    "available balance, or settlement finality."
)
L2 = (
    "Includes transactions that are not completed (pending, failed, or reversed); "
    "funds may not have moved as shown."
)
L3 = (
    "Includes a reversal record; the original transfer and its reversal are shown separately, "
    "not netted."
)
L4 = "Path stops at the hop limit; further onward transfers may exist."
L5 = "Amounts are in different currencies and are not comparable without an exchange rate."
L6 = "Funds return to the starting party; a loop alone does not indicate wrongdoing."
L_RETURNED = "Funds returned to the sender by a reversal; this is not a circular flow."


def acc(name: str) -> PartyKey:
    return ("account", name)


def ben(name: str) -> PartyKey:
    return ("beneficiary", name)


def fact(
    tx_id: str,
    source: PartyKey,
    destination: PartyKey,
    at: datetime,
    *,
    amount: str = "1000.00",
    currency: str = "INR",
    status: TransactionStatus = TransactionStatus.SETTLED,
    reversed_by: tuple[str, ...] = (),
    reverses: str | None = None,
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
    )


def ids(path: MoneyPath) -> list[str]:
    return [e.fact.id for e in path.edges]


def all_ids(result: PathResult) -> list[list[str]]:
    return [ids(p) for p in result.paths]


def chain(*hops: tuple[str, PartyKey, PartyKey, datetime]) -> list[TransactionFact]:
    return [fact(tx_id, src, dst, at) for tx_id, src, dst, at in hops]


FR_10482 = [
    fact("TX-1001", acc("ACC-001"), ben("BEN-B"), T0, amount="48500.00"),
    fact("TX-1002", ben("BEN-B"), acc("ACC-C"), T0 + timedelta(seconds=328), amount="45000.00"),
]


def test_fr_10482_single_two_hop_path() -> None:
    result = find_money_paths(["TX-1001", "TX-1002"], FR_10482, PathParams())

    [path] = result.paths
    assert [(e.hop, e.fact.id, e.kind, e.is_final) for e in path.edges] == [
        (1, "TX-1001", "transfer", True),
        (2, "TX-1002", "transfer", True),
    ]
    assert path.elapsed_seconds == 328
    assert path.currencies == ("INR",)
    assert path.limitations == (L1,)
    assert not path.is_cycle
    assert not path.has_non_final_edges
    assert result.truncated is False


def test_sub_paths_of_longer_paths_are_dropped() -> None:
    result = find_money_paths(["TX-1001", "TX-1002"], FR_10482, PathParams())

    assert all_ids(result) == [["TX-1001", "TX-1002"]]


def test_path_never_goes_back_in_time() -> None:
    facts = [
        fact("TX-1", acc("A"), acc("B"), T0),
        fact("TX-2", acc("B"), acc("C"), T0 - timedelta(minutes=1)),
    ]

    result = find_money_paths(["TX-1", "TX-2"], facts, PathParams())

    assert all_ids(result) == [["TX-2"], ["TX-1"]]


def test_equal_timestamps_ordered_by_id() -> None:
    chained = [fact("TX-1", acc("A"), acc("B"), T0), fact("TX-2", acc("B"), acc("C"), T0)]
    swapped = [fact("TX-2", acc("A"), acc("B"), T0), fact("TX-1", acc("B"), acc("C"), T0)]

    assert all_ids(find_money_paths(["TX-1"], chained, PathParams())) == [["TX-1", "TX-2"]]
    assert all_ids(find_money_paths(["TX-2"], swapped, PathParams())) == [["TX-2"]]


def test_window_bounds_path() -> None:
    inside = chain(
        ("TX-1", acc("A"), acc("B"), T0), ("TX-2", acc("B"), acc("C"), T0 + timedelta(hours=24))
    )
    outside = chain(
        ("TX-1", acc("A"), acc("B"), T0),
        ("TX-2", acc("B"), acc("C"), T0 + timedelta(hours=24, minutes=1)),
    )

    assert all_ids(find_money_paths(["TX-1"], inside, PathParams())) == [["TX-1", "TX-2"]]
    assert all_ids(find_money_paths(["TX-1"], outside, PathParams())) == [["TX-1"]]


def test_max_hops_truncates_with_limitation() -> None:
    facts = chain(
        ("TX-1", acc("A"), acc("B"), T0),
        ("TX-2", acc("B"), acc("C"), T0 + timedelta(minutes=1)),
        ("TX-3", acc("C"), acc("D"), T0 + timedelta(minutes=2)),
        ("TX-4", acc("D"), acc("E"), T0 + timedelta(minutes=3)),
    )

    result = find_money_paths(["TX-1"], facts, PathParams(max_hops=3))

    [path] = result.paths
    assert ids(path) == ["TX-1", "TX-2", "TX-3"]
    assert result.truncated is True
    assert L4 in path.limitations


def test_cycle_is_closed_and_flagged() -> None:
    facts = chain(
        ("TX-4001", acc("ACC-401"), ben("BEN-402"), T0),
        ("TX-4002", ben("BEN-402"), acc("ACC-403"), T0 + timedelta(hours=2)),
        ("TX-4003", acc("ACC-403"), acc("ACC-401"), T0 + timedelta(hours=5)),
    )

    result = find_money_paths(["TX-4001", "TX-4002", "TX-4003"], facts, PathParams())

    [path] = result.paths
    assert ids(path) == ["TX-4001", "TX-4002", "TX-4003"]
    assert path.is_cycle
    assert path.limitations == (L1, L6)


def test_no_intermediate_node_revisited() -> None:
    facts = chain(
        ("TX-1", acc("A"), acc("B"), T0),
        ("TX-2", acc("B"), acc("C"), T0 + timedelta(minutes=1)),
        ("TX-3", acc("C"), acc("B"), T0 + timedelta(minutes=2)),
        ("TX-4", acc("B"), acc("D"), T0 + timedelta(minutes=3)),
    )

    result = find_money_paths(["TX-1"], facts, PathParams(max_hops=5))

    for path in result.paths:
        visited = [path.edges[0].fact.source] + [e.fact.destination for e in path.edges]
        assert visited.count(acc("B")) == 1


def test_reversal_and_onward_both_shown_unnetted() -> None:
    t = datetime(2026, 9, 18, 4, 0, 0, tzinfo=UTC)
    facts = [
        fact(
            "TX-5001",
            acc("ACC-501"),
            ben("BEN-501"),
            t,
            amount="20000.00",
            reversed_by=("TX-5002",),
        ),
        fact(
            "TX-5003", ben("BEN-501"), acc("ACC-502"), t + timedelta(minutes=10), amount="19000.00"
        ),
        fact(
            "TX-5002",
            ben("BEN-501"),
            acc("ACC-501"),
            t + timedelta(minutes=20),
            amount="20000.00",
            status=TransactionStatus.REVERSED,
            reverses="TX-5001",
        ),
    ]

    result = find_money_paths(["TX-5001", "TX-5002", "TX-5003"], facts, PathParams())

    assert all_ids(result) == [["TX-5001", "TX-5002"], ["TX-5001", "TX-5003"]]
    reversal_path, onward_path = result.paths
    assert reversal_path.edges[0].is_final is False
    assert reversal_path.edges[1].kind == "reversal"
    assert reversal_path.contains_reversal
    assert reversal_path.is_cycle is False
    assert reversal_path.returned_by_reversal is True
    assert reversal_path.limitations == (L1, L2, L3, L_RETURNED)
    assert onward_path.returned_by_reversal is False
    assert onward_path.limitations == (L1, L2)


def test_pending_edge_included_and_flagged() -> None:
    facts = [
        fact("TX-1", acc("A"), acc("B"), T0),
        fact(
            "TX-2", acc("B"), acc("C"), T0 + timedelta(minutes=1), status=TransactionStatus.PENDING
        ),
    ]

    [path] = find_money_paths(["TX-1"], facts, PathParams()).paths

    assert ids(path) == ["TX-1", "TX-2"]
    assert path.has_non_final_edges
    assert path.limitations == (L1, L2)


def test_mixed_currencies_flagged_not_combined() -> None:
    facts = [
        fact("TX-1", acc("A"), acc("B"), T0),
        fact("TX-2", acc("B"), acc("C"), T0 + timedelta(minutes=1), currency="USD"),
    ]

    [path] = find_money_paths(["TX-1"], facts, PathParams()).paths

    assert path.currencies == ("INR", "USD")
    assert path.limitations == (L1, L5)


def test_expansion_budget_truncates_dense_graph() -> None:
    parties = [acc(f"P{i}") for i in range(6)]
    rng = random.Random(3)
    facts: list[TransactionFact] = []
    for n in range(60):
        src, dst = rng.sample(parties, 2)
        facts.append(fact(f"TX-{n:03d}", src, dst, T0 + timedelta(minutes=n)))

    result = find_money_paths(
        [f.id for f in facts], facts, PathParams(max_hops=5, max_expansions=200)
    )

    assert result.truncated is True


def test_max_paths_cap() -> None:
    facts = [
        fact(f"TX-{n:03d}", acc(f"S{n}"), acc(f"D{n}"), T0 + timedelta(seconds=n))
        for n in range(80)
    ]

    result = find_money_paths([f.id for f in facts], facts, PathParams())

    assert len(result.paths) == 50
    assert result.truncated is True


def test_output_is_deterministic() -> None:
    facts = chain(
        ("TX-1", acc("A"), acc("B"), T0),
        ("TX-2", acc("B"), acc("C"), T0 + timedelta(minutes=1)),
        ("TX-3", acc("B"), acc("D"), T0 + timedelta(minutes=2)),
        ("TX-4", acc("X"), acc("Y"), T0 + timedelta(minutes=3)),
    )
    expected = find_money_paths(["TX-1", "TX-4"], facts, PathParams())

    shuffled = facts.copy()
    random.Random(11).shuffle(shuffled)

    assert find_money_paths(["TX-4", "TX-1"], shuffled, PathParams()) == expected
    assert all_ids(expected) == [["TX-1", "TX-2"], ["TX-1", "TX-3"], ["TX-4"]]


def test_start_ids_not_in_facts_are_ignored() -> None:
    result = find_money_paths(["TX-NOPE", "TX-1001"], FR_10482, PathParams())

    assert all_ids(result) == [["TX-1001", "TX-1002"]]


def test_hop_limit_on_one_path_does_not_stop_other_starts() -> None:
    facts = chain(
        ("TX-4001", acc("ACC-401"), ben("BEN-402"), T0),
        ("TX-4002", ben("BEN-402"), acc("ACC-403"), T0 + timedelta(hours=2)),
        ("TX-4003", acc("ACC-403"), acc("ACC-401"), T0 + timedelta(hours=5)),
    )

    result = find_money_paths(["TX-4001", "TX-4002", "TX-4003"], facts, PathParams(max_hops=2))

    assert all_ids(result) == [["TX-4001", "TX-4002"], ["TX-4002", "TX-4003"]]
    assert result.truncated is True
    assert L4 in result.paths[0].limitations
    assert L4 not in result.paths[1].limitations


def test_sub_path_dropping_scales_with_wide_fan_out() -> None:
    """Review C1: 12,000 onward transfers from one party must not take seconds to post-process."""
    facts = [fact("TX-START", acc("A"), acc("B"), T0)]
    facts += [
        fact(f"TX-{n:05d}", acc("B"), acc(f"D{n}"), T0 + timedelta(seconds=n + 1))
        for n in range(12_000)
    ]

    began = time.perf_counter()
    result = find_money_paths(["TX-START"], facts, PathParams(max_expansions=20_000))
    elapsed = time.perf_counter() - began

    assert len(result.paths) == 50
    assert result.truncated is True
    assert elapsed < 2.0


def test_next_hop_lookup_skips_earlier_transfers() -> None:
    """Review I2: a party's long history before a start must not be rescanned per step."""
    earlier = [
        fact(f"TX-OLD-{n:05d}", acc("B"), acc("Z"), T0 - timedelta(days=2, seconds=n))
        for n in range(50_000)
    ]
    starts = [
        fact(f"TX-IN-{n:03d}", acc(f"S{n}"), acc("B"), T0 + timedelta(seconds=n))
        for n in range(300)
    ]

    began = time.perf_counter()
    result = find_money_paths([f.id for f in starts], earlier + starts, PathParams())
    elapsed = time.perf_counter() - began

    assert len(result.paths) == 50
    assert elapsed < 1.5


def test_budget_is_shared_across_starts() -> None:
    """Review I4: one dense start must not starve the others."""
    dense = [fact("TX-D0", acc("A"), acc("B"), T0)]
    dense += [
        fact(f"TX-D{n:03d}", acc("B"), acc(f"X{n}"), T0 + timedelta(seconds=n))
        for n in range(1, 400)
    ]
    simple = chain(
        ("TX-S1", acc("P"), acc("Q"), T0 + timedelta(minutes=1)),
        ("TX-S2", acc("Q"), acc("R"), T0 + timedelta(minutes=2)),
    )

    result = find_money_paths(["TX-D0", "TX-S1"], dense + simple, PathParams(max_expansions=200))

    assert ["TX-S1", "TX-S2"] in all_ids(result)


def test_hop_limit_ignores_revisit_only_candidates() -> None:
    """Review M1: an onward transfer back to a non-start party is not 'further onward transfers'."""
    facts = chain(
        ("TX-1", acc("A"), acc("B"), T0),
        ("TX-2", acc("B"), acc("C"), T0 + timedelta(minutes=1)),
        ("TX-3", acc("C"), acc("B"), T0 + timedelta(minutes=2)),
    )

    result = find_money_paths(["TX-1"], facts, PathParams(max_hops=2))

    [path] = result.paths
    assert ids(path) == ["TX-1", "TX-2"]
    assert result.truncated is False
    assert L4 not in path.limitations


def test_budget_exhaustion_marks_paths() -> None:
    """Review M2: paths returned after the work limit is hit say they may be incomplete."""
    facts = [fact("TX-0", acc("A"), acc("B"), T0)]
    facts += [
        fact(f"TX-{n:03d}", acc("B"), acc(f"X{n}"), T0 + timedelta(seconds=n)) for n in range(1, 50)
    ]

    result = find_money_paths(["TX-0"], facts, PathParams(max_expansions=10))

    assert result.truncated is True
    assert result.paths
    assert all(BUDGET in p.limitations for p in result.paths)


def test_transfer_back_to_start_that_is_not_a_reversal_is_still_a_cycle() -> None:
    facts = chain(
        ("TX-1", acc("A"), acc("B"), T0),
        ("TX-2", acc("B"), acc("A"), T0 + timedelta(minutes=5)),
    )

    [path] = find_money_paths(["TX-1"], facts, PathParams()).paths

    assert path.is_cycle is True
    assert path.returned_by_reversal is False
    assert L6 in path.limitations
