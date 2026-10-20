from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.modules.cases.models import Alert, Case, case_transactions
from app.modules.cases.schemas import CaseOut


class CaseNotFoundError(AppError):
    status = 404
    code = "CASE_NOT_FOUND"
    message = "Case not found"


def get_case(session: Session, case_id: str) -> CaseOut:
    case = session.get(Case, case_id)
    if case is None:
        raise CaseNotFoundError
    alert_ids = session.scalars(
        select(Alert.id).where(Alert.case_id == case_id).order_by(Alert.id)
    ).all()
    transaction_count = session.scalar(
        select(func.count()).where(case_transactions.c.case_id == case_id)
    )
    return CaseOut(
        id=case.id,
        title=case.title,
        status=case.status,
        opened_at=case.opened_at,
        alert_ids=list(alert_ids),
        transaction_count=transaction_count or 0,
        is_synthetic=case.is_synthetic,
    )


def ensure_case_exists(session: Session, case_id: str) -> None:
    if session.get(Case, case_id) is None:
        raise CaseNotFoundError
