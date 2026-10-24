from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.pagination import PageParams
from app.core.errors import AppError
from app.modules.cases.models import Alert, Case, case_transactions
from app.modules.cases.schemas import CaseOut, CaseSummaryOut


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


def list_cases(session: Session, page: PageParams) -> tuple[list[CaseSummaryOut], int]:
    total = session.scalar(select(func.count()).select_from(Case)) or 0
    alert_counts = select(Alert.case_id, func.count().label("n")).group_by(Alert.case_id).subquery()
    tx_counts = (
        select(case_transactions.c.case_id, func.count().label("n"))
        .group_by(case_transactions.c.case_id)
        .subquery()
    )
    rows = session.execute(
        select(Case, alert_counts.c.n, tx_counts.c.n)
        .outerjoin(alert_counts, alert_counts.c.case_id == Case.id)
        .outerjoin(tx_counts, tx_counts.c.case_id == Case.id)
        .order_by(Case.opened_at.desc(), Case.id)
        .limit(page.limit)
        .offset(page.offset)
    ).all()
    items = [
        CaseSummaryOut(
            id=case.id,
            title=case.title,
            status=case.status,
            opened_at=case.opened_at,
            alert_count=alerts or 0,
            transaction_count=transactions or 0,
            is_synthetic=case.is_synthetic,
        )
        for case, alerts, transactions in rows
    ]
    return items, total
