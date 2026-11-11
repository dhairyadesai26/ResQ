"""
ResQ Web - System Metrics REST Endpoints
"""

from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.schemas.metrics import SystemMetricResponse
from backend.app.models.system_metric import SystemMetric
from agent.process_manager.inspector import ProcessInspector
from agent.monitoring.monitor_engine import monitor_engine

router = APIRouter(prefix="/metrics", tags=["System Metrics"])


@router.get("/current")
def get_current_system_metrics():
    """Retrieves instantaneous system CPU and physical RAM statistics."""
    stats = ProcessInspector.get_system_metrics()
    apps = monitor_engine.list_applications()
    running_count = sum(1 for a in apps if a.get("state") == "RUNNING")

    return {
        **stats,
        "managed_process_count": running_count,
        "total_applications": len(apps),
    }


@router.get("/history", response_model=List[SystemMetricResponse])
def get_metrics_history(
    limit: int = Query(30, ge=5, le=300),
    db: Session = Depends(get_db),
):
    """Retrieves time-series metric records for analytical charts."""
    metrics = (
        db.query(SystemMetric)
        .order_by(SystemMetric.timestamp.desc())
        .limit(limit)
        .all()
    )
    return list(reversed(metrics))

