"""
Model manager service for lazy loading and managing ML models
"""

import asyncio
from typing import Any, Dict, Optional

import structlog
import torch
from core.config import settings
from services.asr_service import ASRService
from services.ocr_service import OCRService
from services.search_service import SearchService
from services.temporal_service import TemporalService

logger = structlog.get_logger()


class ModelManager:
    """Manages ML models with lazy loading"""

    def __init__(self):
        self._models_loaded = False
        self._loading_lock = asyncio.Lock()

        # Service instances
        self.search_service: Optional[SearchService] = None
        self.ocr_service: Optional[OCRService] = None
        self.asr_service: Optional[ASRService] = None
        self.temporal_service: Optional[TemporalService] = None

        logger.info("ModelManager initialized")

    async def ensure_models_loaded(self):
        """Ensure all models are loaded (lazy loading)"""
        if self._models_loaded:
            return

        async with self._loading_lock:
            if self._models_loaded:  # Double-check pattern
                return

            logger.info("Loading ML models...")

            try:
                # Initialize services (this will trigger model loading)
                self.search_service = SearchService()
                self.ocr_service = OCRService()
                self.asr_service = ASRService()
                self.temporal_service = TemporalService()

                # Services will be loaded lazily when first accessed
                logger.info("Services created, will be loaded on first access")

                self._models_loaded = True
                logger.info("All ML models loaded successfully")

            except Exception as e:
                logger.error("Failed to load ML models", error=str(e))
                raise

    async def get_search_service(self) -> SearchService:
        """Get search service, loading models if needed"""
        await self.ensure_models_loaded()
        return self.search_service

    async def get_ocr_service(self) -> OCRService:
        """Get OCR service, loading models if needed"""
        await self.ensure_models_loaded()
        return self.ocr_service

    async def get_asr_service(self) -> ASRService:
        """Get ASR service, loading models if needed"""
        await self.ensure_models_loaded()
        return self.asr_service

    async def get_temporal_service(self) -> TemporalService:
        """Get temporal service, loading models if needed"""
        await self.ensure_models_loaded()
        return self.temporal_service

    def get_model_status(self) -> Dict[str, Any]:
        """Get status of all models"""
        return {
            "models_loaded": self._models_loaded,
            "device": str(torch.device("cuda" if torch.cuda.is_available() else "cpu")),
            "cuda_available": torch.cuda.is_available(),
            "services": {
                "search": self.search_service is not None,
                "ocr": self.ocr_service is not None,
                "asr": self.asr_service is not None,
                "temporal": self.temporal_service is not None,
            },
        }

    async def cleanup(self):
        """Cleanup resources"""
        logger.info("Cleaning up ModelManager")

        # Cleanup services
        if self.search_service:
            await self.search_service.cleanup()
        if self.ocr_service:
            await self.ocr_service.cleanup()
        if self.asr_service:
            await self.asr_service.cleanup()
        if self.temporal_service:
            await self.temporal_service.cleanup()

        # Clear CUDA cache if available
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        logger.info("ModelManager cleanup completed")
