"""
ResQ Web - Windows Process Launcher
Responsible for launching real operating system processes safely:
- Validates binary and arguments against security rules
- Spawns processes with shell=False
- Captures true Windows PID and creation timestamp
- Associates native process handle and Windows Job Object
"""

import os
import sys
import time
import subprocess
from dataclasses import dataclass
from typing import List, Optional
import logging

from agent.security.validator import ProcessSecurityValidator, SecurityValidationError
from agent.process_manager.process_handle import ProcessHandle
from agent.process_manager.job_object import JobObject

logger = logging.getLogger("resq.agent.launcher")


@dataclass
class LaunchedProcessInfo:
    pid: int
    executable: str
    arguments: List[str]
    working_directory: str
    start_time: float
    process: subprocess.Popen
    handle: ProcessHandle
    job_object: Optional[JobObject] = None


class ProcessLauncher:
    """Spawns and binds Windows processes."""

    @classmethod
    def launch(
        cls,
        executable_path: str,
        arguments: Optional[any] = None,
        working_dir: Optional[str] = None,
        use_job_object: bool = True,
    ) -> LaunchedProcessInfo:
        """
        Launches an approved application as a real Windows process.
        """
        # 1. Sanitize and validate executable
        safe_exe = ProcessSecurityValidator.sanitize_path(executable_path)
        safe_args = ProcessSecurityValidator.sanitize_arguments(arguments)
        safe_dir = ProcessSecurityValidator.sanitize_working_directory(working_dir, safe_exe)

        # 2. Build execution command list
        cmd: List[str] = []
        if safe_exe.lower().endswith(".py"):
            cmd = [sys.executable, safe_exe] + safe_args
        else:
            cmd = [safe_exe] + safe_args

        creation_flags = 0
        if sys.platform == "win32":
            # CREATE_NEW_PROCESS_GROUP allows independent signal handling
            creation_flags = subprocess.CREATE_NEW_PROCESS_GROUP

        logger.info(f"Launching process: cmd={cmd}, cwd={safe_dir}")
        start_time = time.time()

        try:
            # We explicitly enforce shell=False for security
            proc = subprocess.Popen(
                cmd,
                cwd=safe_dir,
                creationflags=creation_flags,
                shell=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
            )
        except Exception as e:
            logger.error(f"Failed to spawn process '{safe_exe}': {e}")
            raise RuntimeError(f"Operating system failed to start process: {e}") from e

        pid = proc.pid
        logger.info(f"Process spawned successfully: PID={pid}")

        # 3. Acquire native Windows handle
        handle = ProcessHandle(pid)

        # 4. Bind to Windows Job Object
        job_obj = None
        if use_job_object and sys.platform == "win32" and handle.is_valid:
            try:
                job_obj = JobObject(name=f"ResQ_Job_{pid}_{int(start_time)}")
                if job_obj.is_valid:
                    job_obj.assign_process(handle.raw_handle)
                    logger.debug(f"Assigned PID {pid} to Windows Job Object")
            except Exception as e:
                logger.warning(f"Could not assign PID {pid} to Job Object: {e}")

        return LaunchedProcessInfo(
            pid=pid,
            executable=safe_exe,
            arguments=safe_args,
            working_directory=safe_dir,
            start_time=start_time,
            process=proc,
            handle=handle,
            job_object=job_obj,
        )

