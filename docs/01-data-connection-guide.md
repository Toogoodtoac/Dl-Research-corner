# Data Connection Guide - Making Search Work Successfully

## Overview

This guide specifically addresses **how to connect with data** to make the search functionality work. The MM-Data Intelligent Agent requires specific data files and indexes to function properly. Without these, search will fail with errors like "No FAISS index found" or "Model not loaded."

## Critical Data Requirements

### What You Need for Search to Work

```
✅ FAISS Index Files (.bin)     # Vector similarity search
✅ Model Weight Files (.pt)      # ML model capabilities
✅ Image ID Mapping (.json)      # Result metadata
✅ Feature Files (HDF5)          # Pre-computed embeddings
❌ Raw Media Files               # Optional for basic search
```

### File Structure Requirements

```
mm-data-intelligent-agent/
├── dict/                        # CRITICAL: Search indexes
│   ├── faiss_clip_vitb32.bin   # CLIP search index
│   ├── faiss_longclip.bin      # LongCLIP search index
│   ├── faiss_clip2video.bin    # CLIP2Video search index
│   └── id2img.json             # Image metadata mapping
├── support_models/              # CRITICAL: ML models
│   ├── Long-CLIP/
│   │   └── checkpoints/
│   │       └── longclip-B.pt   # LongCLIP weights
│   ├── CLIP/                   # Auto-downloaded
│   └── CLIP2Video/             # Model files
└── data/                        # OPTIONAL: Features & media
    ├── features/                # HDF5 feature files
    └── raw/                     # Original media files
```

## Step-by-Step Data Setup

### Step 1: Check What You Have

```bash
# Navigate to project root
cd mm-data-intelligent-agent

# Check for existing data files
ls -la dict/ 2>/dev/null || echo "dict/ directory missing"
ls -la support_models/ 2>/dev/null || echo "support_models/ directory missing"
ls -la data/ 2>/dev/null || echo "data/ directory missing"
```

### Step 2: Initialize Missing Components

```bash
# Initialize git submodules (ML models)
git submodule update --init --recursive

# Create required directories
mkdir -p dict data/features data/raw
```

### Step 3: Generate Sample Data (Recommended for Testing)

```bash
# Generate sample videos and features
make sample-data

# Run complete indexing pipeline
make index

# Verify files were created
ls -la dict/
ls -la data/
```

### Step 4: Verify Data Integrity

```bash
# Check FAISS indexes exist
ls -la dict/faiss_*.bin

# Check model weights exist
ls -la support_models/Long-CLIP/checkpoints/longclip-B.pt

# Check metadata exists
ls -la dict/id2img.json
```

## Understanding the Data Pipeline

### How Data Flows Through the System

```
1. Raw Media → 2. Feature Extraction → 3. Index Building → 4. Search Ready
   (videos/images)    (CLIP/LongCLIP)     (FAISS)         (API endpoints)
```

### What Each Component Does

#### 1. Raw Media Files

- **Purpose**: Source videos/images for search
- **Format**: MP4, JPG, PNG, etc.
- **Location**: `data/raw/`
- **Status**: Optional for basic search (can use sample data)

#### 2. Feature Extraction

- **Purpose**: Convert media to searchable vectors
- **Models**: CLIP, LongCLIP, CLIP2Video
- **Output**: 512-dimensional feature vectors
- **Storage**: HDF5 format in `data/features/`

#### 3. FAISS Indexes

- **Purpose**: Enable fast similarity search
- **Type**: Vector similarity search
- **Files**: `.bin` files in `dict/`
- **Status**: **CRITICAL** - search won't work without these

#### 4. Metadata Mapping

- **Purpose**: Link search results to actual files
- **File**: `dict/id2img.json`
- **Content**: Image ID → file path mapping
- **Status**: **CRITICAL** - results won't display without this

## Quick Data Generation (Sample Data)

### Option 1: Use Built-in Sample Generator

