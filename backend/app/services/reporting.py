from collections import Counter
from datetime import UTC, date, datetime, timedelta
from statistics import mean
from typing import Any, cast

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.business import Meal, NutritionAnalysis, RiskAlert
from app.models.reporting import InterventionTask, Report
from app.schemas.reporting import ReportGenerateRequest
from app.services.nutrition import generate_daily_analysis

RECOMMENDATION_LIBRARY: dict[str, dict[str, str]] = {
    "sugar_high": {
        "title": "降低含糖饮品频次",
        "action": "未来 7 天把奶茶、甜饮替换为无糖茶、白水或无糖酸奶。",
        "task_type": "diet_adjustment",
        "priority": "high",
    },
    "protein_low": {
        "title": "提高蛋白质达标率",
        "action": "每天至少安排 2 餐包含鸡蛋、鱼虾、瘦肉、豆制品或牛奶。",
        "task_type": "nutrition_target",
        "priority": "medium",
    },
    "fiber_low": {
        "title": "增加膳食纤维",
        "action": "每日至少 2 份蔬菜，并把一部分精制主食替换为杂粮或燕麦。",
        "task_type": "nutrition_target",
        "priority": "medium",
    },
    "calorie_excess": {
        "title": "控制热量波动",
        "action": "高热量日后的下一餐优先选择少油蛋白、蔬菜和半份主食。",
        "task_type": "calorie_control",
        "priority": "high",
    },
    "late_dinner": {
        "title": "提前晚餐时间",
        "action": "尽量把晚餐安排在 21:00 前，晚餐后选择 10-20 分钟轻松步行。",
        "task_type": "routine",
        "priority": "low",
    },
    "night_snack_frequent": {
        "title": "减少夜宵干扰",
        "action": "夜间饥饿时选择牛奶或无糖酸奶，避免高油高糖夜宵。",
        "task_type": "routine",
        "priority": "low",
    },
}


def _date_range(start: date, end: date) -> list[date]:
    days = (end - start).days
    return [start + timedelta(days=offset) for offset in range(days + 1)]


def _validate_period(period_start: date, period_end: date) -> None:
    if period_end < period_start:
        raise ValueError("period_end must be greater than or equal to period_start")
    if (period_end - period_start).days > 45:
        raise ValueError("report period cannot exceed 45 days")


def _ensure_period_analyses(
    db: Session,
    user_id: str,
    period_start: date,
    period_end: date,
) -> list[NutritionAnalysis]:
    meal_dates = set(
        db.scalars(
            select(Meal.meal_date)
            .where(
                Meal.user_id == user_id,
                Meal.meal_date >= period_start,
                Meal.meal_date <= period_end,
            )
            .distinct()
        )
    )
    existing_dates = set(
        db.scalars(
            select(NutritionAnalysis.analysis_date).where(
                NutritionAnalysis.user_id == user_id,
                NutritionAnalysis.analysis_date >= period_start,
                NutritionAnalysis.analysis_date <= period_end,
                NutritionAnalysis.period_type == "daily",
            )
        )
    )
    for analysis_date in sorted(meal_dates - existing_dates):
        generate_daily_analysis(db, user_id, analysis_date)

    return list(
        db.scalars(
            select(NutritionAnalysis)
            .where(
                NutritionAnalysis.user_id == user_id,
                NutritionAnalysis.analysis_date >= period_start,
                NutritionAnalysis.analysis_date <= period_end,
                NutritionAnalysis.period_type == "daily",
            )
            .order_by(NutritionAnalysis.analysis_date)
        )
    )


def _risk_items(db: Session, user_id: str, analyses: list[NutritionAnalysis]) -> list[RiskAlert]:
    analysis_ids = [analysis.id for analysis in analyses]
    if not analysis_ids:
        return []
    return list(
        db.scalars(
            select(RiskAlert)
            .where(
                RiskAlert.user_id == user_id,
                RiskAlert.analysis_id.in_(analysis_ids),
            )
            .order_by(RiskAlert.created_at.desc())
        )
    )


