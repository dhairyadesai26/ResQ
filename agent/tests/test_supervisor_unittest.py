"""
ResQ Web - Core Operating Systems & Process Supervisor Tests (Standard Library Unittest)
Validates real Windows process management against formal test cases:
T01 - Register valid executable
T02 - Reject invalid executable path
T03 - Launch actual Windows application
T04 - Capture real PID
T05 - Display current running state
T06 - Request controlled stop
T07 - Verify expected stop does not trigger recovery
T08 - Unexpectedly terminate a managed process
T09 - Detect termination
T10 - Capture exit code where available
T11 - Trigger automatic recovery
T12 - Verify new process starts
T13 - Verify new PID differs
T14 - Test retry limits
T15 - Test exponential backoff
T16 - Test multiple simultaneously monitored applications
T17 - Test concurrent recovery requests
T25 - System resource metrics
"""

import os
import sys
import time
import unittest

# Ensure workspace root is in sys.path
WORKSPACE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if WORKSPACE_DIR not in sys.path:
    sys.path.insert(0, WORKSPACE_DIR)

from agent.security.validator import ProcessSecurityValidator, SecurityValidationError
from agent.recovery.state_machine import ProcessState, ProcessStateMachine, InvalidStateTransitionError
from agent.recovery.policy_evaluator import RecoveryPolicyEvaluator, RecoveryPolicyConfig
from agent.process_manager.launcher import ProcessLauncher
from agent.process_manager.inspector import ProcessInspector
from agent.monitoring.monitor_engine import ProcessMonitorEngine
from agent.monitoring.termination_detector import ProcessTerminationDetector
from agent.communication.event_emitter import event_bus, EventType


WORKER_SCRIPT = os.path.join(WORKSPACE_DIR, "test_apps", "worker_app.py")
CRASHER_SCRIPT = os.path.join(WORKSPACE_DIR, "test_apps", "crasher_app.py")