```bash
# Generate 5 sample videos with features
make sample-data

# This creates:
# - examples/sample_data/ (sample videos)
# - data/hdf5_features/ (extracted features)
# - dict/faiss_*.bin (search indexes)
# - dict/id2img.json (metadata mapping)
```

### Option 2: Custom Sample Generation

```bash
# Generate custom sample data
python scripts/sample_data_generator.py \
  --num-videos 10 \
  --frames-per-video 30 \
  --feature-dim 512 \
  --output examples/custom_data

# Process the custom data
python scripts/ingest.py \
  --input examples/custom_data \
  --output data/hdf5_features

# Build indexes
python scripts/build_faiss.py \
  --input data/hdf5_features \
  --output data/indexes/faiss \
  --combined \
  --validate
```

## Troubleshooting Data Connection Issues

### Problem 1: "No FAISS Index Found"

```bash
# Error message
FileNotFoundError: [Errno 2] No such file or directory: '../dict/faiss_longclip.bin'

# Solution
make index  # Generate sample data and build indexes
```

### Problem 2: "Model Not Loaded"

```bash
# Error message
RuntimeError: Model not loaded. Please check model paths.

# Solution
# 1. Check environment variables
cat backend/.env | grep -E "(LONGCLIP|CLIP|MODEL)"

# 2. Verify model files exist
ls -la support_models/Long-CLIP/checkpoints/

# 3. Restart backend
make dev-backend
```

### Problem 3: "Search Returns No Results"

```bash
# Problem: Search API returns empty results
# Solution: Check data integrity

# Verify indexes exist and have data
python -c "
import faiss
import json

# Check FAISS index
index = faiss.read_index('dict/faiss_longclip.bin')
print(f'FAISS index has {index.ntotal} vectors')

# Check metadata
with open('dict/id2img.json', 'r') as f:
    data = json.load(f)
print(f'Metadata has {len(data)} entries')
"
```

### Problem 4: "Frontend Shows Loading Forever"

```bash
# Problem: Frontend stuck on loading
# Solution: Check backend connectivity and data

# 1. Test backend health
curl http://localhost:8000/health/

# 2. Test search API directly
curl -X POST http://localhost:8000/api/search/text \
  -H "Content-Type: application/json" \
  -d '{"query":"test","model_type":"longclip","limit":5}'

# 3. Check backend logs for errors
cd backend && python -m uvicorn main:app --reload --log-level debug
```

## Data Validation Checklist

### Before Starting Search

- [ ] `dict/faiss_longclip.bin` exists and is > 1KB
- [ ] `dict/id2img.json` exists and contains valid JSON
- [ ] `support_models/Long-CLIP/checkpoints/longclip-B.pt` exists
- [ ] Backend environment variables are set correctly
- [ ] Backend starts without model loading errors
- [ ] Health endpoint returns "healthy" status

### After Running Search

- [ ] Search API returns results (not empty array)
- [ ] Results contain valid image IDs
- [ ] Frontend displays results correctly
- [ ] No console errors in browser
- [ ] Network requests succeed (200 status)

## Advanced Data Management

### Using Your Own Data

```bash
# 1. Place your media files in data/raw/
cp your_videos/* data/raw/

# 2. Run feature extraction
python scripts/ingest.py \
  --input data/raw \
  --output data/hdf5_features \
  --config config/ingestion.yml

# 3. Build search indexes
python scripts/build_faiss.py \
  --input data/hdf5_features \
  --output data/indexes/faiss \
  --combined \
  --validate

# 4. Update environment variables
# Edit backend/.env to point to your new indexes
```

### Data Migration

```bash
# Backup existing data
tar -czf data_backup_$(date +%Y%m%d).tar.gz dict/ data/

# Restore from backup
tar -xzf data_backup_20241201.tar.gz

# Verify restoration
ls -la dict/ data/
```

### Performance Optimization

