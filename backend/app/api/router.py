"""
ResQ Web - API V1 Router Aggregation
"""

from fastapi import APIRouter

from backend.app.api.v1.applications import router as applications_router
from backend.app.api.v1.controls import router as controls_router
from backend.app.api.v1.events import router as events_router
from backend.app.api.v1.recovery import router as recovery_router
from backend.app.api.v1.metrics import router as metrics_router
from backend.app.api.v1.analytics import router as analytics_router
from backend.app.api.v1.system import router as system_router

api_router = APIRouter()

api_router.include_router(applications_router)
api_router.include_router(controls_router)
api_router.include_router(events_router)
api_router.include_router(recovery_router)
api_router.include_router(metrics_router)
api_router.include_router(analytics_router)
api_router.include_router(system_router)

