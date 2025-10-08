"""
Search-related schemas
"""

from typing import List, Optional

from pydantic import BaseModel, Field

from .common import ModelType, SearchLogic, SearchResult


class TextSearchRequest(BaseModel):
    """Text search request"""

    query: str = Field(..., description="Search query text")
    model_type: ModelType = ModelType.CLIP
    limit: int = Field(default=20, ge=1, le=100)


class TextSearchResponse(BaseModel):
    """Text search response"""

    success: bool = True
    message: str = "Search completed successfully"
    data: dict = Field(
        default_factory=dict,
        description="Search results and metadata",
    )


class ImageSearchRequest(BaseModel):
    """Image search request"""

    image_source: str = Field(..., description="Image source (URL, path, or base64)")
    model_type: ModelType = ModelType.CLIP
    limit: int = Field(default=20, ge=1, le=100)


class ImageSearchResponse(BaseModel):
    """Image search response"""

    success: bool = True
    message: str = "Search completed successfully"
    data: dict = Field(
        default_factory=dict,
        description="Search results and metadata",
    )


class VisualSearchRequest(BaseModel):
    """Visual search request"""

    object_list: List[dict] = Field(..., description="List of detected objects")
    logic: SearchLogic = SearchLogic.AND
    model_type: ModelType = ModelType.CLIP
    limit: int = Field(default=20, ge=1, le=100)


class VisualSearchResponse(BaseModel):
    """Visual search response"""

    success: bool = True
    message: str = "Search completed successfully"
    data: dict = Field(
        default_factory=dict,
        description="Search results and metadata",
    )


class NeighborSearchRequest(BaseModel):
    """Neighbor search request"""

    image_id: str = Field(..., description="Image ID to find neighbors for")
    model_type: ModelType = ModelType.CLIP
    limit: int = Field(default=20, ge=1, le=100)


class NeighborSearchResponse(BaseModel):
    """Neighbor search response"""

    success: bool = True
    message: str = "Search completed successfully"
    data: dict = Field(
        default_factory=dict,
        description="Search results and metadata",
    )


class SearchMetadata(BaseModel):
    """Search metadata"""

    total_results: int
    query_time_ms: float
    model_used: str
    search_type: str


class SearchResponse(BaseModel):
    """Search response"""

    data: dict = Field(..., description="Search results")
    metadata: dict = Field(default_factory=dict, description="Search metadata")
