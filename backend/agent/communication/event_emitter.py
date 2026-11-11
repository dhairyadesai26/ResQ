"""
ResQ Web - Event Emitter & Internal Event Bus
Provides decoupled event publication and listener subscription.
All process lifecycle, termination, and recovery events are emitted here
for database recording and live WebSocket broadcasting.
"""

import uuid
import time
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Any
import logging

logger = logging.getLogger("resq.agent.events")


class EventType:
    PROCESS_LAUNCHED = "PROCESS_LAUNCHED"
    PROCESS_STOPPED_EXPECTED = "PROCESS_STOPPED_EXPECTED"
    PROCESS_CRASHED_UNEXPECTED = "PROCESS_CRASHED_UNEXPECTED"
    RECOVERY_SCHEDULED = "RECOVERY_SCHEDULED"
    RECOVERY_STARTED = "RECOVERY_STARTED"
    RECOVERY_SUCCEEDED = "RECOVERY_SUCCEEDED"
    RECOVERY_FAILED = "RECOVERY_FAILED"
    RETRY_LIMIT_REACHED = "RETRY_LIMIT_REACHED"
    STATE_CHANGED = "STATE_CHANGED"
    METRICS_UPDATED = "METRICS_UPDATED"
    AGENT_STATUS = "AGENT_STATUS"


@dataclass
class SupervisorEvent:
    event_type: str
    app_id: str
    app_name: str
    severity: str  # "INFO", "WARNING", "ERROR", "CRITICAL"
    message: str
    pid: Optional[int] = None
    exit_code: Optional[int] = None
    timestamp: float = field(default_factory=time.time)
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "app_id": self.app_id,
            "app_name": self.app_name,
            "severity": self.severity,
            "message": self.message,
            "pid": self.pid,
            "exit_code": self.exit_code,
            "timestamp": self.timestamp,
            "details": self.details,
        }


class EventEmitter:
    """Thread-safe event dispatcher for ResQ Web."""

    def __init__(self):
        self._listeners: List[Callable[[SupervisorEvent], None]] = []

    def subscribe(self, listener: Callable[[SupervisorEvent], None]):
        """Registers a listener for supervisor events."""
        if listener not in self._listeners:
            self._listeners.append(listener)

    def unsubscribe(self, listener: Callable[[SupervisorEvent], None]):
        """Removes a registered listener."""
        if listener in self._listeners:
            self._listeners.remove(listener)

    def emit(self, event: SupervisorEvent):
        """Dispatches an event to all subscribers."""
        logger.debug(f"Emitting event: {event.event_type} for app '{event.app_name}'")
        for listener in list(self._listeners):
            try:
                listener(event)
            except Exception as e:
                logger.error(f"Error in event listener: {e}")


# Singleton instance for system-wide event broadcasting
event_bus = EventEmitter()

