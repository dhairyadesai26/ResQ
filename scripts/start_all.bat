@echo off
REM ============================================================================
REM ResQ Web - Full-Stack Local Startup Launcher
REM Coordinated launcher for Backend (Port 8000) and Frontend (Port 3000)
REM ============================================================================
title ResQ Web - Main Control Launcher
echo ============================================================================
echo   ResQ Web - Process Monitoring and Automatic Recovery System
echo   B.Tech CSE Operating Systems Course Project
echo   Team: Dhairya Desai, Neet Bhimani, Mrugen Bhalodiya, Keval Chorada, Svetal Barad
echo ============================================================================

echo.
echo [*] Launching Backend Process Supervisor (Port 8000)...
start "ResQ Web Backend" cmd /c "%~dp0start_backend.bat"

timeout /t 2 /nobreak >nul

echo [*] Launching Next.js Frontend Dashboard (Port 3000)...
start "ResQ Web Frontend" cmd /c "%~dp0start_frontend.bat"

echo.
echo [*] All services launched!
echo [*] Open your browser at: http://localhost:3000
echo [*] API Documentation:     http://localhost:8000/docs
echo ============================================================================
pause

