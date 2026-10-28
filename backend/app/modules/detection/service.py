"""Run registered rules over the stored transactions and record their hits as alerts."""

from collections import defaultdict
from collections.abc import Collection, Sequence
from datetime import datetime

from sqlalchemy import or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.modules.audit import service as audit
from app.modules.audit.models import Outcome
from app.modules.cases.models import Alert, PartyType, case_transactions
from app.modules.detection.contract import DetectionRule, RuleHit
from app.modules.detection.facts import PartyKey, TransactionFact
from app.modules.detection.registry import RULES
from app.modules.evidence.models import Evidence, EvidenceLabel, EvidenceType
from app.modules.transactions.models import Transaction

DetectionSummary = dict[str, int]


def _party(account_id: str | None, beneficiary_id: str | None) -> PartyKey:
    # The database guarantees exactly one side is set.
    if account_id is not None:
        return ("account", account_id)
    if beneficiary_id is None:
        raise ValueError("transaction side has neither an account nor a beneficiary")
    return ("beneficiary", beneficiary_id)


def load_facts(
    session: Session,
    *,
    since: datetime | None = None,
    until: datetime | None = None,
    involving: Collection[PartyKey] | None = None,
    transaction_ids: Collection[str] | None = None,
    limit: int | None = None,
) -> list[TransactionFact]:
    """Transactions as facts in (occurred_at, id) order, optionally filtered.

    `since`/`until` bound occurred_at (inclusive); `involving` keeps transactions with any of the
    parties as source or destination; `transaction_ids` keeps only those IDs. Reversal links are
    always resolved against the whole table, so a fact still knows it was reversed by a record
    outside the filter.
    """
    query = select(Transaction)
    if since is not None:
        query = query.where(Transaction.occurred_at >= since)
    if until is not None:
        query = query.where(Transaction.occurred_at <= until)
    if transaction_ids is not None:
        query = query.where(Transaction.id.in_(list(transaction_ids)))
    if involving is not None:
        accounts = [party_id for kind, party_id in involving if kind == "account"]
        beneficiaries = [party_id for kind, party_id in involving if kind == "beneficiary"]
        query = query.where(
            or_(
                Transaction.source_account_id.in_(accounts),
                Transaction.destination_account_id.in_(accounts),
                Transaction.source_beneficiary_id.in_(beneficiaries),
                Transaction.destination_beneficiary_id.in_(beneficiaries),
            )
        )
    query = query.order_by(Transaction.occurred_at, Transaction.id)
    if limit is not None:
        query = query.limit(limit)
    reversals: defaultdict[str, list[str]] = defaultdict(list)
    for reversal_id, original_id in session.execute(
        select(Transaction.id, Transaction.reversal_of_transaction_id)
        .where(Transaction.reversal_of_transaction_id.is_not(None))
        .order_by(Transaction.id)
    ):
        if original_id is not None:
            reversals[original_id].append(reversal_id)
    return [
        TransactionFact(
            id=tx.id,
            source=_party(tx.source_account_id, tx.source_beneficiary_id),
            destination=_party(tx.destination_account_id, tx.destination_beneficiary_id),
            amount=tx.amount,
            currency=tx.currency,
            occurred_at=tx.occurred_at,
            status=tx.status,
            reversed_by=tuple(reversals.get(tx.id, ())),
            reverses=tx.reversal_of_transaction_id,
            rail=tx.rail,
            reference=tx.reference,
        )
        for tx in session.scalars(query)
    ]


def alert_id_for(hit: RuleHit) -> str:
    return f"AL-{hit.rule_code}-{hit.trigger_transaction_id}"


def run_detection(session: Session, rules: Sequence[DetectionRule] = RULES) -> DetectionSummary:
    """Record every rule hit. Idempotent: existing alerts (and their case links) are never changed.

    Flushes, never commits.
    """
    facts = load_facts(session)
    summary: DetectionSummary = {}
    new_alerts = 0
    for rule in rules:
        hits = rule.evaluate(facts)
        summary[rule.rule_id] = len(hits)
        new_alerts += sum(_record_hit(session, hit) for hit in hits)
    audit.record(
        session,
        action="detection.run",
        outcome=Outcome.SUCCESS,
        actor_user_id=None,
        request_id=None,
        resource_type="detection",
        details={
            **{rule_id: str(hits) for rule_id, hits in summary.items()},
            "rule_versions": ",".join(f"{r.rule_id}:{r.version}" for r in rules),
            "new_alerts": str(new_alerts),
        },
    )
    session.flush()
    return summary


def _single_case_for(session: Session, transaction_id: str) -> str | None:
    case_ids = session.scalars(
        select(case_transactions.c.case_id).where(
            case_transactions.c.transaction_id == transaction_id
        )
    ).all()
    # Attach only when unambiguous; otherwise an analyst decides where the alert belongs.
    return case_ids[0] if len(case_ids) == 1 else None


def _record_hit(session: Session, hit: RuleHit) -> bool:
    """Insert the alert (and its case evidence) if new. Returns True when an alert was created."""
    trigger = session.get_one(Transaction, hit.trigger_transaction_id)
    alert_id = alert_id_for(hit)
    created = session.execute(
        insert(Alert)
        .values(
            id=alert_id,
            case_id=_single_case_for(session, hit.trigger_transaction_id),
            rule_id=hit.rule_id,
            rule_version=hit.rule_version,
            rule_code=hit.rule_code,
            entity_type=PartyType(hit.entity[0]),
            entity_id=hit.entity[1],
            trigger_transaction_id=hit.trigger_transaction_id,
            transaction_ids=list(hit.transaction_ids),
            triggered_at=hit.triggered_at,
            explanation=hit.explanation,
            metrics=dict(hit.metrics),
            is_synthetic=trigger.is_synthetic,
            scenario_id=trigger.scenario_id,
        )
        .on_conflict_do_nothing()
        .returning(Alert.id)
    ).scalar_one_or_none()
    case_id = session.scalar(select(Alert.case_id).where(Alert.id == alert_id))
    if case_id is None:
        return created is not None
    session.execute(
        insert(Evidence)
        .values(
            id=f"EV-{case_id.removeprefix('FR-')}-{alert_id}",
            case_id=case_id,
            evidence_type=EvidenceType.ALERT,
            source_table="alerts",
            source_record_id=alert_id,
            label=EvidenceLabel.INDICATOR,
            is_synthetic=trigger.is_synthetic,
            scenario_id=trigger.scenario_id,
        )
        .on_conflict_do_nothing()
    )
    return created is not None
