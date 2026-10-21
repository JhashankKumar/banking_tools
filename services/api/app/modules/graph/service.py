from bisect import bisect_left
from collections.abc import Sequence
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import func, select, tuple_
from sqlalchemy.orm import Session

from app.modules.cases.models import Alert, PartyType, case_transactions
from app.modules.cases.service import ensure_case_exists
from app.modules.detection.facts import PartyKey, TransactionFact, is_completed
from app.modules.detection.service import load_facts
from app.modules.evidence.models import Evidence
from app.modules.graph.paths import BUDGET, PathParams, find_money_paths
from app.modules.graph.schemas import (
    CaseGraphOut,
    CaseGraphParams,
    GraphEdgeOut,
    GraphNodeOut,
    GraphWindow,
    MoneyPathOut,
    MoneyPathParams,
    MoneyPathsOut,
    PathEdgeOut,
)
from app.modules.parties.models import Account, Beneficiary, Customer
from app.modules.transactions.models import Transaction
from app.modules.transactions.schemas import PartyRef


def _ref(party: PartyKey) -> PartyRef:
    return PartyRef(type=party[0], id=party[1])


def edge_fields(fact: TransactionFact, evidence_id: str | None) -> dict[str, Any]:
    """Fields of TransactionEdgeOut for one fact (extended by PathEdgeOut and GraphEdgeOut)."""
    return {
        "transaction_id": fact.id,
        "kind": "reversal" if fact.reverses is not None else "transfer",
        "source": _ref(fact.source),
        "destination": _ref(fact.destination),
        "amount": fact.amount,
        "currency": fact.currency,
        "occurred_at": fact.occurred_at,
        "status": fact.status,
        "is_final": is_completed(fact),
        "reversed_by": list(fact.reversed_by),
        "evidence_id": evidence_id,
    }


def case_transaction_ids(session: Session, case_id: str) -> list[str]:
    return list(
        session.scalars(
            select(case_transactions.c.transaction_id).where(case_transactions.c.case_id == case_id)
        ).all()
    )


def case_evidence_by_transaction(session: Session, case_id: str) -> dict[str, str]:
    rows = session.execute(
        select(Evidence.source_record_id, Evidence.id).where(
            Evidence.case_id == case_id, Evidence.source_table == "transactions"
        )
    ).all()
    return {record_id: evidence_id for record_id, evidence_id in rows}


def case_time_span(session: Session, transaction_ids: list[str]) -> tuple[datetime, datetime]:
    earliest, latest = session.execute(
        select(func.min(Transaction.occurred_at), func.max(Transaction.occurred_at)).where(
            Transaction.id.in_(transaction_ids)
        )
    ).one()
    return earliest, latest


MAX_PATH_FACTS = 20_000  # transactions loaded for one money-paths request
MAX_GRAPH_NEIGHBOUR_ROWS = 5_000  # candidate neighbour transactions ranked for the graph


def _merged_windows(
    times: Sequence[datetime], window: timedelta
) -> list[tuple[datetime, datetime]]:
    spans: list[tuple[datetime, datetime]] = []
    for t in sorted(times):
        if spans and t <= spans[-1][1]:
            spans[-1] = (spans[-1][0], max(spans[-1][1], t + window))
        else:
            spans.append((t, t + window))
    return spans


def _load_path_facts(
    session: Session, start_times: Sequence[datetime], window: timedelta, max_facts: int
) -> tuple[list[TransactionFact], bool]:
    """Facts inside each start's own window, at most `max_facts`. Returns (facts, capped)."""
    facts: list[TransactionFact] = []
    for since, until in _merged_windows(start_times, window):
        remaining = max_facts - len(facts)
        if remaining <= 0:
            return facts, True
        batch = load_facts(session, since=since, until=until, limit=remaining + 1)
        facts.extend(batch[:remaining])
        if len(batch) > remaining:
            return facts, True
    return facts, False


def get_money_paths(
    session: Session,
    case_id: str,
    *,
    max_hops: int,
    window_hours: int,
    max_facts: int = MAX_PATH_FACTS,
) -> MoneyPathsOut:
    ensure_case_exists(session, case_id)
    window = timedelta(hours=window_hours)
    start_ids = case_transaction_ids(session, case_id)
    parameters = MoneyPathParams(max_hops=max_hops, window_hours=window_hours)
    if not start_ids:
        return MoneyPathsOut(case_id=case_id, parameters=parameters, truncated=False, paths=[])

    # Every hop is within `window` of its path's first hop, and every path starts at a case
    # transaction, so only each start's own window can contribute.
    start_times = [f.occurred_at for f in load_facts(session, transaction_ids=start_ids)]
    facts, capped = _load_path_facts(session, start_times, window, max_facts)
    result = find_money_paths(start_ids, facts, PathParams(max_hops=max_hops, window=window))
    evidence = case_evidence_by_transaction(session, case_id)

    def limitations(path_limitations: Sequence[str]) -> list[str]:
        extra = [BUDGET] if capped and BUDGET not in path_limitations else []
        return [*path_limitations, *extra]

    paths = [
        MoneyPathOut(
            hops=len(path.edges),
            is_cycle=path.is_cycle,
            has_non_final_edges=path.has_non_final_edges,
            contains_reversal=path.contains_reversal,
            returned_by_reversal=path.returned_by_reversal,
            currencies=list(path.currencies),
            started_at=path.edges[0].fact.occurred_at,
            ended_at=path.edges[-1].fact.occurred_at,
            elapsed_seconds=path.elapsed_seconds,
            limitations=limitations(path.limitations),
            edges=[
                PathEdgeOut(hop=edge.hop, **edge_fields(edge.fact, evidence.get(edge.fact.id)))
                for edge in path.edges
            ],
        )
        for path in result.paths
    ]
    return MoneyPathsOut(
        case_id=case_id,
        parameters=parameters,
        truncated=result.truncated or capped,
        paths=paths,
    )


