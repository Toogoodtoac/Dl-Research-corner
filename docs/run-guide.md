# MM-Data Intelligent Agent - Run Guide

This guide will help you run the complete MM-Data Intelligent Agent system in two modes: **local development** (no Docker) and **Docker Compose**.

## Prerequisites

Before starting, ensure you have the following installed:

- **Node.js** ≥ 18.0.0 and **pnpm** ≥ 8.0.0
- **Python** ≥ 3.11 and **pip**
- **Git** with submodule support
- **(Optional)** NVIDIA GPU + CUDA for `MODEL_DEVICE=cuda`

## Initial Setup

### 1. Clone and Initialize Submodules

```bash
# Clone the repository
git clone <your-repo-url>
cd mm-data-intelligent-agent

# Initialize and update submodules (CLIP, LongCLIP, CLIP2Video)
git submodule update --init --recursive
```

### 2. Verify Repository Structure

```bash
# Check the structure
tree -L 2 -I 'node_modules|__pycache__|.git'
```

You should see:

```
mm-data-intelligent-agent/
├── apps/
├── backend/
├── frontend/
├── infra/
├── ml/
├── packages/
├── support_models/
└── docs/
```

---

## Mode 1: Run Locally (No Docker)

### Step 1: Backend Environment & Installation

#### 1.1. Set up Backend Environment

```bash
# Copy environment template
cp backend/env.example backend/.env

# Edit the environment file
nano backend/.env  # or use your preferred editor
```

#### 1.2. Critical Environment Variables

**⚠️ IMPORTANT: Set these variables in `backend/.env`:**

```bash
# Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=true

# Model Device (CRITICAL for performance)
MODEL_DEVICE=cpu          # Use 'cuda' if you have NVIDIA GPU + CUDA
LAZY_LOAD_MODELS=true     # Models load only when first requested

# Model Paths (CRITICAL for ML functionality)
SUPPORT_MODELS_DIR=../support_models
CLIP_MODEL_NAME=ViT-B/32
LONGCLIP_CHECKPOINT=../support_models/Long-CLIP/checkpoints/longclip-B.pt
CLIP2VIDEO_CHECKPOINT=../support_models/CLIP2Video/checkpoints

# FAISS Index Paths (CRITICAL for search)
FAISS_CLIP_PATH=../dict/faiss_clip_vitb32.bin
FAISS_LONGCLIP_PATH=../dict/faiss_longclip.bin
FAISS_CLIP2VIDEO_PATH=../dict/faiss_clip2video.bin
ID2IMG_JSON_PATH=../dict/id2img.json

# Data Paths
DATA_ROOT=../data
FEATURES_DIR=../data/features

# Cache Configuration
REDIS_URL=redis://localhost:6379
CACHE_TTL=3600
```

#### 1.3. Install Backend Dependencies

```bash
# Create and activate virtual environment
python -m venv .venv

# Activate virtual environment
# On macOS/Linux:
source .venv/bin/activate
# On Windows:
# .venv\Scripts\activate

# Install Python dependencies
pip install -r backend/requirements.txt

# (Optional) Install ML model dependencies if needed
# pip install -e support_models/CLIP
# pip install -e support_models/CLIP2Video
# pip install -e support_models/Long-CLIP
```

#### 1.4. Start Backend Server

```bash
# Navigate to backend directory
cd backend

# Start FastAPI server with auto-reload
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Expected Output:**

```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using WatchFiles
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

#### 1.5. Test Backend Health

```bash
# In a new terminal, test the backend
curl http://localhost:8000/health/

# Expected response:
# {"status":"healthy","timestamp":1234567890.123,"service":"mm-data-intelligent-agent-backend"}
```

### Step 2: Frontend Environment & Installation

#### 2.1. Set up Frontend Environment

Create `frontend/.env.local` (or `.env`):

```bash
# Navigate to frontend directory
cd frontend

# Create environment file
cat > .env.local << EOF
NEXT_PUBLIC_API_URL=http://localhost:8000
EOF
```

**⚠️ IMPORTANT:** The frontend is already configured to use `process.env.NEXT_PUBLIC_API_URL` in `services/api.ts` (line 58), so this environment variable will automatically connect the frontend to your local backend.

#### 2.2. Install Frontend Dependencies

```bash
# Install Node.js dependencies
pnpm install
```

#### 2.3. Start Frontend Development Server

```bash
# Start Next.js development server
pnpm dev
```

