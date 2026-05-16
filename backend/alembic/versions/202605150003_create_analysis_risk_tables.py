"""create analysis risk tables

Revision ID: 202605150003
Revises: 202605150002
Create Date: 2026-05-15 19:45:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "202605150003"
down_revision: str | None = "202605150002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "nutrition_analyses",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("goal_id", sa.String(length=36), nullable=True),
        sa.Column("analysis_date", sa.Date(), nullable=False),
        sa.Column("period_type", sa.String(length=32), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("totals", sa.JSON(), nullable=False),
        sa.Column("macro_balance", sa.JSON(), nullable=False),
        sa.Column("evidence", sa.JSON(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["goal_id"], ["health_goals.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_nutrition_analyses_analysis_date"),
        "nutrition_analyses",
        ["analysis_date"],
    )
    op.create_index(op.f("ix_nutrition_analyses_user_id"), "nutrition_analyses", ["user_id"])

    op.create_table(
        "risk_alerts",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("analysis_id", sa.String(length=36), nullable=True),
        sa.Column("risk_type", sa.String(length=64), nullable=False),
        sa.Column("severity", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("evidence", sa.JSON(), nullable=False),
        sa.Column("suggestion", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["analysis_id"], ["nutrition_analyses.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_risk_alerts_analysis_id"), "risk_alerts", ["analysis_id"])
    op.create_index(op.f("ix_risk_alerts_user_id"), "risk_alerts", ["user_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_risk_alerts_user_id"), table_name="risk_alerts")
    op.drop_index(op.f("ix_risk_alerts_analysis_id"), table_name="risk_alerts")
    op.drop_table("risk_alerts")
    op.drop_index(op.f("ix_nutrition_analyses_user_id"), table_name="nutrition_analyses")
    op.drop_index(op.f("ix_nutrition_analyses_analysis_date"), table_name="nutrition_analyses")
    op.drop_table("nutrition_analyses")
