"""
ResQ Web - Recovery Policy Pydantic Schemas
"""

from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field, field_serializer


class RecoveryPolicyUpdate(BaseModel):
    auto_recovery: bool = Field(..., description="Enable automatic recovery")
    max_retries: int = Field(default=3, ge=0, le=50)
    retry_delay_seconds: float = Field(default=1.0, ge=0.1, le=300.0)
    backoff_multiplier: float = Field(default=2.0, ge=1.0, le=10.0)
    max_delay_seconds: float = Field(default=30.0, ge=1.0, le=600.0)


class RecoveryAttemptResponse(BaseModel):
    id: str
    app_id: str
    attempt_number: int
    backoff_delay_seconds: float
    status: str
    error_message: Optional[str] = None
    new_pid: Optional[int] = None
    created_at: datetime

    @field_serializer("created_at")
    def serialize_created_at(self, dt: datetime, _info) -> str:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()

    class Config:
        from_attributes = True
