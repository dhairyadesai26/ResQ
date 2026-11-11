@echo off
REM ============================================================================
REM ResQ Web - Frontend Next.js Startup Script
REM Launches Next.js Dashboard on http://localhost:3000
REM ============================================================================
title ResQ Web - Next.js Frontend (Port 3000)
cd /d "%~dp0\..\frontend"

echo [*] Starting ResQ Web Next.js Dashboard...
pnpm run dev
pause

