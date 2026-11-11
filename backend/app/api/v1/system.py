"""
ResQ Web - System & Health Information
"""

import os
import sys
import platform
import psutil
from fastapi import APIRouter

router = APIRouter(prefix="/system", tags=["System & Health"])


@router.get("/health")
def health_check():
    """Returns the operational status of the ResQ Web server and local process supervisor."""
    return {
        "status": "healthy",
        "agent": "online",
        "platform": sys.platform,
        "os": platform.platform(),
        "python_version": platform.python_version(),
        "cpu_count": psutil.cpu_count(logical=True),
    }


@router.get("/info")
def get_system_information():
    """Returns technical environment details, OS properties, and team information."""
    return {
        "product_name": "ResQ Web",
        "full_title": "A Web-Based Process Monitoring and Automatic Recovery System for Windows",
        "version": "1.0.0",
        "operating_system": platform.platform(),
        "architecture": platform.architecture()[0],
        "processor": platform.processor(),
        "academic_context": "B.Tech Computer Science & Engineering - Operating Systems Course Project",
        "team_members": [
            {"name": "Dhairya Desai", "student_id": "202451051"},
            {"name": "Neet Bhimani", "student_id": "202451035"},
            {"name": "Mrugen Bhalodiya", "student_id": "202451031"},
            {"name": "Keval Chorada", "student_id": "202451089"},
            {"name": "Svetal Barad", "student_id": "202452311"},
        ],
    }

