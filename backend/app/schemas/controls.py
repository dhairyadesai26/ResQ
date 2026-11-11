"""
ResQ Web - Controls & Process Schemas
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel


class ProcessControlResponse(BaseModel):
    success: bool
    message: str
    app_id: str
    status: str
    pid: Optional[int] = None


class ProcessStateDetail(BaseModel):
    app_id: str
    name: str
    status: str
    pid: Optional[int] = None
    uptime_seconds: float = 0.0
    cpu_percent: float = 0.0
    memory_rss_bytes: int = 0
    memory_percent: float = 0.0
    num_threads: int = 0
    num_handles: int = 0
    consecutive_retries: int = 0
    max_retries: int = 3
    total_recoveries: int = 0
    last_exit_code: Optional[int] = None

