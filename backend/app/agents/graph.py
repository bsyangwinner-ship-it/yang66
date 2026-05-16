from collections.abc import Callable, Generator
from datetime import UTC, date, datetime
from time import perf_counter
from typing import Any, cast

from langgraph.graph import END, START, StateGraph
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents.state import AgentGoal, NutritionAgentState
from app.models.business import (
    HealthGoal,
    HealthProfile,
    NutritionAnalysis,
    RiskAlert,
    UserFitnessProfile,
)
from app.services.knowledge import search_knowledge_context
from app.services.nutrition import generate_daily_analysis

GRAPH_NAME = "nutrition_agent_v1"

GOAL_KEYWORDS: dict[AgentGoal, tuple[str, ...]] = {
    "fat_loss": ("减脂", "减肥", "瘦", "fat loss", "cut"),
    "muscle_gain": ("增肌", "练肌肉", "蛋白", "muscle", "bulk"),
    "maintenance": ("维持", "保持", "健康", "maintenance"),
    "glucose_control": ("控糖", "血糖", "少糖", "glucose", "sugar"),
    "sleep_improvement": ("作息", "熬夜", "睡眠", "sleep"),
    "body_shaping": ("塑形", "身材", "线条", "shape"),
}


def build_agent_graph_placeholder() -> dict[str, str]:
    return {
        "planner": "understand user goal and decide next tools",
        "profile": "summarize health profile and fitness profile",
        "nutrition": "calculate nutrition intake and score",
        "risk": "detect diet risks with deterministic rules",
        "knowledge": "retrieve nutrition and intervention knowledge with RAG",
        "meal_plan": "generate personalized meal plan",
        "exercise": "recommend exercise interventions from diet intake and fitness profile",
        "intervention": "track long-term progress and next actions",
    }


