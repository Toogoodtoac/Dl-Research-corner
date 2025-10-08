"""
Metadata service for handling video-frame relationships and detailed information
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import structlog
from core.config import settings

logger = structlog.get_logger()


class MetadataService:
    """Service for managing video-frame metadata and relationships"""

    def __init__(self):
        self._id2img_mapping = None
        self._keyframe_mapping = None
        self._video_info = None
        self._initialized = False

    async def initialize(self):
        """Initialize the metadata service by loading mapping files"""
        if self._initialized:
            return

        try:
            # Load ID to image mapping
            if os.path.exists(settings.ID2IMG_JSON_PATH):
                with open(settings.ID2IMG_JSON_PATH, "r", encoding="utf-8") as f:
                    self._id2img_mapping = json.load(f)
                logger.info(
                    f"Loaded ID to image mapping: {len(self._id2img_mapping)} entries"
                )
            else:
                logger.warning(
                    f"ID to image mapping not found at: {settings.ID2IMG_JSON_PATH}"
                )
                self._id2img_mapping = {}

            # Load keyframe mapping
            if os.path.exists(settings.MAP_KEYFRAMES_PATH):
                with open(settings.MAP_KEYFRAMES_PATH, "r", encoding="utf-8") as f:
                    self._keyframe_mapping = json.load(f)
                logger.info(
                    f"Loaded keyframe mapping: {len(self._keyframe_mapping)} entries"
                )
            else:
                logger.warning(
                    f"Keyframe mapping not found at: {settings.MAP_KEYFRAMES_PATH}"
                )
                self._keyframe_mapping = {}

            # Initialize video information
            self._video_info = self._build_video_info()

            self._initialized = True
            logger.info("Metadata service initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize metadata service: {e}")
            self._initialized = False

    def _build_video_info(self) -> Dict[str, Dict]:
        """Build video information from the data structure"""
        video_info = {}

        try:
            # Scan video directory for available videos
            if os.path.exists(settings.VIDEO_DATA_DIR):
                for video_file in os.listdir(settings.VIDEO_DATA_DIR):
                    if video_file.endswith(".mp4"):
                        video_id = video_file.replace(".mp4", "")
                        video_info[video_id] = {
                            "filename": video_file,
                            "path": os.path.join(settings.VIDEO_DATA_DIR, video_file),
                            "keyframes": [],
                        }

                # Scan keyframe directory for corresponding keyframes
                if os.path.exists(settings.KEYFRAME_DATA_DIR):
                    for video_folder in os.listdir(settings.KEYFRAME_DATA_DIR):
                        if video_folder.startswith("L21_"):
                            video_id = video_folder
                            if video_id in video_info:
                                keyframe_path = os.path.join(
                                    settings.KEYFRAME_DATA_DIR,
                                    video_folder,
                                    "keyframes",
                                )
                                if os.path.exists(keyframe_path):
                                    video_info[video_id]["keyframes"] = os.listdir(
                                        keyframe_path
                                    )

                logger.info(f"Built video info for {len(video_info)} videos")
            else:
                logger.warning(
                    f"Video data directory not found: {settings.VIDEO_DATA_DIR}"
                )

        except Exception as e:
            logger.error(f"Error building video info: {e}")

        return video_info

    def get_video_info(self, video_id: str) -> Optional[Dict]:
        """Get information about a specific video"""
        if not self._initialized:
            logger.warning("Metadata service not initialized")
            return None

        return self._video_info.get(video_id)

    def get_frame_metadata(self, frame_id: str) -> Optional[Dict]:
        """Get detailed metadata for a specific frame"""
        if not self._initialized:
            logger.warning("Metadata service not initialized")
            return None

        # Get basic image mapping
        img_info = self._id2img_mapping.get(frame_id, {})

        # Get keyframe mapping if available
        keyframe_info = self._keyframe_mapping.get(frame_id, {})

        # Combine information
        metadata = {
            "frame_id": frame_id,
            "image_info": img_info,
            "keyframe_info": keyframe_info,
            "video_info": None,
        }

        # Try to find video information
        if "video_id" in img_info:
            metadata["video_info"] = self.get_video_info(img_info["video_id"])
        elif "video_id" in keyframe_info:
            metadata["video_info"] = self.get_video_info(keyframe_info["video_id"])

        return metadata

    def get_video_frames(self, video_id: str) -> List[str]:
        """Get all frame IDs for a specific video"""
        if not self._initialized:
            logger.warning("Metadata service not initialized")
            return []

        frames = []
        for frame_id, img_info in self._id2img_mapping.items():
            if img_info.get("video_id") == video_id:
                frames.append(frame_id)

        return frames

    def search_frames_by_video(self, video_id: str, limit: int = 100) -> List[Dict]:
        """Search for frames belonging to a specific video"""
        if not self._initialized:
            logger.warning("Metadata service not initialized")
            return []

        frames = []
        for frame_id, img_info in self._id2img_mapping.items():
            if img_info.get("video_id") == video_id:
                frame_metadata = self.get_frame_metadata(frame_id)
                if frame_metadata:
                    frames.append(frame_metadata)

                if len(frames) >= limit:
                    break

        return frames

    def get_video_summary(self, video_id: str) -> Optional[Dict]:
        """Get a summary of video information including frame count and timestamps"""
        if not self._initialized:
            logger.warning("Metadata service not initialized")
            return None

        video_info = self.get_video_info(video_id)
        if not video_info:
            return None

        frames = self.get_video_frames(video_id)

        # Calculate frame statistics
        frame_timestamps = []
        for frame_id in frames:
            metadata = self.get_frame_metadata(frame_id)
            if metadata and "keyframe_info" in metadata:
                timestamp = metadata["keyframe_info"].get("timestamp")
                if timestamp:
                    frame_timestamps.append(timestamp)

        summary = {
            "video_id": video_id,
            "filename": video_info.get("filename"),
            "total_frames": len(frames),
            "frame_timestamps": sorted(frame_timestamps) if frame_timestamps else [],
            "duration_estimate": max(frame_timestamps) if frame_timestamps else 0,
            "keyframe_count": len(video_info.get("keyframes", [])),
        }

        return summary

    def get_all_videos(self) -> List[str]:
        """Get list of all available video IDs"""
        if not self._initialized:
            logger.warning("Metadata service not initialized")
            return []

        return list(self._video_info.keys())

    def is_initialized(self) -> bool:
        """Check if the metadata service is initialized"""
        return self._initialized


# Global metadata service instance
metadata_service = MetadataService()
