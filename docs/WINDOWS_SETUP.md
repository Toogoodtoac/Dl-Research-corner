# Windows Development Setup

This guide is for Windows users who want to run the development environment.

## Prerequisites

1. **Python 3.8+** - Install from [python.org](https://www.python.org/downloads/)
2. **Node.js 18+** - Install from [nodejs.org](https://nodejs.org/)
3. **pnpm** - Install with: `npm install -g pnpm`

## Quick Start

### Option 1: Batch Scripts (Recommended for beginners)

1. **Start both frontend and backend:**
   ```cmd
   start-dev.bat
   ```
   This will open two separate command windows - one for backend and one for frontend.

2. **Start only backend:**
   ```cmd
   start-backend.bat
   ```

### Option 2: PowerShell Script (More advanced)

1. **Start both frontend and backend:**
   ```powershell
   .\start-dev.ps1
   ```
   This runs both servers in background jobs and shows status in one window.

## What Each Script Does

### `start-dev.bat`
- Opens two separate command windows
- Backend runs on http://localhost:8000
- Frontend runs on http://localhost:3000
- Close the windows to stop the servers

### `start-dev.ps1`
- Runs both servers in background PowerShell jobs
- Shows status in one window
- Press Ctrl+C to stop both servers
- More reliable for development

### `start-backend.bat`
- Starts only the backend server
- Useful for backend-only development

## Environment Variables

The scripts automatically set `KMP_DUPLICATE_LIB_OK=TRUE` which is required for the backend to run properly on Windows.

## Troubleshooting

1. **"python is not recognized"** - Make sure Python is installed and added to PATH
2. **"pnpm is not recognized"** - Install pnpm with `npm install -g pnpm`
3. **Port already in use** - Make sure no other services are using ports 3000 or 8000
4. **PowerShell execution policy** - If PowerShell script doesn't run, execute:
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

## Manual Commands (if scripts don't work)

### Backend only:
```cmd
cd backend
set KMP_DUPLICATE_LIB_OK=TRUE
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend only:
```cmd
cd frontend
pnpm dev
```

## URLs

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **Backend Docs:** http://localhost:8000/docs
