#!/usr/bin/env python3
"""
Video ingestion pipeline for MM-Data Intelligent Agent
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import structlog

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))

from feature_extractors.color_detector import ColorDetector
from feature_extractors.object_detector import ObjectDetector
from feature_extractors.temporal_extractor import TemporalExtractor
from indexer.hdf5_storage import HDF5Storage, create_hdf5_file

# Try to import model wrappers
try:
    from features.features_clip2video.clip2video_wrapper import (
        CLIP2VideoFeatureExtraction,
    )

    CLIP2VIDEO_AVAILABLE = True
except ImportError:
    CLIP2VIDEO_AVAILABLE = False
    print("Warning: CLIP2Video not available, using mock features")

try:
    from features.features_longclip.longclip_wrapper import LongCLIPModel

    LONGCLIP_AVAILABLE = True
except ImportError:
    LONGCLIP_AVAILABLE = False
    print("Warning: LongCLIP not available, using mock features")

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


class VideoIngestionPipeline:
    """Main video ingestion pipeline"""

    def __init__(self, config: Dict):
        self.config = config
        self.temporal_extractor = TemporalExtractor(
            threshold=config.get("temporal_threshold", 0.3),
            min_shot_length=config.get("min_shot_length", 1.0),
        )
        self.object_detector = ObjectDetector(
            model_type=config.get("object_detection_model", "mock")
        )
        self.color_detector = ColorDetector()

        # Initialize feature extractors
        self.clip2video_extractor = None
        self.longclip_extractor = None
        self._initialize_feature_extractors()

    def _initialize_feature_extractors(self):
        """Initialize feature extraction models"""
        if CLIP2VIDEO_AVAILABLE:
            try:
                checkpoint_dir = self.config.get("clip2video_checkpoint")
                clip_weights = self.config.get("clip_weights_path")
                if checkpoint_dir and clip_weights:
                    self.clip2video_extractor = CLIP2VideoFeatureExtraction(
                        checkpoint_dir=checkpoint_dir,
                        clip_weights_path=clip_weights,
                        device=self.config.get("device", "cpu"),
                    )
                    logger.info("CLIP2Video feature extractor initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize CLIP2Video: {e}")

        if LONGCLIP_AVAILABLE:
            try:
                checkpoint_path = self.config.get("longclip_checkpoint")
                if checkpoint_path:
                    self.longclip_extractor = LongCLIPModel(
                        checkpoint_path=checkpoint_path,
                        device=self.config.get("device", "cpu"),
                    )
                    logger.info("LongCLIP feature extractor initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize LongCLIP: {e}")

    def process_video(
        self,
        video_path: str,
        output_dir: str,
        extract_features: bool = True,
        extract_objects: bool = True,
        extract_colors: bool = True,
    ) -> Dict:
        """Process a single video file"""
        logger.info(f"Processing video: {video_path}")

        # Create output directory
        video_name = Path(video_path).stem
        video_output_dir = os.path.join(output_dir, video_name)
        os.makedirs(video_output_dir, exist_ok=True)

        # Extract temporal information
        logger.info("Extracting temporal information...")
        shots = self.temporal_extractor.detect_shots(
            video_path, method=self.config.get("shot_detection_method", "histogram")
        )

        # Save shot metadata
        shots_file = os.path.join(video_output_dir, "shots.json")
        self.temporal_extractor.save_shot_metadata(shots, shots_file)

        # Extract representative frames
        logger.info("Extracting representative frames...")
        representative_frames = self.temporal_extractor.extract_representative_frames(
            shots, video_path, frames_per_shot=self.config.get("frames_per_shot", 3)
        )

        # Process frames
        frame_features = []
        frame_metadata = []
        all_bboxes = []

        for i, frame_info in enumerate(representative_frames):
            frame = frame_info["frame"]
            frame_number = frame_info["frame_number"]
            shot_id = frame_info["shot_id"]

            # Extract features
            features = {}
            if extract_features:
                features = self._extract_frame_features(frame, frame_info)

            # Extract objects and colors
            bboxes = []
            if extract_objects or extract_colors:
                bboxes = self._extract_frame_objects_and_colors(
                    frame, frame_info, extract_objects, extract_colors
                )

            # Store frame information
            frame_features.append(features)
            frame_metadata.append(
                {
                    "video_id": video_name,
                    "frame_id": f"frame_{frame_number:06d}",
                    "shot_id": shot_id,
                    "timestamp": frame_info["timestamp"],
                    "frame_number": frame_number,
                }
            )

            # Store bbox information
            for bbox in bboxes:
                bbox["frame_index"] = i
                all_bboxes.append(bbox)

            if (i + 1) % 10 == 0:
                logger.info(f"Processed {i + 1}/{len(representative_frames)} frames")

        # Create HDF5 file
        hdf5_path = os.path.join(video_output_dir, f"{video_name}_features.h5")
        self._create_hdf5_file(hdf5_path, frame_features, frame_metadata, all_bboxes)

        # Return processing summary
        summary = {
            "video_path": video_path,
            "video_name": video_name,
            "total_shots": len(shots),
            "total_frames": len(representative_frames),
            "total_bboxes": len(all_bboxes),
            "output_dir": video_output_dir,
            "hdf5_file": hdf5_path,
            "shots_file": shots_file,
        }

        logger.info(f"Video processing completed: {summary}")
        return summary

    def _extract_frame_features(self, frame: np.ndarray, frame_info: Dict) -> Dict:
        """Extract features from a frame"""
        features = {}

        # CLIP2Video features
        if self.clip2video_extractor:
            try:
                # Mock CLIP2Video features for now (would need video tensor)
                features["clip2video"] = np.random.randn(512).astype(np.float32)
            except Exception as e:
                logger.warning(f"CLIP2Video feature extraction failed: {e}")
                features["clip2video"] = np.random.randn(512).astype(np.float32)

        # LongCLIP features
        if self.longclip_extractor:
            try:
                # Convert frame to PIL Image for LongCLIP
                import cv2
                from PIL import Image

                # Convert BGR to RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_image = Image.fromarray(frame_rgb)

                # Save temporary image for LongCLIP
                temp_path = f"/tmp/temp_frame_{frame_info['frame_number']}.jpg"
                pil_image.save(temp_path)

                # Extract features
                longclip_features = self.longclip_extractor.encode_image(temp_path)
                features["longclip"] = longclip_features.flatten()

                # Clean up
                os.remove(temp_path)

            except Exception as e:
                logger.warning(f"LongCLIP feature extraction failed: {e}")
                features["longclip"] = np.random.randn(512).astype(np.float32)

        # Mock features if no extractors available
        if not features:
            features["mock"] = np.random.randn(512).astype(np.float32)

        return features

    def _extract_frame_objects_and_colors(
        self,
        frame: np.ndarray,
        frame_info: Dict,
        extract_objects: bool,
        extract_colors: bool,
    ) -> List[Dict]:
        """Extract objects and colors from a frame"""
        bboxes = []

        if extract_objects:
            # Detect objects
            detections = self.object_detector.detect_objects(frame)

            for detection in detections:
                bbox_info = {
                    "bbox": detection["bbox"],
                    "class_id": detection["class_id"],
                    "class_name": detection["class_name"],
                    "confidence": detection["confidence"],
                    "color_name": "unknown",
                }

                # Extract color information
                if extract_colors:
                    colors = self.color_detector.detect_colors(frame, detection["bbox"])
                    if colors:
                        bbox_info["color_name"] = colors[0]["color_name"]

                bboxes.append(bbox_info)

        return bboxes

    def _create_hdf5_file(
        self,
        hdf5_path: str,
        frame_features: List[Dict],
        frame_metadata: List[Dict],
        bboxes: List[Dict],
    ):
        """Create HDF5 file with features and metadata"""
        if not frame_features:
            logger.warning("No features to store")
            return

        # Determine feature dimensions
        feature_dims = {}
        for feature_name, feature_array in frame_features[0].items():
            if isinstance(feature_array, np.ndarray):
                feature_dims[feature_name] = feature_array.shape[0]
            else:
                feature_dims[feature_name] = 1

        # Create HDF5 file
        with create_hdf5_file(hdf5_path, len(frame_features), feature_dims) as storage:
            # Store features
            for i, features in enumerate(frame_features):
                frame_features_dict = {}
                for feature_name, feature_array in features.items():
                    if isinstance(feature_array, np.ndarray):
                        frame_features_dict[feature_name] = feature_array.reshape(1, -1)
                    else:
                        frame_features_dict[feature_name] = np.array(
                            [feature_array]
                        ).reshape(1, -1)

                storage.store_features(i, frame_features_dict)

            # Store metadata
            video_ids = [meta["video_id"] for meta in frame_metadata]
            frame_ids = [meta["frame_id"] for meta in frame_metadata]
            shot_ids = [meta["shot_id"] for meta in frame_metadata]

            storage.store_metadata(0, video_ids, frame_ids, shot_ids)

            # Store bboxes
            if bboxes:
                storage.store_bboxes(bboxes)

        logger.info(f"Created HDF5 file: {hdf5_path}")

    def process_video_collection(
        self, input_dir: str, output_dir: str, video_extensions: List[str] = None
    ) -> List[Dict]:
        """Process a collection of videos"""
        if video_extensions is None:
            video_extensions = [".mp4", ".avi", ".mov", ".mkv", ".wmv"]

        # Find video files
        video_files = []
        for ext in video_extensions:
            video_files.extend(Path(input_dir).glob(f"**/*{ext}"))

        if not video_files:
            logger.warning(f"No video files found in {input_dir}")
            return []

        logger.info(f"Found {len(video_files)} video files")

        # Process each video
        results = []
        for i, video_path in enumerate(video_files):
            try:
                logger.info(f"Processing video {i+1}/{len(video_files)}: {video_path}")
                result = self.process_video(str(video_path), output_dir)
                results.append(result)

            except Exception as e:
                logger.error(f"Failed to process {video_path}: {e}")
                continue

        logger.info(f"Completed processing {len(results)} videos")
        return results


def load_config(config_path: str) -> Dict:
    """Load configuration from file"""
    if not os.path.exists(config_path):
        logger.warning(f"Config file not found: {config_path}, using defaults")
        return {}

    with open(config_path, "r") as f:
        config = json.load(f)

    return config


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Video ingestion pipeline")
    parser.add_argument(
        "--input", "-i", required=True, help="Input directory or video file"
    )
    parser.add_argument("--output", "-o", required=True, help="Output directory")
    parser.add_argument("--config", "-c", help="Configuration file path")
    parser.add_argument(
        "--extract-features", action="store_true", default=True, help="Extract features"
    )
    parser.add_argument(
        "--extract-objects", action="store_true", default=True, help="Extract objects"
    )
    parser.add_argument(
        "--extract-colors", action="store_true", default=True, help="Extract colors"
    )
    parser.add_argument(
        "--video-only", action="store_true", help="Process single video file"
    )

    args = parser.parse_args()

    # Load configuration
    config = {}
    if args.config:
        config = load_config(args.config)

    # Default configuration
    default_config = {
        "temporal_threshold": 0.3,
        "min_shot_length": 1.0,
        "shot_detection_method": "histogram",
        "frames_per_shot": 3,
        "object_detection_model": "mock",
        "device": "cpu",
        "clip2video_checkpoint": None,
        "clip_weights_path": None,
        "longclip_checkpoint": None,
    }

    # Merge with user config
    config = {**default_config, **config}

    # Initialize pipeline
    pipeline = VideoIngestionPipeline(config)

    # Process input
    if args.video_only or os.path.isfile(args.input):
        # Single video file
        result = pipeline.process_video(
            args.input,
            args.output,
            extract_features=args.extract_features,
            extract_objects=args.extract_objects,
            extract_colors=args.extract_colors,
        )
        results = [result]
    else:
        # Directory of videos
        results = pipeline.process_video_collection(args.input, args.output)

    # Save processing summary
    summary_file = os.path.join(args.output, "ingestion_summary.json")
    with open(summary_file, "w") as f:
        json.dump(results, f, indent=2)

    logger.info(f"Processing summary saved to {summary_file}")
    logger.info(f"Successfully processed {len(results)} videos")


if __name__ == "__main__":
    main()
