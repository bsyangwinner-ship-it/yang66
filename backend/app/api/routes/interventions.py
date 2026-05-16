from datetime import UTC, date, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.auth import User
from app.models.reporting import InterventionTask, Report
from app.schemas.reporting import (
    InterventionScheduleRequest,
    InterventionStatusUpdate,
    InterventionTaskRead,
)
from app.services.reporting import create_interventions_from_report, update_intervention_status

router = APIRouter(prefix="/interventions", tags=["interventions"])


def get_owned_task(db: Session, user_id: str, task_id: str) -> InterventionTask:
    task = db.get(InterventionTask, task_id)
    if task is None or task.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Intervention task not found",
        )
    return task


def get_owned_report(db: Session, user_id: str, report_id: str) -> Report:
    report = db.get(Report, report_id)
    if report is None or report.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    return report


@router.get("", response_model=list[InterventionTaskRead])
def list_interventions(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    task_status: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[InterventionTask]:
    statement = (
        select(InterventionTask)
        .where(InterventionTask.user_id == current_user.id)
        .order_by(InterventionTask.scheduled_for, InterventionTask.created_at.desc())
    )
    if task_status is not None:
        statement = statement.where(InterventionTask.status == task_status)
    if start_date is not None:
        statement = statement.where(InterventionTask.scheduled_for >= start_date)
    if end_date is not None:
        statement = statement.where(InterventionTask.scheduled_for <= end_date)
    return list(db.scalars(statement))


@router.post("/schedule", response_model=list[InterventionTaskRead])
def schedule_interventions(
    payload: InterventionScheduleRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[InterventionTask]:
    report: Report | None = None
    if payload.report_id is not None:
        report = get_owned_report(db, current_user.id, payload.report_id)
    else:
        report = db.scalar(
            select(Report)
            .where(Report.user_id == current_user.id, Report.status == "completed")
            .order_by(Report.generated_at.desc())
        )

    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No completed report available for intervention scheduling",
        )

    create_interventions_from_report(db, report)
    return list(
        db.scalars(
            select(InterventionTask)
            .where(
                InterventionTask.user_id == current_user.id,
                InterventionTask.report_id == report.id,
            )
            .order_by(InterventionTask.scheduled_for)
        )
    )


@router.patch("/{task_id}/status", response_model=InterventionTaskRead)
def patch_intervention_status(
    task_id: str,
    payload: InterventionStatusUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> InterventionTask:
    task = get_owned_task(db, current_user.id, task_id)
    if payload.status == "completed":
        task.completed_at = datetime.now(UTC)
    return update_intervention_status(db, task, payload.status)
