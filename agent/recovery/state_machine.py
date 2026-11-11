"""
ResQ Web - Process State Machine
Implements a formal, thread-safe deterministic state machine:
States:
  - STOPPED: Application is inactive.
  - STARTING: Process creation initiated.
  - RUNNING: Active and executing.
  - STOPPING: Controlled shutdown requested by user.
  - RECOVERY_WAIT: Unexpected exit detected, cooling off in backoff timer.
  - FAILED: Retry limit exceeded or unrecoverable error.
"""

from enum import Enum
import threading
from typing import Callable, Dict, List, Optional, Set
import logging

logger = logging.getLogger("resq.agent.state_machine")


class ProcessState(str, Enum):
    STOPPED = "STOPPED"
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    STOPPING = "STOPPING"
    RECOVERY_WAIT = "RECOVERY_WAIT"
    FAILED = "FAILED"


class InvalidStateTransitionError(Exception):
    """Raised when an illegal state transition is attempted."""
    def __init__(self, from_state: ProcessState, to_state: ProcessState, reason: str = ""):
        self.from_state = from_state
        self.to_state = to_state
        msg = f"Invalid state transition: {from_state.value} -> {to_state.value}."
        if reason:
            msg += f" Reason: {reason}"
        super().__init__(msg)


class ProcessStateMachine:
    """Thread-safe state machine for managed processes."""

    VALID_TRANSITIONS: Dict[ProcessState, Set[ProcessState]] = {
        ProcessState.STOPPED: {
            ProcessState.STARTING,
        },
        ProcessState.STARTING: {
            ProcessState.RUNNING,
            ProcessState.FAILED,
            ProcessState.STOPPED,
        },
        ProcessState.RUNNING: {
            ProcessState.STOPPING,
            ProcessState.RECOVERY_WAIT,
            ProcessState.FAILED,
            ProcessState.STOPPED,
        },
        ProcessState.STOPPING: {
            ProcessState.STOPPED,
            ProcessState.FAILED,
        },
        ProcessState.RECOVERY_WAIT: {
            ProcessState.STARTING,
            ProcessState.STOPPING,
            ProcessState.STOPPED,
            ProcessState.FAILED,
        },
        ProcessState.FAILED: {
            ProcessState.STARTING,
            ProcessState.STOPPED,
        },
    }

    def __init__(self, initial_state: ProcessState = ProcessState.STOPPED):
        self._current_state = initial_state
        self._lock = threading.Lock()
        self._listeners: List[Callable[[ProcessState, ProcessState, Optional[str]], None]] = []

    @property
    def current_state(self) -> ProcessState:
        with self._lock:
            return self._current_state

    def add_listener(self, callback: Callable[[ProcessState, ProcessState, Optional[str]], None]):
        """Registers a callback for state changes."""
        with self._lock:
            self._listeners.append(callback)

    def transition_to(self, new_state: ProcessState, reason: Optional[str] = None) -> ProcessState:
        """
        Atomically validates and applies a transition to `new_state`.
        Raises `InvalidStateTransitionError` if transition is forbidden.
        """
        callbacks_to_invoke = []
        old_state = None

        with self._lock:
            old_state = self._current_state
            if old_state == new_state:
                return new_state

            allowed = self.VALID_TRANSITIONS.get(old_state, set())
            if new_state not in allowed:
                raise InvalidStateTransitionError(old_state, new_state, reason or "Forbidden by state matrix")

            self._current_state = new_state
            callbacks_to_invoke = list(self._listeners)

        logger.info(f"State transition: {old_state.value} -> {new_state.value} (reason: {reason})")

        # Invoke callbacks outside lock to avoid deadlocks
        for cb in callbacks_to_invoke:
            try:
                cb(old_state, new_state, reason)
            except Exception as e:
                logger.error(f"Error executing state listener callback: {e}")

        return new_state

