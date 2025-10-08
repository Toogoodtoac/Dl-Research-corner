"""
Temporal analysis and shot detection for videos
"""

import os
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np
import structlog
from scipy.spatial.distance import cosine

logger = structlog.get_logger()


class TemporalExtractor:
    """Temporal analysis and shot detection for videos"""

    def __init__(self, threshold: float = 0.3, min_shot_length: float = 1.0):
        self.threshold = threshold
        self.min_shot_length = min_shot_length

    def extract_keyframes(
        self, video_path: str, fps: int = 5, max_frames: int = 100
    ) -> List[Dict]:
        """Extract keyframes from video"""
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise RuntimeError(f"Could not open video: {video_path}")

        # Get video properties
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        video_fps = cap.get(cv2.CAP_PROP_FPS)
        duration = total_frames / video_fps

        logger.info(
            f"Processing video: {total_frames} frames, {duration:.2f}s, {video_fps:.2f} fps"
        )

        # Calculate frame interval
        frame_interval = max(1, int(video_fps / fps))

        keyframes = []
        frame_count = 0
        last_frame = None

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_count % frame_interval == 0:
                # Convert to grayscale for comparison
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

                # Check if this is a keyframe
                is_keyframe = True
                if last_frame is not None:
                    # Calculate frame difference
                    diff = self._calculate_frame_difference(last_frame, gray)
                    is_keyframe = diff > self.threshold

                if is_keyframe:
                    keyframe_info = {
                        "frame_number": frame_count,
                        "timestamp": frame_count / video_fps,
                        "frame": frame.copy(),
                        "gray": gray.copy(),
                    }
                    keyframes.append(keyframe_info)
                    last_frame = gray.copy()

                    if len(keyframes) >= max_frames:
                        break

            frame_count += 1

        cap.release()

        logger.info(f"Extracted {len(keyframes)} keyframes from video")
        return keyframes

    def detect_shots(
        self, video_path: str, method: str = "histogram", min_shot_length: float = None
    ) -> List[Dict]:
        """Detect shots in video using different methods"""
        if min_shot_length is None:
            min_shot_length = self.min_shot_length

        if method == "histogram":
            return self._detect_shots_histogram(video_path, min_shot_length)
        elif method == "optical_flow":
            return self._detect_shots_optical_flow(video_path, min_shot_length)
        else:
            raise ValueError(f"Unknown shot detection method: {method}")

    def _detect_shots_histogram(
        self, video_path: str, min_shot_length: float
    ) -> List[Dict]:
        """Detect shots using histogram comparison"""
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise RuntimeError(f"Could not open video: {video_path}")

        video_fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        shots = []
        current_shot_start = 0
        last_histogram = None

        frame_count = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Calculate histogram
            hist = cv2.calcHist(
                [frame], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256]
            )
            hist = cv2.normalize(hist, hist).flatten()

            if last_histogram is not None:
                # Compare histograms
                similarity = 1 - cosine(hist, last_histogram)

                if similarity < self.threshold:
                    # Shot boundary detected
                    shot_duration = (frame_count - current_shot_start) / video_fps

                    if shot_duration >= min_shot_length:
                        shots.append(
                            {
                                "shot_id": len(shots),
                                "start_frame": current_shot_start,
                                "end_frame": frame_count - 1,
                                "start_time": current_shot_start / video_fps,
                                "end_time": (frame_count - 1) / video_fps,
                                "duration": shot_duration,
                                "boundary_strength": 1 - similarity,
                            }
                        )

                    current_shot_start = frame_count

            last_histogram = hist
            frame_count += 1

        # Add final shot
        if frame_count > current_shot_start:
            shot_duration = (frame_count - current_shot_start) / video_fps
            if shot_duration >= min_shot_length:
                shots.append(
                    {
                        "shot_id": len(shots),
                        "start_frame": current_shot_start,
                        "end_frame": frame_count - 1,
                        "start_time": current_shot_start / video_fps,
                        "end_time": (frame_count - 1) / video_fps,
                        "duration": shot_duration,
                        "boundary_strength": 1.0,
                    }
                )

        cap.release()

        logger.info(f"Detected {len(shots)} shots using histogram method")
        return shots

    def _detect_shots_optical_flow(
        self, video_path: str, min_shot_length: float
    ) -> List[Dict]:
        """Detect shots using optical flow analysis"""
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise RuntimeError(f"Could not open video: {video_path}")

        video_fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        shots = []
        current_shot_start = 0
        prev_frame = None

        frame_count = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if prev_frame is not None:
                # Calculate optical flow
                prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
                curr_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

                # Use Lucas-Kanade optical flow
                flow = cv2.calcOpticalFlowFarneback(
                    prev_gray, curr_gray, None, 0.5, 3, 15, 3, 5, 1.2, 0
                )

                # Calculate flow magnitude
                magnitude = np.sqrt(flow[..., 0] ** 2 + flow[..., 1] ** 2)
                mean_magnitude = np.mean(magnitude)

                # Detect shot boundary based on flow magnitude
                if mean_magnitude > self.threshold * 100:  # Scale threshold for flow
                    shot_duration = (frame_count - current_shot_start) / video_fps

                    if shot_duration >= min_shot_length:
                        shots.append(
                            {
                                "shot_id": len(shots),
                                "start_frame": current_shot_start,
                                "end_frame": frame_count - 1,
                                "start_time": current_shot_start / video_fps,
                                "end_time": (frame_count - 1) / video_fps,
                                "duration": shot_duration,
                                "boundary_strength": mean_magnitude / 100,
                            }
                        )

                    current_shot_start = frame_count

            prev_frame = frame.copy()
            frame_count += 1

        # Add final shot
        if frame_count > current_shot_start:
            shot_duration = (frame_count - current_shot_start) / video_fps
            if shot_duration >= min_shot_length:
                shots.append(
                    {
                        "shot_id": len(shots),
                        "start_frame": current_shot_start,
                        "end_frame": frame_count - 1,
                        "start_time": current_shot_start / video_fps,
                        "end_time": (frame_count - 1) / video_fps,
                        "duration": shot_duration,
                        "boundary_strength": 1.0,
                    }
                )

        cap.release()

        logger.info(f"Detected {len(shots)} shots using optical flow method")
        return shots

    def _calculate_frame_difference(
        self, frame1: np.ndarray, frame2: np.ndarray
    ) -> float:
        """Calculate difference between two frames"""
        # Use mean squared error
        diff = cv2.absdiff(frame1, frame2)
        mse = np.mean(diff.astype(np.float32) ** 2)
        return mse / 255.0  # Normalize to [0, 1]

    def extract_representative_frames(
        self, shots: List[Dict], video_path: str, frames_per_shot: int = 3
    ) -> List[Dict]:
        """Extract representative frames from each shot"""
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise RuntimeError(f"Could not open video: {video_path}")

        representative_frames = []

        for shot in shots:
            start_frame = shot["start_frame"]
            end_frame = shot["end_frame"]

            # Calculate frame positions for this shot
            if frames_per_shot == 1:
                frame_positions = [start_frame + (end_frame - start_frame) // 2]
            else:
                frame_positions = np.linspace(
                    start_frame, end_frame, frames_per_shot, dtype=int
                )

            for frame_pos in frame_positions:
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_pos)
                ret, frame = cap.read()

                if ret:
                    representative_frames.append(
                        {
                            "shot_id": shot["shot_id"],
                            "frame_number": frame_pos,
                            "timestamp": frame_pos / cap.get(cv2.CAP_PROP_FPS),
                            "frame": frame.copy(),
                            "shot_info": shot,
                        }
                    )

        cap.release()

        logger.info(
            f"Extracted {len(representative_frames)} representative frames from {len(shots)} shots"
        )
        return representative_frames

    def analyze_temporal_patterns(self, shots: List[Dict]) -> Dict:
        """Analyze temporal patterns in shots"""
        if not shots:
            return {}

        durations = [shot["duration"] for shot in shots]
        boundary_strengths = [shot["boundary_strength"] for shot in shots]

        analysis = {
            "total_shots": len(shots),
            "total_duration": sum(durations),
            "avg_shot_duration": np.mean(durations),
            "min_shot_duration": min(durations),
            "max_shot_duration": max(durations),
            "shot_duration_std": np.std(durations),
            "avg_boundary_strength": np.mean(boundary_strengths),
            "shot_pattern": self._classify_shot_pattern(durations),
        }

        return analysis

    def _classify_shot_pattern(self, durations: List[float]) -> str:
        """Classify shot pattern based on duration distribution"""
        if len(durations) < 3:
            return "insufficient_data"

        # Calculate coefficient of variation
        cv = np.std(durations) / np.mean(durations)

        if cv < 0.3:
            return "uniform"
        elif cv < 0.7:
            return "moderate_variation"
        else:
            return "high_variation"

    def save_shot_metadata(self, shots: List[Dict], output_path: str) -> None:
        """Save shot metadata to JSON file"""
        import json

        # Convert numpy types to native Python types
        serializable_shots = []
        for shot in shots:
            serializable_shot = {}
            for key, value in shot.items():
                if isinstance(value, np.integer):
                    serializable_shot[key] = int(value)
                elif isinstance(value, np.floating):
                    serializable_shot[key] = float(value)
                else:
                    serializable_shot[key] = value
            serializable_shots.append(serializable_shot)

        with open(output_path, "w") as f:
            json.dump(serializable_shots, f, indent=2)

        logger.info(f"Saved shot metadata to {output_path}")

    def load_shot_metadata(self, input_path: str) -> List[Dict]:
        """Load shot metadata from JSON file"""
        import json

        with open(input_path, "r") as f:
            shots = json.load(f)

        logger.info(f"Loaded shot metadata from {input_path}: {len(shots)} shots")
        return shots
