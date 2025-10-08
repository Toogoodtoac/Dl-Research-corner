# Development Workflow Guide

## Overview

This guide covers the complete development workflow for the MM-Data Intelligent Agent, from daily development tasks to testing and deployment. It's designed to help team members understand how to work with the system effectively.

## Daily Development Workflow

### Morning Setup

```bash
# 1. Navigate to project
cd mm-data-intelligent-agent

# 2. Pull latest changes
git pull origin main

# 3. Check system status
make help

# 4. Start development environment
make dev
```

### Development Session

```bash
# Terminal 1: Backend development
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Frontend development
cd frontend
pnpm dev

# Terminal 3: Monitoring and testing
# Keep open for running tests, checking logs, etc.
```

### End of Day

```bash
# 1. Stop development servers (Ctrl+C)
# 2. Commit your changes
git add .
git commit -m "feat: description of changes"
git push origin feature-branch

# 3. Clean up (optional)
make clean  # Only if you want to clean build artifacts
```

## Development Commands Reference

### Essential Commands

```bash
# Development
make dev              # Start both frontend and backend
make dev-frontend     # Frontend only
make dev-backend      # Backend only

# Building
make build            # Build both frontend and backend
make build-frontend   # Frontend only
make build-backend    # Backend only

# Testing
make test             # Run all tests
make test-frontend    # Frontend tests
make test-backend     # Backend tests

# Utilities
make clean            # Clean build artifacts
make install          # Install dependencies
make lint             # Code quality checks
```

### Data Pipeline Commands

```bash
# Generate sample data
make sample-data      # Create test videos and features

# Run indexing pipeline
make index            # Complete pipeline (sample-data + ingest + build indexes)

# Individual steps
make ingest           # Feature extraction only
make build-faiss      # Build FAISS indexes only
make build-lucene     # Build text indexes only
```

### Docker Commands

```bash
# Docker development
make docker-up        # Start all services
make docker-down      # Stop services
make docker-build     # Build images
```

## Project Structure Understanding

### Backend Structure

```
backend/
├── api/                    # API endpoints
│   ├── search.py          # Search APIs
│   ├── ocr.py             # OCR APIs
│   ├── asr.py             # ASR APIs
│   ├── temporal.py        # Video search APIs
│   └── health.py          # Health check APIs
├── services/               # Business logic
│   ├── model_manager.py   # ML model management
│   ├── search_service.py  # Search functionality
│   ├── ocr_service.py     # OCR processing
│   └── asr_service.py     # Speech recognition
├── models/                 # ML model wrappers
├── schemas/                # Pydantic models
├── core/                   # Configuration and utilities
├── utils/                  # Helper functions
└── main.py                 # FastAPI application entry point
```

### Frontend Structure

```
frontend/
├── app/                    # Next.js App Router
│   ├── page.tsx           # Main search interface
│   ├── find-image/        # ID-based search
│   ├── image/[id]/        # Image detail view
│   └── api/               # API routes
├── components/             # React components
│   ├── search-bar.tsx     # Search input
│   ├── search-results.tsx # Results display
│   ├── symbol-grid.tsx    # Visual search
│   └── ui/                # Shadcn/UI components
├── services/               # API service layer
├── hooks/                 # Custom React hooks
├── lib/                   # Utility functions
└── types/                 # TypeScript definitions
```

## Development Workflow Patterns

### 1. Adding New API Endpoints

#### Backend Changes

```python
# 1. Add new schema in schemas/
# schemas/new_feature.py
from pydantic import BaseModel

class NewFeatureRequest(BaseModel):
    param1: str
    param2: int

class NewFeatureResponse(BaseModel):
    success: bool
    data: dict

# 2. Add service logic in services/
# services/new_feature_service.py
class NewFeatureService:
    async def process_feature(self, request: NewFeatureRequest):
        # Implementation logic
        pass

# 3. Add API endpoint in api/
# api/new_feature.py
from fastapi import APIRouter, Depends
from schemas.new_feature import NewFeatureRequest, NewFeatureResponse
from services.new_feature_service import NewFeatureService

router = APIRouter()

@router.post("/", response_model=NewFeatureResponse)
async def new_feature(
    request: NewFeatureRequest,
    service: NewFeatureService = Depends()
):
    result = await service.process_feature(request)
    return NewFeatureResponse(success=True, data=result)

# 4. Include router in main.py
from api import new_feature
app.include_router(new_feature.router, prefix="/api/new-feature", tags=["new-feature"])
```

#### Frontend Integration

