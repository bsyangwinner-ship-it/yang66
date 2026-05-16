from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.auth import User
from app.models.reporting import Report
from app.schemas.reporting import ReportGenerateRequest, ReportGenerateResponse, ReportRead
from app.services.reporting import (
    build_report_payload,
    create_report_record,
    generate_report_by_id,
)
from app.tasks.report_tasks import generate_report_task

router = APIRouter(prefix="/reports", tags=["reports"])


def get_owned_report(db: Session, user_id: str, report_id: str) -> Report:
    report = db.get(Report, report_id)
    if report is None or report.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    return report


@router.get("", response_model=list[ReportRead])
def list_reports(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    report_type: str | None = None,
    report_status: str | None = None,
) -> list[Report]:
    statement = (
        select(Report)
        .where(Report.user_id == current_user.id)
        .order_by(Report.created_at.desc())
    )
    if report_type is not None:
        statement = statement.where(Report.report_type == report_type)
    if report_status is not None:
        statement = statement.where(Report.status == report_status)
    return list(db.scalars(statement))


@router.post(
    "/generate",
    response_model=ReportGenerateResponse,
    status_code=status.HTTP_201_CREATED,
)
def generate_report(
    payload: ReportGenerateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, object]:
    try:
        report = create_report_record(db, current_user.id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    if payload.run_async:
        try:
            async_result = generate_report_task.delay(report.id)
            report.task_id = async_result.id
            db.commit()
            db.refresh(report)
            return build_report_payload(report, intervention_count=0, task_enqueued=True)
        except Exception:
            report.status = "running"
            db.commit()

    try:
        generated_report, intervention_count = generate_report_by_id(db, report.id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return build_report_payload(
        generated_report,
        intervention_count=intervention_count,
        task_enqueued=False,
    )


@router.get("/{report_id}", response_model=ReportRead)
def get_report(
    report_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> Report:
    return get_owned_report(db, current_user.id, report_id)
