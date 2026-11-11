"""
ResQ Web - Multi-Process Monitoring & Supervision Engine
The core supervisor component:
- Concurrently manages multiple Windows processes
- Encapsulates launcher, inspector, watcher threads, and recovery orchestrators
- Thread-safe synchronization protecting shared application state
- Distinguishes graceful stops from abnormal crashes
"""

import os
import time
import threading
from typing import Dict, List, Optional, Any
import logging

from backend.agent.process_manager.launcher import ProcessLauncher, LaunchedProcessInfo
from backend.agent.process_manager.inspector import ProcessInspector, ProcessMetrics
from backend.agent.recovery.state_machine import ProcessState, ProcessStateMachine
from backend.agent.recovery.policy_evaluator import RecoveryPolicyEvaluator, RecoveryPolicyConfig
from backend.agent.recovery.recovery_orchestrator import RecoveryOrchestrator
from backend.agent.monitoring.watcher_thread import ProcessWatcherThread
from backend.agent.monitoring.termination_detector import ProcessTerminationDetector
from backend.agent.communication.event_emitter import event_bus, SupervisorEvent, EventType

logger = logging.getLogger("resq.agent.engine")


class ManagedAppEntry:
    """Internal registry model for an active managed application."""

    def __init__(
        self,
        app_id: str,
        name: str,
        executable_path: str,
        arguments: any,
        working_dir: Optional[str],
        policy_config: RecoveryPolicyConfig,
    ):
        self.app_id = app_id
        self.name = name
        self.executable_path = executable_path
        self.arguments = arguments
        self.working_dir = working_dir

        self.state_machine = ProcessStateMachine(ProcessState.STOPPED)
        self.policy = RecoveryPolicyEvaluator(policy_config)

        self.process_info: Optional[LaunchedProcessInfo] = None
        self.watcher: Optional[ProcessWatcherThread] = None
        self.orchestrator: Optional[RecoveryOrchestrator] = None

        self.last_exit_code: Optional[int] = None
        self.last_crash_timestamp: Optional[float] = None
        self.last_metrics: Optional[ProcessMetrics] = None


