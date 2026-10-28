from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.pagination import PageParams, count_rows, paged
from app.core.errors import NotFoundError
from app.modules.alerts.schemas import AlertOut, RuleRef
from app.modules.cases.models import Alert
from app.modules.detection.registry import get_rule
from app.modules.evidence.models import Evidence
from app.modules.transactions.schemas import PartyRef


class AlertNotFoundError(NotFoundError):
    code = "ALERT_NOT_FOUND"
    message = "Alert not found"


def _to_out(alert: Alert, evidence_id: str | None) -> AlertOut:
    rule = get_rule(alert.rule_id)
    return AlertOut(
        id=alert.id,
        rule=RuleRef(
            id=alert.rule_id,
            version=alert.rule_version,
            title=rule.title if rule is not None else alert.rule_id,
        ),
        entity=PartyRef(type=alert.entity_type.value, id=alert.entity_id),
        trigger_transaction_id=alert.trigger_transaction_id,
        transaction_ids=list(alert.transaction_ids),
        case_id=alert.case_id,
        triggered_at=alert.triggered_at,
        explanation=alert.explanation,
        metrics=dict(alert.metrics),
        evidence_id=evidence_id,
        is_synthetic=alert.is_synthetic,
    )


def _evidence_ids(session: Session, alerts: list[Alert]) -> dict[str, str]:
    """Case evidence ID per alert (alert evidence lives in the alert's case)."""
    if not alerts:
        return {}
    rows = session.execute(
        select(Evidence.source_record_id, Evidence.id).where(
            Evidence.source_table == "alerts",
            Evidence.source_record_id.in_([a.id for a in alerts]),
        )
    ).all()
    return {record_id: evidence_id for record_id, evidence_id in rows}


def list_alerts(
    session: Session, page: PageParams, *, case_id: str | None, rule_id: str | None
) -> tuple[list[AlertOut], int]:
    query = select(Alert)
    if case_id is not None:
        query = query.where(Alert.case_id == case_id)
    if rule_id is not None:
        query = query.where(Alert.rule_id == rule_id)
    total = count_rows(session, query)
    alerts = session.scalars(paged(query.order_by(Alert.triggered_at.desc(), Alert.id), page)).all()
    evidence = _evidence_ids(session, list(alerts))
    return [_to_out(a, evidence.get(a.id)) for a in alerts], total


def get_alert(session: Session, alert_id: str) -> AlertOut:
    alert = session.get(Alert, alert_id)
    if alert is None:
        raise AlertNotFoundError
    return _to_out(alert, _evidence_ids(session, [alert]).get(alert.id))
