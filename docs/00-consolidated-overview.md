# MM-Data Intelligent Agent - Consolidated System Overview

## System Purpose

The MM-Data Intelligent Agent is a **multi-modal data search and analysis platform** that enables intelligent search across video and image datasets using AI models (CLIP, LongCLIP, CLIP2Video). It provides both text-based and visual search capabilities with a modern web interface.

## 🏗️ High-Level Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │   Data Layer    │
│   (Next.js 15)  │◄──►│   (FastAPI)     │◄──►│   (FAISS + HDF5)│
│                 │    │                 │    │                 │
│ • Search UI     │    │ • ML Models     │    │ • Vector Index  │
│ • Visual Search │    │ • Search APIs   │    │ • Feature Store │
│ • Results Display│   │ • OCR/ASR       │    │ • Metadata      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Complete Data Flow

### 1. Data Ingestion Pipeline

```
Video/Image Files → Feature Extraction → HDF5 Storage → FAISS Indexing → Search Ready
```

**Detailed Steps:**

1. **Input**: Raw video/image files
2. **Processing**: Extract features using CLIP/LongCLIP/CLIP2Video models
3. **Storage**: Store features in HDF5 format with metadata
4. **Indexing**: Build FAISS vector indexes for fast similarity search
5. **Search**: Enable real-time search across the indexed data

### 2. Search Request Flow

```
User Query → Frontend → Backend API → ML Model → FAISS Search → Results → Frontend Display
```

**Detailed Steps:**

1. **User Input**: Text query or visual search parameters
2. **Frontend Processing**: Format request and send to backend
3. **Backend Processing**: Load ML model, encode query
4. **Vector Search**: Query FAISS index for similar vectors
5. **Result Processing**: Format and return search results
6. **Frontend Display**: Show results with images and metadata

## Frontend (Next.js 15)

### Core Components

- **Search Interface**: Text-based search with natural language queries
- **Visual Search**: Drag-and-drop symbol positioning for object-based search
- **Results Display**: Grid layout showing search results with metadata
- **Image Detail View**: Individual image inspection and analysis

### Key Features

- **Responsive Design**: Mobile-first UI with Tailwind CSS
- **Real-time Search**: Instant results as you type
- **Visual Search**: Interactive canvas for positioning search objects
- **Image Caching**: Local storage for performance optimization

### Technology Stack

- **Framework**: Next.js 15 with App Router
- **Language**: TypeScript 5.0
- **Styling**: Tailwind CSS + Radix UI components
- **State Management**: React hooks + Context API
- **Canvas**: Konva.js for interactive graphics

## Backend (FastAPI)

### Core Services

- **Model Manager**: Lazy loading of ML models (CLIP, LongCLIP, CLIP2Video)
- **Search Service**: FAISS integration for vector similarity search
- **OCR Service**: Text extraction from images
- **ASR Service**: Speech-to-text conversion
- **Temporal Service**: Video sequence search capabilities

### API Endpoints

- **Search APIs**: `/api/search/text`, `/api/search/image`, `/api/search/visual`
- **OCR APIs**: `/api/ocr/extract`, `/api/ocr/languages`
- **ASR APIs**: `/api/asr/transcribe`, `/api/asr/models`
- **Health APIs**: `/health/`, `/health/detailed`, `/health/ready`

### Technology Stack

- **Framework**: FastAPI with async/await
- **Language**: Python 3.11+
- **ML Models**: CLIP, LongCLIP, CLIP2Video
- **Vector Search**: FAISS with GPU acceleration support
- **Caching**: Redis integration for performance

## Data Layer

### Storage Structure

```
data/
├── hdf5_features/           # Extracted features in HDF5 format
│   ├── clip/               # CLIP model features
│   ├── longclip/           # LongCLIP model features
│   └── clip2video/         # CLIP2Video model features
├── indexes/                 # Search indexes
│   ├── faiss/              # FAISS vector indexes
│   └── lucene/             # Text search indexes
└── raw/                     # Original media files
```

### Index Types

- **FAISS Indexes**: Vector similarity search (CLIP, LongCLIP, CLIP2Video)
- **Lucene/Whoosh**: Text-based search across metadata and OCR text
- **Metadata**: Image/video information, timestamps, object detections

