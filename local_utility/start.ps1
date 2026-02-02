# Outreach.AI Startup Script (Windows PowerShell)
# This script starts all components of the application in separate windows

$ErrorActionPreference = "Stop"

Write-Host "====================================" -ForegroundColor Cyan
Write-Host "   Outreach.AI Application Starter  " -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

# Get the script directory and go up one level to project root
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$PROJECT_ROOT = Split-Path -Parent $SCRIPT_DIR
$BACKEND_DIR = Join-Path $PROJECT_ROOT "backend"
$FRONTEND_DIR = Join-Path $PROJECT_ROOT "frontend"

# Check if backend directory exists
if (-not (Test-Path $BACKEND_DIR)) {
    Write-Host "ERROR: Backend directory not found at $BACKEND_DIR" -ForegroundColor Red
    exit 1
}

# Check if frontend directory exists
if (-not (Test-Path $FRONTEND_DIR)) {
    Write-Host "ERROR: Frontend directory not found at $FRONTEND_DIR" -ForegroundColor Red
    exit 1
}

# Check if Python virtual environment exists
$VENV_DIR = Join-Path $BACKEND_DIR "venv"
if (-not (Test-Path $VENV_DIR)) {
    Write-Host "ERROR: Python virtual environment not found at $VENV_DIR" -ForegroundColor Red
    Write-Host "Please run: cd backend && python -m venv venv && .\venv\Scripts\activate && pip install -r requirements.txt" -ForegroundColor Yellow
    exit 1
}

# Check if node_modules exists
$NODE_MODULES = Join-Path $FRONTEND_DIR "node_modules"
if (-not (Test-Path $NODE_MODULES)) {
    Write-Host "WARNING: node_modules not found. Installing frontend dependencies..." -ForegroundColor Yellow
    Set-Location $FRONTEND_DIR
    npm install
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to install frontend dependencies" -ForegroundColor Red
        exit 1
    }
    Set-Location $SCRIPT_DIR
}

# Check if backend .env exists
$BACKEND_ENV = Join-Path $BACKEND_DIR ".env"
if (-not (Test-Path $BACKEND_ENV)) {
    Write-Host "WARNING: Backend .env file not found at $BACKEND_ENV" -ForegroundColor Yellow
    Write-Host "Please create a .env file with required configuration" -ForegroundColor Yellow
    $response = Read-Host "Continue anyway? (y/N)"
    if ($response -ne "y" -and $response -ne "Y") {
        exit 1
    }
}

Write-Host "Starting application components..." -ForegroundColor Green
Write-Host ""

# Start Backend API Server
Write-Host "[1/3] Starting Backend API Server..." -ForegroundColor Yellow
$backendCmd = @"
Set-Location '$BACKEND_DIR'
. .\venv\Scripts\Activate.ps1
Write-Host 'Backend API Server Starting...' -ForegroundColor Green
Write-Host 'API will be available at: http://localhost:8000' -ForegroundColor Cyan
Write-Host 'API Docs available at: http://localhost:8000/docs' -ForegroundColor Cyan
Write-Host ''
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
"@
Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCmd

Start-Sleep -Seconds 2

# Start Background Worker
Write-Host "[2/3] Starting Background Worker..." -ForegroundColor Yellow
$workerCmd = @"
Set-Location '$BACKEND_DIR'
. .\venv\Scripts\Activate.ps1
Write-Host 'Background Worker Starting...' -ForegroundColor Green
Write-Host 'Processing scheduled email jobs...' -ForegroundColor Cyan
Write-Host ''
python -m app.services.worker
"@
Start-Process powershell -ArgumentList "-NoExit", "-Command", $workerCmd

Start-Sleep -Seconds 2

# Start Frontend Development Server
Write-Host "[3/3] Starting Frontend Development Server..." -ForegroundColor Yellow
$frontendCmd = @"
Set-Location '$FRONTEND_DIR'
Write-Host 'Frontend Development Server Starting...' -ForegroundColor Green
Write-Host 'Frontend will be available at: http://localhost:5173' -ForegroundColor Cyan
Write-Host ''
npm run dev
"@
Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendCmd

Write-Host ""
Write-Host "====================================" -ForegroundColor Green
Write-Host "   All components started!          " -ForegroundColor Green
Write-Host "====================================" -ForegroundColor Green
Write-Host ""
Write-Host "Services:" -ForegroundColor Cyan
Write-Host "  - Backend API:  http://localhost:8000" -ForegroundColor White
Write-Host "  - API Docs:     http://localhost:8000/docs" -ForegroundColor White
Write-Host "  - Frontend:     http://localhost:5173" -ForegroundColor White
Write-Host "  - Worker:       Running in background" -ForegroundColor White
Write-Host ""
Write-Host "Press any key to stop all services and exit..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

# Cleanup: Kill all spawned processes
Write-Host ""
Write-Host "Stopping all services..." -ForegroundColor Yellow
Get-Process | Where-Object { $_.ProcessName -eq "powershell" -and $_.Id -ne $PID } | Stop-Process -Force
Get-Process | Where-Object { $_.ProcessName -eq "node" } | Stop-Process -Force
Get-Process | Where-Object { $_.ProcessName -eq "python" } | Stop-Process -Force

Write-Host "All services stopped." -ForegroundColor Green
