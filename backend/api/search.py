"""
Search endpoints for text, image, and visual search
"""

import time
from typing import List

import structlog
from core.config import settings
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from schemas.common import SearchResult
from schemas.search import (
    ImageSearchRequest,
    NeighborSearchRequest,
    SearchMetadata,
    SearchResponse,
    TextSearchRequest,
    VisualSearchRequest,
)
from services.search_service import SearchService

router = APIRouter()
logger = structlog.get_logger()


async def get_search_service(request: Request) -> SearchService:
    """Get search service instance"""
    return await request.app.state.model_manager.get_search_service()


@router.post("/text")
async def text_search(
    request: TextSearchRequest,
    search_service: SearchService = Depends(get_search_service),
):
    """Text-based search endpoint"""
    start_time = time.time()

    try:
        logger.info(
            "Text search request", query=request.query, model=request.model_type
        )

        results = await search_service.text_search(
            query=request.query, model_type=request.model_type, limit=request.limit
        )

        processing_time = (time.time() - start_time) * 1000

        metadata = SearchMetadata(
            total_results=len(results),
            query_time_ms=processing_time,
            model_used=str(request.model_type),
            search_type="text",
        )

        response = SearchResponse(
            data={"results": [result.dict() for result in results]},
            metadata=metadata.dict(),
        )

        logger.info(
            "Text search completed",
            query=request.query,
            results_count=len(results),
            processing_time_ms=processing_time,
        )

        return response

    except Exception as e:
        logger.error("Text search failed", query=request.query, error=str(e))
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.post("/image")
async def image_search(
    request: ImageSearchRequest,
    search_service: SearchService = Depends(get_search_service),
):
    """Image-based search endpoint"""
    start_time = time.time()

    try:
        logger.info("Image search request", model=request.model_type)

        results = await search_service.image_search(
            image_source=request.image_source,
            model_type=request.model_type,
            limit=request.limit,
        )

        processing_time = (time.time() - start_time) * 1000

        metadata = SearchMetadata(
            total_results=len(results),
            query_time_ms=processing_time,
            model_used=str(request.model_type),
            search_type="image",
        )

        response = SearchResponse(
            data={"results": [result.dict() for result in results]},
            metadata=metadata.dict(),
        )

        logger.info(
            "Image search completed",
            results_count=len(results),
            processing_time_ms=processing_time,
        )

        return response

    except Exception as e:
        logger.error("Image search failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Image search failed: {str(e)}")


@router.post("/visual")
async def visual_search(
    request: VisualSearchRequest,
    search_service: SearchService = Depends(get_search_service),
):
    """Visual search with object detection endpoint"""
    start_time = time.time()

    try:
        logger.info(
            "Visual search request",
            object_count=len(request.object_list),
            logic=request.logic,
            model=request.model_type,
        )

        results = await search_service.visual_search(
            object_list=request.object_list,
            logic=request.logic,
            model_type=request.model_type,
            limit=request.limit,
        )

        processing_time = (time.time() - start_time) * 1000

        metadata = SearchMetadata(
            total_results=len(results),
            query_time_ms=processing_time,
            model_used=str(request.model_type),
            search_type="visual",
        )

        response = SearchResponse(
            data={"results": [result.dict() for result in results]},
            metadata=metadata.dict(),
        )

        logger.info(
            "Visual search completed",
            results_count=len(results),
            processing_time_ms=processing_time,
        )

        return response

    except Exception as e:
        logger.error("Visual search failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Visual search failed: {str(e)}")


