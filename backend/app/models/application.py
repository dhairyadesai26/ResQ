"""
ResQ Web - Application SQLAlchemy Model
"""

from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, Integer, Float, DateTime
from sqlalchemy.orm import relationship

from backend.app.database.base import Base


class Application(Base):
    __tablename__ = "applications"

    id = Column(String(36), primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    executable_path = Column(String(500), nullable=False)
    arguments = Column(String(1000), nullable=True, default="")
    working_dir = Column(String(500), nullable=True)

    # Recovery policy configuration
    auto_recovery = Column(Boolean, default=True, nullable=False)
    max_retries = Column(Integer, default=3, nullable=False)
    retry_delay_seconds = Column(Float, default=1.0, nullable=False)
    backoff_multiplier = Column(Float, default=2.0, nullable=False)
    max_delay_seconds = Column(Float, default=30.0, nullable=False)

    # Runtime state snapshot
    status = Column(String(20), default="STOPPED", nullable=False)
    current_pid = Column(Integer, nullable=True)
    consecutive_retries = Column(Integer, default=0, nullable=False)
    total_recoveries = Column(Integer, default=0, nullable=False)
    last_exit_code = Column(Integer, nullable=True)
    last_crash_timestamp = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    process_runs = relationship("ProcessRun", back_populates="application", cascade="all, delete-orphan")
    recovery_attempts = relationship("RecoveryAttempt", back_populates="application", cascade="all, delete-orphan")

