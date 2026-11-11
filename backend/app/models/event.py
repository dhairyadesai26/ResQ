"""
ResQ Web - Event SQLAlchemy Model
Audit log of all process supervisor events, lifecycle transitions, crashes, and recoveries.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, Text

from backend.app.database.base import Base


class Event(Base):
    __tablename__ = "events"

    id = Column(String(36), primary_key=True, index=True)
    app_id = Column(String(36), nullable=True, index=True)
    app_name = Column(String(100), nullable=True, index=True)

    event_type = Column(String(50), nullable=False, index=True)
    severity = Column(String(20), default="INFO", nullable=False, index=True)  # INFO, WARNING, ERROR, CRITICAL
    message = Column(Text, nullable=False)

    pid = Column(Integer, nullable=True)
    exit_code = Column(Integer, nullable=True)
    details = Column(Text, nullable=True)  # JSON payload string

    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

