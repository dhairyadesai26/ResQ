"""
ResQ Web - Metrics Collector Service
Background daemon task collecting real system-wide resource utilization:
- CPU utilization %
- Physical RAM (Used, Available, Total)
- Monitored process count
- Real-time WebSocket metric streaming
"""

import time
import uuid
import threading
from datetime import datetime, timezone
import logging

from backend.app.database.session import SessionLocal
from backend.app.models.system_metric import SystemMetric
from backend.app.websocket.connection_manager import ws_manager
from backend.agent.process_manager.inspector import ProcessInspector
from backend.agent.monitoring.monitor_engine import monitor_engine

logger = logging.getLogger("resq.backend.metrics")


class MetricsCollectorService:
    """Collects and broadcasts system resource usage periodically."""

    def __init__(self, interval_seconds: float = 2.0):
        self.interval = interval_seconds
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def start(self):
        """Starts the background metrics collection daemon."""
        if self._thread and self._thread.is_alive():
            return

        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run_loop,
            name="MetricsCollectorDaemon",
            daemon=True,
        )
        self._thread.start()
        logger.info(f"Metrics collection daemon started (interval: {self.interval}s)")

    def stop(self):
        """Stops the collection daemon."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2.0)
            logger.info("Metrics collection daemon stopped.")

    def _run_loop(self):
        last_db_save = 0.0

        while not self._stop_event.is_set():
            try:
                metrics = ProcessInspector.get_system_metrics()
                apps = monitor_engine.list_applications()
                running_count = sum(1 for a in apps if a.get("state") == "RUNNING")

                payload = {
                    "cpu_percent": metrics["cpu_percent"],
                    "memory_total_bytes": metrics["memory_total"],
                    "memory_used_bytes": metrics["memory_used"],
                    "memory_available_bytes": metrics["memory_available"],
                    "memory_percent": metrics["memory_percent"],
                    "managed_process_count": running_count,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }

                # Broadcast live tick over WebSockets every interval
                ws_manager.broadcast_threadsafe({
                    "type": "system_metrics",
                    "data": payload,
                })

                # Persist to database once every ~6 seconds to prevent excessive SQLite writes
                now = time.time()
                if now - last_db_save >= 6.0:
                    last_db_save = now
                    self._persist_metric(payload)

            except Exception as e:
                logger.debug(f"Error in metrics loop: {e}")

            self._stop_event.wait(timeout=self.interval)

    def _persist_metric(self, payload: dict):
        db = SessionLocal()
        try:
            record = SystemMetric(
                id=str(uuid.uuid4()),
                cpu_percent=payload["cpu_percent"],
                memory_used_bytes=payload["memory_used_bytes"],
                memory_total_bytes=payload["memory_total_bytes"],
                memory_percent=payload["memory_percent"],
                managed_process_count=payload["managed_process_count"],
                timestamp=datetime.now(timezone.utc),
            )
            db.add(record)
            db.commit()
        except Exception:
            db.rollback()
        finally:
            db.close()


metrics_collector = MetricsCollectorService()

