from fastapi import APIRouter

from app.api.routes import (
    agent,
    analysis,
    auth,
    goals,
    health,
    interventions,
    knowledge,
    meals,
    profile,
    reports,
    risks,
)
from app.core.config import settings

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(agent.router, prefix=settings.api_v1_prefix)
api_router.include_router(auth.router, prefix=settings.api_v1_prefix)
api_router.include_router(profile.router, prefix=settings.api_v1_prefix)
api_router.include_router(goals.router, prefix=settings.api_v1_prefix)
api_router.include_router(meals.router, prefix=settings.api_v1_prefix)
api_router.include_router(analysis.router, prefix=settings.api_v1_prefix)
api_router.include_router(risks.router, prefix=settings.api_v1_prefix)
api_router.include_router(knowledge.router, prefix=settings.api_v1_prefix)
api_router.include_router(reports.router, prefix=settings.api_v1_prefix)
api_router.include_router(interventions.router, prefix=settings.api_v1_prefix)
