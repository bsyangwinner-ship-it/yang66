"""create core business tables

Revision ID: 202605150002
Revises: 202605150001
Create Date: 2026-05-15 19:15:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "202605150002"
down_revision: str | None = "202605150001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "health_profiles",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("age", sa.Integer(), nullable=False),
        sa.Column("gender", sa.String(length=32), nullable=False),
        sa.Column("height_cm", sa.Float(), nullable=False),
        sa.Column("weight_kg", sa.Float(), nullable=False),
        sa.Column("sleep_hours", sa.Float(), nullable=False),
        sa.Column("bedtime", sa.Time(), nullable=True),
        sa.Column("wake_time", sa.Time(), nullable=True),
        sa.Column("activity_level", sa.String(length=32), nullable=False),
        sa.Column("exercise_frequency", sa.Integer(), nullable=False),
        sa.Column("dietary_preferences", sa.JSON(), nullable=False),
        sa.Column("allergies", sa.JSON(), nullable=False),
        sa.Column("budget_level", sa.String(length=32), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_health_profiles_user_id"), "health_profiles", ["user_id"], unique=True)

    op.create_table(
        "user_fitness_profiles",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("exercise_level", sa.String(length=32), nullable=False),
        sa.Column("weekly_frequency", sa.Integer(), nullable=False),
        sa.Column("preferred_exercise", sa.JSON(), nullable=False),
        sa.Column("available_time_minutes", sa.Integer(), nullable=False),
        sa.Column("fitness_goal", sa.String(length=48), nullable=False),
        sa.Column("contraindications", sa.JSON(), nullable=False),
        sa.Column("is_sedentary", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_user_fitness_profiles_user_id"),
        "user_fitness_profiles",
        ["user_id"],
        unique=True,
    )

    op.create_table(
        "health_goals",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("goal_type", sa.String(length=48), nullable=False),
        sa.Column("target_weight_kg", sa.Float(), nullable=True),
        sa.Column("target_calories", sa.Float(), nullable=True),
        sa.Column("target_protein_g", sa.Float(), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_health_goals_user_id"), "health_goals", ["user_id"])

    op.create_table(
        "meals",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("meal_date", sa.Date(), nullable=False),
        sa.Column("meal_time", sa.Time(), nullable=True),
        sa.Column("meal_type", sa.String(length=32), nullable=False),
        sa.Column("location", sa.String(length=64), nullable=True),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_meals_meal_date"), "meals", ["meal_date"])
    op.create_index(op.f("ix_meals_user_id"), "meals", ["user_id"])

    op.create_table(
        "food_items",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("meal_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("unit", sa.String(length=32), nullable=False),
        sa.Column("calories", sa.Float(), nullable=False),
        sa.Column("protein_g", sa.Float(), nullable=False),
        sa.Column("fat_g", sa.Float(), nullable=False),
        sa.Column("carbs_g", sa.Float(), nullable=False),
        sa.Column("fiber_g", sa.Float(), nullable=False),
        sa.Column("sugar_g", sa.Float(), nullable=False),
        sa.Column("sodium_mg", sa.Float(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["meal_id"], ["meals.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_food_items_meal_id"), "food_items", ["meal_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_food_items_meal_id"), table_name="food_items")
    op.drop_table("food_items")
    op.drop_index(op.f("ix_meals_user_id"), table_name="meals")
    op.drop_index(op.f("ix_meals_meal_date"), table_name="meals")
    op.drop_table("meals")
    op.drop_index(op.f("ix_health_goals_user_id"), table_name="health_goals")
    op.drop_table("health_goals")
    op.drop_index(op.f("ix_user_fitness_profiles_user_id"), table_name="user_fitness_profiles")
    op.drop_table("user_fitness_profiles")
    op.drop_index(op.f("ix_health_profiles_user_id"), table_name="health_profiles")
    op.drop_table("health_profiles")
