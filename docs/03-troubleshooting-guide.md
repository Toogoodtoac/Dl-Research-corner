# Troubleshooting Guide - Common Issues & Solutions

## Overview

This troubleshooting guide covers the most common issues you'll encounter when working with the MM-Data Intelligent Agent. Each section includes diagnostic commands, step-by-step solutions, and prevention tips.

## Critical Issues (Search Not Working)

### Issue 1: "No FAISS Index Found" Error

#### Symptoms

- Backend fails to start
- Search API returns 500 errors
- Logs show `FileNotFoundError: [Errno 2] No such file or directory: '../dict/faiss_longclip.bin'`

#### Diagnostic Commands

```bash
# Check if FAISS indexes exist
ls -la dict/ 2>/dev/null || echo "dict/ directory missing"
ls -la dict/faiss_*.bin 2>/dev/null || echo "FAISS indexes missing"

# Check file sizes (should be > 1KB)
ls -lh dict/faiss_*.bin 2>/dev/null || echo "No FAISS files found"

# Check environment variables
cat backend/.env | grep -E "(FAISS|dict)" || echo "FAISS paths not configured"
```

#### Solution

```bash
# Option 1: Generate sample data (recommended for testing)
make sample-data
make index

# Option 2: Check if indexes exist in wrong location
find . -name "faiss_*.bin" -type f

# Option 3: Rebuild indexes from existing features
python scripts/build_faiss.py \
  --input data/hdf5_features \
  --output data/indexes/faiss \
  --combined \
  --validate

# Copy to correct location
cp data/indexes/faiss/*.bin dict/
cp data/indexes/faiss/*.json dict/
```

#### Prevention

- Always run `make index` after cloning the repository
- Check `backend/.env` has correct FAISS paths
- Verify `dict/` directory exists in project root

---

### Issue 2: "Model Not Loaded" Error

#### Symptoms

- Backend starts but search fails
- Logs show `RuntimeError: Model not loaded`
- Health endpoint shows models as unavailable

#### Diagnostic Commands

```bash
# Check model files exist
ls -la support_models/Long-CLIP/checkpoints/ 2>/dev/null || echo "LongCLIP missing"
ls -la support_models/CLIP/ 2>/dev/null || echo "CLIP missing"

# Check model file sizes (should be > 100MB)
ls -lh support_models/Long-CLIP/checkpoints/*.pt 2>/dev/null || echo "No model weights"

# Check environment variables
cat backend/.env | grep -E "(LONGCLIP|CLIP|MODEL)" || echo "Model paths not configured"

# Check git submodules
git submodule status | grep -E "(Long-CLIP|CLIP)" || echo "Submodules not initialized"
```

#### Solution

```bash
# Option 1: Initialize git submodules
git submodule update --init --recursive

# Option 2: Check model paths in .env
# Edit backend/.env and verify these paths:
# SUPPORT_MODELS_DIR=../support_models
# LONGCLIP_CHECKPOINT=../support_models/Long-CLIP/checkpoints/longclip-B.pt

# Option 3: Download models manually
cd support_models
git clone https://github.com/microsoft/Long-CLIP.git
cd Long-CLIP
# Download checkpoint files to checkpoints/ directory

# Option 4: Restart backend after fixing paths
make dev-backend
```

#### Prevention

- Always run `git submodule update --init --recursive` after cloning
- Verify model paths in `backend/.env` are correct
- Check that model files are actually present (not just directories)

---

### Issue 3: Search Returns No Results

#### Symptoms

- Search API returns empty results array
- Frontend shows "No results found"
- Backend logs show successful search but 0 results

#### Diagnostic Commands

```bash
# Check FAISS index has data
python -c "
import faiss
try:
    index = faiss.read_index('dict/faiss_longclip.bin')
    print(f'FAISS index has {index.ntotal} vectors')
    if index.ntotal == 0:
        print('WARNING: Index is empty!')
except Exception as e:
    print(f'Error reading index: {e}')
"

# Check metadata has entries
python -c "
import json
try:
    with open('dict/id2img.json', 'r') as f:
        data = json.load(f)
    print(f'Metadata has {len(data)} entries')
    if len(data) == 0:
        print('WARNING: Metadata is empty!')
except Exception as e:
    print(f'Error reading metadata: {e}')
"

# Test search API directly
curl -X POST http://localhost:8000/api/search/text \
  -H "Content-Type: application/json" \
  -d '{"query":"test","model_type":"longclip","limit":5}' \
  | jq '.data.results | length'
```

#### Solution

