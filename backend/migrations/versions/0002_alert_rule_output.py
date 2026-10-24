"""alert rule output

Alerts now store full rule output (rule code, entity, trigger, supporting transactions,
metrics, explanation). Existing alert rows are synthetic seed data: they and their alert
evidence are deleted here and recreated by `python -m app.seed` / detection.

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-20 10:27:07.008104

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: str | Sequence[str] | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

party_type = postgresql.ENUM("account", "beneficiary", name="party_type", create_type=False)


def upgrade() -> None:
    op.execute("DELETE FROM evidence WHERE evidence_type = 'alert'")
    op.execute("DELETE FROM alerts")
    party_type.create(op.get_bind(), checkfirst=True)

    op.alter_column("alerts", "summary", new_column_name="explanation")
    op.drop_constraint("fk_alerts_transaction_id_transactions", "alerts", type_="foreignkey")
    op.alter_column(
        "alerts", "transaction_id", new_column_name="trigger_transaction_id", nullable=False
    )
    op.create_foreign_key(
        op.f("fk_alerts_trigger_transaction_id_transactions"),
        "alerts",
        "transactions",
        ["trigger_transaction_id"],
        ["id"],
    )
    op.add_column("alerts", sa.Column("rule_code", sa.Text(), nullable=False))
    op.add_column("alerts", sa.Column("entity_type", party_type, nullable=False))
    op.add_column("alerts", sa.Column("entity_id", sa.Text(), nullable=False))
    op.add_column(
        "alerts", sa.Column("transaction_ids", postgresql.ARRAY(sa.Text()), nullable=False)
    )
    op.add_column(
        "alerts",
        sa.Column(
            "metrics",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
    )
    op.create_unique_constraint(
        "uq_alerts_rule_trigger", "alerts", ["rule_id", "trigger_transaction_id"]
    )


def downgrade() -> None:
    # Data is not restored; re-run the seed after downgrading.
    op.execute("DELETE FROM evidence WHERE evidence_type = 'alert'")
    op.execute("DELETE FROM alerts")
    op.drop_constraint("uq_alerts_rule_trigger", "alerts", type_="unique")
    for column in ("metrics", "transaction_ids", "entity_id", "entity_type", "rule_code"):
        op.drop_column("alerts", column)
    op.drop_constraint(
        op.f("fk_alerts_trigger_transaction_id_transactions"), "alerts", type_="foreignkey"
    )
    op.alter_column(
        "alerts", "trigger_transaction_id", new_column_name="transaction_id", nullable=True
    )
    op.create_foreign_key(
        "fk_alerts_transaction_id_transactions",
        "alerts",
        "transactions",
        ["transaction_id"],
        ["id"],
    )
    op.alter_column("alerts", "explanation", new_column_name="summary")
    party_type.drop(op.get_bind(), checkfirst=True)