```typescript
// 1. Add API service function
// services/api.ts
export async function newFeature(params: NewFeatureParams): Promise<NewFeatureResult> {
  const response = await fetch(`${BASE_URL}/api/new-feature`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });

  if (!response.ok) {
    throw new Error(`API call failed: ${response.status}`);
  }

  return response.json();
}

// 2. Add TypeScript types
// types/new-feature.ts
export interface NewFeatureParams {
  param1: string;
  param2: number;
}

export interface NewFeatureResult {
  success: boolean;
  data: any;
}

// 3. Create React component
// components/new-feature.tsx
'use client';

import { useState } from 'react';
import { newFeature } from '@/services/api';
import type { NewFeatureParams } from '@/types/new-feature';

export default function NewFeature() {
  const [params, setParams] = useState<NewFeatureParams>({ param1: '', param2: 0 });

  const handleSubmit = async () => {
    try {
      const result = await newFeature(params);
      console.log('Feature result:', result);
    } catch (error) {
      console.error('Feature error:', error);
    }
  };

  return (
    <div>
      {/* Component JSX */}
    </div>
  );
}
```

### 2. Adding New Search Models

#### Backend Model Integration

```python
# 1. Add model wrapper in models/
# models/new_model.py
import torch
from typing import Optional

class NewModelWrapper:
    def __init__(self, checkpoint_path: str, device: str = "cpu"):
        self.device = device
        self.model = self._load_model(checkpoint_path)

    def _load_model(self, checkpoint_path: str):
        # Model loading logic
        pass

    def encode_text(self, text: str) -> torch.Tensor:
        # Text encoding logic
        pass

    def encode_image(self, image) -> torch.Tensor:
        # Image encoding logic
        pass

# 2. Update model manager
# services/model_manager.py
from models.new_model import NewModelWrapper

class ModelManager:
    def __init__(self):
        self.new_model = None

    async def get_new_model(self) -> NewModelWrapper:
        if self.new_model is None:
            self.new_model = NewModelWrapper(
                settings.NEW_MODEL_CHECKPOINT,
                settings.MODEL_DEVICE
            )
        return self.new_model

# 3. Add to search service
# services/search_service.py
async def search_with_new_model(self, query: str, limit: int = 20):
    model = await self.model_manager.get_new_model()
    # Search implementation
    pass
```

#### Frontend Model Selection

```typescript
// 1. Add model type to search interface
// components/search-bar.tsx
interface SearchBarProps {
  onSearch: (query: string, model: string) => void;
}

export default function SearchBar({ onSearch }: SearchBarProps) {
  const [query, setQuery] = useState('');
  const [model, setModel] = useState('longclip');

  const handleSearch = () => {
    onSearch(query, model);
  };

  return (
    <div>
      <input
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Enter search query..."
      />
      <select value={model} onChange={(e) => setModel(e.target.value)}>
        <option value="longclip">LongCLIP</option>
        <option value="clip">CLIP</option>
        <option value="clip2video">CLIP2Video</option>
        <option value="new_model">New Model</option>
      </select>
      <button onClick={handleSearch}>Search</button>
    </div>
  );
}
```

## Testing Workflow

### Backend Testing

```bash
# Run all backend tests
cd backend
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_search_service.py -v

# Run with coverage
python -m pytest tests/ --cov=. --cov-report=html

# Run specific test function
python -m pytest tests/test_search_service.py::test_text_search -v
```

### Frontend Testing

```bash
# Run frontend tests
cd frontend
pnpm test

# Run tests in watch mode
pnpm test:watch

# Run tests with coverage
pnpm test:coverage

# Run specific test file
pnpm test components/search-bar.test.tsx
```

### Integration Testing

```bash
# Test complete system
make test-installation

# Test API endpoints
curl http://localhost:8000/health/
curl -X POST http://localhost:8000/api/search/text \
  -H "Content-Type: application/json" \
  -d '{"query":"test","model_type":"longclip","limit":5}'

# Test frontend-backend connection
# Open http://localhost:3000 and perform search
```

## Debugging Workflow

### Backend Debugging

```bash
# 1. Enable debug logging
export LOG_LEVEL=DEBUG

# 2. Start with debug mode
cd backend
python -m uvicorn main:app --reload --log-level debug

# 3. Check specific endpoints
curl -v http://localhost:8000/health/detailed

# 4. Monitor logs for errors
# Look for: Model loading, FAISS index loading, API errors
```

### Frontend Debugging

```bash
# 1. Start frontend with debugging
cd frontend
pnpm dev

# 2. Open browser developer tools
# - Console tab for JavaScript errors
# - Network tab for API calls
# - Sources tab for breakpoint debugging

# 3. Check API responses
# Look for: CORS errors, 404/500 responses, empty data
```

### Common Debugging Scenarios

#### 1. Search Returns No Results

```bash
# Check backend logs
cd backend
python -m uvicorn main:app --reload --log-level debug

# Look for:
# - "FAISS index loaded successfully"
# - "Model loaded successfully"
# - "Search query processed"

# Test API directly
curl -X POST http://localhost:8000/api/search/text \
  -H "Content-Type: application/json" \
  -d '{"query":"test","model_type":"longclip","limit":5}'
```

#### 2. Frontend Can't Connect to Backend

```bash
# Check backend status
curl http://localhost:8000/health/

# Check CORS configuration
# Verify backend/.env has correct ALLOWED_ORIGINS

# Check frontend environment
cat frontend/.env.local

# Verify ports match
# Backend: 8000, Frontend: 3000
```