```bash
# Option 1: Regenerate data (if indexes are empty)
make clean
make sample-data
make index

# Option 2: Check data integrity
python scripts/build_faiss.py --validate
python scripts/build_lucene.py --test-search

# Option 3: Verify feature extraction worked
ls -la data/hdf5_features/
python -c "
import h5py
try:
    with h5py.File('data/hdf5_features/features.h5', 'r') as f:
        print('HDF5 file structure:')
        for key in f.keys():
            print(f'  {key}: {f[key].shape}')
except Exception as e:
    print(f'Error reading HDF5: {e}')
"
```

#### Prevention

- Always verify data generation with `make index`
- Check that sample data generation creates non-empty files
- Monitor backend logs for data loading messages

---

### Issue 4: Frontend Can't Connect to Backend

#### Symptoms

- Frontend shows loading forever
- Browser console shows CORS errors
- Network tab shows failed requests to backend

#### Diagnostic Commands

```bash
# Check backend is running
curl http://localhost:8000/health/ || echo "Backend not responding"

# Check ports are correct
netstat -tlnp | grep -E "(3000|8000)" || echo "Ports not in use"

# Check CORS configuration
cat backend/.env | grep ALLOWED_ORIGINS || echo "CORS not configured"

# Check frontend environment
cat frontend/.env.local 2>/dev/null || echo "Frontend .env.local missing"
```

#### Solution

```bash
# Option 1: Start backend
make dev-backend

# Option 2: Fix CORS configuration
# Edit backend/.env and ensure:
# ALLOWED_ORIGINS=["http://localhost:3000", "http://localhost:8080"]

# Option 3: Check frontend environment
# Create frontend/.env.local with:
# NEXT_PUBLIC_API_URL=http://localhost:8000

# Option 4: Verify ports match
# Backend should be on 8000, Frontend on 3000
# Check for port conflicts
lsof -i :8000
lsof -i :3000
```

#### Prevention

- Always start backend before frontend
- Verify CORS settings include frontend URL
- Check that ports are not already in use

---

## Development Environment Issues

### Issue 5: Python Dependencies Not Found

#### Symptoms

- `ModuleNotFoundError: No module named 'clip'`
- Import errors for ML libraries
- Backend fails to start due to missing packages

#### Diagnostic Commands

```bash
# Check Python environment
python --version
which python

# Check if virtual environment is activated
echo $VIRTUAL_ENV

# Check installed packages
pip list | grep -E "(clip|torch|faiss)" || echo "ML packages not installed"

# Check requirements.txt
cat backend/requirements.txt
```

#### Solution

```bash
# Option 1: Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Option 2: Install dependencies
pip install -r backend/requirements.txt

# Option 3: Install ML packages individually
pip install torch torchvision
pip install faiss-cpu  # or faiss-gpu if you have CUDA
pip install clip

# Option 4: Check Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)/support_models/CLIP"
export PYTHONPATH="${PYTHONPATH}:$(pwd)/support_models/Long-CLIP"
```

#### Prevention

- Always use virtual environments
- Install requirements before starting development
- Check Python version compatibility (3.11+)

---

### Issue 6: Node.js/npm Issues

#### Symptoms

- `pnpm: command not found`
- Frontend build fails
- Package installation errors

#### Diagnostic Commands

```bash
# Check Node.js version
node --version  # Should be ≥ 18.0.0

# Check npm version
npm --version

# Check pnpm version
pnpm --version  # Should be ≥ 8.0.0

# Check if pnpm is installed
which pnpm || echo "pnpm not found"
```

#### Solution

```bash
# Option 1: Install pnpm
npm install -g pnpm

# Option 2: Use npm instead
cd frontend
npm install
npm run dev

# Option 3: Install Node.js (if missing)
# Download from https://nodejs.org/

# Option 4: Clear npm cache
npm cache clean --force
rm -rf frontend/node_modules frontend/package-lock.json
npm install
```

#### Prevention

- Install Node.js 18+ before starting
- Use pnpm for better performance
- Clear cache if package installation fails

---

### Issue 7: Git Submodule Issues

#### Symptoms

- `ModuleNotFoundError: No module named 'clip'`
- Missing ML model directories
- Git status shows submodules as uninitialized

#### Diagnostic Commands

```bash
# Check submodule status
git submodule status

# Check if submodule directories exist
ls -la support_models/ 2>/dev/null || echo "support_models missing"
ls -la support_models/CLIP/ 2>/dev/null || echo "CLIP submodule missing"
ls -la support_models/Long-CLIP/ 2>/dev/null || echo "LongCLIP submodule missing"

# Check .gitmodules file
cat .gitmodules
```

