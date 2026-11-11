# ============================================================================
# ResQ Web - Coordinated PowerShell Launcher
# ============================================================================
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "  ResQ Web - Process Monitoring & Automatic Recovery for Windows" -ForegroundColor Cyan
Write-Host "  Third-Year B.Tech CSE Operating Systems Course Project" -ForegroundColor Gray
Write-Host "============================================================================" -ForegroundColor Cyan

$root = Split-Path -Parent $PSScriptRoot

Write-Host "`n[*] Starting Backend Supervisor on port 8000..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$root'; python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload"

Start-Sleep -Seconds 2

Write-Host "[*] Starting Next.js Dashboard on port 3000..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$root\frontend'; pnpm run dev"

Write-Host "`n[*] ResQ Web successfully initialized!" -ForegroundColor Cyan
Write-Host "[*] Dashboard: http://localhost:3000" -ForegroundColor Yellow
Write-Host "[*] Swagger API Docs: http://127.0.0.1:8000/docs" -ForegroundColor Yellow