MAX_GRAPH_EDGES = 200


def _party_labels(
    session: Session, parties: set[PartyKey]
) -> dict[PartyKey, tuple[str, str | None]]:
    """(label, status) per party: customer name (else account ID), or beneficiary label."""
    account_ids = [party_id for kind, party_id in parties if kind == "account"]
    beneficiary_ids = [party_id for kind, party_id in parties if kind == "beneficiary"]
    labels: dict[PartyKey, tuple[str, str | None]] = {}
    for account_id, status, customer_name in session.execute(
        select(Account.id, Account.status, Customer.display_name)
        .outerjoin(Customer, Customer.id == Account.customer_id)
        .where(Account.id.in_(account_ids))
    ):
        labels[("account", account_id)] = (customer_name or account_id, status.value)
    for beneficiary_id, label in session.execute(
        select(Beneficiary.id, Beneficiary.display_label).where(Beneficiary.id.in_(beneficiary_ids))
    ):
        labels[("beneficiary", beneficiary_id)] = (label, None)
    return labels


def _alerts_by_party(session: Session, parties: set[PartyKey]) -> dict[PartyKey, list[str]]:
    keys = [(PartyType(kind), party_id) for kind, party_id in parties]
    by_party: dict[PartyKey, list[str]] = {}
    if not keys:
        return by_party
    for alert_id, entity_type, entity_id in session.execute(
        select(Alert.id, Alert.entity_type, Alert.entity_id)
        .where(tuple_(Alert.entity_type, Alert.entity_id).in_(keys))
        .order_by(Alert.id)
    ):
        party: PartyKey = (
            ("account", entity_id)
            if entity_type == PartyType.ACCOUNT
            else (
                "beneficiary",
                entity_id,
            )
        )
        by_party.setdefault(party, []).append(alert_id)
    return by_party


def get_case_graph(session: Session, case_id: str, *, window_hours: int) -> CaseGraphOut:
    """Case parties plus every transaction touching them inside the window (one level only)."""
    ensure_case_exists(session, case_id)
    parameters = CaseGraphParams(window_hours=window_hours)
    case_ids = case_transaction_ids(session, case_id)
    if not case_ids:
        return CaseGraphOut(
            case_id=case_id, parameters=parameters, window=None, truncated=False, nodes=[], edges=[]
        )

    window = timedelta(hours=window_hours)
    earliest, latest = case_time_span(session, case_ids)
    start, end = earliest - window, latest + window
    case_facts = load_facts(session, transaction_ids=case_ids)
    case_parties = {f.source for f in case_facts} | {f.destination for f in case_facts}

    # Case transactions are always kept; the rest fill the cap closest-in-time first, so a busy
    # counterparty's distant history cannot crowd out transfers around the case.
    room = max(MAX_GRAPH_EDGES - len(case_facts), 0)
    case_set = set(case_ids)
    candidates = load_facts(
        session, since=start, until=end, involving=case_parties, limit=MAX_GRAPH_NEIGHBOUR_ROWS
    )
    neighbours = [f for f in candidates if f.id not in case_set]
    case_times = sorted(f.occurred_at for f in case_facts)
    neighbours.sort(key=lambda f: (_distance(f.occurred_at, case_times), f.occurred_at, f.id))
    truncated = len(neighbours) > room or len(candidates) == MAX_GRAPH_NEIGHBOUR_ROWS
    facts = sorted([*case_facts, *neighbours[:room]], key=lambda f: (f.occurred_at, f.id))

    evidence = case_evidence_by_transaction(session, case_id)
    edges = [
        GraphEdgeOut(in_case=f.id in case_set, **edge_fields(f, evidence.get(f.id))) for f in facts
    ]
    parties = {f.source for f in facts} | {f.destination for f in facts}
    labels = _party_labels(session, parties)
    alerts = _alerts_by_party(session, parties)
    nodes = [
        GraphNodeOut(
            id=party[1],
            type=party[0],
            label=labels.get(party, (party[1], None))[0],
            status=labels.get(party, (party[1], None))[1],
            is_case_party=party in case_parties,
            alert_ids=alerts.get(party, []),
        )
        for party in sorted(parties)
    ]
    return CaseGraphOut(
        case_id=case_id,
        parameters=parameters,
        window=GraphWindow(start=start, end=end),
        truncated=truncated,
        nodes=nodes,
        edges=edges,
    )


def _distance(at: datetime, sorted_times: Sequence[datetime]) -> timedelta:
    """Time from `at` to the nearest of `sorted_times` (non-empty)."""
    index = bisect_left(sorted_times, at)
    near = sorted_times[max(index - 1, 0) : index + 1]
    return min(abs(at - t) for t in near)