#### Solution

```bash
# Option 1: Initialize submodules
git submodule update --init --recursive

# Option 2: Clone with submodules
git clone --recursive <repository-url>

# Option 3: Manual submodule setup
git submodule init
git submodule update

# Option 4: Reset submodules
git submodule deinit -f .
git submodule update --init --recursive
```

#### Prevention

- Always use `git clone --recursive` or `git submodule update --init --recursive`
- Check submodule status after pulling changes
- Verify `.gitmodules` file is present

---

## Docker Issues

### Issue 8: Docker Build Failures

#### Symptoms

- `docker-compose build` fails
- Container startup errors
- Port conflicts in Docker

#### Diagnostic Commands

```bash
# Check Docker is running
docker --version
docker-compose --version

# Check for port conflicts
docker ps | grep -E "(3000|8000)" || echo "No containers using ports"

# Check Docker resources
docker system df

# Check Docker logs
docker-compose -f infra/docker-compose.yml logs
```

#### Solution

```bash
# Option 1: Clean Docker system
docker system prune -a
docker volume prune

# Option 2: Rebuild without cache
docker-compose -f infra/docker-compose.yml build --no-cache

# Option 3: Check port conflicts
# Stop any local services using ports 3000/8000
lsof -i :3000 | awk 'NR>1 {print $2}' | xargs kill -9
lsof -i :8000 | awk 'NR>1 {print $2}' | xargs kill -9

# Option 4: Use different ports
# Edit infra/docker-compose.yml and change ports
```

#### Prevention

- Ensure Docker has enough resources (4GB+ RAM)
- Stop local services before starting Docker
- Use `docker system prune` regularly

---

### Issue 9: Container Startup Issues

#### Symptoms

- Containers start but immediately exit
- Health checks fail
- Services not accessible

#### Diagnostic Commands

```bash
# Check container status
docker-compose -f infra/docker-compose.yml ps

# Check container logs
docker-compose -f infra/docker-compose.yml logs backend
docker-compose -f infra/docker-compose.yml logs frontend

# Check container health
docker inspect mm-data-intelligent-agent-backend-1 | jq '.[0].State.Health'

# Check resource usage
docker stats --no-stream
```

#### Solution

```bash
# Option 1: Check environment variables
docker-compose -f infra/docker-compose.yml config

# Option 2: Start services individually
docker-compose -f infra/docker-compose.yml up backend
docker-compose -f infra/docker-compose.yml up frontend

# Option 3: Check container resources
# Ensure containers have enough memory/CPU

# Option 4: Restart Docker daemon
sudo systemctl restart docker
```

#### Prevention

- Check container resource limits
- Verify environment variables are set
- Monitor container logs during startup

---

## Performance Issues

### Issue 10: Slow Search Response

#### Symptoms

- Search takes 10+ seconds
- High CPU/memory usage
- Timeout errors

#### Diagnostic Commands

```bash
# Check response times
time curl -X POST http://localhost:8000/api/search/text \
  -H "Content-Type: application/json" \
  -d '{"query":"test","model_type":"longclip","limit":5}'

# Check system resources
htop
nvidia-smi  # If using GPU

# Check backend performance
curl http://localhost:8000/health/detailed | jq '.performance'

# Check FAISS index type
python -c "
import faiss
index = faiss.read_index('dict/faiss_longclip.bin')
print(f'Index type: {type(index).__name__}')
print(f'Index size: {index.ntotal} vectors')
"
```

#### Solution

```bash
# Option 1: Use GPU acceleration
export MODEL_DEVICE=cuda
# Restart backend

# Option 2: Optimize FAISS index
python scripts/build_faiss.py \
  --input data/hdf5_features \
  --output data/indexes/faiss \
  --index-type ivf \
  --use-gpu \
  --validate

# Option 3: Reduce search limit
# Use smaller limit in search requests

# Option 4: Enable caching
# Ensure Redis is running and configured
```

#### Prevention

- Use GPU if available
- Build optimized FAISS indexes
- Monitor system resources
- Implement result caching

---

### Issue 11: High Memory Usage

#### Symptoms

- Out of memory errors
- System becomes unresponsive
- Container crashes

#### Diagnostic Commands

```bash
# Check memory usage
free -h
ps aux --sort=-%mem | head -10

# Check Python memory
python -c "
import psutil
process = psutil.Process()
print(f'Memory usage: {process.memory_info().rss / 1024 / 1024:.1f} MB')
"

# Check Docker memory
docker stats --no-stream | grep -E "(backend|frontend)"

# Check ML model memory
# Models can use 2-4GB each
```

