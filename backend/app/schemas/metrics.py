"""
ResQ Web - Metrics & Analytics Schemas
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class SystemMetricResponse(BaseModel):
    cpu_percent: float
    memory_used_bytes: int
    memory_total_bytes: int
    memory_percent: float
    managed_process_count: int
    timestamp: datetime

    class Config:
        from_attributes = True


class AnalyticsSummaryResponse(BaseModel):
    total_applications: int
    running_applications: int
    stopped_applications: int
    recovering_applications: int
    failed_applications: int
    total_recovery_attempts: int
    successful_recoveries: int
    failed_recoveries: int
    recovery_success_rate: float
    average_recovery_latency_seconds: float
    average_crash_detection_latency_seconds: float
    system_cpu_percent: float
    system_memory_percent: float
    system_memory_used_mb: float
    system_memory_total_mb: float

