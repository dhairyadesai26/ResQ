"""
ResQ Web - Application Pydantic Schemas
"""

from datetime import datetime, timezone
from typing import Optional, List
from pydantic import BaseModel, Field, field_serializer


class ApplicationBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Display name of the application")
    executable_path: str = Field(..., min_length=1, max_length=500, description="Absolute or relative path to executable")
    arguments: Optional[str] = Field(default="", description="Command-line arguments string")
    working_dir: Optional[str] = Field(default=None, description="Working directory for process execution")

    # Recovery policy
    auto_recovery: bool = Field(default=True, description="Enable automatic process recovery")
    max_retries: int = Field(default=3, ge=0, le=50, description="Maximum consecutive recovery retries")
    retry_delay_seconds: float = Field(default=1.0, ge=0.1, le=300.0, description="Initial delay in seconds before restart")
    backoff_multiplier: float = Field(default=2.0, ge=1.0, le=10.0, description="Multiplier applied to retry delay")
    max_delay_seconds: float = Field(default=30.0, ge=1.0, le=600.0, description="Maximum ceiling for recovery delay")


class ApplicationCreate(ApplicationBase):
    pass


class ApplicationUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    executable_path: Optional[str] = Field(default=None, min_length=1, max_length=500)
    arguments: Optional[str] = None
    working_dir: Optional[str] = None
    auto_recovery: Optional[bool] = None
    max_retries: Optional[int] = Field(default=None, ge=0, le=50)
    retry_delay_seconds: Optional[float] = Field(default=None, ge=0.1, le=300.0)
    backoff_multiplier: Optional[float] = Field(default=None, ge=1.0, le=10.0)
    max_delay_seconds: Optional[float] = Field(default=None, ge=1.0, le=600.0)


class ApplicationResponse(ApplicationBase):
    id: str
    status: str
    current_pid: Optional[int] = None
    uptime_seconds: float = 0.0
    cpu_percent: float = 0.0
    memory_rss_bytes: int = 0
    memory_percent: float = 0.0
    num_threads: int = 0
    num_handles: int = 0
    consecutive_retries: int = 0
    total_recoveries: int = 0
    last_exit_code: Optional[int] = None
    last_crash_timestamp: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    @field_serializer("created_at", "updated_at", "last_crash_timestamp")
    def serialize_datetimes(self, dt: Optional[datetime], _info) -> Optional[str]:
        if dt is None:
            return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()

    class Config:
        from_attributes = True