#### Solution

```bash
# Option 1: Use CPU instead of GPU
export MODEL_DEVICE=cpu
# Restart backend

# Option 2: Lazy load models
export LAZY_LOAD_MODELS=true
# Restart backend

# Option 3: Reduce batch sizes
# Edit backend configuration

# Option 4: Monitor and restart
# Set up memory monitoring
# Restart services when memory gets high
```

#### Prevention

- Use lazy loading for models
- Monitor memory usage
- Set memory limits in Docker
- Restart services periodically

---

## Frontend-Specific Issues

### Issue 12: React Component Errors

#### Symptoms

- White screen or error page
- Console shows React errors
- Components not rendering

#### Diagnostic Commands

```bash
# Check frontend build
cd frontend
pnpm build

# Check for TypeScript errors
pnpm type-check

# Check browser console
# Open Developer Tools → Console tab

# Check network requests
# Open Developer Tools → Network tab
```

#### Solution

```bash
# Option 1: Clear Next.js cache
rm -rf frontend/.next
pnpm dev

# Option 2: Fix TypeScript errors
pnpm type-check
# Fix any type errors shown

# Option 3: Check component imports
# Verify all imports are correct
# Check for circular dependencies

# Option 4: Restart development server
pnpm dev
```

#### Prevention

- Run type checking before committing
- Use TypeScript strict mode
- Avoid circular dependencies
- Test components individually

---

### Issue 13: API Integration Issues

#### Symptoms

- Frontend can't fetch data
- CORS errors in console
- API calls fail silently

#### Diagnostic Commands

```bash
# Check API service configuration
cat frontend/services/api.ts | grep BASE_URL

# Check environment variables
cat frontend/.env.local 2>/dev/null || echo "No .env.local"

# Test API directly
curl -v http://localhost:8000/api/search/text \
  -H "Content-Type: application/json" \
  -d '{"query":"test","model_type":"longclip","limit":5}'

# Check CORS headers
curl -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type" \
  -X OPTIONS http://localhost:8000/api/search/text
```

#### Solution

```bash
# Option 1: Fix API URL
# Create frontend/.env.local with:
# NEXT_PUBLIC_API_URL=http://localhost:8000

# Option 2: Fix CORS
# Ensure backend/.env has:
# ALLOWED_ORIGINS=["http://localhost:3000"]

# Option 3: Check backend is running
make dev-backend

# Option 4: Verify API endpoints
curl http://localhost:8000/health/
```

#### Prevention

- Always set `NEXT_PUBLIC_API_URL` in frontend
- Test API endpoints before frontend integration
- Use consistent port configuration

---

## Emergency Recovery

### Complete System Reset

```bash
# If everything is broken, start fresh
make clean
git submodule deinit -f .
git submodule update --init --recursive
make sample-data
make index
make dev
```

### Data Recovery

```bash
# If data is corrupted
rm -rf dict/ data/
make sample-data
make index
```

### Service Recovery

```bash
# Stop all services
make docker-down
pkill -f uvicorn
pkill -f next

# Start fresh
make dev
```

---

## Troubleshooting Checklist

### Before Asking for Help

- [ ] Check this troubleshooting guide
- [ ] Run diagnostic commands
- [ ] Check logs (backend and frontend)
- [ ] Verify environment configuration
- [ ] Test with sample data
- [ ] Check system resources

### When Reporting Issues

1. **Describe the problem clearly**
2. **Include error messages**
3. **Share diagnostic command output**
4. **Mention your environment (OS, Python/Node versions)**
5. **Include steps to reproduce**

### Prevention Tips

- Always use virtual environments
- Keep dependencies updated
- Monitor system resources
- Test changes incrementally
- Document custom configurations

---

## Quick Fix Reference

| Issue | Quick Fix |
|-------|-----------|
| FAISS not found | `make index` |
| Model not loaded | `git submodule update --init --recursive` |
| Frontend can't connect | Check `NEXT_PUBLIC_API_URL` in frontend |
| CORS errors | Verify `ALLOWED_ORIGINS` in backend |
| High memory usage | Set `MODEL_DEVICE=cpu` |
| Slow search | Check GPU availability, optimize FAISS indexes |
| Python errors | `pip install -r backend/requirements.txt` |
| Node errors | `pnpm install` |
| Docker issues | `docker system prune -a` |

**Remember**: Most issues can be resolved by following the diagnostic steps and using the appropriate solution. When in doubt, start with the data connection verification and work your way up the stack.
