"""
Color detection for video frames and bounding boxes
"""

from collections import Counter
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np
import structlog

logger = structlog.get_logger()


class ColorDetector:
    """Color detection and analysis for video frames"""

    def __init__(self):
        # Define basic color names and their HSV ranges
        self.color_ranges = {
            "red": [
                ([0, 50, 50], [10, 255, 255]),  # Lower red
                ([170, 50, 50], [180, 255, 255]),  # Upper red
            ],
            "orange": [([10, 50, 50], [25, 255, 255])],
            "yellow": [([25, 50, 50], [35, 255, 255])],
            "green": [([35, 50, 50], [85, 255, 255])],
            "blue": [([85, 50, 50], [130, 255, 255])],
            "purple": [([130, 50, 50], [170, 255, 255])],
            "pink": [([145, 50, 50], [165, 255, 255])],
            "brown": [([10, 100, 20], [20, 255, 200])],
            "gray": [([0, 0, 40], [180, 30, 220])],
            "white": [([0, 0, 200], [180, 30, 255])],
            "black": [([0, 0, 0], [180, 255, 30])],
        }

        # Color name mapping for more descriptive names
        self.color_names = {
            "red": ["red", "crimson", "scarlet", "maroon"],
            "orange": ["orange", "tangerine", "amber"],
            "yellow": ["yellow", "gold", "lemon"],
            "green": ["green", "emerald", "lime", "olive"],
            "blue": ["blue", "navy", "azure", "teal"],
            "purple": ["purple", "violet", "lavender", "magenta"],
            "pink": ["pink", "rose", "fuchsia"],
            "brown": ["brown", "tan", "beige", "chocolate"],
            "gray": ["gray", "grey", "silver"],
            "white": ["white", "ivory", "cream"],
            "black": ["black", "charcoal", "onyx"],
        }

    def detect_colors(self, frame: np.ndarray, bbox: List[float] = None) -> List[Dict]:
        """Detect dominant colors in frame or bounding box"""
        if bbox is None:
            # Analyze entire frame
            roi = frame
        else:
            # Extract bounding box region
            x1, y1, x2, y2 = [int(coord) for coord in bbox]
            roi = frame[y1:y2, x1:x2]

        if roi.size == 0:
            return []

        # Convert to HSV
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

        # Analyze colors
        color_counts = {}
        total_pixels = hsv.shape[0] * hsv.shape[1]

        for color_name, ranges in self.color_ranges.items():
            mask = np.zeros(hsv.shape[:2], dtype=np.uint8)

            for lower, upper in ranges:
                lower = np.array(lower, dtype=np.uint8)
                upper = np.array(upper, dtype=np.uint8)
                color_mask = cv2.inRange(hsv, lower, upper)
                mask = cv2.bitwise_or(mask, color_mask)

            # Count pixels of this color
            pixel_count = cv2.countNonZero(mask)
            percentage = (pixel_count / total_pixels) * 100

            if percentage > 5:  # Only include colors with >5% presence
                color_counts[color_name] = {
                    "percentage": percentage,
                    "pixel_count": pixel_count,
                }

        # Sort by percentage and return top colors
        sorted_colors = sorted(
            color_counts.items(), key=lambda x: x[1]["percentage"], reverse=True
        )

        results = []
        for color_name, stats in sorted_colors[:3]:  # Top 3 colors
            results.append(
                {
                    "color_name": color_name,
                    "percentage": stats["percentage"],
                    "pixel_count": stats["pixel_count"],
                    "descriptive_names": self.color_names.get(color_name, [color_name]),
                }
            )

        return results

    def get_dominant_color(self, frame: np.ndarray, bbox: List[float] = None) -> str:
        """Get the most dominant color"""
        colors = self.detect_colors(frame, bbox)
        if colors:
            return colors[0]["color_name"]
        return "unknown"

    def get_color_palette(
        self, frame: np.ndarray, bbox: List[float] = None, num_colors: int = 5
    ) -> List[Dict]:
        """Get color palette with percentages"""
        colors = self.detect_colors(frame, bbox)
        return colors[:num_colors]

    def analyze_color_distribution(
        self, frame: np.ndarray, bbox: List[float] = None
    ) -> Dict:
        """Analyze color distribution in frame/bbox"""
        colors = self.detect_colors(frame, bbox)

        if not colors:
            return {"total_colors": 0, "dominant_color": "unknown", "color_entropy": 0}

        # Calculate color entropy (diversity)
        percentages = [c["percentage"] for c in colors]
        total_percentage = sum(percentages)

        if total_percentage > 0:
            normalized_percentages = [p / total_percentage for p in percentages]
            entropy = -sum(
                p * np.log2(p) if p > 0 else 0 for p in normalized_percentages
            )
        else:
            entropy = 0

        return {
            "total_colors": len(colors),
            "dominant_color": colors[0]["color_name"],
            "color_entropy": entropy,
            "color_distribution": colors,
        }

    def get_color_name_from_rgb(self, rgb: Tuple[int, int, int]) -> str:
        """Get color name from RGB values"""
        # Convert RGB to HSV
        rgb_array = np.uint8([[rgb]])
        hsv = cv2.cvtColor(rgb_array, cv2.COLOR_RGB2HSV)[0][0]

        # Find closest color
        min_distance = float("inf")
        closest_color = "unknown"

        for color_name, ranges in self.color_ranges.items():
            for lower, upper in ranges:
                lower = np.array(lower)
                upper = np.array(upper)

                # Check if HSV falls within range
                if np.all(hsv >= lower) and np.all(hsv <= upper):
                    return color_name

                # Calculate distance to range center
                center = (lower + upper) / 2
                distance = np.linalg.norm(hsv - center)

                if distance < min_distance:
                    min_distance = distance
                    closest_color = color_name

        return closest_color

    def enhance_color_description(self, color_name: str, percentage: float) -> str:
        """Create enhanced color description"""
        if percentage > 80:
            intensity = "very dominant"
        elif percentage > 60:
            intensity = "dominant"
        elif percentage > 40:
            intensity = "prominent"
        elif percentage > 20:
            intensity = "present"
        else:
            intensity = "subtle"

        descriptive_names = self.color_names.get(color_name, [color_name])
        descriptive_name = descriptive_names[0]

        return f"{intensity} {descriptive_name}"

    def get_color_contrast(self, color1: str, color2: str) -> float:
        """Calculate color contrast between two colors"""
        # Simplified contrast calculation
        contrast_scores = {
            ("black", "white"): 1.0,
            ("red", "green"): 0.8,
            ("blue", "yellow"): 0.9,
            ("black", "yellow"): 0.9,
            ("white", "blue"): 0.8,
        }

        # Check both orderings
        pair1 = (color1, color2)
        pair2 = (color2, color1)

        for pair in [pair1, pair2]:
            if pair in contrast_scores:
                return contrast_scores[pair]

        # Default contrast for other combinations
        return 0.5

    def create_color_summary(self, frame: np.ndarray, bbox: List[float] = None) -> str:
        """Create a natural language summary of colors"""
        colors = self.detect_colors(frame, bbox)

        if not colors:
            return "No significant colors detected"

        if len(colors) == 1:
            color = colors[0]
            return f"The frame is predominantly {self.enhance_color_description(color['color_name'], color['percentage'])}"

        # Multiple colors
        descriptions = []
        for color in colors[:3]:
            desc = self.enhance_color_description(
                color["color_name"], color["percentage"]
            )
            descriptions.append(desc)

        if len(descriptions) == 2:
            return f"The frame shows {descriptions[0]} and {descriptions[1]}"
        else:
            return f"The frame features {', '.join(descriptions[:-1])}, and {descriptions[-1]}"
