"""
OCR endpoints for text extraction from images
"""

import time

import structlog
from core.config import settings
from fastapi import APIRouter, Depends, HTTPException, Request
from schemas.ocr import OCRData, OCRMetadata, OCRRequest, OCRResponse
from services.ocr_service import OCRService

router = APIRouter()
logger = structlog.get_logger()


async def get_ocr_service(request: Request) -> OCRService:
    """Get OCR service instance"""
    return request.app.state.model_manager.ocr_service


@router.post("/extract")
async def extract_text(
    request: OCRRequest, ocr_service: OCRService = Depends(get_ocr_service)
):
    """Extract text from image using OCR"""
    start_time = time.time()

    try:
        logger.info("OCR request received", language=request.language)

        result = await ocr_service.extract_text(
            image_source=request.image_source,
            language=request.language,
            confidence_threshold=request.confidence_threshold,
        )

        processing_time = (time.time() - start_time) * 1000

        metadata = OCRMetadata(processing_time_ms=processing_time, ocr_engine="default")

        response = OCRResponse(data=result.dict(), metadata=metadata.dict())

        logger.info(
            "OCR completed successfully",
            processing_time_ms=processing_time,
            text_length=len(result.full_text),
        )

        return response

    except Exception as e:
        logger.error("OCR failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"OCR failed: {str(e)}")


@router.get("/languages")
async def list_supported_languages():
    """List supported OCR languages"""
    return {
        "languages": [
            {"code": "en", "name": "English"},
            {"code": "vi", "name": "Vietnamese"},
            {"code": "zh", "name": "Chinese"},
            {"code": "ja", "name": "Japanese"},
            {"code": "ko", "name": "Korean"},
        ]
    }