```bash
# Use GPU acceleration (if available)
export MODEL_DEVICE=cuda

# Build optimized FAISS indexes
python scripts/build_faiss.py \
  --input data/hdf5_features \
  --output data/indexes/faiss \
  --index-type ivf \
  --use-gpu \
  --validate
```

## Testing Data Connection

### Test 1: Backend Data Loading

```bash
# Start backend with debug logging
cd backend
export LOG_LEVEL=DEBUG
python -m uvicorn main:app --reload --log-level debug

# Look for these success messages:
# "Model loaded successfully: longclip"
# "FAISS index loaded: ../dict/faiss_longclip.bin"
# "Metadata loaded: ../dict/id2img.json"
```

### Test 2: API Endpoint Testing

```bash
# Test search endpoint
curl -X POST http://localhost:8000/api/search/text \
  -H "Content-Type: application/json" \
  -d '{"query":"person","model_type":"longclip","limit":5}' \
  | jq '.data.results | length'

# Expected: Returns number > 0
```

### Test 3: Frontend Integration

```bash
# 1. Start frontend
cd frontend && pnpm dev

# 2. Open browser to http://localhost:3000
# 3. Enter search query
# 4. Check browser console for errors
# 5. Verify results display
```

## Data Connection Reference

### Environment Variables (backend/.env)

```bash
# CRITICAL - Model paths
SUPPORT_MODELS_DIR=../support_models
LONGCLIP_CHECKPOINT=../support_models/Long-CLIP/checkpoints/longclip-B.pt

# CRITICAL - FAISS index paths
FAISS_LONGCLIP_PATH=../dict/faiss_longclip.bin
ID2IMG_JSON_PATH=../dict/id2img.json

# OPTIONAL - Data paths
DATA_ROOT=../data
FEATURES_DIR=../data/features
```

### File Permissions

```bash
# Ensure files are readable
chmod 644 dict/*.bin dict/*.json
chmod 644 support_models/Long-CLIP/checkpoints/*.pt

# Check file ownership
ls -la dict/ support_models/Long-CLIP/checkpoints/
```

### Data File Sizes (Expected)

```bash
# FAISS indexes (should be > 1KB)
ls -lh dict/faiss_*.bin

# Model weights (should be > 100MB)
ls -lh support_models/Long-CLIP/checkpoints/*.pt

# Metadata (should be > 1KB)
ls -lh dict/id2img.json
```

## Emergency Data Recovery

### If All Data is Lost

```bash
# 1. Clean everything
make clean

# 2. Reinitialize submodules
git submodule update --init --recursive

# 3. Generate fresh sample data
make sample-data
make index

# 4. Verify system works
make dev-backend
curl http://localhost:8000/health/
```

### If Only Indexes are Missing

```bash
# Rebuild indexes from existing features
python scripts/build_faiss.py \
  --input data/hdf5_features \
  --output data/indexes/faiss \
  --combined \
  --validate

# Copy to dict/ directory
cp data/indexes/faiss/*.bin dict/
cp data/indexes/faiss/*.json dict/
```

## Success Criteria

### You Know Data Connection is Working When

1. ✅ Backend starts without errors
2. ✅ Health endpoint returns "healthy"
3. ✅ Search API returns results
4. ✅ Frontend displays search results
5. ✅ No console errors in browser
6. ✅ Network requests succeed

### Common Success Indicators

- Search returns 5-20 results for common queries
- Results include valid image IDs and scores
- Frontend displays results in grid format
- No "No results found" messages for basic queries
- Backend logs show successful model loading

---

## Next Steps After Data Connection

Once your data connection is working:

1. **Explore the API**: Visit `http://localhost:8000/docs`
2. **Test Different Queries**: Try various search terms
3. **Customize the Interface**: Modify frontend components
4. **Add Your Own Data**: Process your media files
5. **Optimize Performance**: Enable GPU acceleration if available

**Remember**: The data connection is the foundation. Without proper FAISS indexes and model weights, the search functionality cannot work. Always start with the data setup before attempting to use the search features.
