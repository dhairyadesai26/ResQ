"""
ResQ Web - Process Recovery Orchestrator
Coordinates automatic recovery with thread-safe locking and exponential backoff:
- Enforces strict single-recovery execution per application
- Applies backoff delays without blocking the supervisor
- Supports cancellation if the user triggers manual STOP during backoff
- Relaunches process, captures new PID, and resumes monitoring
"""

import time
import threading
from typing import Callable, Dict, Optional
import logging

from backend.agent.recovery.state_machine import ProcessState, ProcessStateMachine
from backend.agent.recovery.policy_evaluator import RecoveryPolicyEvaluator
from backend.agent.process_manager.launcher import ProcessLauncher, LaunchedProcessInfo
from backend.agent.communication.event_emitter import event_bus, SupervisorEvent, EventType

logger = logging.getLogger("resq.agent.recovery")


class RecoveryOrchestrator:
    """Manages recovery lifecycles for supervised applications."""

    def __init__(
        self,
        app_id: str,
        app_name: str,
        executable_path: str,
        arguments: any,
        working_dir: Optional[str],
        state_machine: ProcessStateMachine,
        policy_evaluator: RecoveryPolicyEvaluator,
        on_process_restarted: Callable[[str, LaunchedProcessInfo], None],
    ):
        self.app_id = app_id
        self.app_name = app_name
        self.executable_path = executable_path
        self.arguments = arguments
        self.working_dir = working_dir
        self.state_machine = state_machine
        self.policy = policy_evaluator
        self.on_process_restarted = on_process_restarted

        self._lock = threading.Lock()
        self._cancel_recovery_event = threading.Event()
        self._recovery_thread: Optional[threading.Thread] = None

    def cancel_active_recovery(self):
        """Cancels any ongoing recovery timer."""
        with self._lock:
            self._cancel_recovery_event.set()

    def trigger_recovery(self, crash_exit_code: Optional[int]):
        """
        Initiates recovery workflow if allowed by policy.
        Must be called from a worker thread or async callback.
        """
        with self._lock:
            if not self.policy.should_recover():
                logger.warning(
                    f"Retry limit exceeded for '{self.app_name}' "
                    f"({self.policy.current_retries}/{self.policy.config.max_retries}). Marking FAILED."
                )
                try:
                    self.state_machine.transition_to(
                        ProcessState.FAILED,
                        reason=f"Exceeded max retries ({self.policy.config.max_retries})",
                    )
                except Exception as e:
                    logger.debug(f"State transition to FAILED: {e}")

                event_bus.emit(
                    SupervisorEvent(
                        event_type=EventType.RETRY_LIMIT_REACHED,
                        app_id=self.app_id,
                        app_name=self.app_name,
                        severity="CRITICAL",
                        message=f"Application '{self.app_name}' exceeded maximum recovery attempts ({self.policy.config.max_retries}). Automatic recovery aborted.",
                        exit_code=crash_exit_code,
                        details={"max_retries": self.policy.config.max_retries},
                    )
                )
                return

            # Compute backoff
            delay = self.policy.calculate_delay()
            attempt = self.policy.register_recovery_attempt()

            try:
                self.state_machine.transition_to(
                    ProcessState.RECOVERY_WAIT,
                    reason=f"Recovery attempt #{attempt} scheduled in {delay:.2f}s",
                )
            except Exception as e:
                logger.warning(f"Error transitioning to RECOVERY_WAIT: {e}")

            self._cancel_recovery_event.clear()

            event_bus.emit(
                SupervisorEvent(
                    event_type=EventType.RECOVERY_SCHEDULED,
                    app_id=self.app_id,
                    app_name=self.app_name,
                    severity="WARNING",
                    message=f"Recovery attempt #{attempt} scheduled in {delay:.2f}s for '{self.app_name}'.",
                    exit_code=crash_exit_code,
                    details={
                        "attempt": attempt,
                        "delay_seconds": delay,
                        "max_retries": self.policy.config.max_retries,
                    },
                )
            )

            # Spawn background worker to wait and execute restart
            self._recovery_thread = threading.Thread(
                target=self._execute_delayed_recovery,
                args=(attempt, delay),
                name=f"RecoveryWorker-{self.app_name}-#{attempt}",
                daemon=True,
            )
            self._recovery_thread.start()

    def _execute_delayed_recovery(self, attempt: int, delay: float):
        """Executes the recovery delay and launches the new process."""
        logger.info(f"Recovery delay {delay:.2f}s started for '{self.app_name}'...")
        cancelled = self._cancel_recovery_event.wait(timeout=delay)
        if cancelled:
            logger.info(f"Recovery attempt #{attempt} for '{self.app_name}' was cancelled by user.")
            return

        with self._lock:
            # Check state before relaunch
            if self.state_machine.current_state != ProcessState.RECOVERY_WAIT:
                logger.info(
                    f"Recovery aborted: current state is {self.state_machine.current_state.value}, not RECOVERY_WAIT"
                )
                return

            try:
                self.state_machine.transition_to(
                    ProcessState.STARTING,
                    reason=f"Executing recovery relaunch #{attempt}",
                )
            except Exception as e:
                logger.warning(f"Error transitioning to STARTING: {e}")
                return

            event_bus.emit(
                SupervisorEvent(
                    event_type=EventType.RECOVERY_STARTED,
                    app_id=self.app_id,
                    app_name=self.app_name,
                    severity="INFO",
                    message=f"Starting recovery relaunch #{attempt} for '{self.app_name}'.",
                    details={"attempt": attempt},
                )
            )

            recovery_start = time.time()
            try:
                proc_info = ProcessLauncher.launch(
                    executable_path=self.executable_path,
                    arguments=self.arguments,
                    working_dir=self.working_dir,
                )
                recovery_latency = time.time() - recovery_start

                self.state_machine.transition_to(
                    ProcessState.RUNNING,
                    reason=f"Recovery succeeded. New PID: {proc_info.pid}",
                )
                self.policy.record_start()

                event_bus.emit(
                    SupervisorEvent(
                        event_type=EventType.RECOVERY_SUCCEEDED,
                        app_id=self.app_id,
                        app_name=self.app_name,
                        severity="INFO",
                        message=f"Application '{self.app_name}' successfully recovered with new PID {proc_info.pid} (Launch latency: {recovery_latency:.3f}s).",
                        pid=proc_info.pid,
                        details={
                            "attempt": attempt,
                            "recovery_latency_seconds": round(recovery_latency, 3),
                        },
                    )
                )

                # Re-bind watcher thread in supervisor
                self.on_process_restarted(self.app_id, proc_info)

            except Exception as e:
                logger.error(f"Failed to relaunch '{self.app_name}' during recovery: {e}")
                try:
                    self.state_machine.transition_to(
                        ProcessState.FAILED,
                        reason=f"Relaunch failed: {e}",
                    )
                except Exception:
                    pass

                event_bus.emit(
                    SupervisorEvent(
                        event_type=EventType.RECOVERY_FAILED,
                        app_id=self.app_id,
                        app_name=self.app_name,
                        severity="ERROR",
                        message=f"Recovery #{attempt} failed for '{self.app_name}': {e}",
                        details={"attempt": attempt, "error": str(e)},
                    )
                )