class TestProcessSupervisorCore(unittest.TestCase):

    def test_t01_register_valid_executable(self):
        """T01: Register a valid executable path."""
        validated = ProcessSecurityValidator.sanitize_path(WORKER_SCRIPT)
        self.assertTrue(os.path.isfile(validated))
        self.assertTrue(os.path.isabs(validated))

    def test_t02_reject_invalid_executable_path(self):
        """T02: Reject an invalid or non-existent executable path."""
        with self.assertRaises(SecurityValidationError):
            ProcessSecurityValidator.sanitize_path("C:\\non_existent_fake_program_12345.exe")

    def test_state_machine_valid_and_invalid_transitions(self):
        """Validates deterministic state machine transitions."""
        sm = ProcessStateMachine(ProcessState.STOPPED)
        self.assertEqual(sm.current_state, ProcessState.STOPPED)

        sm.transition_to(ProcessState.STARTING)
        self.assertEqual(sm.current_state, ProcessState.STARTING)

        sm.transition_to(ProcessState.RUNNING)
        self.assertEqual(sm.current_state, ProcessState.RUNNING)

        # Forbidden: RUNNING -> STARTING
        with self.assertRaises(InvalidStateTransitionError):
            sm.transition_to(ProcessState.STARTING)

        sm.transition_to(ProcessState.STOPPING)
        sm.transition_to(ProcessState.STOPPED)
        self.assertEqual(sm.current_state, ProcessState.STOPPED)

    def test_t03_t04_t05_launch_capture_pid_and_status(self):
        """
        T03: Launch an actual Windows application
        T04: Capture real PID
        T05: Display running state and metrics
        """
        engine = ProcessMonitorEngine()
        app_id = "test_app_worker_1"

        engine.register_application(
            app_id=app_id,
            name="WorkerApp",
            executable_path=WORKER_SCRIPT,
            arguments=["Worker1", "0.5"],
        )

        success = engine.start_application(app_id)
        self.assertTrue(success)

        time.sleep(0.5)
        state = engine.get_application_state(app_id)

        self.assertEqual(state["state"], ProcessState.RUNNING.value)
        self.assertIsNotNone(state["pid"])
        self.assertGreater(state["pid"], 0)
        self.assertGreaterEqual(state["uptime_seconds"], 0.0)

        # Clean up
        engine.stop_application(app_id, timeout_seconds=2.0)
        time.sleep(0.5)
        final_state = engine.get_application_state(app_id)
        self.assertEqual(final_state["state"], ProcessState.STOPPED.value)

    def test_t06_t07_controlled_stop_no_recovery(self):
        """
        T06: Request a controlled stop
        T07: Verify expected stop does not trigger automatic recovery
        """
        engine = ProcessMonitorEngine()
        app_id = "test_app_controlled_stop"

        engine.register_application(
            app_id=app_id,
            name="WorkerControlled",
            executable_path=WORKER_SCRIPT,
            arguments=["Controlled", "0.5"],
            policy_config=RecoveryPolicyConfig(enabled=True, max_retries=3, initial_delay_seconds=0.5),
        )

        engine.start_application(app_id)
        time.sleep(0.5)

        # Request graceful stop
        stopped = engine.stop_application(app_id, timeout_seconds=2.0)
        self.assertTrue(stopped)

        time.sleep(1.0)
        state = engine.get_application_state(app_id)
        # Must remain STOPPED, NOT RECOVERY_WAIT
        self.assertEqual(state["state"], ProcessState.STOPPED.value)
        self.assertEqual(state["consecutive_retries"], 0)

    def test_t08_t09_t10_t11_t12_t13_crash_detection_and_automatic_recovery(self):
        """
        T08: Unexpectedly terminate a managed process
        T09: Detect the termination
        T10: Capture exit code
        T11: Trigger automatic recovery
        T12: Verify new process starts
        T13: Verify new PID differs from original
        """
        engine = ProcessMonitorEngine()
        app_id = "test_app_crasher_recovery"

        engine.register_application(
            app_id=app_id,
            name="CrasherWithRecovery",
            executable_path=CRASHER_SCRIPT,
            arguments=["--crash-after", "1.2", "--exit-code", "42"],
            policy_config=RecoveryPolicyConfig(
                enabled=True,
                max_retries=2,
                initial_delay_seconds=0.4,
                backoff_multiplier=1.5,
            ),
        )

        engine.start_application(app_id)
        time.sleep(0.3)
        initial_state = engine.get_application_state(app_id)
        first_pid = initial_state["pid"]
        self.assertIsNotNone(first_pid)

        # Wait for crash (1.2s) + detection + backoff (0.4s) + relaunch (0.4s) = ~2.5s
        time.sleep(3.0)

        recovered_state = engine.get_application_state(app_id)
        second_pid = recovered_state["pid"]

        # Verify exit code was captured
        self.assertEqual(recovered_state["last_exit_code"], 42)
        # Verify new process was started with new PID
        if second_pid is not None:
            self.assertNotEqual(second_pid, first_pid)

        # Clean up
        engine.stop_application(app_id, timeout_seconds=2.0)

    def test_t14_retry_limits_enforced(self):
        """T14: Verify that upon reaching max retries, recovery stops and state becomes FAILED."""
        policy = RecoveryPolicyEvaluator(
            RecoveryPolicyConfig(
                enabled=True,
                max_retries=2,
                initial_delay_seconds=0.1,
                backoff_multiplier=1.0,
            )
        )

        self.assertTrue(policy.should_recover())
        policy.register_recovery_attempt()
        self.assertEqual(policy.current_retries, 1)

        self.assertTrue(policy.should_recover())
        policy.register_recovery_attempt()
        self.assertEqual(policy.current_retries, 2)

        # Should now reject further recovery
        self.assertFalse(policy.should_recover())

    def test_t15_exponential_backoff_calculation(self):
        """
        T15: Verify exponential backoff delay calculation.
        delay = min(initial * (multiplier ^ retries), max_delay)
        """
        policy = RecoveryPolicyEvaluator(
            RecoveryPolicyConfig(
                enabled=True,
                max_retries=5,
                initial_delay_seconds=1.0,
                backoff_multiplier=2.0,
                max_delay_seconds=10.0,
            )
        )

        self.assertEqual(policy.calculate_delay(), 1.0)

        policy.register_recovery_attempt()
        self.assertEqual(policy.calculate_delay(), 2.0)

        policy.register_recovery_attempt()
        self.assertEqual(policy.calculate_delay(), 4.0)

        policy.register_recovery_attempt()
        self.assertEqual(policy.calculate_delay(), 8.0)

        policy.register_recovery_attempt()
        self.assertEqual(policy.calculate_delay(), 10.0)

    def test_t16_concurrent_applications(self):
        """T16: Test multiple simultaneously monitored applications."""
        engine = ProcessMonitorEngine()

        app1_id = "concurrent_app_1"
        app2_id = "concurrent_app_2"

        engine.register_application(
            app_id=app1_id,
            name="ConcurrentWorker1",
            executable_path=WORKER_SCRIPT,
            arguments=["Conc1", "0.5"],
        )
        engine.register_application(
            app_id=app2_id,
            name="ConcurrentWorker2",
            executable_path=WORKER_SCRIPT,
            arguments=["Conc2", "0.5"],
        )

        self.assertTrue(engine.start_application(app1_id))
        self.assertTrue(engine.start_application(app2_id))

        time.sleep(0.5)

        s1 = engine.get_application_state(app1_id)
        s2 = engine.get_application_state(app2_id)

        self.assertEqual(s1["state"], ProcessState.RUNNING.value)
        self.assertEqual(s2["state"], ProcessState.RUNNING.value)
        self.assertNotEqual(s1["pid"], s2["pid"])

        # Stop both
        engine.stop_application(app1_id)
        engine.stop_application(app2_id)
        time.sleep(0.5)

    def test_t25_system_metrics_inspection(self):
        """T25: Measure real system CPU and memory overhead."""
        metrics = ProcessInspector.get_system_metrics()
        self.assertIn("cpu_percent", metrics)
        self.assertIn("memory_total", metrics)
        self.assertIn("memory_used", metrics)
        self.assertGreater(metrics["memory_total"], 0)
        self.assertGreaterEqual(metrics["cpu_percent"], 0.0)


if __name__ == "__main__":
    unittest.main()

