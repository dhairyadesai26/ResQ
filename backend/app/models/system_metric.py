"""
ResQ Web - SystemMetric SQLAlchemy Model
Tracks system-wide resource utilization over time for performance evaluation.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, DateTime

from backend.app.database.base import Base


class SystemMetric(Base):
    __tablename__ = "system_metrics"

    id = Column(String(36), primary_key=True, index=True)
    cpu_percent = Column(Float, nullable=False)
    memory_used_bytes = Column(Integer, nullable=False)
    memory_total_bytes = Column(Integer, nullable=False)
    memory_percent = Column(Float, nullable=False)
    managed_process_count = Column(Integer, default=0, nullable=False)

    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

