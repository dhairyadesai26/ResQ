"""
ResQ Web - Event Service
Persists supervisor events to SQLite and dispatches real-time WebSocket alerts.
"""

import json
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.app.database.session import SessionLocal
from backend.app.models.event import Event
from backend.app.schemas.event import EventResponse, EventFilterQuery
from backend.app.websocket.connection_manager import ws_manager
from agent.communication.event_emitter import SupervisorEvent, event_bus


class EventService:
    """Handles event persistence and queries."""

    @classmethod
    def record_event_from_supervisor(cls, supervisor_event: SupervisorEvent):
        """Callback listener connected directly to the supervisor event bus."""
        db: Session = SessionLocal()
        try:
            details_str = json.dumps(supervisor_event.details) if supervisor_event.details else None
            db_event = Event(
                id=supervisor_event.event_id,
                app_id=supervisor_event.app_id,
                app_name=supervisor_event.app_name,
                event_type=supervisor_event.event_type,
                severity=supervisor_event.severity,
                message=supervisor_event.message,
                pid=supervisor_event.pid,
                exit_code=supervisor_event.exit_code,
                details=details_str,
                timestamp=datetime.fromtimestamp(supervisor_event.timestamp, timezone.utc),
            )
            db.add(db_event)
            db.commit()

            # Push to WebSocket
            ws_manager.broadcast_threadsafe({
                "type": "event",
                "data": {
                    "id": db_event.id,
                    "app_id": db_event.app_id,
                    "app_name": db_event.app_name,
                    "event_type": db_event.event_type,
                    "severity": db_event.severity,
                    "message": db_event.message,
                    "pid": db_event.pid,
                    "exit_code": db_event.exit_code,
                    "details": details_str,
                    "timestamp": db_event.timestamp.isoformat(),
                }
            })
        except Exception as e:
            db.rollback()
        finally:
            db.close()

    @classmethod
    def get_events(
        cls,
        db: Session,
        filters: EventFilterQuery,
    ) -> Tuple[List[Event], int]:
        """Queries stored events with optional filtering and pagination."""
        query = db.query(Event)

        if filters.app_id:
            query = query.filter(Event.app_id == filters.app_id)
        if filters.event_type:
            query = query.filter(Event.event_type == filters.event_type)
        if filters.severity:
            query = query.filter(Event.severity == filters.severity)
        if filters.search:
            pattern = f"%{filters.search}%"
            query = query.filter(
                (Event.message.ilike(pattern)) | (Event.app_name.ilike(pattern))
            )

        total = query.count()
        events = query.order_by(desc(Event.timestamp)).offset(filters.offset).limit(filters.limit).all()
        return events, total


# Auto-subscribe event recorder to the supervisor bus
event_bus.subscribe(EventService.record_event_from_supervisor)

