from datetime import date, datetime, time

from pydantic import BaseModel, ConfigDict, Field


class HealthProfileBase(BaseModel):
    age: int = Field(ge=18, le=80)
    gender: str = Field(min_length=1, max_length=32)
    height_cm: float = Field(gt=0, le=260)
    weight_kg: float = Field(gt=0, le=300)
    sleep_hours: float = Field(ge=0, le=24)
    bedtime: time | None = None
    wake_time: time | None = None
    activity_level: str = Field(min_length=1, max_length=32)
    exercise_frequency: int = Field(ge=0, le=14)
    dietary_preferences: list[str] = Field(default_factory=list)
    allergies: list[str] = Field(default_factory=list)
    budget_level: str | None = Field(default=None, max_length=32)


class HealthProfileUpsert(HealthProfileBase):
    pass


class HealthProfileRead(HealthProfileBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FitnessProfileBase(BaseModel):
    exercise_level: str = Field(min_length=1, max_length=32)
    weekly_frequency: int = Field(ge=0, le=14)
    preferred_exercise: list[str] = Field(default_factory=list)
    available_time_minutes: int = Field(ge=0, le=300)
    fitness_goal: str = Field(min_length=1, max_length=48)
    contraindications: list[str] = Field(default_factory=list)
    is_sedentary: bool = False


class FitnessProfileUpsert(FitnessProfileBase):
    pass


class FitnessProfileRead(FitnessProfileBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class HealthGoalBase(BaseModel):
    goal_type: str = Field(min_length=1, max_length=48)
    target_weight_kg: float | None = Field(default=None, gt=0, le=300)
    target_calories: float | None = Field(default=None, gt=0, le=10000)
    target_protein_g: float | None = Field(default=None, ge=0, le=500)
    start_date: date
    end_date: date | None = None
    status: str = Field(default="active", max_length=32)


class HealthGoalCreate(HealthGoalBase):
    pass


class HealthGoalUpdate(BaseModel):
    goal_type: str | None = Field(default=None, min_length=1, max_length=48)
    target_weight_kg: float | None = Field(default=None, gt=0, le=300)
    target_calories: float | None = Field(default=None, gt=0, le=10000)
    target_protein_g: float | None = Field(default=None, ge=0, le=500)
    start_date: date | None = None
    end_date: date | None = None
    status: str | None = Field(default=None, max_length=32)


class GoalStatusUpdate(BaseModel):
    status: str = Field(min_length=1, max_length=32)


class HealthGoalRead(HealthGoalBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FoodItemBase(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    amount: float = Field(gt=0)
    unit: str = Field(min_length=1, max_length=32)
    calories: float = Field(default=0, ge=0)
    protein_g: float = Field(default=0, ge=0)
    fat_g: float = Field(default=0, ge=0)
    carbs_g: float = Field(default=0, ge=0)
    fiber_g: float = Field(default=0, ge=0)
    sugar_g: float = Field(default=0, ge=0)
    sodium_mg: float = Field(default=0, ge=0)
    confidence: float | None = Field(default=None, ge=0, le=1)


class FoodItemCreate(FoodItemBase):
    pass


class FoodItemRead(FoodItemBase):
    id: str
    meal_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MealBase(BaseModel):
    meal_date: date
    meal_time: time | None = None
    meal_type: str = Field(min_length=1, max_length=32)
    location: str | None = Field(default=None, max_length=64)
    source: str = Field(default="manual", max_length=32)
    note: str | None = None


class MealCreate(MealBase):
    food_items: list[FoodItemCreate] = Field(default_factory=list)


class MealUpdate(BaseModel):
    meal_date: date | None = None
    meal_time: time | None = None
    meal_type: str | None = Field(default=None, min_length=1, max_length=32)
    location: str | None = Field(default=None, max_length=64)
    source: str | None = Field(default=None, max_length=32)
    note: str | None = None
    food_items: list[FoodItemCreate] | None = None


class MealRead(MealBase):
    id: str
    user_id: str
    food_items: list[FoodItemRead]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AnalysisGenerateRequest(BaseModel):
    analysis_date: date
    period_type: str = Field(default="daily", pattern="^(daily)$")


class NutritionAnalysisRead(BaseModel):
    id: str
    user_id: str
    goal_id: str | None
    analysis_date: date
    period_type: str
    score: int
    totals: dict[str, float]
    macro_balance: dict[str, float]
    evidence: dict[str, object]
    summary: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RiskAlertRead(BaseModel):
    id: str
    user_id: str
    analysis_id: str | None
    risk_type: str
    severity: str
    title: str
    description: str
    evidence: dict[str, object]
    suggestion: str
    status: str
    created_at: datetime
    resolved_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class RiskEvaluateRequest(BaseModel):
    analysis_date: date


class RiskStatusUpdate(BaseModel):
    status: str = Field(min_length=1, max_length=32)
