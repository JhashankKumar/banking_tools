"""Bounded, time-respecting money-path search over transaction facts.

Pure: no database or HTTP. Rules (docs/project/DOMAIN_MODEL_AND_APIS.md, money-path semantics):
each hop happens at or after the previous one (ties by transaction ID) and within the window of
the first hop; no party is visited twice except returning to the start (a cycle); every status is
included and labelled; nothing is summed or netted.
"""

from bisect import bisect_right
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Literal

from app.modules.detection.facts import PartyKey, TransactionFact, is_completed

EdgeKind = Literal["transfer", "reversal"]

LIMITED_TO_DATASET = (
    "Limited to records in this dataset. A path does not establish ownership, intent, "
    "available balance, or settlement finality."
)
NON_FINAL = (
    "Includes transactions that are not completed (pending, failed, or reversed); "
    "funds may not have moved as shown."
)
REVERSAL = (
    "Includes a reversal record; the original transfer and its reversal are shown separately, "
    "not netted."
)
HOP_LIMIT = "Path stops at the hop limit; further onward transfers may exist."
MIXED_CURRENCY = (
    "Amounts are in different currencies and are shown as recorded. Compare them only through a "
    "conversion recorded on a transfer (shown on its alert), never an assumed rate."
)
CYCLE = "Funds return to the starting party; a loop alone does not indicate wrongdoing."
RETURNED_BY_REVERSAL = "Funds returned to the sender by a reversal; this is not a circular flow."
BUDGET = "The search reached its work limit; some paths may be missing or incomplete."


@dataclass(frozen=True)
class PathParams:
    max_hops: int = 3
    window: timedelta = timedelta(hours=24)
    max_paths: int = 50
    max_expansions: int = 10_000


@dataclass(frozen=True)
class PathEdge:
    hop: int
    fact: TransactionFact
    kind: EdgeKind
    is_final: bool


@dataclass(frozen=True)
class MoneyPath:
    edges: tuple[PathEdge, ...]
    is_cycle: bool
    has_non_final_edges: bool
    contains_reversal: bool
    returned_by_reversal: bool  # ends with a reversal back to the start (not a cycle)
    currencies: tuple[str, ...]
    elapsed_seconds: int
    limitations: tuple[str, ...]


@dataclass(frozen=True)
class PathResult:
    paths: tuple[MoneyPath, ...]
    truncated: bool


def _order(fact: TransactionFact) -> tuple[datetime, str]:
    return (fact.occurred_at, fact.id)


class _Search:
    """Depth-first search with a per-start expansion budget. Recursion depth <= max_hops."""

    def __init__(self, facts: Sequence[TransactionFact], params: PathParams) -> None:
        self.params = params
        self.outgoing: defaultdict[PartyKey, list[TransactionFact]] = defaultdict(list)
        for fact in sorted(facts, key=_order):
            self.outgoing[fact.source].append(fact)
        # Parallel sort keys so the next-hop lookup can bisect past earlier transfers.
        self.keys = {party: [_order(f) for f in out] for party, out in self.outgoing.items()}
        self.truncated = False  # any cap hit; reported to the caller
        self.budget_exhausted = False  # some start ran out of expansions
        self.hit_hop_limit: set[tuple[str, ...]] = set()
        self.found: list[tuple[TransactionFact, ...]] = []
        self._remaining = 0

    def run(self, start: TransactionFact, budget: int) -> None:
        self._remaining = budget
        self._extend((start,), {start.source, start.destination})

    def _next_hops(
        self, path: tuple[TransactionFact, ...], nodes: set[PartyKey]
    ) -> list[TransactionFact]:
        first, last = path[0], path[-1]
        party = last.destination
        outgoing = self.outgoing.get(party, [])
        index = bisect_right(self.keys.get(party, []), _order(last))
        used = {f.id for f in path}
        hops: list[TransactionFact] = []
        for candidate in outgoing[index:]:
            if candidate.occurred_at - first.occurred_at > self.params.window:
                break
            revisits = candidate.destination in nodes and candidate.destination != first.source
            if candidate.id not in used and not revisits:
                hops.append(candidate)
        return hops

    def _extend(self, path: tuple[TransactionFact, ...], nodes: set[PartyKey]) -> None:
        start_party = path[0].source
        if len(path) > 1 and path[-1].destination == start_party:
            self.found.append(path)  # cycle closed: stop here
            return
        candidates = self._next_hops(path, nodes)
        if len(path) == self.params.max_hops:
            if candidates:
                self.hit_hop_limit.add(tuple(f.id for f in path))
                self.truncated = True
            self.found.append(path)
            return
        if not candidates:
            self.found.append(path)
            return
        for candidate in candidates:
            if self._remaining <= 0:
                self.budget_exhausted = True
                self.truncated = True
                self.found.append(path)
                return
            self._remaining -= 1
            self._extend((*path, candidate), nodes | {candidate.destination})


