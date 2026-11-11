"""
ResQ Web - Windows Job Object Wrapper
Demonstrates Windows Job Objects for process hierarchy control:
- Prevents rogue/orphaned descendant processes
- Guarantees complete cleanup of child trees upon termination
- Tracks process tree membership
"""

from typing import Optional
import logging
from backend.agent.process_manager.win32_api import (
    create_job_object_with_kill_on_close,
    assign_process_to_job_native,
    close_process_handle,
    IS_WINDOWS,
)

logger = logging.getLogger("resq.agent.job_object")


class JobObject:
    """Manages a Windows Job Object for a monitored process."""

    def __init__(self, name: Optional[str] = None):
        self.name = name
        self._handle = None
        if IS_WINDOWS:
            self._handle = create_job_object_with_kill_on_close(name)

    @property
    def is_valid(self) -> bool:
        return self._handle is not None and self._handle > 0

    def assign_process(self, process_handle: int) -> bool:
        """Assigns a Windows process handle to this job object."""
        if not self.is_valid or not process_handle:
            return False
        return assign_process_to_job_native(self._handle, process_handle)

    def close(self):
        """Closes the job object handle."""
        if self._handle:
            close_process_handle(self._handle)
            self._handle = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __del__(self):
        self.close()

