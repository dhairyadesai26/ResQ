@echo off
REM ============================================================================
REM ResQ Web - Backend Server Startup Script
REM Launches FastAPI Backend & Windows Process Supervisor on 127.0.0.1:8000
REM ============================================================================
title ResQ Web - Backend Server (Port 8000)
cd /d "%~dp0\.."

echo [*] Starting ResQ Web Process Supervisor Backend...
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
pause

