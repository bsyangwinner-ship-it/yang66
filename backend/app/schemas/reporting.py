from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class ReportGenerateRequest(BaseModel):
    report_type: str = Field(pattern="^(weekly|monthly)$")
    period_start: date
    period_end: date
    run_async: bool = False
    export_format: str = Field(default="markdown", pattern="^(markdown)$")


class ReportRead(BaseModel):
    id: str
    user_id: str
    report_type: str
    period_start: date
    period_end: date
    title: str
    status: str
    summary: str
    metrics: dict[str, object]
    recommendations: list[dict[str, object]]
    export_format: str
    export_object_key: str | None
    export_content: str | None
    task_id: str | None
    generated_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReportGenerateResponse(BaseModel):
    report: ReportRead
    intervention_count: int
    task_enqueued: bool


class InterventionTaskRead(BaseModel):
    id: str
    user_id: str
    report_id: str | None
    risk_type: str
    title: str
    description: str
    task_type: str
    priority: str
    status: str
    scheduled_for: date
    due_date: date
    source: str
    evidence: dict[str, object]
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InterventionStatusUpdate(BaseModel):
    status: str = Field(pattern="^(open|in_progress|completed|skipped)$")


class InterventionScheduleRequest(BaseModel):
    report_id: str | None = None
    period_start: date | None = None
    period_end: date | None = None