## Getting Started - Complete Setup

### Prerequisites

- **Python** ≥ 3.11
- **Node.js** ≥ 18.0.0
- **pnpm** ≥ 8.0.0
- **Git** with submodule support
- **(Optional)** NVIDIA GPU + CUDA for `MODEL_DEVICE=cuda`

### Step 1: Repository Setup

```bash
# Clone and initialize submodules
git clone <repository-url>
cd mm-data-intelligent-agent
git submodule update --init --recursive
```

### Step 2: Backend Configuration

```bash
# Copy environment template
cp backend/env.example backend/.env

# Edit backend/.env with your paths
nano backend/.env
```

**Critical Environment Variables:**

```bash
# Model Paths (CRITICAL for ML functionality)
SUPPORT_MODELS_DIR=../support_models
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

# Model Device
MODEL_DEVICE=cpu  # Use 'cuda' if you have NVIDIA GPU
```

### Step 3: Data Pipeline Setup

```bash
# Generate sample data for testing
make sample-data

# Run complete indexing pipeline
make index

# This creates:
# - Sample videos with features
# - HDF5 feature files
# - FAISS vector indexes
# - Text search indexes
```

### Step 4: Service Startup

```bash
# Start backend (in one terminal)
make dev-backend

# Start frontend (in another terminal)
make dev-frontend

# Or start both together
make dev
```

## How Search Works - Technical Deep Dive

### 1. Text Search Process

```
User Query → Text Encoding → Vector Search → Result Ranking → Display
```

**Technical Details:**

1. **Query Processing**: Natural language text input
2. **Model Encoding**: CLIP/LongCLIP converts text to 512-dimensional vector
3. **FAISS Search**: k-NN search finds most similar vectors in index
4. **Result Processing**: Convert vector indices back to image metadata
5. **Response**: Return ranked results with scores and image links

### 2. Visual Search Process

```
Visual Query → Object Detection → Feature Extraction → Spatial Search → Results
```

**Technical Details:**

1. **Object Detection**: Identify objects and bounding boxes
2. **Feature Extraction**: Extract CLIP features for detected regions
3. **Spatial Reasoning**: Consider object positions and relationships
4. **Multi-modal Search**: Combine visual and spatial information
5. **Result Ranking**: Score based on visual similarity and spatial constraints

### 3. Image Similarity Search

```
Input Image → Feature Extraction → Vector Comparison → Similar Images
```

**Technical Details:**

1. **Image Processing**: Resize and normalize input image
2. **Feature Extraction**: Generate CLIP/LongCLIP embedding
3. **Similarity Calculation**: Cosine similarity with indexed vectors
4. **Result Selection**: Top-k most similar images

## Data Connection Requirements

### Required Files for Search to Work

```
dict/
├── faiss_clip_vitb32.bin      # CLIP FAISS index
├── faiss_longclip.bin         # LongCLIP FAISS index
├── faiss_clip2video.bin       # CLIP2Video FAISS index
└── id2img.json                # Image ID to file mapping

support_models/
├── Long-CLIP/
│   └── checkpoints/
│       └── longclip-B.pt      # LongCLIP model weights
├── CLIP/                      # CLIP model (auto-downloaded)
└── CLIP2Video/                # CLIP2Video models

data/
├── features/                   # Pre-computed features
└── raw/                       # Original media files
```

### How to Generate Required Data

```bash
# Option 1: Use sample data (for testing)
make sample-data
make index

# Option 2: Process your own data
python scripts/ingest.py --input your_videos/ --output data/hdf5_features
python scripts/build_faiss.py --input data/hdf5_features --output data/indexes/faiss
python scripts/build_lucene.py --input data/hdf5_features --output data/indexes/lucene
```

## Testing the System

### 1. Health Check

```bash
# Test backend health
curl http://localhost:8000/health/

# Expected response:
# {"status":"healthy","timestamp":1234567890.123,"service":"mm-data-intelligent-agent-backend"}
```

### 2. Search API Test

```bash
# Test text search
curl -X POST http://localhost:8000/api/search/text \
  -H "Content-Type: application/json" \
  -d '{"query":"a red car","model_type":"longclip","limit":5}'

# Expected response:
# {"success":true,"data":{"results":[...]},"metadata":{...}}
```

