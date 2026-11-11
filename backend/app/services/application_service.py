"""
ResQ Web - Application Service
Coordinates database operations with the local Windows process supervisor.
Guarantees bidirectional synchronization between persisted configurations
and active OS processes.
"""

import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.app.database.session import SessionLocal
from backend.app.models.application import Application
from backend.app.models.process_run import ProcessRun
from backend.app.models.recovery_attempt import RecoveryAttempt
from backend.app.schemas.application import ApplicationCreate, ApplicationUpdate
from backend.app.websocket.connection_manager import ws_manager
from agent.monitoring.monitor_engine import monitor_engine
from agent.recovery.policy_evaluator import RecoveryPolicyConfig
from agent.communication.event_emitter import event_bus, SupervisorEvent, EventType
from agent.security.validator import ProcessSecurityValidator


class ApplicationService:
    """Manages application persistence and synchronization with OS supervisor."""

    @classmethod
    def load_persisted_applications(cls):
        """Called on system startup to sync database records into the supervisor engine."""
        db: Session = SessionLocal()
        try:
            apps = db.query(Application).all()
            for app in apps:
                policy = RecoveryPolicyConfig(
                    enabled=app.auto_recovery,
                    max_retries=app.max_retries,
                    initial_delay_seconds=app.retry_delay_seconds,
                    backoff_multiplier=app.backoff_multiplier,
                    max_delay_seconds=app.max_delay_seconds,
                )
                monitor_engine.register_application(
                    app_id=app.id,
                    name=app.name,
                    executable_path=app.executable_path,
                    arguments=app.arguments,
                    working_dir=app.working_dir,
                    policy_config=policy,
                )
                # Reset stale RUNNING states in DB to STOPPED on fresh server startup
                if app.status in ("RUNNING", "STARTING", "RECOVERY_WAIT", "STOPPING"):
                    app.status = "STOPPED"
                    app.current_pid = None
            db.commit()
        except Exception as e:
            db.rollback()
        finally:
            db.close()

    @classmethod
    def create_application(cls, db: Session, payload: ApplicationCreate) -> Application:
        """Registers and persists a new application after strict security validation."""
        # Validate path and working directory
        safe_exe = ProcessSecurityValidator.sanitize_path(payload.executable_path)
        safe_workdir = (
            ProcessSecurityValidator.sanitize_working_directory(payload.working_dir, safe_exe)
            if payload.working_dir
            else None
        )

        app_id = str(uuid.uuid4())
        policy = RecoveryPolicyConfig(
            enabled=payload.auto_recovery,
            max_retries=payload.max_retries,
            initial_delay_seconds=payload.retry_delay_seconds,
            backoff_multiplier=payload.backoff_multiplier,
            max_delay_seconds=payload.max_delay_seconds,
        )

        # Register in supervisor engine
        monitor_engine.register_application(
            app_id=app_id,
            name=payload.name,
            executable_path=safe_exe,
            arguments=payload.arguments,
            working_dir=safe_workdir,
            policy_config=policy,
        )

        db_app = Application(
            id=app_id,
            name=payload.name,
            executable_path=safe_exe,
            arguments=payload.arguments or "",
            working_dir=safe_workdir,
            auto_recovery=payload.auto_recovery,
            max_retries=payload.max_retries,
            retry_delay_seconds=payload.retry_delay_seconds,
            backoff_multiplier=payload.backoff_multiplier,
            max_delay_seconds=payload.max_delay_seconds,
            status="STOPPED",
            consecutive_retries=0,
            total_recoveries=0,
        )
        db.add(db_app)
        db.commit()
        db.refresh(db_app)

        cls._broadcast_app_update(app_id)
        return db_app

    @classmethod
    def update_application(cls, db: Session, app_id: str, payload: ApplicationUpdate) -> Optional[Application]:
        """Updates application configuration and recovery policy."""
        db_app = db.query(Application).filter(Application.id == app_id).first()
        if not db_app:
            return None

        update_data = payload.model_dump(exclude_unset=True)
        if "executable_path" in update_data:
            update_data["executable_path"] = ProcessSecurityValidator.sanitize_path(update_data["executable_path"])

        for key, value in update_data.items():
            setattr(db_app, key, value)

        db.commit()
        db.refresh(db_app)

        # Update in supervisor engine
        policy = RecoveryPolicyConfig(
            enabled=db_app.auto_recovery,
            max_retries=db_app.max_retries,
            initial_delay_seconds=db_app.retry_delay_seconds,
            backoff_multiplier=db_app.backoff_multiplier,
            max_delay_seconds=db_app.max_delay_seconds,
        )
        monitor_engine.register_application(
            app_id=app_id,
            name=db_app.name,
            executable_path=db_app.executable_path,
            arguments=db_app.arguments,
            working_dir=db_app.working_dir,
            policy_config=policy,
        )

        cls._broadcast_app_update(app_id)
        return db_app

    @classmethod
    def delete_application(cls, db: Session, app_id: str) -> bool:
        """Stops application and deletes registration from database."""
        db_app = db.query(Application).filter(Application.id == app_id).first()
        if not db_app:
            return False

        # Unregister and stop in supervisor
        monitor_engine.unregister_application(app_id)

        db.delete(db_app)
        db.commit()

        ws_manager.broadcast_threadsafe({
            "type": "application_deleted",
            "app_id": app_id,
        })
        return True

    @classmethod
    def start_application(cls, db: Session, app_id: str) -> bool:
        """Launches process via supervisor."""
        db_app = db.query(Application).filter(Application.id == app_id).first()
        if not db_app:
            return False

        success = monitor_engine.start_application(app_id)
        if success:
            cls.sync_runtime_state_to_db(app_id)
        return success

    @classmethod
    def stop_application(cls, db: Session, app_id: str) -> bool:
        """Gracefully stops process via supervisor."""
        db_app = db.query(Application).filter(Application.id == app_id).first()
        if not db_app:
            return False

        success = monitor_engine.stop_application(app_id)
        cls.sync_runtime_state_to_db(app_id)
        return success

    @classmethod
    def restart_application(cls, db: Session, app_id: str) -> bool:
        """Restarts process via supervisor."""
        db_app = db.query(Application).filter(Application.id == app_id).first()
        if not db_app:
            return False

        success = monitor_engine.restart_application(app_id)
        cls.sync_runtime_state_to_db(app_id)
        return success

    @classmethod
    def reset_recovery_counter(cls, db: Session, app_id: str) -> bool:
        """Resets retry counter to 0."""
        db_app = db.query(Application).filter(Application.id == app_id).first()
        if not db_app:
            return False

        monitor_engine.reset_recovery_counter(app_id)
        db_app.consecutive_retries = 0
        if db_app.status == "FAILED":
            db_app.status = "STOPPED"
        db.commit()

        cls._broadcast_app_update(app_id)
        return True

    @classmethod
    def get_application_with_live_state(cls, db: Session, app_id: str) -> Optional[Dict[str, Any]]:
        """Returns database metadata merged with real-time supervisor metrics."""
        db_app = db.query(Application).filter(Application.id == app_id).first()
        if not db_app:
            return None

        live_state = {}
        try:
            live_state = monitor_engine.get_application_state(app_id)
        except Exception:
            pass

        return cls._merge_app_dict(db_app, live_state)

    @classmethod
    def list_applications_with_live_states(cls, db: Session) -> List[Dict[str, Any]]:
        """Returns all applications with real-time statuses."""
        apps = db.query(Application).order_by(Application.name).all()
        result = []
        for a in apps:
            live_state = {}
            try:
                live_state = monitor_engine.get_application_state(a.id)
            except Exception:
                pass
            result.append(cls._merge_app_dict(a, live_state))
        return result

    @classmethod
    def sync_runtime_state_to_db(cls, app_id: str):
        """Syncs the supervisor's live memory state into SQLite."""
        db: Session = SessionLocal()
        try:
            db_app = db.query(Application).filter(Application.id == app_id).first()
            if not db_app:
                return

            live = monitor_engine.get_application_state(app_id)
            db_app.status = live.get("state", "STOPPED")
            db_app.current_pid = live.get("pid")
            db_app.consecutive_retries = live.get("consecutive_retries", 0)
            db_app.total_recoveries = live.get("total_recoveries", 0)
            if live.get("last_exit_code") is not None:
                db_app.last_exit_code = live.get("last_exit_code")
            if live.get("last_crash_timestamp"):
                db_app.last_crash_timestamp = datetime.fromtimestamp(
                    live["last_crash_timestamp"], timezone.utc
                )

            db.commit()
            cls._broadcast_app_update(app_id)
        except Exception as e:
            db.rollback()
        finally:
            db.close()

    @classmethod
    def _merge_app_dict(cls, db_app: Application, live: Dict[str, Any]) -> Dict[str, Any]:
        """Combines database model and live inspector metrics."""
        status = live.get("state", db_app.status)
        pid = live.get("pid") if status == "RUNNING" else None

        return {
            "id": db_app.id,
            "name": db_app.name,
            "executable_path": db_app.executable_path,
            "arguments": db_app.arguments,
            "working_dir": db_app.working_dir,
            "auto_recovery": db_app.auto_recovery,
            "max_retries": db_app.max_retries,
            "retry_delay_seconds": db_app.retry_delay_seconds,
            "backoff_multiplier": db_app.backoff_multiplier,
            "max_delay_seconds": db_app.max_delay_seconds,
            "status": status,
            "current_pid": pid,
            "uptime_seconds": live.get("uptime_seconds", 0.0),
            "cpu_percent": live.get("cpu_percent", 0.0),
            "memory_rss_bytes": live.get("memory_rss_bytes", 0),
            "memory_percent": live.get("memory_percent", 0.0),
            "num_threads": live.get("num_threads", 0),
            "num_handles": live.get("num_handles", 0),
            "consecutive_retries": live.get("consecutive_retries", db_app.consecutive_retries),
            "total_recoveries": live.get("total_recoveries", db_app.total_recoveries),
            "last_exit_code": live.get("last_exit_code", db_app.last_exit_code),
            "last_crash_timestamp": db_app.last_crash_timestamp,
            "created_at": db_app.created_at,
            "updated_at": db_app.updated_at,
        }

    @classmethod
    def _broadcast_app_update(cls, app_id: str):
        """Broadcasts single application state update to WebSocket clients."""
        db: Session = SessionLocal()
        try:
            merged = cls.get_application_with_live_state(db, app_id)
            if merged:
                ws_manager.broadcast_threadsafe({
                    "type": "application_updated",
                    "data": merged,
                })
        finally:
            db.close()


