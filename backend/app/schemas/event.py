"""
ResQ Web - Event Pydantic Schemas
"""

from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, field_serializer


class EventResponse(BaseModel):
    id: str
    app_id: Optional[str] = None
    app_name: Optional[str] = None
    event_type: str
    severity: str
    message: str
    pid: Optional[int] = None
    exit_code: Optional[int] = None
    details: Optional[str] = None
    timestamp: datetime

    @field_serializer("timestamp")
    def serialize_timestamp(self, dt: datetime, _info) -> str:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()

    class Config:
        from_attributes = True


class EventFilterQuery(BaseModel):
    app_id: Optional[str] = None
    event_type: Optional[str] = None
    severity: Optional[str] = None
    search: Optional[str] = None
    limit: int = 50
    offset: int = 0
