from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.pagination import PageParams
from app.modules.cases.models import case_transactions
from app.modules.evidence.models import Evidence
from app.modules.transactions.models import Transaction
from app.modules.transactions.schemas import PartyRef, TransactionOut


def _party(account_id: str | None, beneficiary_id: str | None) -> PartyRef:
    # The database guarantees exactly one of the two is set.
    if account_id is not None:
        return PartyRef(type="account", id=account_id)
    if beneficiary_id is None:
        raise ValueError("transaction side has neither an account nor a beneficiary")
    return PartyRef(type="beneficiary", id=beneficiary_id)


def list_case_transactions(
    session: Session, case_id: str, page: PageParams
) -> tuple[list[TransactionOut], int]:
    in_case = select(case_transactions.c.transaction_id).where(
        case_transactions.c.case_id == case_id
    )
    total = session.scalar(select(func.count()).select_from(in_case.subquery())) or 0
    rows = session.execute(
        select(Transaction, Evidence.id)
        .outerjoin(
            Evidence,
            (Evidence.case_id == case_id)
            & (Evidence.source_table == "transactions")
            & (Evidence.source_record_id == Transaction.id),
        )
        .where(Transaction.id.in_(in_case))
        .order_by(Transaction.occurred_at, Transaction.id)
        .limit(page.limit)
        .offset(page.offset)
    ).all()
    items = [
        TransactionOut(
            id=tx.id,
            source=_party(tx.source_account_id, tx.source_beneficiary_id),
            destination=_party(tx.destination_account_id, tx.destination_beneficiary_id),
            amount=tx.amount,
            currency=tx.currency,
            occurred_at=tx.occurred_at,
            status=tx.status,
            source_status=tx.source_status,
            rail=tx.rail,
            reference=tx.reference,
            description=tx.description,
            reversal_of_transaction_id=tx.reversal_of_transaction_id,
            evidence_id=evidence_id,
        )
        for tx, evidence_id in rows
    ]
    return items, total