def _json_ready(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.astimezone(UTC).isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    return value


def _record_tool_call(
    state: NutritionAgentState,
    tool_name: str,
    input_payload: dict[str, Any],
    output_payload: dict[str, Any],
    latency_ms: int,
    status: str = "success",
) -> None:
    tool_calls = state.setdefault("tool_calls", [])
    tool_calls.append(
        {
            "tool_name": tool_name,
            "input": _json_ready(input_payload),
            "output": _json_ready(output_payload),
            "status": status,
            "latency_ms": latency_ms,
        }
    )


def _run_tool(
    state: NutritionAgentState,
    tool_name: str,
    input_payload: dict[str, Any],
    action: Callable[[], dict[str, Any]],
) -> dict[str, Any]:
    started = perf_counter()
    try:
        output = action()
    except Exception as exc:
        latency_ms = round((perf_counter() - started) * 1000)
        _record_tool_call(
            state,
            tool_name,
            input_payload,
            {"error": str(exc)},
            latency_ms,
            status="failed",
        )
        raise

    latency_ms = round((perf_counter() - started) * 1000)
    _record_tool_call(state, tool_name, input_payload, output, latency_ms)
    return output


def _infer_goal(message: str, active_goal: HealthGoal | None) -> AgentGoal:
    normalized = message.lower()
    for goal, keywords in GOAL_KEYWORDS.items():
        if any(keyword in normalized for keyword in keywords):
            return goal

    if active_goal is not None:
        goal_type = active_goal.goal_type.lower()
        if goal_type in GOAL_KEYWORDS:
            return goal_type

    return "maintenance"


def _goal_to_dict(goal: HealthGoal | None) -> dict[str, Any] | None:
    if goal is None:
        return None
    return {
        "id": goal.id,
        "goal_type": goal.goal_type,
        "target_weight_kg": goal.target_weight_kg,
        "target_calories": goal.target_calories,
        "target_protein_g": goal.target_protein_g,
        "start_date": goal.start_date,
        "end_date": goal.end_date,
        "status": goal.status,
    }


def _profile_to_dict(profile: HealthProfile | None) -> dict[str, Any]:
    if profile is None:
        return {"complete": False, "missing": ["health_profile"]}
    return {
        "complete": True,
        "age": profile.age,
        "gender": profile.gender,
        "height_cm": profile.height_cm,
        "weight_kg": profile.weight_kg,
        "sleep_hours": profile.sleep_hours,
        "bedtime": profile.bedtime.isoformat() if profile.bedtime else None,
        "wake_time": profile.wake_time.isoformat() if profile.wake_time else None,
        "activity_level": profile.activity_level,
        "exercise_frequency": profile.exercise_frequency,
        "dietary_preferences": profile.dietary_preferences,
        "allergies": profile.allergies,
        "budget_level": profile.budget_level,
    }


def _fitness_to_dict(profile: UserFitnessProfile | None) -> dict[str, Any]:
    if profile is None:
        return {
            "complete": False,
            "exercise_level": "beginner",
            "weekly_frequency": 0,
            "preferred_exercise": [],
            "available_time_minutes": 30,
            "fitness_goal": "maintenance",
            "contraindications": [],
            "is_sedentary": True,
        }
    return {
        "complete": True,
        "exercise_level": profile.exercise_level,
        "weekly_frequency": profile.weekly_frequency,
        "preferred_exercise": profile.preferred_exercise,
        "available_time_minutes": profile.available_time_minutes,
        "fitness_goal": profile.fitness_goal,
        "contraindications": profile.contraindications,
        "is_sedentary": profile.is_sedentary,
    }


def _analysis_to_dict(analysis: NutritionAnalysis) -> dict[str, Any]:
    return {
        "id": analysis.id,
        "analysis_date": analysis.analysis_date,
        "period_type": analysis.period_type,
        "score": analysis.score,
        "totals": analysis.totals,
        "macro_balance": analysis.macro_balance,
        "evidence": analysis.evidence,
        "summary": analysis.summary,
        "created_at": analysis.created_at,
    }


def _risk_to_dict(risk: RiskAlert) -> dict[str, Any]:
    return {
        "id": risk.id,
        "risk_type": risk.risk_type,
        "severity": risk.severity,
        "title": risk.title,
        "description": risk.description,
        "evidence": risk.evidence,
        "suggestion": risk.suggestion,
        "status": risk.status,
        "created_at": risk.created_at,
    }


def _risk_types(state: NutritionAgentState) -> set[str]:
    return {str(risk.get("risk_type")) for risk in state.get("risks", [])}


def _build_rag_query(state: NutritionAgentState) -> str:
    risk_titles = " ".join(str(risk.get("title", "")) for risk in state.get("risks", []))
    goal = str(state.get("goal", "maintenance"))
    return " ".join(
        part
        for part in [
            state.get("user_message", ""),
            goal,
            risk_titles,
            "nutrition meal exercise intervention",
        ]
        if part
    )


def _build_meal_plan(state: NutritionAgentState) -> dict[str, Any]:
    goal = state.get("goal", "maintenance")
    risks = _risk_types(state)
    totals = state.get("nutrition_analysis", {}).get("totals", {})

    next_meal: list[str] = []
    swaps: list[dict[str, str]] = []

    if "calorie_excess" in risks or "fat_ratio_high" in risks:
        next_meal.append("下一餐选择清蒸/炖煮蛋白、两拳蔬菜和半拳主食，先暂停油炸食品。")
        swaps.append({"from": "炸鸡/汉堡", "to": "鸡胸肉饭、清蒸鱼、番茄牛肉饭"})
    if "sugar_high" in risks:
        next_meal.append("饮品改为无糖茶、白水或无糖酸奶，奶茶改为少糖或不喝。")
        swaps.append({"from": "奶茶/甜饮", "to": "无糖茶、气泡水、无糖酸奶"})
    if "protein_low" in risks:
        next_meal.append("补足一份优质蛋白，例如鸡蛋、鱼虾、瘦肉、豆腐或牛奶。")
    if "fiber_low" in risks:
        next_meal.append("加一份深色蔬菜，并把部分精制主食换成杂粮饭或燕麦。")
    if not next_meal:
        next_meal.append("保持三餐稳定，继续维持蔬菜、优质蛋白和主食的均衡搭配。")

    if goal == "fat_loss":
        strategy = "热量赤字优先，保证蛋白质和膳食纤维，减少油炸和含糖饮品。"
    elif goal == "muscle_gain":
        strategy = "力量训练日保证蛋白质和足量主食，避免只增热量不增优质营养。"
    elif goal == "sleep_improvement":
        strategy = "晚餐提前、减少夜宵和高糖饮品，避免睡前过量进食。"
    else:
        strategy = "维持规律三餐和稳定活动量，优先处理已识别的风险项。"

    return {
        "goal": goal,
        "strategy": strategy,
        "today_adjustment": next_meal,
        "tomorrow_plan": [
            "早餐：牛奶/无糖酸奶 + 鸡蛋 + 全麦主食",
            "午餐：食堂优先选瘦肉/鱼虾/豆制品 + 两份蔬菜 + 适量米饭",
            "晚餐：少油蛋白 + 蔬菜 + 少量主食，尽量在 21:00 前完成",
        ],
        "substitutions": swaps,
        "evidence": {
            "calories": totals.get("calories", 0),
            "protein_g": totals.get("protein_g", 0),
            "risk_types": sorted(risks),
            "knowledge_context": [
                {
                    "title": item.get("title"),
                    "source": item.get("source"),
                    "similarity": item.get("similarity"),
                }
                for item in state.get("rag_context", [])[:3]
            ],
        },
    }


def _build_exercise_plan(state: NutritionAgentState) -> dict[str, Any]:
    analysis = state.get("nutrition_analysis", {})
    totals = cast(dict[str, Any], analysis.get("totals", {}))
    evidence = cast(dict[str, Any], analysis.get("evidence", {}))
    fitness = state.get("fitness_profile", {})
    risks = _risk_types(state)
    target_calories = float(evidence.get("target_calories", 2000))
    surplus = float(totals.get("calories", 0)) - target_calories
    available_time = int(fitness.get("available_time_minutes", 30) or 30)
    exercise_level = str(fitness.get("exercise_level", "beginner"))
    contraindications = cast(list[str], fitness.get("contraindications", []))

    plan: list[dict[str, str]] = []
    if "late_dinner" in risks or "night_snack_frequent" in risks:
        plan.append(
            {
                "type": "恢复",
                "activity": "饭后轻松步行",
                "duration": f"{min(20, available_time)}分钟",
                "intensity": "低",
                "reason": (
                    "晚间进食偏晚或存在夜宵，适合低强度活动帮助消化，"
                    "不建议临睡前高强度训练。"
                ),
            }
        )

    if surplus > 300:
        duration = min(45, max(25, available_time))
        plan.append(
            {
                "type": "有氧",
                "activity": "快走、骑行或椭圆机",
                "duration": f"{duration}分钟",
                "intensity": "中等",
                "reason": f"今日热量约高于目标 {surplus:.0f} kcal，建议用低门槛有氧做温和调节。",
            }
        )

    protein_target = float(evidence.get("target_protein_g", 70))
    if float(totals.get("protein_g", 0)) >= protein_target * 0.8 and exercise_level != "beginner":
        plan.append(
            {
                "type": "力量",
                "activity": "深蹲、俯卧撑、划船、平板支撑",
                "duration": f"{min(30, available_time)}分钟",
                "intensity": "中等",
                "reason": "蛋白质摄入接近目标，适合配合力量训练维持或提升肌肉量。",
            }
        )

    if not plan:
        plan.append(
            {
                "type": "基础活动",
                "activity": "校园步行或拉伸",
                "duration": f"{min(30, available_time)}分钟",
                "intensity": "低到中等",
                "reason": "当前更适合稳定活动量，先形成可持续习惯。",
            }
        )

    return {
        "exercise_goal": state.get("goal", "maintenance"),
        "calorie_surplus": round(surplus, 1),
        "recommended_plan": plan,
        "weekly_baseline": "参考每周至少 150 分钟中等强度有氧，并结合每周 2 天以上肌力训练。",
        "safety_notes": contraindications
        or ["若出现疼痛、头晕或明显不适，应停止训练并咨询专业人士。"],
    }


def _build_intervention_plan(db: Session, state: NutritionAgentState) -> dict[str, Any]:
    user_id = state["user_id"]
    analyses = list(
        db.scalars(
            select(NutritionAnalysis)
            .where(NutritionAnalysis.user_id == user_id)
            .order_by(NutritionAnalysis.analysis_date.desc())
            .limit(7)
        )
    )
    average_score = (
        round(sum(analysis.score for analysis in analyses) / len(analyses), 1) if analyses else 0
    )
    current_score = int(state.get("nutrition_analysis", {}).get("score", 0))
    return {
        "tracking_window_days": 7,
        "recent_analysis_count": len(analyses),
        "average_score": average_score,
        "current_score": current_score,
        "next_actions": [
            "连续记录 3 天早餐和晚餐时间，观察作息相关风险是否下降。",
            "未来 7 天优先跟踪糖摄入、蛋白质达标率和夜宵次数。",
            "下次复盘时比较平均评分、风险数量和热量波动。",
        ],
    }


def _compose_final_response(state: NutritionAgentState) -> str:
    analysis = state.get("nutrition_analysis", {})
    risks = state.get("risks", [])
    meal_plan = state.get("meal_plan", {})
    exercise = state.get("exercise_recommendation", {})
    score = analysis.get("score", 0)
    totals = cast(dict[str, Any], analysis.get("totals", {}))
    top_risks = "、".join(str(risk.get("title")) for risk in risks[:3]) or "暂未发现明显风险"
    meal_tip = "; ".join(cast(list[str], meal_plan.get("today_adjustment", []))[:2])
    exercise_items = cast(list[dict[str, str]], exercise.get("recommended_plan", []))
    exercise_tip = (
        f"{exercise_items[0]['activity']} {exercise_items[0]['duration']}"
        if exercise_items
        else "保持轻量活动"
    )
    rag_context = state.get("rag_context", [])
    knowledge_tip = ""
    if rag_context:
        titles = "、".join(str(item.get("title")) for item in rag_context[:2])
        knowledge_tip = f"参考知识：{titles}。"

    return (
        f"本次 Agent 已完成饮食分析闭环。饮食评分为 {score} 分，"
        f"今日热量约 {float(totals.get('calories', 0)):.0f} kcal。"
        f"主要风险：{top_risks}。饮食调整：{meal_tip}。"
        f"运动干预：{exercise_tip}。{knowledge_tip}建议继续记录 3-7 天，用趋势判断改善效果。"
    )


def build_agent_graph(db: Session) -> Any:
    def planner_node(state: NutritionAgentState) -> NutritionAgentState:
        active_goal = db.scalar(
            select(HealthGoal)
            .where(HealthGoal.user_id == state["user_id"], HealthGoal.status == "active")
            .order_by(HealthGoal.created_at.desc())
        )

        def action() -> dict[str, Any]:
            goal = _infer_goal(state["user_message"], active_goal)
            return {"goal": goal, "active_goal": _goal_to_dict(active_goal)}

        output = _run_tool(
            state,
            "planner_goal_inference",
            {"message": state["user_message"]},
            action,
        )
        state["goal"] = cast(AgentGoal, output["goal"])
        state["active_goal"] = cast(dict[str, Any] | None, output["active_goal"])
        return state

    def profile_node(state: NutritionAgentState) -> NutritionAgentState:
        def action() -> dict[str, Any]:
            profile = db.scalar(
                select(HealthProfile).where(HealthProfile.user_id == state["user_id"])
            )
            fitness = db.scalar(
                select(UserFitnessProfile).where(UserFitnessProfile.user_id == state["user_id"])
            )
            return {
                "profile_summary": _profile_to_dict(profile),
                "fitness_profile": _fitness_to_dict(fitness),
            }

        output = _run_tool(state, "profile_reader", {"user_id": state["user_id"]}, action)
        state["profile_summary"] = cast(dict[str, Any], output["profile_summary"])
        state["fitness_profile"] = cast(dict[str, Any], output["fitness_profile"])
        return state

    def nutrition_node(state: NutritionAgentState) -> NutritionAgentState:
        analysis_date = date.fromisoformat(state["analysis_date"])

        def action() -> dict[str, Any]:
            analysis = generate_daily_analysis(db, state["user_id"], analysis_date)
            return {"nutrition_analysis": _analysis_to_dict(analysis)}

        output = _run_tool(
            state,
            "nutrition_calculator",
            {"user_id": state["user_id"], "analysis_date": analysis_date},
            action,
        )
        state["nutrition_analysis"] = cast(dict[str, Any], output["nutrition_analysis"])
        return state

    def risk_node(state: NutritionAgentState) -> NutritionAgentState:
        analysis_id = str(state["nutrition_analysis"]["id"])

        def action() -> dict[str, Any]:
            risks = list(
                db.scalars(
                    select(RiskAlert)
                    .where(
                        RiskAlert.user_id == state["user_id"],
                        RiskAlert.analysis_id == analysis_id,
                    )
                    .order_by(RiskAlert.created_at.desc())
                )
            )
            return {"risks": [_risk_to_dict(risk) for risk in risks]}

        output = _run_tool(
            state,
            "risk_evaluator",
            {"analysis_id": analysis_id},
            action,
        )
        state["risks"] = cast(list[dict[str, Any]], output["risks"])
        return state

    def knowledge_node(state: NutritionAgentState) -> NutritionAgentState:
        query = _build_rag_query(state)
        output = _run_tool(
            state,
            "rag_search",
            {"query": query, "top_k": 3},
            lambda: {"rag_context": search_knowledge_context(db, query=query, top_k=3)},
        )
        state["rag_context"] = cast(list[dict[str, Any]], output["rag_context"])
        return state

    def meal_plan_node(state: NutritionAgentState) -> NutritionAgentState:
        output = _run_tool(
            state,
            "meal_plan_generator",
            {"goal": state.get("goal"), "risk_count": len(state.get("risks", []))},
            lambda: {"meal_plan": _build_meal_plan(state)},
        )
        state["meal_plan"] = cast(dict[str, Any], output["meal_plan"])
        return state

    def exercise_node(state: NutritionAgentState) -> NutritionAgentState:
        output = _run_tool(
            state,
            "exercise_plan_generator",
            {
                "goal": state.get("goal"),
                "analysis_id": state.get("nutrition_analysis", {}).get("id"),
            },
            lambda: {"exercise_recommendation": _build_exercise_plan(state)},
        )
        state["exercise_recommendation"] = cast(dict[str, Any], output["exercise_recommendation"])
        return state

    def intervention_node(state: NutritionAgentState) -> NutritionAgentState:
        output = _run_tool(
            state,
            "intervention_tracker",
            {"user_id": state["user_id"], "analysis_date": state["analysis_date"]},
            lambda: {"intervention_plan": _build_intervention_plan(db, state)},
        )
        state["intervention_plan"] = cast(dict[str, Any], output["intervention_plan"])
        state["final_response"] = _compose_final_response(state)
        return state

    graph = StateGraph(NutritionAgentState)
    graph.add_node("planner", planner_node)
    graph.add_node("profile", profile_node)
    graph.add_node("nutrition", nutrition_node)
    graph.add_node("risk", risk_node)
    graph.add_node("knowledge", knowledge_node)
    graph.add_node("meal_plan", meal_plan_node)
    graph.add_node("exercise", exercise_node)
    graph.add_node("intervention", intervention_node)

    graph.add_edge(START, "planner")
    graph.add_edge("planner", "profile")
    graph.add_edge("profile", "nutrition")
    graph.add_edge("nutrition", "risk")
    graph.add_edge("risk", "knowledge")
    graph.add_edge("knowledge", "meal_plan")
    graph.add_edge("meal_plan", "exercise")
    graph.add_edge("exercise", "intervention")
    graph.add_edge("intervention", END)
    return graph.compile()


def run_rule_fallback(state: NutritionAgentState) -> NutritionAgentState:
    goal = state.get("goal", "maintenance")
    state["final_response"] = (
        f"已收到目标 {goal}。当前使用规则兜底模式，可继续完成营养分析、风险识别、"
        "餐单建议和运动干预。"
    )
    return state


def _build_initial_state(
    user_id: str,
    session_id: str,
    user_message: str,
    analysis_date: date,
) -> NutritionAgentState:
    return {
        "user_id": user_id,
        "session_id": session_id,
        "user_message": user_message,
        "analysis_date": analysis_date.isoformat(),
        "meal_window_days": 7,
        "tool_calls": [],
    }


def run_nutrition_agent(
    db: Session,
    user_id: str,
    session_id: str,
    user_message: str,
    analysis_date: date,
) -> NutritionAgentState:
    initial_state = _build_initial_state(user_id, session_id, user_message, analysis_date)
    compiled = build_agent_graph(db)
    result = compiled.invoke(initial_state)
    return cast(NutritionAgentState, _json_ready(result))


def stream_nutrition_agent(
    db: Session,
    user_id: str,
    session_id: str,
    user_message: str,
    analysis_date: date,
) -> Generator[dict[str, Any], None, None]:
    initial_state = _build_initial_state(user_id, session_id, user_message, analysis_date)
    compiled = build_agent_graph(db)
    for chunk in compiled.stream(initial_state):
        if not isinstance(chunk, dict):
            continue
        for node_name, node_state in chunk.items():
            if isinstance(node_state, dict):
                yield {
                    "node": str(node_name),
                    "state": cast(NutritionAgentState, _json_ready(node_state)),
                }
