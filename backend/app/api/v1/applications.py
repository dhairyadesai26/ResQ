"""
ResQ Web - Application REST API Endpoints
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.schemas.application import ApplicationCreate, ApplicationUpdate, ApplicationResponse
from backend.app.services.application_service import ApplicationService
from backend.app.models.process_run import ProcessRun
from agent.security.validator import SecurityValidationError

router = APIRouter(prefix="/applications", tags=["Applications"])


@router.get("", response_model=List[ApplicationResponse])
def list_applications(db: Session = Depends(get_db)):
    """Retrieves all registered applications with their live running state and metrics."""
    return ApplicationService.list_applications_with_live_states(db)


@router.post("", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
def register_application(payload: ApplicationCreate, db: Session = Depends(get_db)):
    """Registers a new approved application for supervision."""
    try:
        app = ApplicationService.create_application(db, payload)
        live = ApplicationService.get_application_with_live_state(db, app.id)
        return live
    except SecurityValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{app_id}", response_model=ApplicationResponse)
def get_application(app_id: str, db: Session = Depends(get_db)):
    """Retrieves a single application by ID with live metrics."""
    app_data = ApplicationService.get_application_with_live_state(db, app_id)
    if not app_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    return app_data


@router.put("/{app_id}", response_model=ApplicationResponse)
def update_application(app_id: str, payload: ApplicationUpdate, db: Session = Depends(get_db)):
    """Updates application configuration or recovery policy."""
    try:
        app = ApplicationService.update_application(db, app_id, payload)
        if not app:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
        return ApplicationService.get_application_with_live_state(db, app_id)
    except SecurityValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{app_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_application(app_id: str, db: Session = Depends(get_db)):
    """Stops the application process and removes its registration."""
    success = ApplicationService.delete_application(db, app_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    return None


@router.get("/{app_id}/runs")
def get_application_runs(app_id: str, db: Session = Depends(get_db)):
    """Returns historical process execution runs for this application."""
    runs = (
        db.query(ProcessRun)
        .filter(ProcessRun.app_id == app_id)
        .order_by(ProcessRun.start_time.desc())
        .limit(50)
        .all()
    )
    return [
        {
            "id": r.id,
            "pid": r.pid,
            "start_time": r.start_time.isoformat(),
            "end_time": r.end_time.isoformat() if r.end_time else None,
            "duration_seconds": r.duration_seconds,
            "exit_code": r.exit_code,
            "termination_type": r.termination_type,
        }
        for r in runs
    ]

