"""
ResQ Web - Recovery Management REST Endpoints
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.schemas.recovery import RecoveryPolicyUpdate, RecoveryAttemptResponse
from backend.app.models.recovery_attempt import RecoveryAttempt
from backend.app.services.application_service import ApplicationService

router = APIRouter(prefix="/recovery", tags=["Recovery Management"])


@router.put("/applications/{app_id}/policy")
def update_recovery_policy(
    app_id: str,
    payload: RecoveryPolicyUpdate,
    db: Session = Depends(get_db),
):
    """Updates recovery parameters (max retries, backoff multiplier, retry delay) for an application."""
    app = ApplicationService.update_application(db, app_id, payload)
    if not app:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    return ApplicationService.get_application_with_live_state(db, app_id)


@router.get("/attempts", response_model=List[RecoveryAttemptResponse])
def list_recovery_attempts(
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """Lists historical recovery attempts across all applications."""
    attempts = (
        db.query(RecoveryAttempt)
        .order_by(RecoveryAttempt.created_at.desc())
        .limit(limit)
        .all()
    )
    return attempts

