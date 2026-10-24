"""copilot and notes

Milestone 5: copilot chats, messages and metered runs; case notes with versions, supervisor
reviews, and the append-only case status history. `case_status` already exists (0001) and is
reused, not recreated.

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-24 10:38:38.898021

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003"
down_revision: str | Sequence[str] | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

case_status = postgresql.ENUM(
    "open", "in_review", "escalated", "closed", name="case_status", create_type=False
)
NEW_ENUMS = ("review_decision", "note_origin", "note_status", "copilot_role", "copilot_outcome")


def upgrade() -> None:
    op.create_table(
        "copilot_chats",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("case_id", sa.Text(), nullable=False),
        sa.Column("author_id", sa.UUID(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["author_id"], ["users.id"], name=op.f("fk_copilot_chats_author_id_users")
        ),
        sa.ForeignKeyConstraint(
            ["case_id"], ["cases.id"], name=op.f("fk_copilot_chats_case_id_cases")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_copilot_chats")),
    )
    op.create_index(
        "ix_copilot_chats_case_author", "copilot_chats", ["case_id", "author_id"], unique=False
    )
    op.create_table(
        "copilot_runs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("chat_id", sa.UUID(), nullable=True),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("case_id", sa.Text(), nullable=False),
        sa.Column("model", sa.Text(), nullable=False),
        sa.Column(
            "outcome",
            sa.Enum("answered", "declined", "failed", "limited", name="copilot_outcome"),
            nullable=False,
        ),
        sa.Column("tool_calls", sa.Integer(), nullable=False),
        sa.Column("prompt_tokens", sa.Integer(), nullable=False),
        sa.Column("completion_tokens", sa.Integer(), nullable=False),
        sa.Column("cost_usd", sa.Numeric(precision=10, scale=6), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["case_id"], ["cases.id"], name=op.f("fk_copilot_runs_case_id_cases")
        ),
        sa.ForeignKeyConstraint(
            ["chat_id"], ["copilot_chats.id"], name=op.f("fk_copilot_runs_chat_id_copilot_chats")
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_copilot_runs_user_id_users")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_copilot_runs")),
    )
    op.create_index(
        op.f("ix_copilot_runs_created_at"), "copilot_runs", ["created_at"], unique=False
    )
    op.create_index(
        "ix_copilot_runs_user_created", "copilot_runs", ["user_id", "created_at"], unique=False
    )
    op.create_table(
        "copilot_messages",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("chat_id", sa.UUID(), nullable=False),
        sa.Column("role", sa.Enum("user", "assistant", name="copilot_role"), nullable=False),
        sa.Column("run_id", sa.UUID(), nullable=True),
        sa.Column("question", sa.Text(), nullable=True),
        sa.Column("answer", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["chat_id"],
            ["copilot_chats.id"],
            name=op.f("fk_copilot_messages_chat_id_copilot_chats"),
        ),
        sa.ForeignKeyConstraint(
            ["run_id"], ["copilot_runs.id"], name=op.f("fk_copilot_messages_run_id_copilot_runs")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_copilot_messages")),
    )
    op.create_index(
        op.f("ix_copilot_messages_chat_id"), "copilot_messages", ["chat_id"], unique=False
    )
    op.create_table(
        "case_notes",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("case_id", sa.Text(), nullable=False),
        sa.Column("author_id", sa.UUID(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("draft", "awaiting_review", "returned", "approved", name="note_status"),
            nullable=False,
        ),
        sa.Column("origin", sa.Enum("ai_drafted", "written", name="note_origin"), nullable=False),
        sa.Column("source_message_id", sa.UUID(), nullable=True),
        sa.Column("current_version", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["author_id"], ["users.id"], name=op.f("fk_case_notes_author_id_users")
        ),
        sa.ForeignKeyConstraint(
            ["case_id"], ["cases.id"], name=op.f("fk_case_notes_case_id_cases")
        ),
        sa.ForeignKeyConstraint(
            ["source_message_id"],
            ["copilot_messages.id"],
            name=op.f("fk_case_notes_source_message_id_copilot_messages"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_case_notes")),
    )
    op.create_index(op.f("ix_case_notes_case_id"), "case_notes", ["case_id"], unique=False)
    op.create_index(
        "uq_case_notes_one_pending",
        "case_notes",
        ["case_id"],
        unique=True,
        postgresql_where=sa.text("status = 'awaiting_review'"),
    )
    op.create_table(
        "case_note_versions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("note_id", sa.UUID(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("cited_ids", postgresql.ARRAY(sa.Text()), nullable=False),
        sa.Column("edited_by", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["edited_by"], ["users.id"], name=op.f("fk_case_note_versions_edited_by_users")
        ),
        sa.ForeignKeyConstraint(
            ["note_id"], ["case_notes.id"], name=op.f("fk_case_note_versions_note_id_case_notes")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_case_note_versions")),
        sa.UniqueConstraint("note_id", "version", name="uq_case_note_versions_note"),
    )
    op.create_index(
        op.f("ix_case_note_versions_note_id"), "case_note_versions", ["note_id"], unique=False
    )
    op.create_table(
        "case_status_changes",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("case_id", sa.Text(), nullable=False),
        sa.Column("from_status", case_status, nullable=False),
        sa.Column("to_status", case_status, nullable=False),
        sa.Column("actor_id", sa.UUID(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("note_id", sa.UUID(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["actor_id"], ["users.id"], name=op.f("fk_case_status_changes_actor_id_users")
        ),
        sa.ForeignKeyConstraint(
            ["case_id"], ["cases.id"], name=op.f("fk_case_status_changes_case_id_cases")
        ),
        sa.ForeignKeyConstraint(
            ["note_id"], ["case_notes.id"], name=op.f("fk_case_status_changes_note_id_case_notes")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_case_status_changes")),
    )
    op.create_index(
        op.f("ix_case_status_changes_case_id"), "case_status_changes", ["case_id"], unique=False
    )
    op.create_table(
        "note_reviews",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("note_id", sa.UUID(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("reviewer_id", sa.UUID(), nullable=False),
        sa.Column(
            "decision",
            sa.Enum(
                "return",
                "approve_keep_open",
                "approve_escalate",
                "approve_close",
                name="review_decision",
            ),
            nullable=False,
        ),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["note_id"], ["case_notes.id"], name=op.f("fk_note_reviews_note_id_case_notes")
        ),
        sa.ForeignKeyConstraint(
            ["reviewer_id"], ["users.id"], name=op.f("fk_note_reviews_reviewer_id_users")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_note_reviews")),
    )
    op.create_index(op.f("ix_note_reviews_note_id"), "note_reviews", ["note_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_note_reviews_note_id"), table_name="note_reviews")
    op.drop_table("note_reviews")
    op.drop_index(op.f("ix_case_status_changes_case_id"), table_name="case_status_changes")
    op.drop_table("case_status_changes")
    op.drop_index(op.f("ix_case_note_versions_note_id"), table_name="case_note_versions")
    op.drop_table("case_note_versions")
    op.drop_index(
        "uq_case_notes_one_pending",
        table_name="case_notes",
        postgresql_where=sa.text("status = 'awaiting_review'"),
    )
    op.drop_index(op.f("ix_case_notes_case_id"), table_name="case_notes")
    op.drop_table("case_notes")
    op.drop_index(op.f("ix_copilot_messages_chat_id"), table_name="copilot_messages")
    op.drop_table("copilot_messages")
    op.drop_index("ix_copilot_runs_user_created", table_name="copilot_runs")
    op.drop_index(op.f("ix_copilot_runs_created_at"), table_name="copilot_runs")
    op.drop_table("copilot_runs")
    op.drop_index("ix_copilot_chats_case_author", table_name="copilot_chats")
    op.drop_table("copilot_chats")
    for name in NEW_ENUMS:
        op.execute(f"DROP TYPE IF EXISTS {name}")
