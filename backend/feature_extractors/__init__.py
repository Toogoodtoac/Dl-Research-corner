"""
Feature extraction modules for video processing
"""

from .color_detector import ColorDetector
from .object_detector import ObjectDetector
from .temporal_extractor import TemporalExtractor

__all__ = ["ObjectDetector", "ColorDetector", "TemporalExtractor"]
