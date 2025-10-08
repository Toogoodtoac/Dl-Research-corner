"""
ASR endpoints for speech-to-text conversion
"""

import time

import structlog
from core.config import settings
from fastapi import APIRouter, Depends, HTTPException, Request
from schemas.asr import ASRData, ASRMetadata, ASRRequest, ASRResponse
from services.asr_service import ASRService

router = APIRouter()
logger = structlog.get_logger()


async def get_asr_service(request: Request) -> ASRService:
    """Get ASR service instance"""
    return request.app.state.model_manager.asr_service


@router.post("/transcribe")
async def transcribe_audio(
    request: ASRRequest, asr_service: ASRService = Depends(get_asr_service)
):
    """Transcribe audio to text using ASR"""
    start_time = time.time()

    try:
        logger.info(
            "ASR request received", language=request.language, model=request.model_type
        )

        result = await asr_service.transcribe(
            audio_source=request.audio_source,
            language=request.language,
            model_type=request.model_type,
            timestamp=request.timestamp,
        )

        processing_time = (time.time() - start_time) * 1000

        metadata = ASRMetadata(
            processing_time_ms=processing_time, asr_engine=request.model_type
        )

        response = ASRResponse(data=result.dict(), metadata=metadata.dict())

        logger.info(
            "ASR completed successfully",
            processing_time_ms=processing_time,
            text_length=len(result.full_text),
        )

        return response

    except Exception as e:
        logger.error("ASR failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"ASR failed: {str(e)}")


@router.get("/models")
async def list_available_models():
    """List available ASR models"""
    return {
        "models": [
            {"id": "whisper", "name": "OpenAI Whisper", "type": "multilingual"},
            {"id": "wav2vec", "name": "Facebook Wav2Vec", "type": "multilingual"},
            {"id": "conformer", "name": "Conformer ASR", "type": "multilingual"},
        ]
    }


@router.get("/languages")
async def list_supported_languages():
    """List supported ASR languages"""
    return {
        "languages": [
            {"code": "vi", "name": "Vietnamese", "primary": True},
            {"code": "en", "name": "English"},
            {"code": "zh", "name": "Chinese"},
            {"code": "ja", "name": "Japanese"},
            {"code": "ko", "name": "Korean"},
        ]
    }
