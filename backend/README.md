# MM-Data Intelligent Agent Backend

FastAPI backend for multi-modal search and analysis with lazy loading and caching.

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Setup Environment

```bash
cp env.example .env
# Edit .env with your paths and settings
```

### 3. Run Development Server

```bash
# Using uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Using the startup script
python run.py

# Using make (from root directory)
make dev-backend
```

## Architecture

### Core Components

- **`main.py`** - FastAPI application entry point
- **`core/`** - Configuration, logging, and core utilities
- **`api/`** - API routers and endpoints
- **`services/`** - Business logic and ML model management
- **`schemas/`** - Pydantic request/response models
- **`utils/`** - Utility functions and ML model wrappers

### Service Layer

- **ModelManager** - Lazy loading and coordination of ML services
- **SearchService** - Text, image, and visual search
- **OCRService** - Text extraction from images
- **ASRService** - Speech-to-text conversion
- **TemporalService** - Video sequence search

## API Endpoints

### Health Checks

- `GET /health/` - Basic health status
- `GET /health/detailed` - System metrics
- `GET /health/ready` - Readiness probe

### Search API

- `POST /api/search/text` - Text-based image search
- `POST /api/search/image` - Image similarity search
- `POST /api/search/visual` - Visual object search
- `POST /api/search/neighbor` - Similar image discovery

### OCR API

- `POST /api/ocr/extract` - Extract text from images
- `GET /api/ocr/languages` - Supported languages

### ASR API

- `POST /api/asr/transcribe` - Speech-to-text conversion
- `GET /api/asr/models` - Available models
- `GET /api/asr/languages` - Supported languages

### Temporal API

- `POST /api/temporal/search` - Video sequence search
- `GET /api/temporal/info` - Capabilities info

## Configuration

### Environment Variables

- `HOST` - Server host (default: 0.0.0.0)
- `PORT` - Server port (default: 8000)
- `DEBUG` - Debug mode (default: false)
- `REDIS_URL` - Redis connection URL
- `LAZY_LOAD_MODELS` - Lazy load ML models (default: true)

### Model Paths

- `SUPPORT_MODELS_DIR` - Directory containing ML models
- `FAISS_*_PATH` - Paths to FAISS index files
- `ID2IMG_JSON_PATH` - Image ID to path mapping

## Testing

### Run Tests

```bash
# All tests
pytest tests/ -v

# Specific test file
pytest tests/test_health.py -v

# With coverage
pytest tests/ --cov=backend --cov-report=html
```

### Test Structure

- `tests/backend/` - Backend API tests
- `tests/unit/` - Unit tests for services
- `tests/integration/` - Integration tests

## Performance Features

### Lazy Loading

- ML models loaded only when first requested
- Reduces startup time and memory usage
- Automatic fallback to mock responses

### Caching

- Redis integration for search results
- In-memory caching for embeddings
- Configurable TTL for different data types

### Async Processing

- FastAPI async/await for concurrent requests
- Non-blocking I/O operations
- Background task processing

## Docker

### Build Image

```bash
docker build -f infra/Dockerfile.backend -t mm-data-backend .
```

### Run Container

```bash
docker run -p 8000:8000 mm-data-backend
```

### With Docker Compose

```bash
# From root directory
make docker-up
```

## Development

### Code Quality

```bash
# Format code
black .
isort .

# Lint code
flake8 .

# Type checking
mypy .
```

### Adding New Endpoints

1. Create schema in `schemas/`
2. Add service method in appropriate service
3. Create router endpoint in `api/`
4. Add tests in `tests/`

### Adding New Models

1. Create model wrapper in `utils/`
2. Add to appropriate service
3. Update configuration
4. Add tests

## Documentation

- **API Docs**: Available at `http://localhost:8000/docs` when running
- **ReDoc**: Alternative docs at `http://localhost:8000/redoc`
- **OpenAPI Schema**: `http://localhost:8000/openapi.json`

## Troubleshooting

### Common Issues

1. **Import Errors**
   - Ensure you're in the backend directory
   - Check Python path includes backend directory
   - Verify all dependencies are installed

2. **Model Loading Failures**
   - Check model paths in configuration
   - Verify model files exist
   - Check CUDA availability for GPU models

3. **FAISS Errors**
   - Verify index file paths
   - Check index file integrity
   - Ensure FAISS version compatibility

### Debug Mode

Enable debug mode for detailed error messages:

```bash
export DEBUG=true
python run.py
```
