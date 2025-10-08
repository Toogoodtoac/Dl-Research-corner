"""
Main FastAPI application for MM-Data Intelligent Agent
"""

import os
import sys
from contextlib import asynccontextmanager

# Add the backend directory to the Python path
backend_dir = os.path.dirname(__file__)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

import structlog
import uvicorn
from api import asr, health, ocr, search, temporal
from core.config import settings
from core.logging import setup_logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles

# Setup logging
setup_logging()
logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    logger.info("Starting MM-Data Intelligent Agent Backend")

    # Initialize services (lazy loading)
    from services.model_manager import ModelManager

    app.state.model_manager = ModelManager()

    logger.info("Backend services initialized")

    yield

    # Shutdown
    logger.info("Shutting down MM-Data Intelligent Agent Backend")
    if hasattr(app.state, "model_manager"):
        await app.state.model_manager.cleanup()


# Create FastAPI app
app = FastAPI(
    title="MM-Data Intelligent Agent API",
    description="Multi-modal search and analysis backend for video/image data",
    version="2.0.0",
    lifespan=lifespan,
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# Mount static files for serving images
try:
    # Use the env path manager to get the correct data root directory
    # This will be the local data directory in dev, or Google Drive in prod
    from env_path_manager import get_path_manager

    path_manager = get_path_manager()
    data_dir = path_manager.get_data_root()

    if os.path.exists(data_dir):
        app.mount("/data", StaticFiles(directory=data_dir), name="data")
        logger.info(f"Static files mounted at /data from {data_dir}")
        logger.info(f"Environment: {path_manager.env}")
    else:
        logger.warning(f"Data directory not found: {data_dir}")
except Exception as e:
    logger.warning(f"Failed to mount static files: {e}")

# Include routers
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(search.router, prefix="/api/search", tags=["search"])
app.include_router(ocr.router, prefix="/api/ocr", tags=["ocr"])
app.include_router(asr.router, prefix="/api/asr", tags=["asr"])
app.include_router(temporal.router, prefix="/api/temporal", tags=["temporal"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "MM-Data Intelligent Agent Backend",
        "version": "2.0.0",
        "status": "running",
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error("Unhandled exception", exc_info=exc)
    return HTTPException(status_code=500, detail="Internal server error")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info",
    )
