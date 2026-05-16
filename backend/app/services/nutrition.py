from dataclasses import dataclass
from datetime import UTC, date, datetime, time

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, selectinload

from app.models.business import (
    HealthGoal,
    HealthProfile,
    Meal,
    NutritionAnalysis,
    RiskAlert,
)


@dataclass(frozen=True)
class NutritionTargets:
    calories: float
    protein_g: float
    fiber_g: float = 25
    sugar_g: float = 50
    sodium_mg: float = 2300


ACTIVITY_FACTORS = {
    "sedentary": 1.2,
    "light": 1.375,
    "moderate": 1.55,
    "active": 1.725,
    "久坐": 1.2,
    "轻度": 1.375,
    "中度": 1.55,
    "高强度": 1.725,
}

BREAKFAST_TYPES = {"breakfast", "早餐"}
DINNER_TYPES = {"dinner", "晚餐"}
NIGHT_SNACK_TYPES = {"night_snack", "夜宵"}


def get_active_goal(db: Session, user_id: str) -> HealthGoal | None:
    return db.scalar(
        select(HealthGoal)
        .where(HealthGoal.user_id == user_id, HealthGoal.status == "active")
        .order_by(HealthGoal.created_at.desc())
    )


def get_meals_for_date(db: Session, user_id: str, analysis_date: date) -> list[Meal]:
    return list(
        db.scalars(
            select(Meal)
            .options(selectinload(Meal.food_items))
            .where(Meal.user_id == user_id, Meal.meal_date == analysis_date)
            .order_by(Meal.created_at)
        )
    )


def estimate_targets(profile: HealthProfile | None, goal: HealthGoal | None) -> NutritionTargets:
    if goal is not None and goal.target_calories:
        calories = goal.target_calories
    elif profile is not None:
        base_bmr = 10 * profile.weight_kg + 6.25 * profile.height_cm - 5 * profile.age
        gender = profile.gender.lower()
        bmr = base_bmr + 5 if gender in {"male", "男", "男性"} else base_bmr - 161
        factor = ACTIVITY_FACTORS.get(profile.activity_level, 1.2)
        calories = max(1200, bmr * factor)
    else:
        calories = 2000

    if goal is not None and goal.target_protein_g:
        protein = goal.target_protein_g
    elif profile is not None:
        protein = max(50, profile.weight_kg * 1.2)
    else:
        protein = 70

    return NutritionTargets(calories=round(calories, 1), protein_g=round(protein, 1))


def calculate_totals(meals: list[Meal]) -> dict[str, float]:
    totals = {
        "calories": 0.0,
        "protein_g": 0.0,
        "fat_g": 0.0,
        "carbs_g": 0.0,
        "fiber_g": 0.0,
        "sugar_g": 0.0,
        "sodium_mg": 0.0,
    }
    for meal in meals:
        for item in meal.food_items:
            totals["calories"] += item.calories
            totals["protein_g"] += item.protein_g
            totals["fat_g"] += item.fat_g
            totals["carbs_g"] += item.carbs_g
            totals["fiber_g"] += item.fiber_g
            totals["sugar_g"] += item.sugar_g
            totals["sodium_mg"] += item.sodium_mg
    return {key: round(value, 1) for key, value in totals.items()}


def calculate_macro_balance(totals: dict[str, float]) -> dict[str, float]:
    protein_kcal = totals["protein_g"] * 4
    carbs_kcal = totals["carbs_g"] * 4
    fat_kcal = totals["fat_g"] * 9
    macro_kcal = protein_kcal + carbs_kcal + fat_kcal
    if macro_kcal <= 0:
        return {"protein_pct": 0, "carbs_pct": 0, "fat_pct": 0}
    return {
        "protein_pct": round(protein_kcal / macro_kcal * 100, 1),
        "carbs_pct": round(carbs_kcal / macro_kcal * 100, 1),
        "fat_pct": round(fat_kcal / macro_kcal * 100, 1),
    }


def has_late_dinner(meals: list[Meal]) -> bool:
    late_threshold = time(21, 0)
    return any(
        meal.meal_type in DINNER_TYPES
        and meal.meal_time is not None
        and meal.meal_time >= late_threshold
        for meal in meals
    )