def _build_metrics(analyses: list[NutritionAnalysis], risks: list[RiskAlert]) -> dict[str, object]:
    if not analyses:
        return {
            "analysis_count": 0,
            "average_score": 0,
            "average_calories": 0,
            "average_protein_g": 0,
            "score_delta": 0,
            "risk_count": len(risks),
            "open_risk_count": sum(risk.status == "open" for risk in risks),
            "top_risk_types": [],
        }

    scores = [analysis.score for analysis in analyses]
    calories = [float(analysis.totals.get("calories", 0)) for analysis in analyses]
    protein = [float(analysis.totals.get("protein_g", 0)) for analysis in analyses]
    risk_counter = Counter(risk.risk_type for risk in risks)
    top_risk_types = [
        {"risk_type": risk_type, "count": count}
        for risk_type, count in risk_counter.most_common(5)
    ]
    return {
        "analysis_count": len(analyses),
        "average_score": round(mean(scores), 1),
        "average_calories": round(mean(calories), 1),
        "average_protein_g": round(mean(protein), 1),
        "score_delta": scores[-1] - scores[0],
        "risk_count": len(risks),
        "open_risk_count": sum(risk.status == "open" for risk in risks),
        "top_risk_types": top_risk_types,
    }


def _build_recommendations(metrics: dict[str, object]) -> list[dict[str, object]]:
    top_risk_types = metrics.get("top_risk_types", [])
    recommendations: list[dict[str, object]] = []
    for item in top_risk_types if isinstance(top_risk_types, list) else []:
        if not isinstance(item, dict):
            continue
        risk_type = str(item.get("risk_type", ""))
        template = RECOMMENDATION_LIBRARY.get(risk_type)
        if template is None:
            continue
        recommendations.append(
            {
                "risk_type": risk_type,
                "title": template["title"],
                "action": template["action"],
                "priority": template["priority"],
                "evidence": {"count": item.get("count", 0)},
            }
        )

    if not recommendations:
        recommendations.append(
            {
                "risk_type": "baseline",
                "title": "保持稳定记录",
                "action": "继续记录三餐、饮品和运动反馈，优先观察热量、蛋白质和作息趋势。",
                "priority": "medium",
                "evidence": {"analysis_count": metrics.get("analysis_count", 0)},
            }
        )
    return recommendations[:5]


def _metric_float(metrics: dict[str, object], key: str) -> float:
    value = metrics.get(key, 0)
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return 0.0
    return 0.0


def _metric_int(metrics: dict[str, object], key: str) -> int:
    return int(_metric_float(metrics, key))


def _build_summary(metrics: dict[str, object]) -> str:
    if _metric_int(metrics, "analysis_count") == 0:
        return "本周期暂无可分析饮食记录，建议先连续记录 3 天三餐、饮品和夜宵情况。"

    average_score = metrics.get("average_score", 0)
    score_delta = _metric_float(metrics, "score_delta")
    open_risk_count = metrics.get("open_risk_count", 0)
    if score_delta > 0:
        trend = "改善"
    elif score_delta < 0:
        trend = "波动或下降"
    else:
        trend = "基本稳定"
    return (
        f"本周期平均饮食评分为 {average_score} 分，较周期起点趋势为{trend}。"
        f"当前仍有 {open_risk_count} 项开放风险，需要通过饮食选择和作息安排持续干预。"
    )


def _build_export_content(report: Report) -> str:
    recommendations = "\n".join(
        f"- {item.get('title')}: {item.get('action')}" for item in report.recommendations
    )
    return (
        f"# {report.title}\n\n"
        f"周期：{report.period_start.isoformat()} 至 {report.period_end.isoformat()}\n\n"
        f"## 总结\n\n{report.summary}\n\n"
        f"## 核心指标\n\n"
        f"- 平均评分：{report.metrics.get('average_score', 0)}\n"
        f"- 平均热量：{report.metrics.get('average_calories', 0)} kcal\n"
        f"- 平均蛋白质：{report.metrics.get('average_protein_g', 0)} g\n"
        f"- 开放风险：{report.metrics.get('open_risk_count', 0)}\n\n"
        f"## 干预建议\n\n{recommendations}\n\n"
        "健康建议仅作辅助参考，不替代医生或注册营养师建议。\n"
    )


