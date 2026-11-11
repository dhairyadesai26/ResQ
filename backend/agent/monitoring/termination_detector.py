"""
ResQ Web - Termination Classifier and Fault Detector
Distinguishes between:
1. Expected termination (User/system initiated STOP).
2. Unexpected termination (Crash, abnormal termination, external kill).
Prevents race conditions between stop requests and termination events.
"""

from typing import Optional, Dict, Any
import logging

from backend.agent.recovery.state_machine import ProcessState, ProcessStateMachine
from backend.agent.communication.event_emitter import event_bus, SupervisorEvent, EventType

logger = logging.getLogger("resq.agent.detector")


class TerminationResult:
    def __init__(
        self,
        app_id: str,
        app_name: str,
        pid: int,
        exit_code: Optional[int],
        duration: float,
        is_expected: bool,
        message: str,
    ):
        self.app_id = app_id
        self.app_name = app_name
        self.pid = pid
        self.exit_code = exit_code
        self.duration = duration
        self.is_expected = is_expected
        self.message = message


class ProcessTerminationDetector:
    """Analyzes process termination in real time."""

    @classmethod
    def handle_termination(
        cls,
        app_id: str,
        app_name: str,
        pid: int,
        exit_code: Optional[int],
        duration: float,
        state_machine: ProcessStateMachine,
    ) -> TerminationResult:
        """
        Classifies termination based on current state machine state.
        Ensures thread-safe classification and emits corresponding events.
        """
        current_state = state_machine.current_state

        if current_state == ProcessState.STOPPING:
            # Expected termination requested by user/system
            logger.info(f"Process '{app_name}' (PID: {pid}) stopped gracefully as requested.")
            try:
                state_machine.transition_to(
                    ProcessState.STOPPED,
                    reason=f"Controlled shutdown complete (Exit code: {exit_code})",
                )
            except Exception as e:
                logger.warning(f"State transition error: {e}")

            event = SupervisorEvent(
                event_type=EventType.PROCESS_STOPPED_EXPECTED,
                app_id=app_id,
                app_name=app_name,
                severity="INFO",
                message=f"Application '{app_name}' stopped intentionally (Exit code: {exit_code}).",
                pid=pid,
                exit_code=exit_code,
                details={"duration_seconds": round(duration, 2)},
            )
            event_bus.emit(event)

            return TerminationResult(
                app_id=app_id,
                app_name=app_name,
                pid=pid,
                exit_code=exit_code,
                duration=duration,
                is_expected=True,
                message="Application stopped intentionally by user.",
            )

        else:
            # Unexpected termination (Crash, SIGKILL, fatal exception)
            severity = "WARNING" if exit_code == 0 else "ERROR"
            msg = (
                f"Application '{app_name}' (PID: {pid}) terminated unexpectedly with exit code {exit_code} "
                f"after {duration:.2f} seconds."
            )
            logger.warning(msg)

            event = SupervisorEvent(
                event_type=EventType.PROCESS_CRASHED_UNEXPECTED,
                app_id=app_id,
                app_name=app_name,
                severity=severity,
                message=msg,
                pid=pid,
                exit_code=exit_code,
                details={"duration_seconds": round(duration, 2)},
            )
            event_bus.emit(event)

            return TerminationResult(
                app_id=app_id,
                app_name=app_name,
                pid=pid,
                exit_code=exit_code,
                duration=duration,
                is_expected=False,
                message=msg,
            )