**Expected Output:**

```
> mm-data-intelligent-agent@ dev
> next dev

  ▲ Next.js 15.2.4
  - Local:        http://localhost:3000
  - Network:      http://192.168.1.100:3000
```

#### 2.4. Access Frontend

Open your browser and navigate to: [http://localhost:3000](http://localhost:3000)

### Step 3: Verify Frontend ↔ Backend Connection

#### 3.1. Test API Connection

In your browser's Developer Tools (F12) → Console, you should see:

- No CORS errors
- API calls to `http://localhost:8000` succeeding

#### 3.2. Test Search Functionality

1. Go to the search interface
2. Enter a test query (e.g., "a red car")
3. Click search
4. Check the Network tab to see API calls to the backend
5. Verify results are displayed

---

## Mode 2: Run with Docker Compose

### Step 1: Build Docker Images

```bash
# Navigate to the root directory
cd /path/to/mm-data-intelligent-agent

# Build all services
docker compose -f infra/docker-compose.yml build
```

**Expected Output:**

```
Building backend
Building frontend
Building redis
Building postgres
```

### Step 2: Start the Stack

```bash
# Start all services
docker compose -f infra/docker-compose.yml up

# Or run in detached mode (background)
docker compose -f infra/docker-compose.yml up -d
```

**Expected Output:**

```
Creating mm-data-intelligent-agent_redis_1    ... done
Creating mm-data-intelligent-agent_postgres_1  ... done
Creating mm-data-intelligent-agent_backend_1   ... done
Creating mm-data-intelligent-agent_frontend_1  ... done
```

### Step 3: Verify Services

#### 3.1. Check Service Status

```bash
# List running containers
docker compose -f infra/docker-compose.yml ps

# Expected services:
# - frontend (port 3000)
# - backend (port 8000)
# - redis (port 6379)
# - postgres (port 5432)
```

#### 3.2. Test Backend Health

```bash
# Test backend health endpoint
curl http://localhost:8000/health/

# Test detailed health
curl http://localhost:8000/health/detailed
```

#### 3.3. Access Applications

- **Frontend**: [http://localhost:3000](http://localhost:3000)
- **Backend API**: [http://localhost:8000](http://localhost:8000)
- **Backend Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

### Step 4: Monitor and Debug

#### 4.1. View Logs

```bash
# View all service logs
docker compose -f infra/docker-compose.yml logs -f

# View specific service logs
docker compose -f infra/docker-compose.yml logs -f backend
docker compose -f infra/docker-compose.yml logs -f frontend

# View logs for multiple services
docker compose -f infra/docker-compose.yml logs -f backend frontend
```

#### 4.2. Stop Services

```bash
# Stop all services
docker compose -f infra/docker-compose.yml down

# Stop and remove volumes (WARNING: This will delete data)
docker compose -f infra/docker-compose.yml down -v
```

---

## Testing ML Models (CLIP & LongCLIP)

### Test Backend Search Endpoints

#### 1. CLIP Text Search

```bash
curl -X POST http://localhost:8000/api/search/text \
  -H "Content-Type: application/json" \
  -d '{
    "query": "a red car on the street",
    "model_type": "clip",
    "limit": 5
  }'
```

#### 2. LongCLIP Text Search

```bash
curl -X POST http://localhost:8000/api/search/text \
  -H "Content-Type: application/json" \
  -d '{
    "query": "person drinking coffee",
    "model_type": "longclip",
    "limit": 5
  }'
```

#### 3. Image Search

```bash
curl -X POST http://localhost:8000/api/search/image \
  -H "Content-Type: application/json" \
  -d '{
    "image_source": "path/to/your/image.jpg",
    "model_type": "longclip",
    "limit": 5
  }'
```

#### 4. Visual Search

```bash
curl -X POST http://localhost:8000/api/search/visual \
  -H "Content-Type: application/json" \
  -d '{
    "object_list": [
      {
        "class_name": "car",
        "bbox": [100, 100, 200, 200]
      }
    ],
    "logic": "AND",
    "model_type": "longclip",
    "limit": 5
  }'
```

### Expected API Response Format

```json
{
  "success": true,
  "message": "Search completed successfully",
  "data": {
    "results": [
      {
        "image_id": "clip_123",
        "score": 0.85,
        "link": "path/to/image.jpg",
        "watch_url": null,
        "ocr_text": null
      }
    ]
  },
  "metadata": {
    "total_results": 1,
    "query_time_ms": 150.5,
    "model_used": "clip",
    "search_type": "text"
  }
}
```

---

## Model Weights & Preload

### Required Model Files

Ensure these files exist in your repository:

```
support_models/
├── Long-CLIP/
│   └── checkpoints/
│       └── longclip-B.pt          # LongCLIP model weights
├── CLIP/                           # CLIP model (auto-downloaded)
└── CLIP2Video/                    # CLIP2Video models
```

### FAISS Index Files

```
dict/
├── faiss_clip_vitb32.bin          # CLIP FAISS index
├── faiss_longclip.bin             # LongCLIP FAISS index
├── faiss_clip2video.bin           # CLIP2Video FAISS index
└── id2img.json                    # Image ID mapping
```

### Data Directory Structure

```
data/
├── features/                       # Pre-computed features
│   ├── clip/
│   ├── longclip/
│   └── clip2video/
└── raw/                           # Raw media files
```

---

## Troubleshooting

### Common Issues & Solutions

#### 1. CORS Errors

**Problem:** Frontend can't connect to backend due to CORS policy.

**Solution:** Backend already has CORS configured in `main.py`. If issues persist:

```python
# In backend/main.py, verify CORS settings:
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,  # Should include http://localhost:3000
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

#### 2. CUDA/GPU Errors

**Problem:** `RuntimeError: CUDA out of memory` or CUDA not available.

**Solution:** Set `MODEL_DEVICE=cpu` in `backend/.env`:

```bash
# Edit backend/.env
MODEL_DEVICE=cpu
```

#### 3. Submodules Not Initialized

**Problem:** `ModuleNotFoundError: No module named 'clip'`

**Solution:** Initialize git submodules:

```bash
git submodule update --init --recursive
```

#### 4. Frontend Not Calling Backend

**Problem:** Search requests fail or show network errors.

**Solution:** Check environment variables:

```bash
# Verify frontend/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8000

# Verify backend is running
curl http://localhost:8000/health/
```

#### 5. FAISS Index Not Found

**Problem:** `FileNotFoundError: [Errno 2] No such file or directory`

**Solution:** Check file paths in `backend/.env`:

```bash
# Verify these files exist:
ls -la dict/faiss_*.bin
ls -la dict/id2img.json
```

#### 6. Port Already in Use

**Problem:** `Address already in use` error.

**Solution:** Find and kill the process using the port:

```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or use different ports
# Backend: uvicorn main:app --host 0.0.0.0 --port 8001 --reload
# Frontend: Update .env.local with NEXT_PUBLIC_API_URL=http://localhost:8001
```

#### 7. Docker Build Failures

**Problem:** Docker build fails with dependency errors.

**Solution:** Clean and rebuild:

```bash
# Clean Docker cache
docker system prune -a

# Rebuild without cache
docker compose -f infra/docker-compose.yml build --no-cache
```

---

## Performance Monitoring

### Backend Health Endpoints

- **Basic Health**: `GET /health/`
- **Detailed Health**: `GET /health/detailed`
- **Readiness Probe**: `GET /health/ready`

### Model Status

Check model loading status:

```bash
curl http://localhost:8000/health/detailed | jq '.models'
```

### Performance Metrics

Monitor response times and model performance through the health endpoints.

---

## Development Workflow

### 1. Code Changes

- **Backend**: Changes auto-reload with `uvicorn --reload`
- **Frontend**: Changes auto-reload with Next.js dev server

### 2. Environment Updates

- **Backend**: Restart server after `.env` changes
- **Frontend**: Restart dev server after `.env.local` changes

### 3. Model Updates

- **Local**: Restart backend server
- **Docker**: Rebuild and restart backend container

---

## Additional Resources

- **Backend API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Backend Architecture**: See `docs/backend-architecture.md`
- **Project Overview**: See `README.md`
- **ML Model Documentation**: Check each submodule's README

---

## Getting Help

If you encounter issues not covered in this guide:

1. Check the **Troubleshooting** section above
2. Review **Backend logs** for error messages
3. Check **Frontend console** for JavaScript errors
4. Verify **Environment variables** are set correctly
5. Ensure **All prerequisites** are installed
6. Check **Git submodules** are initialized

For persistent issues, check the project's issue tracker or create a new issue with:

- Your operating system
- Python/Node.js versions
- Error messages and logs
- Steps to reproduce the issue
