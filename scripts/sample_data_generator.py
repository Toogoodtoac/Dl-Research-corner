#!/usr/bin/env python3
"""
Generate sample data for testing the video indexing pipeline
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

import cv2
import numpy as np
import structlog

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))

from indexer.hdf5_storage import create_hdf5_file

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


class SampleDataGenerator:
    """Generate sample data for testing"""

    def __init__(self, config: Dict):
        self.config = config
        self.num_videos = config.get("num_videos", 5)
        self.frames_per_video = config.get("frames_per_video", 20)
        self.feature_dim = config.get("feature_dim", 512)
        self.output_dir = config.get("output_dir", "examples/sample_data")

    def generate_sample_videos(self) -> List[str]:
        """Generate sample video files"""
        os.makedirs(self.output_dir, exist_ok=True)

        video_files = []

        for i in range(self.num_videos):
            video_name = f"sample_video_{i+1:02d}"
            video_path = os.path.join(self.output_dir, f"{video_name}.mp4")

            # Generate simple video with colored rectangles
            self._generate_video(video_path, video_name, self.frames_per_video)
            video_files.append(video_path)

            logger.info(f"Generated sample video: {video_path}")

        return video_files

    def _generate_video(self, output_path: str, video_name: str, num_frames: int):
        """Generate a simple video file"""
        # Video parameters
        width, height = 640, 480
        fps = 10

        # Create video writer
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

        # Generate frames
        for frame_num in range(num_frames):
            # Create base frame
            frame = np.ones((height, width, 3), dtype=np.uint8) * 128

            # Add colored rectangles that move
            colors = [
                (255, 0, 0),  # Red
                (0, 255, 0),  # Green
                (0, 0, 255),  # Blue
                (255, 255, 0),  # Yellow
                (255, 0, 255),  # Magenta
            ]

            # Add moving rectangles
            for j, color in enumerate(colors):
                x = int((frame_num * 10 + j * 100) % (width - 100))
                y = int((frame_num * 5 + j * 50) % (height - 100))

                cv2.rectangle(frame, (x, y), (x + 80, y + 80), color, -1)

                # Add text label
                cv2.putText(
                    frame,
                    f"obj_{j}",
                    (x + 5, y + 45),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (255, 255, 255),
                    2,
                )

            # Add frame number
            cv2.putText(
                frame,
                f"Frame {frame_num}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (255, 255, 255),
                2,
            )

            # Add video name
            cv2.putText(
                frame,
                video_name,
                (10, height - 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (255, 255, 255),
                2,
            )

            out.write(frame)

        out.release()

    def generate_sample_hdf5(self, video_files: List[str]) -> str:
        """Generate sample HDF5 file with features and metadata"""
        os.makedirs(self.output_dir, exist_ok=True)

        # Calculate total frames
        total_frames = len(video_files) * self.frames_per_video

        # Create HDF5 file
        hdf5_path = os.path.join(self.output_dir, "sample_features.h5")

        with create_hdf5_file(
            hdf5_path,
            total_frames,
            {
                "clip2video": self.feature_dim,
                "longclip": self.feature_dim,
                "mock": self.feature_dim,
            },
        ) as storage:

            # Generate features and metadata
            frame_idx = 0

            for video_idx, video_path in enumerate(video_files):
                video_name = Path(video_path).stem

                for frame_idx_in_video in range(self.frames_per_video):
                    # Generate mock features
                    features = {
                        "clip2video": np.random.randn(1, self.feature_dim).astype(
                            np.float32
                        ),
                        "longclip": np.random.randn(1, self.feature_dim).astype(
                            np.float32
                        ),
                        "mock": np.random.randn(1, self.feature_dim).astype(np.float32),
                    }

                    # Store features
                    storage.store_features(frame_idx, features)

                    # Store metadata
                    storage.store_metadata(
                        frame_idx,
                        [video_name],
                        [f"frame_{frame_idx_in_video:06d}"],
                        [frame_idx_in_video],
                    )

                    frame_idx += 1

            # Generate sample bounding boxes
            bboxes = []
            for frame_idx in range(total_frames):
                # Generate 1-3 random bboxes per frame
                num_bboxes = np.random.randint(1, 4)

                for bbox_idx in range(num_bboxes):
                    # Random bbox coordinates
                    x1 = np.random.uniform(0, 0.8)
                    y1 = np.random.uniform(0, 0.8)
                    x2 = x1 + np.random.uniform(0.1, 0.2)
                    y2 = y1 + np.random.uniform(0.1, 0.2)

                    # Random class and color
                    class_id = np.random.randint(0, 5)
                    colors = ["red", "green", "blue", "yellow", "orange"]
                    color_name = colors[np.random.randint(0, len(colors))]

                    bboxes.append(
                        {
                            "bbox": [x1, y1, x2, y2],
                            "frame_index": frame_idx,
                            "class_id": class_id,
                            "color_name": color_name,
                        }
                    )

            # Store bboxes
            if bboxes:
                storage.store_bboxes(bboxes)

        logger.info(f"Generated sample HDF5 file: {hdf5_path}")
        return hdf5_path

    def generate_sample_shots(self, video_files: List[str]) -> Dict:
        """Generate sample shot metadata for videos"""
        shots_data = {}

        for video_path in video_files:
            video_name = Path(video_path).stem

            # Generate 3-8 shots per video
            num_shots = np.random.randint(3, 9)
            shots = []

            frames_per_shot = self.frames_per_video // num_shots
            remaining_frames = self.frames_per_video % num_shots

            current_frame = 0

            for shot_idx in range(num_shots):
                # Calculate shot boundaries
                shot_frames = frames_per_shot
                if shot_idx < remaining_frames:
                    shot_frames += 1

                start_frame = current_frame
                end_frame = current_frame + shot_frames - 1

                shot = {
                    "shot_id": shot_idx,
                    "start_frame": start_frame,
                    "end_frame": end_frame,
                    "start_time": start_frame / 10.0,  # Assuming 10 fps
                    "end_time": end_frame / 10.0,
                    "duration": shot_frames / 10.0,
                    "boundary_strength": np.random.uniform(0.5, 1.0),
                }

                shots.append(shot)
                current_frame += shot_frames

            # Save shots metadata
            shots_file = os.path.join(self.output_dir, f"{video_name}_shots.json")
            with open(shots_file, "w") as f:
                json.dump(shots, f, indent=2)

            shots_data[video_name] = {"shots": shots, "shots_file": shots_file}

            logger.info(f"Generated shots for {video_name}: {len(shots)} shots")

        return shots_data

    def generate_sample_dataset(self) -> Dict:
        """Generate complete sample dataset"""
        logger.info("Generating sample dataset...")

        # Generate sample videos
        video_files = self.generate_sample_videos()

        # Generate shot metadata
        shots_data = self.generate_sample_shots(video_files)

        # Generate HDF5 features
        hdf5_path = self.generate_sample_hdf5(video_files)

        # Create dataset summary
        dataset_summary = {
            "num_videos": len(video_files),
            "total_frames": len(video_files) * self.frames_per_video,
            "feature_dimension": self.feature_dim,
            "video_files": video_files,
            "shots_data": shots_data,
            "hdf5_file": hdf5_path,
            "output_directory": self.output_dir,
        }

        # Save dataset summary
        summary_file = os.path.join(self.output_dir, "dataset_summary.json")
        with open(summary_file, "w") as f:
            json.dump(dataset_summary, f, indent=2)

        logger.info(f"Sample dataset generated successfully: {summary_file}")
        return dataset_summary


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
    parser = argparse.ArgumentParser(description="Generate sample data for testing")
    parser.add_argument(
        "--output", "-o", default="examples/sample_data", help="Output directory"
    )
    parser.add_argument("--config", "-c", help="Configuration file path")
    parser.add_argument(
        "--num-videos", type=int, default=5, help="Number of sample videos to generate"
    )
    parser.add_argument(
        "--frames-per-video", type=int, default=20, help="Frames per video"
    )
    parser.add_argument(
        "--feature-dim", type=int, default=512, help="Feature dimension"
    )
    parser.add_argument(
        "--clean", action="store_true", help="Clean output directory before generating"
    )

    args = parser.parse_args()

    # Load configuration
    config = {}
    if args.config:
        config = load_config(args.config)

    # Default configuration
    default_config = {
        "num_videos": args.num_videos,
        "frames_per_video": args.frames_per_video,
        "feature_dim": args.feature_dim,
        "output_dir": args.output,
    }

    # Merge with user config
    config = {**default_config, **config}

    # Clean output directory if requested
    if args.clean and os.path.exists(args.output):
        import shutil

        shutil.rmtree(args.output)
        logger.info(f"Cleaned output directory: {args.output}")

    # Initialize generator
    generator = SampleDataGenerator(config)

    # Generate sample dataset
    dataset_summary = generator.generate_sample_dataset()

    logger.info("Sample dataset generation completed!")
    logger.info(
        f"Generated {dataset_summary['num_videos']} videos with {dataset_summary['total_frames']} total frames"
    )
    logger.info(f"Output directory: {dataset_summary['output_directory']}")
    logger.info(f"HDF5 file: {dataset_summary['hdf5_file']}")


if __name__ == "__main__":
    main()
