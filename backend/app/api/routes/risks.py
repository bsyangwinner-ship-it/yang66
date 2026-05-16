from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.auth import User
from app.models.business import RiskAlert
from app.schemas.business import RiskAlertRead, RiskEvaluateRequest, RiskStatusUpdate
from app.services.nutrition import evaluate_risks_for_date, resolve_risk

router = APIRouter(prefix="/risks", tags=["risks"])


def get_owned_risk(db: Session, user_id: str, risk_id: str) -> RiskAlert:
    risk = db.get(RiskAlert, risk_id)
    if risk is None or risk.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Risk not found")
    return risk


@router.get("", response_model=list[RiskAlertRead])
def list_risks(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    risk_status: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[RiskAlert]:
    query = (
        select(RiskAlert)
        .where(RiskAlert.user_id == current_user.id)
        .order_by(RiskAlert.created_at.desc())
    )
    if risk_status is not None:
        query = query.where(RiskAlert.status == risk_status)
    if start_date is not None:
        query = query.where(RiskAlert.created_at >= start_date)
    if end_date is not None:
        query = query.where(RiskAlert.created_at <= end_date)
    return list(db.scalars(query))


@router.post("/evaluate", response_model=list[RiskAlertRead])
def evaluate_risks(
    payload: RiskEvaluateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[RiskAlert]:
    return evaluate_risks_for_date(db, current_user.id, payload.analysis_date)


@router.patch("/{risk_id}/status", response_model=RiskAlertRead)
def update_risk_status(
    risk_id: str,
    payload: RiskStatusUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> RiskAlert:
    risk = get_owned_risk(db, current_user.id, risk_id)
    return resolve_risk(db, risk, payload.status)
