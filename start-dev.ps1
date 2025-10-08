# PowerShell script to start both frontend and backend development servers
Write-Host "Starting both frontend and backend development servers..." -ForegroundColor Green
Write-Host "Backend will run on http://localhost:8000" -ForegroundColor Yellow
Write-Host "Frontend will run on http://localhost:3000" -ForegroundColor Yellow
Write-Host "Press Ctrl+C to stop both servers" -ForegroundColor Red
Write-Host ""

# Get the script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Start backend job
Write-Host "Starting backend server..." -ForegroundColor Cyan
$BackendJob = Start-Job -ScriptBlock {
    param($Path)
    Set-Location $Path
    $env:KMP_DUPLICATE_LIB_OK = "TRUE"
    python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
} -ArgumentList "$ScriptDir\backend"

# Wait a moment for backend to start
Start-Sleep -Seconds 3

# Start frontend job
Write-Host "Starting frontend server..." -ForegroundColor Cyan
$FrontendJob = Start-Job -ScriptBlock {
    param($Path)
    Set-Location $Path
    pnpm dev
} -ArgumentList "$ScriptDir\frontend"

Write-Host ""
Write-Host "Both servers are running in background jobs." -ForegroundColor Green
Write-Host "Backend Job ID: $($BackendJob.Id)" -ForegroundColor Gray
Write-Host "Frontend Job ID: $($FrontendJob.Id)" -ForegroundColor Gray
Write-Host ""
Write-Host "To stop the servers, press Ctrl+C or close this window." -ForegroundColor Red

try {
    # Wait for user to stop
    while ($true) {
        Start-Sleep -Seconds 1
        
        # Check if jobs are still running
        if ($BackendJob.State -ne "Running" -and $FrontendJob.State -ne "Running") {
            Write-Host "Both servers have stopped." -ForegroundColor Yellow
            break
        }
    }
} finally {
    # Clean up jobs
    Write-Host "Stopping servers..." -ForegroundColor Yellow
    Stop-Job $BackendJob -ErrorAction SilentlyContinue
    Stop-Job $FrontendJob -ErrorAction SilentlyContinue
    Remove-Job $BackendJob -ErrorAction SilentlyContinue
    Remove-Job $FrontendJob -ErrorAction SilentlyContinue
    Write-Host "Servers stopped." -ForegroundColor Green
}