def _export_object_key(report: Report) -> str:
    suffix = "md" if report.export_format == "markdown" else report.export_format
    return (
        f"{settings.report_export_prefix}/{report.user_id}/"
        f"{report.period_start.isoformat()}_{report.period_end.isoformat()}_{report.id}.{suffix}"
    )


def create_report_record(
    db: Session,
    user_id: str,
    payload: ReportGenerateRequest,
) -> Report:
    _validate_period(payload.period_start, payload.period_end)
    title = (
        "周度饮食健康报告"
        if payload.report_type == "weekly"
        else "月度饮食健康报告"
    )
    report = Report(
        user_id=user_id,
        report_type=payload.report_type,
        period_start=payload.period_start,
        period_end=payload.period_end,
        title=title,
        status="queued",
        export_format=payload.export_format,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


def generate_report_by_id(db: Session, report_id: str) -> tuple[Report, int]:
    report = db.get(Report, report_id)
    if report is None:
        raise ValueError("report not found")

    report.status = "running"
    db.commit()
    try:
        analyses = _ensure_period_analyses(
            db,
            report.user_id,
            report.period_start,
            report.period_end,
        )
        risks = _risk_items(db, report.user_id, analyses)
        metrics = _build_metrics(analyses, risks)
        report.metrics = metrics
        report.recommendations = _build_recommendations(metrics)
        report.summary = _build_summary(metrics)
        report.export_content = _build_export_content(report)
        report.export_object_key = _export_object_key(report)
        report.status = "completed"
        report.generated_at = datetime.now(UTC)
        db.commit()
        intervention_count = create_interventions_from_report(db, report)
    except Exception:
        report.status = "failed"
        db.commit()
        raise

    db.refresh(report)
    return report, intervention_count


def create_interventions_from_report(db: Session, report: Report) -> int:
    existing_count = db.scalar(
        select(InterventionTask).where(InterventionTask.report_id == report.id).limit(1)
    )
    if existing_count is not None:
        return 0

    start = date.today()
    count = 0
    for offset, item in enumerate(report.recommendations):
        risk_type = str(item.get("risk_type", "baseline"))
        title = str(item.get("title", "健康干预任务"))
        action = str(item.get("action", "继续记录饮食并观察趋势。"))
        priority = str(item.get("priority", "medium"))
        template = RECOMMENDATION_LIBRARY.get(risk_type, {})
        evidence_value = item.get("evidence", {})
        evidence_payload = cast(
            dict[str, object],
            evidence_value if isinstance(evidence_value, dict) else {},
        )
        task = InterventionTask(
            user_id=report.user_id,
            report_id=report.id,
            risk_type=risk_type,
            title=title,
            description=action,
            task_type=template.get("task_type", "follow_up"),
            priority=priority,
            scheduled_for=start + timedelta(days=offset),
            due_date=start + timedelta(days=offset + 6),
            source="report",
            evidence={
                "report_id": report.id,
                "period_start": report.period_start.isoformat(),
                "period_end": report.period_end.isoformat(),
                **evidence_payload,
            },
        )
        db.add(task)
        count += 1
    db.commit()
    return count


def update_intervention_status(
    db: Session,
    task: InterventionTask,
    status: str,
) -> InterventionTask:
    task.status = status
    task.completed_at = datetime.now(UTC) if status == "completed" else None
    db.commit()
    db.refresh(task)
    return task


def build_report_payload(
    report: Report,
    intervention_count: int,
    task_enqueued: bool,
) -> dict[str, Any]:
    return {
        "report": report,
        "intervention_count": intervention_count,
        "task_enqueued": task_enqueued,
    }
