from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.pagination import PageParams
from app.core.errors import AppError
from app.modules.alerts.schemas import AlertOut, RuleRef
from app.modules.cases.models import Alert
from app.modules.detection.registry import get_rule
from app.modules.transactions.schemas import PartyRef


class AlertNotFoundError(AppError):
    status = 404
    code = "ALERT_NOT_FOUND"
    message = "Alert not found"


def _to_out(alert: Alert) -> AlertOut:
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
        is_synthetic=alert.is_synthetic,
    )


def list_alerts(
    session: Session, page: PageParams, *, case_id: str | None, rule_id: str | None
) -> tuple[list[AlertOut], int]:
    query = select(Alert)
    if case_id is not None:
        query = query.where(Alert.case_id == case_id)
    if rule_id is not None:
        query = query.where(Alert.rule_id == rule_id)
    total = session.scalar(select(func.count()).select_from(query.subquery())) or 0
    alerts = session.scalars(
        query.order_by(Alert.triggered_at.desc(), Alert.id).limit(page.limit).offset(page.offset)
    ).all()
    return [_to_out(a) for a in alerts], total


def get_alert(session: Session, alert_id: str) -> AlertOut:
    alert = session.get(Alert, alert_id)
    if alert is None:
        raise AlertNotFoundError
    return _to_out(alert)
