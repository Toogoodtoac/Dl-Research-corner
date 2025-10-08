"""
OCR service for text extraction from images
"""

from typing import Union

import structlog
from schemas.ocr import OCRData, OCRTextBlock

logger = structlog.get_logger()


class OCRService:
    """OCR service for text extraction"""

    def __init__(self):
        self._model_loaded = False
        logger.info("OCRService initialized")

    async def extract_text(
        self,
        image_source: Union[str, bytes],
        language: str = "en",
        confidence_threshold: float = 0.5,
    ) -> OCRData:
        """Extract text from image using OCR"""
        logger.info(
            "OCR text extraction", language=language, confidence=confidence_threshold
        )

        # TODO: Implement actual OCR using models like EasyOCR, PaddleOCR, or Tesseract

        # Mock response for development
        mock_blocks = [
            OCRTextBlock(
                text="Sample OCR Text",
                confidence=0.95,
                bbox=[100, 100, 300, 150],
                language=language,
            )
        ]

        return OCRData(
            text_blocks=mock_blocks,
            full_text="Sample OCR Text",
            detected_language=language,
        )

    async def cleanup(self):
        """Cleanup resources"""
        logger.info("Cleaning up OCRService")
        self._model_loaded = False