class ProcessMonitorEngine:
    """Singleton process monitor engine managing concurrent applications."""

    def __init__(self):
        self._apps: Dict[str, ManagedAppEntry] = {}
        self._lock = threading.RLock()
        self._is_running = True

    def register_application(
        self,
        app_id: str,
        name: str,
        executable_path: str,
        arguments: any = None,
        working_dir: Optional[str] = None,
        policy_config: Optional[RecoveryPolicyConfig] = None,
    ) -> ManagedAppEntry:
        """Registers a new application to be supervised."""
        with self._lock:
            if app_id in self._apps:
                # Update existing configuration
                entry = self._apps[app_id]
                entry.name = name
                entry.executable_path = executable_path
                entry.arguments = arguments
                entry.working_dir = working_dir
                if policy_config:
                    entry.policy.config = policy_config
                return entry

            config = policy_config or RecoveryPolicyConfig()
            entry = ManagedAppEntry(
                app_id=app_id,
                name=name,
                executable_path=executable_path,
                arguments=arguments,
                working_dir=working_dir,
                policy_config=config,
            )

            # Initialize orchestrator
            entry.orchestrator = RecoveryOrchestrator(
                app_id=app_id,
                app_name=name,
                executable_path=executable_path,
                arguments=arguments,
                working_dir=working_dir,
                state_machine=entry.state_machine,
                policy_evaluator=entry.policy,
                on_process_restarted=self._on_process_restarted_callback,
            )

            self._apps[app_id] = entry
            logger.info(f"Registered application '{name}' (ID: {app_id})")
            return entry

    def unregister_application(self, app_id: str) -> bool:
        """Stops and removes an application from supervision."""
        with self._lock:
            if app_id not in self._apps:
                return False

            entry = self._apps[app_id]
            # Stop if currently running or recovering
            if entry.state_machine.current_state in (
                ProcessState.RUNNING,
                ProcessState.STARTING,
                ProcessState.RECOVERY_WAIT,
            ):
                self.stop_application(app_id, force=True)

            del self._apps[app_id]
            logger.info(f"Unregistered application ID: {app_id}")
            return True

    def start_application(self, app_id: str) -> bool:
        """Launches the registered application."""
        with self._lock:
            if app_id not in self._apps:
                raise ValueError(f"Application {app_id} is not registered.")

            entry = self._apps[app_id]
            current = entry.state_machine.current_state
            if current in (ProcessState.RUNNING, ProcessState.STARTING, ProcessState.RECOVERY_WAIT):
                logger.warning(f"Application '{entry.name}' is already {current.value}. Start ignored.")
                return False

            # Reset state to STARTING
            entry.state_machine.transition_to(
                ProcessState.STARTING,
                reason="User initiated start",
            )

        try:
            proc_info = ProcessLauncher.launch(
                executable_path=entry.executable_path,
                arguments=entry.arguments,
                working_dir=entry.working_dir,
            )

            with self._lock:
                entry.process_info = proc_info
                entry.state_machine.transition_to(
                    ProcessState.RUNNING,
                    reason=f"Process successfully launched (PID: {proc_info.pid})",
                )
                entry.policy.record_start()

                # Spawn watcher thread
                entry.watcher = ProcessWatcherThread(
                    app_id=app_id,
                    app_name=entry.name,
                    process_info=proc_info,
                    on_terminated=self._on_process_terminated_callback,
                )
                entry.watcher.start()

            event_bus.emit(
                SupervisorEvent(
                    event_type=EventType.PROCESS_LAUNCHED,
                    app_id=app_id,
                    app_name=entry.name,
                    severity="INFO",
                    message=f"Application '{entry.name}' launched successfully with PID {proc_info.pid}.",
                    pid=proc_info.pid,
                    details={"executable": proc_info.executable},
                )
            )
            return True

        except Exception as e:
            logger.error(f"Failed to start application '{entry.name}': {e}")
            with self._lock:
                try:
                    entry.state_machine.transition_to(
                        ProcessState.FAILED,
                        reason=f"Failed to launch: {e}",
                    )
                except Exception:
                    pass
            raise

    def stop_application(self, app_id: str, timeout_seconds: float = 3.0, force: bool = False) -> bool:
        """Gracefully stops a running application."""
        with self._lock:
            if app_id not in self._apps:
                return False

            entry = self._apps[app_id]
            current = entry.state_machine.current_state

            # If recovering, cancel the recovery timer
            if current == ProcessState.RECOVERY_WAIT:
                if entry.orchestrator:
                    entry.orchestrator.cancel_active_recovery()
                entry.state_machine.transition_to(ProcessState.STOPPED, reason="Recovery cancelled by user")
                return True

            if current != ProcessState.RUNNING:
                logger.info(f"Application '{entry.name}' is already {current.value}. No need to stop.")
                return True

            # Mark state as STOPPING to classify upcoming termination as expected
            entry.state_machine.transition_to(ProcessState.STOPPING, reason="User initiated graceful stop")
            proc_info = entry.process_info

        if not proc_info or not proc_info.process:
            with self._lock:
                entry.state_machine.transition_to(ProcessState.STOPPED, reason="No active process reference")
            return True

        # Attempt graceful termination
        try:
            proc_info.process.terminate()
            # Wait briefly for process to exit
            try:
                proc_info.process.wait(timeout=timeout_seconds)
            except Exception:
                # Force kill if process does not exit in time
                logger.warning(f"Process PID {proc_info.pid} did not exit in {timeout_seconds}s. Force terminating.")
                if proc_info.handle and proc_info.handle.is_valid:
                    proc_info.handle.terminate(1)
                else:
                    proc_info.process.kill()
        except Exception as e:
            logger.warning(f"Error while terminating process '{entry.name}': {e}")

        return True

    def restart_application(self, app_id: str) -> bool:
        """Performs a controlled stop and subsequent restart."""
        self.stop_application(app_id, timeout_seconds=2.0)
        time.sleep(0.5)
        return self.start_application(app_id)

    def reset_recovery_counter(self, app_id: str) -> bool:
        """Resets the consecutive retry counter and transitions FAILED state to STOPPED."""
        with self._lock:
            if app_id not in self._apps:
                return False
            entry = self._apps[app_id]
            entry.policy.reset_counter()
            if entry.state_machine.current_state == ProcessState.FAILED:
                entry.state_machine.transition_to(ProcessState.STOPPED, reason="Recovery counter reset by user")
            return True

    def get_application_state(self, app_id: str) -> Dict[str, Any]:
        """Queries the current status and metrics of a managed application."""
        with self._lock:
            if app_id not in self._apps:
                raise ValueError(f"Application {app_id} not found.")

            entry = self._apps[app_id]
            current_state = entry.state_machine.current_state
            pid = entry.process_info.pid if entry.process_info and current_state == ProcessState.RUNNING else None
            start_time = entry.process_info.start_time if entry.process_info and current_state == ProcessState.RUNNING else None
            uptime = time.time() - start_time if start_time else 0.0

            # Gather live metrics if running
            cpu = 0.0
            mem_rss = 0
            mem_pct = 0.0
            threads = 0
            handles = 0

            if pid and current_state == ProcessState.RUNNING:
                metrics = ProcessInspector.inspect(pid)
                if metrics:
                    entry.last_metrics = metrics
                    cpu = metrics.cpu_percent
                    mem_rss = metrics.memory_rss
                    mem_pct = metrics.memory_percent
                    threads = metrics.num_threads
                    handles = metrics.num_handles

            return {
                "app_id": entry.app_id,
                "name": entry.name,
                "executable_path": entry.executable_path,
                "arguments": entry.arguments,
                "working_dir": entry.working_dir,
                "state": current_state.value,
                "pid": pid,
                "uptime_seconds": round(uptime, 1),
                "cpu_percent": cpu,
                "memory_rss_bytes": mem_rss,
                "memory_percent": mem_pct,
                "num_threads": threads,
                "num_handles": handles,
                "consecutive_retries": entry.policy.current_retries,
                "max_retries": entry.policy.config.max_retries,
                "total_recoveries": entry.policy.total_recoveries,
                "auto_recovery_enabled": entry.policy.config.enabled,
                "last_exit_code": entry.last_exit_code,
                "last_crash_timestamp": entry.last_crash_timestamp,
            }

    def list_applications(self) -> List[Dict[str, Any]]:
        """Lists all registered applications with their live statuses."""
        with self._lock:
            app_ids = list(self._apps.keys())
        return [self.get_application_state(aid) for aid in app_ids]

    def _on_process_terminated_callback(
        self,
        app_id: str,
        pid: int,
        exit_code: Optional[int],
        duration: float,
    ):
        """Called automatically by the background ProcessWatcherThread upon exit."""
        with self._lock:
            if app_id not in self._apps:
                return

            entry = self._apps[app_id]
            entry.last_exit_code = exit_code

        # Classify termination
        result = ProcessTerminationDetector.handle_termination(
            app_id=app_id,
            app_name=entry.name,
            pid=pid,
            exit_code=exit_code,
            duration=duration,
            state_machine=entry.state_machine,
        )

        if not result.is_expected:
            with self._lock:
                entry.last_crash_timestamp = time.time()
                orchestrator = entry.orchestrator

            # Trigger automatic recovery
            if orchestrator:
                orchestrator.trigger_recovery(crash_exit_code=exit_code)

    def _on_process_restarted_callback(self, app_id: str, proc_info: LaunchedProcessInfo):
        """Called by RecoveryOrchestrator when a process has been relaunched."""
        with self._lock:
            if app_id not in self._apps:
                return

            entry = self._apps[app_id]
            entry.process_info = proc_info

            # Start fresh watcher thread
            entry.watcher = ProcessWatcherThread(
                app_id=app_id,
                app_name=entry.name,
                process_info=proc_info,
                on_terminated=self._on_process_terminated_callback,
            )
            entry.watcher.start()

    def shutdown(self):
        """Cleanly terminates all managed processes and watcher threads."""
        logger.info("Shutting down ProcessMonitorEngine...")
        with self._lock:
            self._is_running = False
            app_ids = list(self._apps.keys())

        for aid in app_ids:
            try:
                self.stop_application(aid, force=True)
            except Exception as e:
                logger.warning(f"Error stopping app {aid} during shutdown: {e}")


# Global singleton engine
monitor_engine = ProcessMonitorEngine()

