"""
ResQ Web - RAII Process Handle Wrapper
Provides safe lifetime management for native Windows process handles.
Prevents handle leaks and ensures proper kernel resource release.
"""

from typing import Optional
from agent.process_manager.win32_api import (
    open_process_handle,
    close_process_handle,
    wait_for_process_handle,
    get_process_exit_code_native,
    terminate_process_native,
    IS_WINDOWS,
)


class ProcessHandle:
    """Encapsulates a native Windows Process Handle."""

    def __init__(self, pid: int, handle: Optional[int] = None):
        self.pid = pid
        self._handle = handle
        if self._handle is None and IS_WINDOWS:
            self._handle = open_process_handle(pid)

    @property
    def raw_handle(self) -> Optional[int]:
        return self._handle

    @property
    def is_valid(self) -> bool:
        return self._handle is not None and self._handle > 0

    def wait(self, timeout_ms: int = 500) -> bool:
        """
        Wait on the process handle.
        Returns True if the process has exited, False if timeout.
        """
        if not self.is_valid:
            return True
        exited, _ = wait_for_process_handle(self._handle, timeout_ms)
        return exited

    def get_exit_code(self) -> Optional[int]:
        """Returns the exit code if terminated, or None if still running."""
        if not self.is_valid:
            return None
        return get_process_exit_code_native(self._handle)

    def terminate(self, exit_code: int = 1) -> bool:
        """Forcibly terminates the process using the native handle."""
        if not self.is_valid:
            return False
        return terminate_process_native(self._handle, exit_code)

    def close(self):
        """Releases the process handle."""
        if self._handle:
            close_process_handle(self._handle)
            self._handle = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __del__(self):
        self.close()

