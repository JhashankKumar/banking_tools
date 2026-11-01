"""transaction conversion

International transfers: the converted amount, its currency and the rate the source system
applied, as recorded. All three or none (RAPID_ONWARD_TRANSFER v2 compares currencies only
through these).

Revision ID: 0004
Revises: 0003
Create Date: 2026-11-01 10:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: str | Sequence[str] | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("transactions", sa.Column("converted_amount", sa.Numeric(18, 2), nullable=True))
    op.add_column(
        "transactions", sa.Column("converted_currency", sa.String(length=3), nullable=True)
    )
    op.add_column("transactions", sa.Column("fx_rate", sa.Numeric(18, 6), nullable=True))
    op.create_check_constraint(
        op.f("ck_transactions_conversion_complete"),
        "transactions",
        "num_nonnulls(converted_amount, converted_currency, fx_rate) IN (0, 3)",
    )
    op.create_check_constraint(
        op.f("ck_transactions_conversion_valid"),
        "transactions",
        "converted_currency ~ '^[A-Z]{3}$' AND converted_currency <> currency"
        " AND converted_amount > 0 AND fx_rate > 0",
    )


def downgrade() -> None:
    op.drop_constraint(op.f("ck_transactions_conversion_valid"), "transactions", type_="check")
    op.drop_constraint(op.f("ck_transactions_conversion_complete"), "transactions", type_="check")
    op.drop_column("transactions", "fx_rate")
    op.drop_column("transactions", "converted_currency")
    op.drop_column("transactions", "converted_amount")
