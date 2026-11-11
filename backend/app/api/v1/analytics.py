"""
ResQ Web - Analytics REST Endpoints
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.schemas.metrics import AnalyticsSummaryResponse
from backend.app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["Analytics & Performance"])


@router.get("/summary", response_model=AnalyticsSummaryResponse)
def get_analytics_summary(db: Session = Depends(get_db)):
    """Computes comprehensive reliability, uptime, and recovery metrics."""
    return AnalyticsService.get_summary(db)


@router.get("/recovery-timeline")
def get_recovery_timeline(db: Session = Depends(get_db)):
    """Returns recent recovery attempts for performance timeline visualizers."""
    return AnalyticsService.get_recovery_history_chart_data(db)

