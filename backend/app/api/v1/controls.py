"""
ResQ Web - Process Control Endpoints (Start, Stop, Restart, Reset Counter)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.schemas.controls import ProcessControlResponse
from backend.app.services.application_service import ApplicationService

router = APIRouter(prefix="/applications", tags=["Process Controls"])


@router.post("/{app_id}/start", response_model=ProcessControlResponse)
def start_process(app_id: str, db: Session = Depends(get_db)):
    """Launches the Windows application process."""
    try:
        success = ApplicationService.start_application(db, app_id)
        live = ApplicationService.get_application_with_live_state(db, app_id)
        if not live:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

        return ProcessControlResponse(
            success=success,
            message=f"Process launch initiated for application {live['name']}.",
            app_id=app_id,
            status=live["status"],
            pid=live.get("current_pid"),
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to launch: {e}")


@router.post("/{app_id}/stop", response_model=ProcessControlResponse)
def stop_process(app_id: str, db: Session = Depends(get_db)):
    """Gracefully terminates the Windows application process."""
    try:
        success = ApplicationService.stop_application(db, app_id)
        live = ApplicationService.get_application_with_live_state(db, app_id)
        if not live:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

        return ProcessControlResponse(
            success=success,
            message=f"Stop signal sent to application {live['name']}.",
            app_id=app_id,
            status=live["status"],
            pid=live.get("current_pid"),
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to stop: {e}")


@router.post("/{app_id}/restart", response_model=ProcessControlResponse)
def restart_process(app_id: str, db: Session = Depends(get_db)):
    """Stops and relaunches the application process."""
    try:
        success = ApplicationService.restart_application(db, app_id)
        live = ApplicationService.get_application_with_live_state(db, app_id)
        if not live:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

        return ProcessControlResponse(
            success=success,
            message=f"Restart triggered for application {live['name']}.",
            app_id=app_id,
            status=live["status"],
            pid=live.get("current_pid"),
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to restart: {e}")


@router.post("/{app_id}/reset-counter", response_model=ProcessControlResponse)
def reset_recovery_counter(app_id: str, db: Session = Depends(get_db)):
    """Resets the consecutive retry counter to 0 and clears FAILED state."""
    success = ApplicationService.reset_recovery_counter(db, app_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

    live = ApplicationService.get_application_with_live_state(db, app_id)
    return ProcessControlResponse(
        success=True,
        message="Consecutive retry counter reset to 0.",
        app_id=app_id,
        status=live["status"],
        pid=live.get("current_pid"),
    )

