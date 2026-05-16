from fastapi import APIRouter, Response

from app.core.config import settings
from app.core.observability import http_metrics

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": settings.app_version,
    }


@router.get("/ready")
def readiness_check() -> dict[str, str]:
    return {"status": "ready"}


@router.get("/metrics", include_in_schema=False)
def metrics() -> Response:
    if not settings.prometheus_enabled:
        return Response(status_code=404)
    return Response(
        content=http_metrics.render_prometheus(),
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )
