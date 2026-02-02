# Outreach.AI Simple Startup Script (Windows PowerShell)
# Starts all components in a single terminal with split panes (requires Windows Terminal)

$ErrorActionPreference = "Stop"

Write-Host "====================================" -ForegroundColor Cyan
Write-Host "  Outreach.AI Simple Starter        " -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

# Get the script directory
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$BACKEND_DIR = Join-Path $SCRIPT_DIR "backend"
$FRONTEND_DIR = Join-Path $SCRIPT_DIR "frontend"

# Validation checks
if (-not (Test-Path $BACKEND_DIR)) {
    Write-Host "ERROR: Backend directory not found" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path (Join-Path $BACKEND_DIR "venv"))) {
    Write-Host "ERROR: Python virtual environment not found" -ForegroundColor Red
    Write-Host "Run: cd backend && python -m venv venv && .\venv\Scripts\activate && pip install -r requirements.txt" -ForegroundColor Yellow
    exit 1
}

Write-Host "Starting all services in background..." -ForegroundColor Green
Write-Host ""

# Start backend in background
Write-Host "[1/3] Starting Backend API..." -ForegroundColor Yellow
Set-Location $BACKEND_DIR
Start-Process powershell -ArgumentList "-NoExit", "-Command", ". .\venv\Scripts\Activate.ps1; uvicorn app.main:app --reload --host 0.0.0.0 --port 8000" -WindowStyle Minimized

# Start worker in background
Write-Host "[2/3] Starting Background Worker..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", ". .\venv\Scripts\Activate.ps1; python -m app.services.worker" -WindowStyle Minimized

# Wait a moment for backend to start
Start-Sleep -Seconds 3

# Start frontend in foreground (this terminal)
Write-Host "[3/3] Starting Frontend..." -ForegroundColor Yellow
Set-Location $FRONTEND_DIR
Write-Host ""
Write-Host "====================================" -ForegroundColor Green
Write-Host "Services running:" -ForegroundColor Cyan
Write-Host "  Backend:  http://localhost:8000" -ForegroundColor White
Write-Host "  Docs:     http://localhost:8000/docs" -ForegroundColor White
Write-Host "  Frontend: http://localhost:5173" -ForegroundColor White
Write-Host "====================================" -ForegroundColor Green
Write-Host ""
npm run dev
