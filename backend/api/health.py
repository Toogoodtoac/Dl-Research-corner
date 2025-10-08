"""
Health check endpoints
"""

import time

import psutil
import structlog
from core.config import settings
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

router = APIRouter()
logger = structlog.get_logger()


@router.get("/")
async def health_check():
    """Basic health check"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "service": "mm-data-intelligent-agent-backend",
    }


@router.get("/detailed")
async def detailed_health_check():
    """Detailed health check with system metrics"""
    try:
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        # Service status
        service_status = {
            "status": "healthy",
            "timestamp": time.time(),
            "service": "mm-data-intelligent-agent-backend",
            "version": "2.0.0",
            "system": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "disk_percent": disk.percent,
                "uptime": time.time() - psutil.boot_time(),
            },
        }

        logger.info("Health check completed", **service_status)
        return service_status

    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return JSONResponse(
            status_code=500,
            content={"status": "unhealthy", "error": str(e), "timestamp": time.time()},
        )


@router.get("/ready")
async def readiness_check():
    """Readiness check for Kubernetes"""
    try:
        # Check if models are loaded (if lazy loading is disabled)
        if not settings.LAZY_LOAD_MODELS:
            # Add model availability checks here
            pass

        return {"status": "ready", "timestamp": time.time()}
    except Exception as e:
        logger.error("Readiness check failed", error=str(e))
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "error": str(e), "timestamp": time.time()},
        )
