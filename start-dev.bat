@echo off
echo Starting both frontend and backend development servers...
echo Backend will run on http://localhost:8000
echo Frontend will run on http://localhost:3000
echo Press Ctrl+C to stop both servers
echo.

cd /d "%~dp0"

REM Start backend in a new window
start "Backend Server" cmd /k "cd /d %~dp0backend && set KMP_DUPLICATE_LIB_OK=TRUE && python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000"

REM Wait a moment for backend to start
timeout /t 3 /nobreak >nul

REM Start frontend in a new window
start "Frontend Server" cmd /k "cd /d %~dp0frontend && pnpm dev"

echo.
echo Both servers are starting in separate windows.
echo Close the command windows to stop the servers.
echo.
pause