### 3. Frontend Test

1. Open [http://localhost:3000](http://localhost:3000)
2. Enter a search query (e.g., "person drinking coffee")
3. Verify results are displayed
4. Check browser console for any errors

## Common Issues & Solutions

### 1. "No FAISS Index Found" Error

**Problem**: Search fails because FAISS indexes don't exist
**Solution**: Run the indexing pipeline

```bash
make index
```

### 2. "Model Not Loaded" Error

**Problem**: ML models haven't been loaded
**Solution**: Check environment variables and restart backend

```bash
# Verify .env file has correct paths
cat backend/.env

# Restart backend
make dev-backend
```

### 3. Frontend Can't Connect to Backend

**Problem**: CORS errors or connection failures
**Solution**: Verify backend is running and CORS is configured

```bash
# Check backend status
curl http://localhost:8000/health/

# Verify frontend environment
cat frontend/.env.local
```

### 4. CUDA/GPU Errors

**Problem**: CUDA out of memory or not available
**Solution**: Use CPU mode

```bash
# Edit backend/.env
MODEL_DEVICE=cpu
```

## Development Workflow

### Daily Development

```bash
# Start development environment
make dev

# Make code changes (auto-reload enabled)
# Backend: uvicorn with --reload
# Frontend: Next.js dev server

# Test changes
make test

# Build for production
make build
```

### Adding New Features

1. **Backend**: Add new API endpoints in `backend/api/`
2. **Frontend**: Create new components in `frontend/components/`
3. **Testing**: Add tests in respective `tests/` directories
4. **Documentation**: Update this consolidated overview

### Debugging

```bash
# Backend logs
cd backend && python -m uvicorn main:app --reload --log-level debug

# Frontend logs
cd frontend && pnpm dev

# Check system health
curl http://localhost:8000/health/detailed
```

## Performance Optimization

### Backend Optimization

- **Lazy Loading**: Models loaded only when needed
- **Redis Caching**: Cache search results and embeddings
- **Async Processing**: Non-blocking I/O operations
- **GPU Acceleration**: CUDA support for ML models

### Frontend Optimization

- **Image Caching**: LocalForage for client-side storage
- **Lazy Loading**: Images loaded on demand
- **Code Splitting**: Automatic with Next.js App Router
- **Bundle Optimization**: Tree shaking and minification

## Deployment

### Docker Compose (Recommended)

```bash
# Build and start all services
make docker-up

# Access applications
# Frontend: http://localhost:3000
# Backend: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Production Considerations

- **Environment Variables**: Set production values
- **Model Preloading**: Load models at startup for faster response
- **Monitoring**: Enable detailed health checks
- **Scaling**: Use Kubernetes for horizontal scaling

## Additional Resources

### Documentation Files

- **Backend Architecture**: `docs/backend-architecture.md`
- **Run Guide**: `docs/run-guide.md`
- **Indexing Pipeline**: `docs/indexing-pipeline.md`

### Code Examples

- **API Usage**: See `frontend/services/api.ts`
- **Backend Services**: See `backend/services/`
- **Frontend Components**: See `frontend/components/`

### Development Commands

```bash
make help          # Show all available commands
make setup         # Initial environment setup
make install       # Install dependencies
make lint          # Code quality checks
make clean         # Clean build artifacts
```

## Getting Help

### When Things Go Wrong

1. **Check Logs**: Backend and frontend console output
2. **Verify Environment**: Check `.env` files and paths
3. **Test Connectivity**: Use health endpoints
4. **Check Dependencies**: Ensure all packages are installed
5. **Review Documentation**: Check relevant doc files

### Support Channels

- **Issues**: GitHub Issues
- **Documentation**: `/docs` directory
- **API Docs**: `http://localhost:8000/docs` (when backend running)
- **Health Check**: `http://localhost:8000/health/`

---

## Quick Start Checklist

- [ ] Clone repository and initialize submodules
- [ ] Set up backend environment variables
- [ ] Install Python and Node.js dependencies
- [ ] Generate sample data and build indexes
- [ ] Start backend and frontend services
- [ ] Test search functionality
- [ ] Verify data connection and search results

**Next Steps**: After completing this checklist, you'll have a fully functional multi-modal search system ready for development and customization.
