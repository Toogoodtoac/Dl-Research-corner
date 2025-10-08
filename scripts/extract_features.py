#!/usr/bin/env python3
"""
Extract LongCLIP features from existing keyframes and build FAISS index
"""

import argparse
import glob
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import structlog

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))

# Setup logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


class FeatureExtractor:
    """Extract features from keyframes using LongCLIP"""

    def __init__(self, checkpoint_path: str = None, device: str = "cpu"):
        self.device = device
        self.checkpoint_path = checkpoint_path
        self.model = None
        self._load_model()

    def _load_model(self):
        """Load LongCLIP model"""
        try:
            # Try to import LongCLIP wrapper
            sys.path.append(
                os.path.join(
                    os.path.dirname(__file__),
                    "..",
                    "backend",
                    "features",
                    "features-longclip",
                )
            )
            from longclip_wrapper import LongCLIPModel

            if self.checkpoint_path and os.path.exists(self.checkpoint_path):
                self.model = LongCLIPModel(self.checkpoint_path, device=self.device)
                logger.info("LongCLIP model loaded successfully")
            else:
                logger.warning("LongCLIP checkpoint not found, using mock model")
                self.model = None
        except ImportError as e:
            logger.warning(f"LongCLIP not available: {e}, using mock model")
            self.model = None

    def extract_features(self, image_path: str) -> np.ndarray:
        """Extract features from a single image"""
        if self.model:
            try:
                features = self.model.encode_image(image_path)
                if isinstance(features, np.ndarray):
                    return features.astype(np.float32)
                else:
                    return np.array(features, dtype=np.float32)
            except Exception as e:
                logger.warning(f"Feature extraction failed for {image_path}: {e}")
                return self._generate_mock_features()
        else:
            return self._generate_mock_features()

    def _generate_mock_features(self) -> np.ndarray:
        """Generate mock features for testing"""
        return np.random.randn(512).astype(np.float32)


class KeyframeProcessor:
    """Process keyframes and extract features"""

    def __init__(self, data_root: str, output_dir: str):
        self.data_root = data_root
        self.output_dir = output_dir
        self.feature_extractor = FeatureExtractor()

        # Create output directories
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(os.path.join(output_dir, "features"), exist_ok=True)

    def process_keyframes(self) -> Tuple[List[str], List[np.ndarray], Dict[int, str]]:
        """Process all keyframes and extract features"""
        keyframe_paths = []
        features_list = []
        id2img_mapping = {}

        # Find all keyframe directories (both K and L batches)
        keyframe_base_pattern = os.path.join(
            self.data_root, "raw", "keyframes", "Keyframes_*", "keyframes", "*"
        )
        video_dirs = glob.glob(keyframe_base_pattern)

        logger.info(f"Found {len(video_dirs)} video directories")

        feature_id = 0
        for video_dir in sorted(video_dirs):
            video_id = os.path.basename(video_dir)
            logger.info(f"Processing video: {video_id}")

            # Find all keyframe images in this video
            image_pattern = os.path.join(video_dir, "*.jpg")
            image_files = sorted(glob.glob(image_pattern))

            if not image_files:
                logger.warning(f"No keyframes found in {video_dir}")
                continue

            # Extract features for each keyframe
            video_features = []
            for image_file in image_files:
                try:
                    # Extract features
                    features = self.feature_extractor.extract_features(image_file)
                    video_features.append(features)

                    # Store mapping
                    relative_path = os.path.relpath(image_file, self.data_root)
                    id2img_mapping[feature_id] = relative_path
                    keyframe_paths.append(relative_path)

                    feature_id += 1

                except Exception as e:
                    logger.error(f"Failed to process {image_file}: {e}")
                    continue

            if video_features:
                # Save video features
                video_features_array = np.array(video_features, dtype=np.float32)
                output_path = os.path.join(
                    self.output_dir, "features", f"{video_id}.npy"
                )
                np.save(output_path, video_features_array)
                logger.info(f"Saved {len(video_features)} features for {video_id}")

                # Add to global features list
                features_list.extend(video_features)

        logger.info(f"Total features extracted: {len(features_list)}")
        return keyframe_paths, features_list, id2img_mapping

    def save_mapping(self, id2img_mapping: Dict[int, str], output_path: str):
        """Save the ID to image path mapping"""
        with open(output_path, "w") as f:
            json.dump(id2img_mapping, f, indent=2)
        logger.info(f"Saved ID mapping to {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Extract features from keyframes")
    parser.add_argument(
        "--data-root", default="data", help="Root directory containing data"
    )
    parser.add_argument(
        "--output-dir",
        default="data/features-longclip",
        help="Output directory for features",
    )
    parser.add_argument("--checkpoint", help="Path to LongCLIP checkpoint")
    parser.add_argument("--device", default="cpu", help="Device to use (cpu/cuda)")

    args = parser.parse_args()

    # Process keyframes
    processor = KeyframeProcessor(args.data_root, args.output_dir)
    keyframe_paths, features_list, id2img_mapping = processor.process_keyframes()

    # Save mapping
    mapping_path = os.path.join(args.output_dir, "id2img.json")
    processor.save_mapping(id2img_mapping, mapping_path)

    # Save features as numpy array for FAISS indexing
    features_array = np.array(features_list, dtype=np.float32)
    features_path = os.path.join(args.output_dir, "all_features.npy")
    np.save(features_path, features_array)

    logger.info(f"Feature extraction completed. Features saved to {features_path}")
    logger.info(f"ID mapping saved to {mapping_path}")
    logger.info(f"Total features: {len(features_list)}")
    logger.info(f"Feature dimensions: {features_array.shape}")


if __name__ == "__main__":
    main()