def _handle_supervisor_lifecycle_event(event: SupervisorEvent):
    """Listens to supervisor events and triggers DB state sync and run tracking."""
    if event.event_type in (
        EventType.PROCESS_LAUNCHED,
        EventType.PROCESS_STOPPED_EXPECTED,
        EventType.PROCESS_CRASHED_UNEXPECTED,
        EventType.RECOVERY_SUCCEEDED,
        EventType.RECOVERY_FAILED,
        EventType.RETRY_LIMIT_REACHED,
        EventType.STATE_CHANGED,
    ):
        ApplicationService.sync_runtime_state_to_db(event.app_id)

    # Track process run history
    if event.event_type == EventType.PROCESS_LAUNCHED and event.pid:
        db: Session = SessionLocal()
        try:
            run = ProcessRun(
                id=str(uuid.uuid4()),
                app_id=event.app_id,
                pid=event.pid,
                start_time=datetime.now(timezone.utc),
                termination_type="ACTIVE",
            )
            db.add(run)
            db.commit()
        except Exception:
            db.rollback()
        finally:
            db.close()

    elif event.event_type in (EventType.PROCESS_STOPPED_EXPECTED, EventType.PROCESS_CRASHED_UNEXPECTED):
        db = SessionLocal()
        try:
            run = (
                db.query(ProcessRun)
                .filter(ProcessRun.app_id == event.app_id, ProcessRun.termination_type == "ACTIVE")
                .order_by(desc(ProcessRun.start_time))
                .first()
            )
            if run:
                run.end_time = datetime.now(timezone.utc)
                run.exit_code = event.exit_code
                run.termination_type = (
                    "EXPECTED" if event.event_type == EventType.PROCESS_STOPPED_EXPECTED else "UNEXPECTED"
                )
                run.duration_seconds = (run.end_time - run.start_time).total_seconds()
                db.commit()
        except Exception:
            db.rollback()
        finally:
            db.close()

    # Track recovery attempts
    elif event.event_type in (EventType.RECOVERY_SCHEDULED, EventType.RECOVERY_SUCCEEDED, EventType.RECOVERY_FAILED):
        db = SessionLocal()
        try:
            attempt_num = event.details.get("attempt", 1)
            backoff_delay = event.details.get("delay_seconds", 0.0)
            status = "SCHEDULED"
            if event.event_type == EventType.RECOVERY_SUCCEEDED:
                status = "SUCCEEDED"
            elif event.event_type == EventType.RECOVERY_FAILED:
                status = "FAILED"

            rec = RecoveryAttempt(
                id=str(uuid.uuid4()),
                app_id=event.app_id,
                attempt_number=attempt_num,
                backoff_delay_seconds=backoff_delay,
                status=status,
                new_pid=event.pid,
                error_message=event.details.get("error"),
            )
            db.add(rec)
            db.commit()
        except Exception:
            db.rollback()
        finally:
            db.close()


event_bus.subscribe(_handle_supervisor_lifecycle_event)
