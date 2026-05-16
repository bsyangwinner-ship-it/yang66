from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.auth import User
from app.models.business import NutritionAnalysis
from app.schemas.business import AnalysisGenerateRequest, NutritionAnalysisRead
from app.services.nutrition import generate_daily_analysis

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.post("/daily", response_model=NutritionAnalysisRead)
def generate_daily(
    payload: AnalysisGenerateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> NutritionAnalysis:
    return generate_daily_analysis(db, current_user.id, payload.analysis_date)


@router.get("/daily", response_model=list[NutritionAnalysisRead])
def list_daily(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[NutritionAnalysis]:
    query = (
        select(NutritionAnalysis)
        .where(
            NutritionAnalysis.user_id == current_user.id,
            NutritionAnalysis.period_type == "daily",
        )
        .order_by(NutritionAnalysis.analysis_date.desc())
    )
    if start_date is not None:
        query = query.where(NutritionAnalysis.analysis_date >= start_date)
    if end_date is not None:
        query = query.where(NutritionAnalysis.analysis_date <= end_date)
    return list(db.scalars(query))


@router.get("/summary", response_model=dict[str, object])
def get_summary(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    start_date: date | None = None,
    end_date: date | None = None,
) -> dict[str, object]:
    analyses = list_daily(current_user, db, start_date, end_date)
    if not analyses:
        return {"count": 0, "average_score": 0, "average_calories": 0}
    return {
        "count": len(analyses),
        "average_score": round(sum(item.score for item in analyses) / len(analyses), 1),
        "average_calories": round(
            sum(item.totals.get("calories", 0) for item in analyses) / len(analyses),
            1,
        ),
    }
