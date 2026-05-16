"""create reporting tables

Revision ID: 202605160003
Revises: 202605160002
Create Date: 2026-05-16 15:20:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "202605160003"
down_revision: str | None = "202605160002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "reports",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("report_type", sa.String(length=32), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("metrics", sa.JSON(), nullable=False),
        sa.Column("recommendations", sa.JSON(), nullable=False),
        sa.Column("export_format", sa.String(length=32), nullable=False),
        sa.Column("export_object_key", sa.String(length=260), nullable=True),
        sa.Column("export_content", sa.Text(), nullable=True),
        sa.Column("task_id", sa.String(length=160), nullable=True),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_reports_period_start"), "reports", ["period_start"])
    op.create_index(op.f("ix_reports_period_end"), "reports", ["period_end"])
    op.create_index(op.f("ix_reports_report_type"), "reports", ["report_type"])
    op.create_index(op.f("ix_reports_status"), "reports", ["status"])
    op.create_index(op.f("ix_reports_user_id"), "reports", ["user_id"])

    op.create_table(
        "intervention_tasks",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("report_id", sa.String(length=36), nullable=True),
        sa.Column("risk_type", sa.String(length=80), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("task_type", sa.String(length=64), nullable=False),
        sa.Column("priority", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("scheduled_for", sa.Date(), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("evidence", sa.JSON(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["report_id"], ["reports.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_intervention_tasks_due_date"),
        "intervention_tasks",
        ["due_date"],
    )
    op.create_index(
        op.f("ix_intervention_tasks_report_id"),
        "intervention_tasks",
        ["report_id"],
    )
    op.create_index(
        op.f("ix_intervention_tasks_risk_type"),
        "intervention_tasks",
        ["risk_type"],
    )
    op.create_index(
        op.f("ix_intervention_tasks_scheduled_for"),
        "intervention_tasks",
        ["scheduled_for"],
    )
    op.create_index(op.f("ix_intervention_tasks_status"), "intervention_tasks", ["status"])
    op.create_index(op.f("ix_intervention_tasks_user_id"), "intervention_tasks", ["user_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_intervention_tasks_user_id"), table_name="intervention_tasks")
    op.drop_index(op.f("ix_intervention_tasks_status"), table_name="intervention_tasks")
    op.drop_index(op.f("ix_intervention_tasks_scheduled_for"), table_name="intervention_tasks")
    op.drop_index(op.f("ix_intervention_tasks_risk_type"), table_name="intervention_tasks")
    op.drop_index(op.f("ix_intervention_tasks_report_id"), table_name="intervention_tasks")
    op.drop_index(op.f("ix_intervention_tasks_due_date"), table_name="intervention_tasks")
    op.drop_table("intervention_tasks")

    op.drop_index(op.f("ix_reports_user_id"), table_name="reports")
    op.drop_index(op.f("ix_reports_status"), table_name="reports")
    op.drop_index(op.f("ix_reports_report_type"), table_name="reports")
    op.drop_index(op.f("ix_reports_period_end"), table_name="reports")
    op.drop_index(op.f("ix_reports_period_start"), table_name="reports")
    op.drop_table("reports")
