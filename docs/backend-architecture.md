# Backend Architecture

## Overview

The MM-Data Intelligent Agent backend is built with FastAPI, providing a high-performance, async API for multi-modal search and analysis. The architecture emphasizes lazy loading, caching, and modular design.

## Architecture Components

### 1. Core Application (`main.py`)

- **FastAPI Application**: Main entry point with middleware and router configuration
- **Lifespan Management**: Handles startup/shutdown of services and models
- **CORS & Middleware**: Configured for frontend integration and performance

### 2. Configuration (`core/config.py`)

- **Environment-based Settings**: Uses Pydantic settings for type-safe configuration
- **Model Paths**: Centralized configuration for ML model locations
- **Service Settings**: Redis, database, and API configuration

### 3. Logging (`core/logging.py`)

- **Structured Logging**: Uses structlog for consistent, searchable logs
- **Performance Monitoring**: Request timing and error tracking
- **JSON Format**: Machine-readable log output

### 4. API Layer (`api/`)

#### Search Router (`api/search.py`)

- `POST /api/search/text` - Text-based image search
- `POST /api/search/image` - Image-based similarity search
- `POST /api/search/visual` - Visual object detection search
- `POST /api/search/neighbor` - Similar image discovery

#### OCR Router (`api/ocr.py`)

- `POST /api/ocr/extract` - Text extraction from images
- `GET /api/ocr/languages` - Supported OCR languages

#### ASR Router (`api/asr.py`)

- `POST /api/asr/transcribe` - Speech-to-text conversion
- `GET /api/asr/models` - Available ASR models
- `GET /api/asr/languages` - Supported languages

#### Temporal Router (`api/temporal.py`)

- `POST /api/temporal/search` - Video sequence search
- `GET /api/temporal/info` - Capabilities and constraints

#### Health Router (`api/health.py`)

- `GET /health/` - Basic health check
- `GET /health/detailed` - System metrics and status
- `GET /health/ready` - Kubernetes readiness probe

### 5. Service Layer (`services/`)

#### Model Manager (`services/model_manager.py`)

- **Lazy Loading**: Models loaded only when first requested
- **Service Coordination**: Manages all ML service instances
- **Resource Management**: Handles cleanup and memory management

#### Search Service (`services/search_service.py`)

- **FAISS Integration**: Direct integration with existing FAISS processing
- **Multi-model Support**: CLIP, LongCLIP, and CLIP2Video
- **Fallback Handling**: Mock responses when models unavailable

#### OCR Service (`services/ocr_service.py`)

- **Text Extraction**: Image-to-text conversion
- **Multi-language Support**: Vietnamese, English, and other languages
- **Confidence Scoring**: Configurable detection thresholds

#### ASR Service (`services/asr_service.py`)

- **Speech Recognition**: Audio/video transcription
- **Vietnamese Focus**: Primary language support
- **Timestamp Support**: Frame-accurate transcription

#### Temporal Service (`services/temporal_service.py`)

- **Sequence Search**: Multi-sentence video queries
- **Dynamic Programming**: Optimal frame sequence matching
- **Temporal Constraints**: Configurable frame spacing

### 6. Data Models (`schemas/`)

- **Request/Response Models**: Pydantic schemas for API validation
- **Type Safety**: Full TypeScript-like type checking
- **Documentation**: Auto-generated API docs with examples

### 7. Utilities (`utils/`)

- **FAISS Processing**: Migrated from original utils
- **Translation**: Vietnamese-to-English translation
- **Model Wrappers**: CLIP, LongCLIP, and CLIP2Video integrations

## Performance Features

### 1. Lazy Loading

- Models loaded only when first API request arrives
- Reduces startup time and memory usage
- Automatic fallback to mock responses during development

### 2. Caching Strategy

- Redis integration for search results and embeddings
- In-memory caching for frequently accessed data
- Configurable TTL for different data types

### 3. Async Processing

- FastAPI async/await for concurrent request handling
- Non-blocking I/O for database and external API calls
- Background task processing for heavy operations

### 4. Resource Management

- Automatic CUDA memory cleanup
- Model unloading and reloading capabilities
- Memory usage monitoring and optimization

## Development Features

### 1. Mock Mode

- Automatic fallback when models unavailable
- Development-friendly responses
- Easy testing without full model setup

### 2. Health Monitoring

- Comprehensive health checks
- System metrics collection
- Performance monitoring endpoints

### 3. Error Handling

- Structured error responses
- Detailed logging for debugging
- Graceful degradation strategies

## Deployment

### 1. Docker Support

- Multi-stage Docker builds
- GPU support for ML models
- Environment-based configuration

### 2. Kubernetes Ready

- Health check endpoints
- Resource limits and requests
- Horizontal scaling support

### 3. Environment Configuration

- `.env` file support
- Environment variable overrides
- Development vs production modes

## Integration Points

### 1. Frontend Integration

- CORS configured for Next.js frontend
- Consistent API response format
- Real-time search capabilities

### 2. ML Model Integration

- Direct integration with existing FAISS code
- Support for multiple model types
- Extensible model loading system

### 3. External Services

- Redis for caching
- PostgreSQL for metadata (optional)
- File system for model storage

## Future Enhancements

### 1. Model Serving

- TensorFlow Serving integration
- Model versioning and A/B testing
- Automatic model updates

### 2. Advanced Caching

- Embedding vector caching
- Query result caching
- Intelligent cache invalidation

### 3. Monitoring & Analytics

- Prometheus metrics
- Request tracing
- Performance analytics

### 4. Security

- API key authentication
- Rate limiting
- Input validation and sanitization
