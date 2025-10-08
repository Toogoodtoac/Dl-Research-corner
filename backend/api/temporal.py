"""
Temporal search endpoints for video sequence search
"""

import time

import structlog
from core.config import settings
from fastapi import APIRouter, Depends, HTTPException, Request
from schemas.temporal import (
    TemporalData,
    TemporalMetadata,
    TemporalSearchRequest,
    TemporalSearchResponse,
)
from services.temporal_service import TemporalService

router = APIRouter()
logger = structlog.get_logger()


async def get_temporal_service(request: Request) -> TemporalService:
    """Get temporal service instance"""
    return await request.app.state.model_manager.get_temporal_service()


@router.post("/search")
async def temporal_search(
    request: TemporalSearchRequest,
    temporal_service: TemporalService = Depends(get_temporal_service),
):
    """Temporal video search endpoint"""
    start_time = time.time()

    try:
        logger.info(
            "Temporal search request",
            query=request.query,
            model=request.model_type,
            max_candidates=request.max_candidate_videos,
        )

        result = await temporal_service.temporal_search(
            query=request.query,
            model_type=request.model_type,
            limit=request.limit,
            topk_per_sentence=request.topk_per_sentence,
            max_candidate_videos=request.max_candidate_videos,
            w_min=request.w_min,
            w_max=request.w_max,
        )

        processing_time = (time.time() - start_time) * 1000

        metadata = TemporalMetadata(
            query_time_ms=processing_time,
            model_used=str(request.model_type),
            num_sentences=len(result.sentences),
            num_candidate_videos=len(result.candidate_videos),
        )

        response = TemporalSearchResponse(data=result.dict(), metadata=metadata.dict())

        logger.info(
            "Temporal search completed",
            query=request.query,
            results_count=len(result.results),
            processing_time_ms=processing_time,
        )

        return response

    except Exception as e:
        logger.error("Temporal search failed", query=request.query, error=str(e))
        raise HTTPException(status_code=500, detail=f"Temporal search failed: {str(e)}")


@router.get("/info")
async def temporal_search_info():
    """Get temporal search information and capabilities"""
    return {
        "capabilities": {
            "supported_models": ["clip", "longclip", "clip2video", "beit3"],
            "max_sentences": 10,
            "max_candidate_videos": 100,
            "frame_constraints": {"w_min": 1, "w_max": 50},
        },
        "description": "Temporal search finds video sequences that match multi-sentence queries",
    }
