"""
ResQ Web - ProcessRun SQLAlchemy Model
Tracks the historical execution record of individual process instances.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from backend.app.database.base import Base


class ProcessRun(Base):
    __tablename__ = "process_runs"

    id = Column(String(36), primary_key=True, index=True)
    app_id = Column(String(36), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)
    pid = Column(Integer, nullable=False)

    start_time = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    end_time = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, nullable=True)

    exit_code = Column(Integer, nullable=True)
    termination_type = Column(String(20), default="ACTIVE", nullable=False)  # ACTIVE, EXPECTED, UNEXPECTED

    application = relationship("Application", back_populates="process_runs")

