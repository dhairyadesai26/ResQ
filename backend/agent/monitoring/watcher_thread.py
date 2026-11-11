"""
ResQ Web - Process Watcher Thread
Demonstrates OS-level wait mechanisms (WaitForSingleObject) and asynchronous monitoring:
- Avoids busy-waiting and high CPU overhead
- Detects process exit within milliseconds using kernel signaling
- Retrieves real exit codes upon process death
"""

import time
import threading
from typing import Callable, Optional
import logging

from backend.agent.process_manager.launcher import LaunchedProcessInfo

logger = logging.getLogger("resq.agent.watcher")


class ProcessWatcherThread(threading.Thread):
    """
    Dedicated worker thread that monitors a single running process handle.
    Uses kernel wait operations (WaitForSingleObject) to detect termination.
    """

    def __init__(
        self,
        app_id: str,
        app_name: str,
        process_info: LaunchedProcessInfo,
        on_terminated: Callable[[str, int, Optional[int], float], None],
        wait_timeout_ms: int = 250,
    ):
        super().__init__(name=f"Watcher-{app_name}-{process_info.pid}", daemon=True)
        self.app_id = app_id
        self.app_name = app_name
        self.process_info = process_info
        self.on_terminated = on_terminated
        self.wait_timeout_ms = wait_timeout_ms
        self._stop_event = threading.Event()
        self.detection_timestamp: Optional[float] = None

    def stop_monitoring(self):
        """Instructs the watcher thread to stop monitoring without signaling crash."""
        self._stop_event.set()

    def run(self):
        logger.debug(f"Started watcher thread for '{self.app_name}' (PID: {self.process_info.pid})")
        pid = self.process_info.pid
        proc = self.process_info.process
        handle = self.process_info.handle

        try:
            while not self._stop_event.is_set():
                # Perform native wait on the Windows process handle
                has_exited = False

                if handle and handle.is_valid:
                    has_exited = handle.wait(timeout_ms=self.wait_timeout_ms)
                else:
                    # Fallback if handle wasn't acquired: standard poll
                    try:
                        ret = proc.poll()
                        has_exited = ret is not None
                        if not has_exited:
                            time.sleep(self.wait_timeout_ms / 1000.0)
                    except Exception:
                        has_exited = True

                if has_exited:
                    self.detection_timestamp = time.time()
                    break

            if self._stop_event.is_set():
                logger.debug(f"Watcher for '{self.app_name}' cancelled by supervisor.")
                return

            # Retrieve exit code
            exit_code = None
            if handle and handle.is_valid:
                exit_code = handle.get_exit_code()

            if exit_code is None:
                # Poll python popen object to guarantee clean reap
                try:
                    proc.poll()
                    exit_code = proc.returncode
                except Exception:
                    pass

            duration = time.time() - self.process_info.start_time
            logger.info(
                f"Process exit detected for '{self.app_name}' (PID: {pid}). "
                f"Exit Code: {exit_code}, Duration: {duration:.2f}s"
            )

            # Signal termination callback
            self.on_terminated(self.app_id, pid, exit_code, duration)

        except Exception as e:
            logger.error(f"Unexpected error in watcher thread for '{self.app_name}': {e}")
        finally:
            # Clean up process handle and job object references
            if handle:
                handle.close()
            if self.process_info.job_object:
                self.process_info.job_object.close()

