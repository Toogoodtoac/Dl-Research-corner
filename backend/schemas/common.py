"""
Common schemas used across different endpoints
"""

from enum import Enum
from typing import List, Optional, Union

from pydantic import BaseModel, Field


class ModelType(str, Enum):
    """Supported model types"""

    CLIP = "clip"
    LONGCLIP = "longclip"
    CLIP2VIDEO = "clip2video"
    BEIT3 = "beit3"
    ALL = "all"


class SearchLogic(str, Enum):
    """Search logic for multi-object queries"""

    AND = "AND"
    OR = "OR"


class BaseResponse(BaseModel):
    """Base response model"""

    success: bool = True
    message: str = "Success"
    data: Optional[dict] = None


class ErrorResponse(BaseModel):
    """Error response model"""

    success: bool = False
    error: str
    details: Optional[str] = None


class SearchResult(BaseModel):
    """Search result item"""

    frame_stamp: Optional[float] = None
    image_id: str
    link: Optional[str] = None
    image_url: Optional[str] = None  # URL for displaying the image
    score: float
    watch_url: Optional[str] = None
    ocr_text: Optional[str] = None
    bbox: Optional[List[float]] = None
    video_id: Optional[str] = None
    shot_index: Optional[int] = None
    file_path: Optional[str] = None  # Folder and filename (e.g., "L21_V001/001.jpg")


class PaginationParams(BaseModel):
    """Pagination parameters"""

    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class ModelParams(BaseModel):
    """Model selection parameters"""

    model_type: ModelType = ModelType.CLIP  # Changed default from LONGCLIP to CLIP
    device: Optional[str] = None
