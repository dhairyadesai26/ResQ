"""
ResQ Web - Fault Recovery Policy Evaluator
Evaluates recovery decisions based on configurable policies:
- Exponential backoff calculation: delay = min(initial * (multiplier ^ retries), max_delay)
- Retry limit enforcement (circuit breaker)
- Automatic reset of retry counters upon stable runtime
- Prevents cascading restart storms and infinite loops
"""

import time
from dataclasses import dataclass
from typing import Optional
import logging

logger = logging.getLogger("resq.agent.policy")


@dataclass
class RecoveryPolicyConfig:
    enabled: bool = True
    max_retries: int = 3
    initial_delay_seconds: float = 1.0
    backoff_multiplier: float = 2.0
    max_delay_seconds: float = 30.0
    stable_runtime_threshold_seconds: float = 60.0


class RecoveryPolicyEvaluator:
    """Calculates backoff delays and decides whether to trigger process recovery."""

    def __init__(self, config: Optional[RecoveryPolicyConfig] = None):
        self.config = config or RecoveryPolicyConfig()
        self.current_retries: int = 0
        self.total_recoveries: int = 0
        self.last_crash_timestamp: Optional[float] = None
        self.last_recovery_timestamp: Optional[float] = None
        self.last_start_timestamp: Optional[float] = None

    def record_start(self):
        """Called whenever the process successfully transitions to RUNNING."""
        self.last_start_timestamp = time.time()

    def check_and_apply_stable_reset(self) -> bool:
        """
        If the process has been running stably for longer than
        `stable_runtime_threshold_seconds`, reset the consecutive retry counter.
        """
        if self.last_start_timestamp and self.current_retries > 0:
            uptime = time.time() - self.last_start_timestamp
            if uptime >= self.config.stable_runtime_threshold_seconds:
                logger.info(
                    f"Process ran stably for {uptime:.1f}s. Resetting consecutive retry counter from {self.current_retries} to 0."
                )
                self.current_retries = 0
                return True
        return False

    def should_recover(self) -> bool:
        """Determines whether recovery should be attempted."""
        if not self.config.enabled:
            return False

        # Apply stable reset if applicable
        self.check_and_apply_stable_reset()

        return self.current_retries < self.config.max_retries

    def calculate_delay(self) -> float:
        """
        Computes the exponential backoff delay before the next recovery attempt:
        delay = min(initial_delay * (backoff_multiplier ** current_retries), max_delay)
        """
        delay = self.config.initial_delay_seconds * (self.config.backoff_multiplier ** self.current_retries)
        return min(delay, self.config.max_delay_seconds)

    def register_recovery_attempt(self) -> int:
        """
        Increments retry counts and updates timestamps.
        Returns the new attempt number.
        """
        self.current_retries += 1
        self.total_recoveries += 1
        self.last_recovery_timestamp = time.time()
        return self.current_retries

    def reset_counter(self):
        """Manually or externally resets consecutive retry counter to 0."""
        self.current_retries = 0
        logger.info("Consecutive retry counter reset to 0.")