def calculate_score(
    totals: dict[str, float],
    macro_balance: dict[str, float],
    targets: NutritionTargets,
    meals: list[Meal],
) -> int:
    score = 100
    calorie_ratio = totals["calories"] / targets.calories if targets.calories else 1
    protein_ratio = totals["protein_g"] / targets.protein_g if targets.protein_g else 1

    if calorie_ratio > 1.25:
        score -= 18
    elif calorie_ratio > 1.1:
        score -= 10
    elif calorie_ratio < 0.7:
        score -= 12

    if protein_ratio < 0.6:
        score -= 16
    elif protein_ratio < 0.8:
        score -= 9

    if totals["fiber_g"] < targets.fiber_g * 0.7:
        score -= 8
    if totals["sugar_g"] > targets.sugar_g:
        score -= 8
    if totals["sodium_mg"] > targets.sodium_mg:
        score -= 8
    if macro_balance["fat_pct"] > 35:
        score -= 8
    if not any(meal.meal_type in BREAKFAST_TYPES for meal in meals):
        score -= 6
    if any(meal.meal_type in NIGHT_SNACK_TYPES for meal in meals):
        score -= 6
    if has_late_dinner(meals):
        score -= 5

    return max(0, min(100, score))


def build_summary(score: int, risk_count: int, totals: dict[str, float]) -> str:
    if score >= 85:
        level = "整体饮食表现较好"
    elif score >= 70:
        level = "饮食结构基本可控"
    else:
        level = "饮食结构需要明显调整"
    return (
        f"{level}，今日摄入约 {totals['calories']:.0f} kcal，"
        f"蛋白质 {totals['protein_g']:.1f} g，识别到 {risk_count} 项风险。"
    )


def build_risk_payloads(
    totals: dict[str, float],
    macro_balance: dict[str, float],
    targets: NutritionTargets,
    meals: list[Meal],
) -> list[dict[str, object]]:
    risks: list[dict[str, object]] = []
    calorie_surplus = totals["calories"] - targets.calories

    if calorie_surplus > max(300, targets.calories * 0.15):
        risks.append(
            {
                "risk_type": "calorie_excess",
                "severity": "high" if calorie_surplus > 600 else "medium",
                "title": "热量摄入高于目标",
                "description": f"今日热量比目标高约 {calorie_surplus:.0f} kcal。",
                "evidence": {
                    "total_calories": totals["calories"],
                    "target_calories": targets.calories,
                },
                "suggestion": (
                    "下一餐减少油炸和含糖饮品，增加蔬菜和优质蛋白；"
                    "可安排低门槛有氧活动。"
                ),
            }
        )

    if totals["calories"] < targets.calories * 0.7 and totals["calories"] > 0:
        risks.append(
            {
                "risk_type": "calorie_too_low",
                "severity": "medium",
                "title": "热量摄入偏低",
                "description": "今日摄入明显低于估算目标，可能影响学习状态和恢复。",
                "evidence": {
                    "total_calories": totals["calories"],
                    "target_calories": targets.calories,
                },
                "suggestion": "补充一份主食和优质蛋白，避免长期极低热量饮食。",
            }
        )

    if totals["protein_g"] < targets.protein_g * 0.8:
        risks.append(
            {
                "risk_type": "protein_low",
                "severity": "medium",
                "title": "蛋白质摄入不足",
                "description": f"今日蛋白质摄入 {totals['protein_g']:.1f} g，低于目标。",
                "evidence": {
                    "protein_g": totals["protein_g"],
                    "target_protein_g": targets.protein_g,
                },
                "suggestion": "优先补充鸡蛋、牛奶、鱼虾、瘦肉、豆腐或无糖酸奶。",
            }
        )

    if totals["fiber_g"] < targets.fiber_g * 0.7:
        risks.append(
            {
                "risk_type": "fiber_low",
                "severity": "low",
                "title": "膳食纤维偏低",
                "description": "蔬菜、全谷物、豆类或水果摄入可能不足。",
                "evidence": {"fiber_g": totals["fiber_g"], "target_fiber_g": targets.fiber_g},
                "suggestion": "下一餐加入一份深色蔬菜，可将精制主食替换为杂粮饭或燕麦。",
            }
        )

    if totals["sugar_g"] > targets.sugar_g:
        risks.append(
            {
                "risk_type": "sugar_high",
                "severity": "medium",
                "title": "糖摄入偏高",
                "description": "含糖饮品、甜点或奶茶可能推高了糖摄入。",
                "evidence": {"sugar_g": totals["sugar_g"], "target_sugar_g": targets.sugar_g},
                "suggestion": "饮品优先选择无糖茶、白水或无糖酸奶。",
            }
        )

    if totals["sodium_mg"] > targets.sodium_mg:
        risks.append(
            {
                "risk_type": "sodium_high",
                "severity": "medium",
                "title": "钠摄入偏高",
                "description": "外卖、重口味菜品或加工食品可能导致钠摄入偏高。",
                "evidence": {
                    "sodium_mg": totals["sodium_mg"],
                    "target_sodium_mg": targets.sodium_mg,
                },
                "suggestion": "减少汤汁、酱料和腌制食物，优先选择清蒸、炖煮或少油少盐菜品。",
            }
        )

    if macro_balance["fat_pct"] > 35:
        risks.append(
            {
                "risk_type": "fat_ratio_high",
                "severity": "medium",
                "title": "脂肪供能占比偏高",
                "description": "今日脂肪供能占比高于建议范围。",
                "evidence": {"fat_pct": macro_balance["fat_pct"]},
                "suggestion": "减少油炸和肥肉，优先选择清蒸鱼、鸡胸肉、虾仁或豆制品。",
            }
        )

    if not any(meal.meal_type in BREAKFAST_TYPES for meal in meals):
        risks.append(
            {
                "risk_type": "breakfast_missing",
                "severity": "low",
                "title": "早餐缺失",
                "description": "缺少早餐可能影响上午学习专注度。",
                "evidence": {"meal_types": [meal.meal_type for meal in meals]},
                "suggestion": "准备可携带早餐，如牛奶、鸡蛋、燕麦杯或全麦三明治。",
            }
        )

    if any(meal.meal_type in NIGHT_SNACK_TYPES for meal in meals):
        risks.append(
            {
                "risk_type": "night_snack_frequent",
                "severity": "low",
                "title": "存在夜宵记录",
                "description": "夜宵可能影响作息和第二天食欲。",
                "evidence": {
                    "night_snack_count": sum(
                        meal.meal_type in NIGHT_SNACK_TYPES for meal in meals
                    )
                },
                "suggestion": "如确实饥饿，选择牛奶、无糖酸奶或少量坚果，避免高油高糖夜宵。",
            }
        )

    if has_late_dinner(meals):
        risks.append(
            {
                "risk_type": "late_dinner",
                "severity": "low",
                "title": "晚餐时间偏晚",
                "description": "晚餐过晚可能影响睡眠和消化。",
                "evidence": {"late_after": "21:00"},
                "suggestion": "晚餐后安排 10-20 分钟轻松步行，当日避免高强度训练。",
            }
        )

    return risks


