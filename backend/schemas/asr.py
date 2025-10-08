"""
ASR-related schemas
"""

from typing import List, Optional, Union

from pydantic import BaseModel, Field

from .common import BaseResponse


class ASRRequest(BaseModel):
    """ASR speech-to-text request"""

    audio_source: Union[str, bytes] = Field(
        ..., description="Audio source (URL, base64, or file)"
    )
    language: str = Field(
        default="vi", description="Language for ASR (default: Vietnamese)"
    )
    model_type: str = Field(default="whisper", description="ASR model to use")
    timestamp: bool = Field(default=True, description="Include timestamps in output")


class ASRTranscript(BaseModel):
    """Individual transcript segment"""

    text: str
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    confidence: Optional[float] = None
    speaker_id: Optional[str] = None


class ASRResponse(BaseModel):
    """ASR response"""

    success: bool = True
    message: str = "ASR completed successfully"
    data: dict = Field(..., description="ASR results")
    metadata: dict = Field(default_factory=dict, description="ASR metadata")


class ASRData(BaseModel):
    """ASR result data"""

    transcript: List[ASRTranscript]
    full_text: str
    detected_language: Optional[str] = None
    duration: Optional[float] = None


class ASRMetadata(BaseModel):
    """ASR metadata"""

    processing_time_ms: float
    audio_duration: Optional[float] = None
    asr_engine: str = "whisper"
    model_version: Optional[str] = None
