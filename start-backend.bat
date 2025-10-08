@echo off
echo Starting backend development server...
echo Backend will run on http://localhost:8000
echo Press Ctrl+C to stop the server
echo.

cd /d "%~dp0backend"
set KMP_DUPLICATE_LIB_OK=TRUE
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

pause
