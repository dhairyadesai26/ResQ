"""
ResQ Web - RecoveryAttempt SQLAlchemy Model
Records details of individual automatic process recovery attempts.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from backend.app.database.base import Base


class RecoveryAttempt(Base):
    __tablename__ = "recovery_attempts"

    id = Column(String(36), primary_key=True, index=True)
    app_id = Column(String(36), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)

    attempt_number = Column(Integer, nullable=False)
    backoff_delay_seconds = Column(Float, nullable=False)
    status = Column(String(20), nullable=False)  # SCHEDULED, STARTED, SUCCEEDED, FAILED
    error_message = Column(String(500), nullable=True)
    new_pid = Column(Integer, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    application = relationship("Application", back_populates="recovery_attempts")