def generate_daily_analysis(db: Session, user_id: str, analysis_date: date) -> NutritionAnalysis:
    profile = db.scalar(select(HealthProfile).where(HealthProfile.user_id == user_id))
    goal = get_active_goal(db, user_id)
    meals = get_meals_for_date(db, user_id, analysis_date)
    targets = estimate_targets(profile, goal)
    totals = calculate_totals(meals)
    macro_balance = calculate_macro_balance(totals)
    risk_payloads = build_risk_payloads(totals, macro_balance, targets, meals)
    score = calculate_score(totals, macro_balance, targets, meals)
    evidence = {
        "target_calories": targets.calories,
        "target_protein_g": targets.protein_g,
        "meal_count": len(meals),
        "risk_count": len(risk_payloads),
    }

    existing = db.scalar(
        select(NutritionAnalysis).where(
            NutritionAnalysis.user_id == user_id,
            NutritionAnalysis.analysis_date == analysis_date,
            NutritionAnalysis.period_type == "daily",
        )
    )
    if existing is not None:
        db.execute(delete(RiskAlert).where(RiskAlert.analysis_id == existing.id))
        db.delete(existing)
        db.flush()

    analysis = NutritionAnalysis(
        user_id=user_id,
        goal_id=goal.id if goal else None,
        analysis_date=analysis_date,
        period_type="daily",
        score=score,
        totals=totals,
        macro_balance=macro_balance,
        evidence=evidence,
        summary=build_summary(score, len(risk_payloads), totals),
    )
    db.add(analysis)
    db.flush()

    for payload in risk_payloads:
        db.add(RiskAlert(user_id=user_id, analysis_id=analysis.id, **payload))

    db.commit()
    db.refresh(analysis)
    return analysis


def evaluate_risks_for_date(db: Session, user_id: str, analysis_date: date) -> list[RiskAlert]:
    analysis = generate_daily_analysis(db, user_id, analysis_date)
    return list(
        db.scalars(
            select(RiskAlert)
            .where(RiskAlert.user_id == user_id, RiskAlert.analysis_id == analysis.id)
            .order_by(RiskAlert.created_at.desc())
        )
    )


def resolve_risk(db: Session, risk: RiskAlert, status: str) -> RiskAlert:
    risk.status = status
    risk.resolved_at = datetime.now(UTC) if status == "resolved" else None
    db.commit()
    db.refresh(risk)
    return risk
