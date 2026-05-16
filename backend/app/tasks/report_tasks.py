from app.db.session import SessionLocal
from app.services.reporting import generate_report_by_id
from app.tasks.celery_app import celery_app


@celery_app.task(name="reports.generate")  # type: ignore[untyped-decorator]
def generate_report_task(report_id: str) -> dict[str, object]:
    db = SessionLocal()
    try:
        report, intervention_count = generate_report_by_id(db, report_id)
        return {
            "report_id": report.id,
            "status": report.status,
            "intervention_count": intervention_count,
            "export_object_key": report.export_object_key,
        }
    finally:
        db.close()
