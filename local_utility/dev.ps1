# Outreach.AI Development Quick Start (Windows PowerShell)
# Quickly start development with auto-restart and logging

param(
    [switch]$SkipFrontend,
    [switch]$SkipWorker,
    [switch]$Verbose
)

$ErrorActionPreference = "Stop"

Write-Host "====================================" -ForegroundColor Cyan
Write-Host "  Outreach.AI Dev Mode              " -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

# Get the script directory
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$BACKEND_DIR = Join-Path $SCRIPT_DIR "backend"
$FRONTEND_DIR = Join-Path $SCRIPT_DIR "frontend"

# Create logs directory
$LOGS_DIR = Join-Path $SCRIPT_DIR "logs"
if (-not (Test-Path $LOGS_DIR)) {
    New-Item -ItemType Directory -Path $LOGS_DIR | Out-Null
}

$timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$backendLog = Join-Path $LOGS_DIR "backend_$timestamp.log"
$workerLog = Join-Path $LOGS_DIR "worker_$timestamp.log"
$frontendLog = Join-Path $LOGS_DIR "frontend_$timestamp.log"

Write-Host "Logs will be saved to: $LOGS_DIR" -ForegroundColor Cyan
Write-Host ""

# Validate setup
if (-not (Test-Path (Join-Path $BACKEND_DIR "venv"))) {
    Write-Host "ERROR: Virtual environment not found. Run setup first." -ForegroundColor Red
    exit 1
}

# Start Backend API
Write-Host "[Backend API] Starting on http://localhost:8000" -ForegroundColor Green
$backendCmd = @"
Set-Location '$BACKEND_DIR'
. .\venv\Scripts\Activate.ps1
`$logLevel = if ('$Verbose' -eq 'True') { 'debug' } else { 'info' }
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --log-level `$logLevel 2>&1 | Tee-Object -FilePath '$backendLog'
"@
$backendJob = Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCmd -PassThru

Start-Sleep -Seconds 2

# Start Worker (optional)
if (-not $SkipWorker) {
    Write-Host "[Worker] Starting background job processor" -ForegroundColor Green
    $workerCmd = @"
Set-Location '$BACKEND_DIR'
. .\venv\Scripts\Activate.ps1
python -m app.services.worker 2>&1 | Tee-Object -FilePath '$workerLog'
"@
    $workerJob = Start-Process powershell -ArgumentList "-NoExit", "-Command", $workerCmd -PassThru
    Start-Sleep -Seconds 2
}

# Start Frontend (optional)
if (-not $SkipFrontend) {
    Write-Host "[Frontend] Starting on http://localhost:5173" -ForegroundColor Green
    $frontendCmd = @"
Set-Location '$FRONTEND_DIR'
npm run dev 2>&1 | Tee-Object -FilePath '$frontendLog'
"@
    $frontendJob = Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendCmd -PassThru
}

Write-Host ""
Write-Host "====================================" -ForegroundColor Green
Write-Host "  Development mode active!          " -ForegroundColor Green
Write-Host "====================================" -ForegroundColor Green
Write-Host ""
Write-Host "URLs:" -ForegroundColor Cyan
Write-Host "  Backend:    http://localhost:8000" -ForegroundColor White
Write-Host "  API Docs:   http://localhost:8000/docs" -ForegroundColor White
if (-not $SkipFrontend) {
    Write-Host "  Frontend:   http://localhost:5173" -ForegroundColor White
}
Write-Host ""
Write-Host "Options used:" -ForegroundColor Cyan
if ($SkipFrontend) { Write-Host "  - Frontend: DISABLED" -ForegroundColor Yellow }
if ($SkipWorker) { Write-Host "  - Worker: DISABLED" -ForegroundColor Yellow }
if ($Verbose) { Write-Host "  - Verbose logging: ENABLED" -ForegroundColor Yellow }
Write-Host ""
Write-Host "Logs directory: $LOGS_DIR" -ForegroundColor Cyan
Write-Host ""
Write-Host "Close all windows to stop services" -ForegroundColor Yellow
