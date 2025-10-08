"""
OCR-related schemas
"""

from typing import List, Optional, Union

from pydantic import BaseModel, Field

from .common import BaseResponse


class OCRRequest(BaseModel):
    """OCR text extraction request"""

    image_source: Union[str, bytes] = Field(
        ..., description="Image source (URL, base64, or file)"
    )
    language: str = Field(default="en", description="Language for OCR")
    confidence_threshold: float = Field(
        default=0.5, ge=0.0, le=1.0, description="Minimum confidence for text detection"
    )


class OCRTextBlock(BaseModel):
    """Individual text block detected by OCR"""

    text: str
    confidence: float
    bbox: List[float] = Field(..., description="Bounding box [x1, y1, x2, y2]")
    language: Optional[str] = None


class OCRResponse(BaseModel):
    """OCR response"""

    success: bool = True
    message: str = "OCR completed successfully"
    data: dict = Field(..., description="OCR results")
    metadata: dict = Field(default_factory=dict, description="OCR metadata")


class OCRData(BaseModel):
    """OCR result data"""

    text_blocks: List[OCRTextBlock]
    full_text: str
    detected_language: Optional[str] = None


class OCRMetadata(BaseModel):
    """OCR metadata"""

    processing_time_ms: float
    image_size: Optional[List[int]] = None
    ocr_engine: str = "default"