def _drop_sub_paths(keys: Sequence[tuple[str, ...]]) -> set[tuple[str, ...]]:
    """Keys that are a proper contiguous slice of another key. Linear: <= max_hops^2 per path."""
    slices: set[tuple[str, ...]] = set()
    for key in keys:
        for i in range(len(key)):
            for j in range(i + 1, len(key) + 1):
                if j - i < len(key):
                    slices.add(key[i:j])
    return slices


def _describe(
    path: tuple[TransactionFact, ...], hit_hop_limit: bool, budget_exhausted: bool
) -> MoneyPath:
    first, last = path[0], path[-1]
    edges = tuple(
        PathEdge(
            hop=index + 1,
            fact=fact,
            kind="reversal" if fact.reverses is not None else "transfer",
            is_final=is_completed(fact),
        )
        for index, fact in enumerate(path)
    )
    returns_to_start = len(path) > 1 and last.destination == first.source
    returned_by_reversal = returns_to_start and last.reverses is not None
    is_cycle = returns_to_start and not returned_by_reversal
    has_non_final = any(not e.is_final for e in edges)
    contains_reversal = any(e.kind == "reversal" for e in edges)
    currencies = tuple(sorted({f.currency for f in path}))
    conditions = [
        (True, LIMITED_TO_DATASET),
        (has_non_final, NON_FINAL),
        (contains_reversal, REVERSAL),
        (hit_hop_limit, HOP_LIMIT),
        (len(currencies) > 1, MIXED_CURRENCY),
        (is_cycle, CYCLE),
        (returned_by_reversal, RETURNED_BY_REVERSAL),
        (budget_exhausted, BUDGET),
    ]
    return MoneyPath(
        edges=edges,
        is_cycle=is_cycle,
        has_non_final_edges=has_non_final,
        contains_reversal=contains_reversal,
        returned_by_reversal=returned_by_reversal,
        currencies=currencies,
        elapsed_seconds=int((last.occurred_at - first.occurred_at).total_seconds()),
        limitations=tuple(text for applies, text in conditions if applies),
    )


def _path_key(path: tuple[TransactionFact, ...]) -> tuple[datetime, tuple[str, ...]]:
    return (path[0].occurred_at, tuple(f.id for f in path))


def _fair_selection(
    paths: Sequence[tuple[TransactionFact, ...]], limit: int
) -> list[tuple[TransactionFact, ...]]:
    """Up to `limit` paths taken round-robin by starting transaction, returned in key order."""
    by_start: defaultdict[str, list[tuple[TransactionFact, ...]]] = defaultdict(list)
    for path in sorted(paths, key=_path_key):
        by_start[path[0].id].append(path)
    queues = list(by_start.values())
    selected: list[tuple[TransactionFact, ...]] = []
    round_index = 0
    while len(selected) < limit and any(round_index < len(q) for q in queues):
        for queue in queues:
            if round_index < len(queue) and len(selected) < limit:
                selected.append(queue[round_index])
        round_index += 1
    return sorted(selected, key=_path_key)


def find_money_paths(
    start_ids: Sequence[str], facts: Sequence[TransactionFact], params: PathParams
) -> PathResult:
    by_id = {f.id: f for f in facts}
    starts = sorted((by_id[i] for i in set(start_ids) if i in by_id), key=_order)
    search = _Search(facts, params)
    # Each start gets an equal share, so one dense start cannot starve the others.
    per_start = max(params.max_expansions // max(len(starts), 1), 1)
    for start in starts:
        search.run(start, per_start)

    unique = {tuple(f.id for f in p): p for p in search.found}
    contained = _drop_sub_paths(list(unique))
    kept = [path for key, path in unique.items() if key not in contained]
    selected = _fair_selection(kept, params.max_paths)
    truncated = search.truncated or len(kept) > params.max_paths
    described = tuple(
        _describe(p, tuple(f.id for f in p) in search.hit_hop_limit, search.budget_exhausted)
        for p in selected
    )
    return PathResult(paths=described, truncated=truncated)
