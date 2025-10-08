"""
Temporal search schemas
"""

from typing import List, Optional

from pydantic import BaseModel, Field

from .common import ModelType, SearchResult


class TemporalSearchRequest(BaseModel):
    """Temporal search request"""

    query: str = Field(..., description="Search query text")
    model_type: ModelType = ModelType.CLIP
    limit: int = Field(default=20, ge=1, le=100)
    topk_per_sentence: int = Field(default=200, ge=1, le=1000)
    max_candidate_videos: int = Field(default=30, ge=1, le=100)
    w_min: int = Field(default=1, ge=1)
    w_max: Optional[int] = Field(default=None, ge=1)


class TemporalSearchResponse(BaseModel):
    """Temporal search response"""

    success: bool = True
    message: str = "Temporal search completed successfully"
    data: dict = Field(
        default_factory=dict,
        description="Temporal search results and metadata",
    )


class TemporalResult(BaseModel):
    """Temporal search result"""

    video_id: str
    frames: List[int]
    images: List[str]
    paths: List[str]
    score: float


class TemporalData(BaseModel):
    """Temporal search data"""

    sentences: List[str]
    per_sentence: List[dict]
    candidate_videos: List[str]
    results: List[TemporalResult]


class TemporalMetadata(BaseModel):
    """Temporal search metadata"""

    query_time_ms: float
    model_used: str
    num_sentences: int
    num_candidate_videos: int