#### 3. Model Loading Errors

```bash
# Check model paths
cat backend/.env | grep -E "(LONGCLIP|CLIP|MODEL)"

# Verify model files exist
ls -la support_models/Long-CLIP/checkpoints/

# Check file permissions
ls -la support_models/Long-CLIP/checkpoints/*.pt

# Restart backend after fixing paths
make dev-backend
```

## Performance Monitoring

### Backend Performance

```bash
# Check system health
curl http://localhost:8000/health/detailed

# Monitor response times
time curl -X POST http://localhost:8000/api/search/text \
  -H "Content-Type: application/json" \
  -d '{"query":"test","model_type":"longclip","limit":5}'

# Check memory usage
ps aux | grep uvicorn
```

### Frontend Performance

```bash
# Use browser developer tools
# - Performance tab for rendering metrics
# - Network tab for API response times
# - Console for JavaScript performance

# Check bundle size
cd frontend
pnpm build
# Look for bundle analysis output
```

## Deployment Workflow

### Development to Staging

```bash
# 1. Test locally
make test
make build

# 2. Commit changes
git add .
git commit -m "feat: ready for staging"
git push origin feature-branch

# 3. Create pull request
# Merge to staging branch

# 4. Deploy to staging
# Use staging environment variables
```

### Staging to Production

```bash
# 1. Test on staging
# Verify all functionality works

# 2. Merge to main
git checkout main
git merge staging
git push origin main

# 3. Deploy to production
make docker-up  # Production environment
```

### Environment Configuration

```bash
# Development
cp backend/env.example backend/.env
# Edit with local paths

# Staging
cp backend/env.example backend/.env.staging
# Edit with staging paths

# Production
cp backend/env.example backend/.env.production
# Edit with production paths
```

## Data Pipeline Workflow

### Daily Data Updates

```bash
# 1. Check data freshness
ls -la dict/ data/

# 2. Update if needed
make index  # Regenerate indexes

# 3. Verify data integrity
python scripts/build_faiss.py --validate
python scripts/build_lucene.py --test-search
```

### Adding New Data

```bash
# 1. Place new media in data/raw/
cp new_videos/* data/raw/

# 2. Extract features
python scripts/ingest.py \
  --input data/raw \
  --output data/hdf5_features

# 3. Rebuild indexes
make build-faiss
make build-lucene

# 4. Update environment variables if paths changed
# Edit backend/.env
```

## Documentation Workflow

### Code Documentation

```python
# Python docstrings
def search_images(query: str, limit: int = 20) -> List[SearchResult]:
    """
    Search for images using text query.

    Args:
        query: Text description of desired images
        limit: Maximum number of results to return

    Returns:
        List of search results with scores and metadata

    Raises:
        ValueError: If query is empty
        ModelNotLoadedError: If ML model is not available
    """
    pass
```

```typescript
// TypeScript documentation
/**
 * Search for images using text query
 * @param query - Text description of desired images
 * @param limit - Maximum number of results to return
 * @returns Promise resolving to search results
 * @throws Error if search fails
 */
export async function searchImages(
  query: string,
  limit: number = 20
): Promise<SearchResult[]> {
  // Implementation
}
```

### API Documentation

```python
# FastAPI endpoint documentation
@router.post("/search/text", response_model=SearchResponse)
async def text_search(
    request: TextSearchRequest,
    service: SearchService = Depends()
) -> SearchResponse:
    """
    Search for images using text query.

    This endpoint performs semantic search across the image database
    using CLIP/LongCLIP models to find images matching the text description.

    Args:
        request: Search parameters including query text and model type

    Returns:
        Search results with ranked images and metadata

    Raises:
        HTTPException: If search fails or model is not available
    """
    pass
```

## Getting Help

### When You're Stuck

1. **Check Documentation**: Review relevant doc files
2. **Check Logs**: Backend and frontend console output
3. **Test Components**: Isolate the problem area
4. **Search Issues**: Check GitHub issues for similar problems
5. **Ask Team**: Use team communication channels

### Useful Debugging Commands

```bash
# System status
make help
curl http://localhost:8000/health/detailed

# Data verification
ls -la dict/ data/ support_models/
python -c "import faiss; print('FAISS available')"

# Service status
ps aux | grep -E "(uvicorn|next)"
netstat -tlnp | grep -E "(3000|8000)"

# Log analysis
tail -f backend/logs/app.log
tail -f frontend/.next/server.log
```

---

## Daily Development Checklist

### Morning

- [ ] Pull latest changes
- [ ] Check system status
- [ ] Start development environment
- [ ] Verify data connection

### During Development

- [ ] Write tests for new features
- [ ] Update documentation
- [ ] Test API endpoints
- [ ] Check frontend integration

### End of Day

- [ ] Commit changes
- [ ] Push to remote
- [ ] Update task status
- [ ] Plan next day's work

**Remember**: The development workflow is iterative. Start small, test frequently, and build up complexity gradually. Always verify that your changes don't break existing functionality.
