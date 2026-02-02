# Outreach.AI Stop Script (Windows PowerShell)
# Stops all running application components

Write-Host "Stopping Outreach.AI services..." -ForegroundColor Yellow

# Stop Node.js processes (Frontend)
$nodeProcesses = Get-Process -Name "node" -ErrorAction SilentlyContinue
if ($nodeProcesses) {
    Write-Host "Stopping Frontend (Node.js)..." -ForegroundColor Cyan
    $nodeProcesses | Stop-Process -Force
    Write-Host "  - Stopped $($nodeProcesses.Count) Node.js process(es)" -ForegroundColor Green
}

# Stop Python processes (Backend & Worker)
$pythonProcesses = Get-Process -Name "python" -ErrorAction SilentlyContinue
if ($pythonProcesses) {
    Write-Host "Stopping Backend & Worker (Python)..." -ForegroundColor Cyan
    $pythonProcesses | Stop-Process -Force
    Write-Host "  - Stopped $($pythonProcesses.Count) Python process(es)" -ForegroundColor Green
}

# Stop uvicorn processes specifically
$uvicornProcesses = Get-Process | Where-Object { $_.ProcessName -like "*uvicorn*" } -ErrorAction SilentlyContinue
if ($uvicornProcesses) {
    Write-Host "Stopping Uvicorn..." -ForegroundColor Cyan
    $uvicornProcesses | Stop-Process -Force
    Write-Host "  - Stopped Uvicorn processes" -ForegroundColor Green
}

Write-Host ""
Write-Host "All Outreach.AI services stopped." -ForegroundColor Green
