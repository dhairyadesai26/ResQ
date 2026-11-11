"""
ResQ Web - Backend API Service & Route Handler Integration Tests
Tests REST endpoints, validation, process control, events, and metrics.
Validates Test Cases:
T01 - Register valid executable via API
T02 - Reject invalid executable via API (400)
T03/T04/T05 - Launch application via API and verify live PID and RUNNING state
T06/T07 - Graceful stop via API and verify no recovery
T21 - Malformed requests rejected by Pydantic validation
T22 - Inaccessible paths rejected
"""

import os
import sys
import time
import unittest
from pydantic import ValidationError

# Ensure workspace root in path
WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

from backend.app.database.session import SessionLocal, engine
from backend.app.database.base import Base
import backend.app.models
from backend.app.schemas.application import ApplicationCreate
from backend.app.api.v1.applications import (
    register_application,
    list_applications,
    get_application,
    delete_application,
)
from backend.app.api.v1.controls import (
    start_process,
    stop_process,
    restart_process,
    reset_recovery_counter,
)
from backend.app.api.v1.events import get_events
from backend.app.api.v1.metrics import get_current_system_metrics
from backend.app.api.v1.analytics import get_analytics_summary
from backend.app.api.v1.system import health_check, get_system_information
from fastapi import HTTPException

WORKER_SCRIPT = os.path.join(WORKSPACE_ROOT, "test_apps", "worker_app.py")


class TestBackendAPIIntegration(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)

    def setUp(self):
        self.db = SessionLocal()

    def tearDown(self):
        self.db.close()

    def test_health_and_system_info(self):
        """Verify health check and system information routes."""
        health = health_check()
        self.assertEqual(health["status"], "healthy")
        self.assertEqual(health["agent"], "online")
        self.assertEqual(health["platform"], sys.platform)

        info = get_system_information()
        self.assertEqual(info["product_name"], "ResQ Web")
        self.assertEqual(len(info["team_members"]), 5)

    def test_t01_t02_register_valid_and_invalid(self):
        """T01: Register valid executable; T02: Reject invalid path."""
        # 1. Valid registration
        valid_payload = ApplicationCreate(
            name="APIWorkerTest",
            executable_path=WORKER_SCRIPT,
            arguments="APIWorker 0.5",
            auto_recovery=True,
            max_retries=3,
            retry_delay_seconds=1.0,
            backoff_multiplier=2.0,
            max_delay_seconds=10.0,
        )
        created = register_application(payload=valid_payload, db=self.db)
        app_id = created["id"]
        self.assertEqual(created["name"], "APIWorkerTest")
        self.assertEqual(created["status"], "STOPPED")

        # 2. Invalid path (T02 / T22)
        invalid_payload = ApplicationCreate(
            name="BadPathTest",
            executable_path="C:\\non_existent_binary_file_abc.exe",
        )
        with self.assertRaises(HTTPException) as ctx:
            register_application(payload=invalid_payload, db=self.db)
        self.assertEqual(ctx.exception.status_code, 400)

        # Cleanup
        delete_application(app_id=app_id, db=self.db)

    def test_t03_t04_t05_t06_process_lifecycle_via_api(self):
        """Tests full lifecycle: Register -> Start -> Get Details -> Stop -> Clean."""
        payload = ApplicationCreate(
            name="APILifecycleTest",
            executable_path=WORKER_SCRIPT,
            arguments="APILifecycle 0.5",
            auto_recovery=True,
            max_retries=2,
            retry_delay_seconds=0.5,
        )
        app = register_application(payload=payload, db=self.db)
        app_id = app["id"]

        try:
            # Start process
            start_res = start_process(app_id=app_id, db=self.db)
            self.assertTrue(start_res.success)

            # Allow brief time for spawn and metrics collection
            time.sleep(0.5)

            # Query details
            detail = get_application(app_id=app_id, db=self.db)
            self.assertEqual(detail["status"], "RUNNING")
            self.assertIsNotNone(detail["current_pid"])
            self.assertGreater(detail["current_pid"], 0)

            # Stop process (T06 / T07)
            stop_res = stop_process(app_id=app_id, db=self.db)
            self.assertTrue(stop_res.success)

            time.sleep(0.5)
            stopped_detail = get_application(app_id=app_id, db=self.db)
            self.assertEqual(stopped_detail["status"], "STOPPED")

            # Reset counter
            reset_res = reset_recovery_counter(app_id=app_id, db=self.db)
            self.assertTrue(reset_res.success)

        finally:
            delete_application(app_id=app_id, db=self.db)

    def test_t21_malformed_request_validation(self):
        """T21: Validates Pydantic schema validation rejects malformed input."""
        with self.assertRaises(ValidationError):
            ApplicationCreate(
                name="",  # min_length=1 violation
                executable_path=WORKER_SCRIPT,
            )

        with self.assertRaises(ValidationError):
            ApplicationCreate(
                name="ValidName",
                executable_path=WORKER_SCRIPT,
                max_retries=-5,  # ge=0 violation
            )

    def test_metrics_events_and_analytics_queries(self):
        """Queries events, current system metrics, and analytics summary."""
        events = get_events(limit=10, offset=0, db=self.db)
        self.assertIsInstance(events, list)

        metrics = get_current_system_metrics()
        self.assertIn("cpu_percent", metrics)
        self.assertIn("memory_used", metrics)

        summary = get_analytics_summary(db=self.db)
        self.assertGreaterEqual(summary.total_applications, 0)
        self.assertGreaterEqual(summary.recovery_success_rate, 0.0)


if __name__ == "__main__":
    unittest.main()
