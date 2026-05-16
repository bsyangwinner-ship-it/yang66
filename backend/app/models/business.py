from datetime import UTC, date, datetime, time

from sqlalchemy import JSON, Date, DateTime, Float, ForeignKey, Integer, String, Text, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.auth import uuid_string


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )


class HealthProfile(TimestampMixin, Base):
    __tablename__ = "health_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_string)
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    gender: Mapped[str] = mapped_column(String(32), nullable=False)
    height_cm: Mapped[float] = mapped_column(Float, nullable=False)
    weight_kg: Mapped[float] = mapped_column(Float, nullable=False)
    sleep_hours: Mapped[float] = mapped_column(Float, nullable=False)
    bedtime: Mapped[time | None] = mapped_column(Time, nullable=True)
    wake_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    activity_level: Mapped[str] = mapped_column(String(32), nullable=False)
    exercise_frequency: Mapped[int] = mapped_column(Integer, nullable=False)
    dietary_preferences: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    allergies: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    budget_level: Mapped[str | None] = mapped_column(String(32), nullable=True)


class UserFitnessProfile(TimestampMixin, Base):
    __tablename__ = "user_fitness_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_string)
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )
    exercise_level: Mapped[str] = mapped_column(String(32), nullable=False)
    weekly_frequency: Mapped[int] = mapped_column(Integer, nullable=False)
    preferred_exercise: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    available_time_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    fitness_goal: Mapped[str] = mapped_column(String(48), nullable=False)
    contraindications: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    is_sedentary: Mapped[bool] = mapped_column(default=False, nullable=False)


class HealthGoal(TimestampMixin, Base):
    __tablename__ = "health_goals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_string)
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    goal_type: Mapped[str] = mapped_column(String(48), nullable=False)
    target_weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    target_calories: Mapped[float | None] = mapped_column(Float, nullable=True)
    target_protein_g: Mapped[float | None] = mapped_column(Float, nullable=True)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)


class Meal(TimestampMixin, Base):
    __tablename__ = "meals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_string)
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    meal_date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    meal_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    meal_type: Mapped[str] = mapped_column(String(32), nullable=False)
    location: Mapped[str | None] = mapped_column(String(64), nullable=True)
    source: Mapped[str] = mapped_column(String(32), default="manual", nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    food_items: Mapped[list["FoodItem"]] = relationship(
        back_populates="meal",
        cascade="all, delete-orphan",
        order_by="FoodItem.created_at",
    )


class FoodItem(TimestampMixin, Base):
    __tablename__ = "food_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_string)
    meal_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("meals.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(32), nullable=False)
    calories: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    protein_g: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    fat_g: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    carbs_g: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    fiber_g: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    sugar_g: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    sodium_mg: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    meal: Mapped[Meal] = relationship(back_populates="food_items")


class NutritionAnalysis(Base):
    __tablename__ = "nutrition_analyses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_string)
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    goal_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("health_goals.id", ondelete="SET NULL"),
        nullable=True,
    )
    analysis_date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    period_type: Mapped[str] = mapped_column(String(32), default="daily", nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    totals: Mapped[dict[str, float]] = mapped_column(JSON, nullable=False)
    macro_balance: Mapped[dict[str, float]] = mapped_column(JSON, nullable=False)
    evidence: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )


class RiskAlert(Base):
    __tablename__ = "risk_alerts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_string)
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    analysis_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("nutrition_analyses.id", ondelete="CASCADE"),
        index=True,
        nullable=True,
    )
    risk_type: Mapped[str] = mapped_column(String(64), nullable=False)
    severity: Mapped[str] = mapped_column(String(32), nullable=False)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    evidence: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    suggestion: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="open", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
