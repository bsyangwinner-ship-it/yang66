from typing import Any, Literal, TypeAlias, TypedDict

AgentGoal: TypeAlias = Literal[
    "fat_loss",
    "muscle_gain",
    "maintenance",
    "glucose_control",
    "sleep_improvement",
    "body_shaping",
]


class NutritionAgentState(TypedDict, total=False):
    user_id: str
    session_id: str
    analysis_date: str
    goal: AgentGoal
    user_message: str
    active_goal: dict[str, Any] | None
    profile_summary: dict[str, Any]
    fitness_profile: dict[str, Any]
    meal_window_days: int
    nutrition_analysis: dict[str, Any]
    risks: list[dict[str, Any]]
    rag_context: list[dict[str, Any]]
    meal_plan: dict[str, Any]
    exercise_recommendation: dict[str, Any]
    intervention_plan: dict[str, Any]
    tool_calls: list[dict[str, Any]]
    final_response: str