@router.post("/neighbor")
async def neighbor_search(
    request: NeighborSearchRequest,
    search_service: SearchService = Depends(get_search_service),
):
    """Similar image search endpoint"""
    start_time = time.time()

    try:
        logger.info(
            "Neighbor search request",
            image_id=request.image_id,
            model=request.model_type,
        )

        results = await search_service.neighbor_search(
            image_id=request.image_id,
            model_type=request.model_type,
            limit=request.limit,
        )

        processing_time = (time.time() - start_time) * 1000

        metadata = SearchMetadata(
            total_results=len(results),
            query_time_ms=processing_time,
            model_used=str(request.model_type),
            search_type="neighbor",
        )

        response = SearchResponse(
            data={"results": [result.dict() for result in results]},
            metadata=metadata.dict(),
        )

        logger.info(
            "Neighbor search completed",
            image_id=request.image_id,
            results_count=len(results),
            processing_time_ms=processing_time,
        )

        return response

    except Exception as e:
        logger.error("Neighbor search failed", image_id=request.image_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Neighbor search failed: {str(e)}")


@router.get("/models")
async def list_available_models():
    """List available search models"""
    return {
        "models": [
            {"id": "clip", "name": "CLIP ViT-B/32", "type": "image_text"},
            {"id": "longclip", "name": "Long-CLIP", "type": "image_text"},
            {"id": "clip2video", "name": "CLIP2Video", "type": "video_text"},
            {"id": "beit3", "name": "BEiT-3", "type": "image_text"},
        ]
    }


@router.get("/metadata/video/{video_id}")
async def get_video_metadata(
    video_id: str,
    search_service: SearchService = Depends(get_search_service),
):
    """Get detailed metadata for a specific video"""
    try:
        logger.info(f"Video metadata request for: {video_id}")

        # Get metadata service from search service
        metadata_service = search_service._metadata_service
        if not metadata_service or not metadata_service.is_initialized():
            raise HTTPException(
                status_code=503, detail="Metadata service not available"
            )

        video_summary = metadata_service.get_video_summary(video_id)
        if not video_summary:
            raise HTTPException(status_code=404, detail=f"Video {video_id} not found")

        return JSONResponse(content=video_summary)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get video metadata for {video_id}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get video metadata: {str(e)}"
        )


@router.get("/metadata/frame/{frame_id}")
async def get_frame_metadata(
    frame_id: str,
    search_service: SearchService = Depends(get_search_service),
):
    """Get detailed metadata for a specific frame"""
    try:
        logger.info(f"Frame metadata request for: {frame_id}")

        # Get metadata service from search service
        metadata_service = search_service._metadata_service
        if not metadata_service or not metadata_service.is_initialized():
            raise HTTPException(
                status_code=503, detail="Metadata service not available"
            )

        frame_metadata = metadata_service.get_frame_metadata(frame_id)
        if not frame_metadata:
            raise HTTPException(status_code=404, detail=f"Frame {frame_id} not found")

        return JSONResponse(content=frame_metadata)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get frame metadata for {frame_id}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get frame metadata: {str(e)}"
        )


@router.get("/metadata/videos")
async def get_all_videos(
    search_service: SearchService = Depends(get_search_service),
):
    """Get list of all available videos"""
    try:
        logger.info("All videos metadata request")

        # Get metadata service from search service
        metadata_service = search_service._metadata_service
        if not metadata_service or not metadata_service.is_initialized():
            raise HTTPException(
                status_code=503, detail="Metadata service not available"
            )

        videos = metadata_service.get_all_videos()

        return JSONResponse(content={"videos": videos})

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get all videos: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get videos list: {str(e)}"
        )


@router.get("/metadata/video/{video_id}/frames")
async def get_video_frames(
    video_id: str,
    limit: int = 100,
    search_service: SearchService = Depends(get_search_service),
):
    """Get all frames for a specific video"""
    try:
        logger.info(f"Video frames request for: {video_id}, limit: {limit}")

        # Get metadata service from search service
        metadata_service = search_service._metadata_service
        if not metadata_service or not metadata_service.is_initialized():
            raise HTTPException(
                status_code=503, detail="Metadata service not available"
            )

        frames = metadata_service.search_frames_by_video(video_id, limit)

        return JSONResponse(
            content={
                "video_id": video_id,
                "frames": frames,
                "total_frames": len(frames),
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get frames for video {video_id}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get video frames: {str(e)}"
        )
