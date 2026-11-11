"""
ResQ Web - Event History REST Endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.schemas.event import EventResponse, EventFilterQuery
from backend.app.services.event_service import EventService

router = APIRouter(prefix="/events", tags=["Event History"])


@router.get("", response_model=List[EventResponse])
def get_events(
    app_id: Optional[str] = None,
    event_type: Optional[str] = None,
    severity: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """Queries audit log events with filtering, search, and pagination."""
    filters = EventFilterQuery(
        app_id=app_id,
        event_type=event_type,
        severity=severity,
        search=search,
        limit=limit,
        offset=offset,
    )
    events, total = EventService.get_events(db, filters)
    return events
