"""
HDF5 storage for video features and metadata
"""

import json
import os
from typing import Dict, List, Optional, Tuple, Union

import h5py
import numpy as np
import structlog

logger = structlog.get_logger()


class HDF5Storage:
    """HDF5 storage for video features and metadata"""

    def __init__(self, file_path: str, mode: str = "a"):
        self.file_path = file_path
        self.mode = mode
        self._file = None

    def __enter__(self):
        """Context manager entry"""
        self._file = h5py.File(self.file_path, self.mode)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        if self._file:
            self._file.close()

    def create_schema(self, num_frames: int, feature_dims: Dict[str, int]):
        """Create HDF5 schema with proper structure"""
        if self._file is None:
            raise RuntimeError("HDF5 file not opened")

        # Create groups
        features_group = self._file.create_group("features")
        meta_group = self._file.create_group("meta")
        bboxes_group = self._file.create_group("bboxes")

        # Create feature datasets
        for model_name, dim in feature_dims.items():
            features_group.create_dataset(
                model_name,
                shape=(num_frames, dim),
                dtype=np.float32,
                compression="gzip",
                compression_opts=9,
            )

        # Create metadata datasets
        meta_group.create_dataset(
            "video_ids", shape=(num_frames,), dtype=h5py.string_dtype()
        )
        meta_group.create_dataset(
            "frame_ids", shape=(num_frames,), dtype=h5py.string_dtype()
        )
        meta_group.create_dataset("shot_ids", shape=(num_frames,), dtype=np.int32)

        # Create bbox datasets (will be resized as needed)
        bboxes_group.create_dataset(
            "indices", shape=(0, 4), dtype=np.float32, maxshape=(None, 4)
        )
        bboxes_group.create_dataset(
            "frame_index", shape=(0,), dtype=np.int32, maxshape=(None,)
        )
        bboxes_group.create_dataset(
            "class", shape=(0,), dtype=np.int32, maxshape=(None,)
        )
        bboxes_group.create_dataset(
            "color_name", shape=(0,), dtype=h5py.string_dtype(), maxshape=(None,)
        )

        logger.info(
            f"Created HDF5 schema with {num_frames} frames and {len(feature_dims)} feature types"
        )

    def store_features(self, frame_start: int, features: Dict[str, np.ndarray]):
        """Store features for a range of frames"""
        if self._file is None:
            raise RuntimeError("HDF5 file not opened")

        features_group = self._file["features"]
        for model_name, feature_array in features.items():
            if model_name in features_group:
                features_group[model_name][
                    frame_start : frame_start + feature_array.shape[0]
                ] = feature_array

    def store_metadata(
        self,
        frame_start: int,
        video_ids: List[str],
        frame_ids: List[str],
        shot_ids: List[int],
    ):
        """Store metadata for a range of frames"""
        if self._file is None:
            raise RuntimeError("HDF5 file not opened")

        meta_group = self._file["meta"]
        end_idx = frame_start + len(video_ids)

        meta_group["video_ids"][frame_start:end_idx] = video_ids
        meta_group["frame_ids"][frame_start:end_idx] = frame_ids
        meta_group["shot_ids"][frame_start:end_idx] = shot_ids

    def store_bboxes(self, bboxes: List[Dict]):
        """Store bounding box data"""
        if self._file is None:
            raise RuntimeError("HDF5 file not opened")

        bboxes_group = self._file["bboxes"]
        current_size = bboxes_group["indices"].shape[0]
        new_size = current_size + len(bboxes)

        # Resize datasets
        for dataset_name in ["indices", "frame_index", "class", "color_name"]:
            bboxes_group[dataset_name].resize((new_size,))

        # Store data
        for i, bbox in enumerate(bboxes):
            idx = current_size + i
            bboxes_group["indices"][idx] = bbox["bbox"]
            bboxes_group["frame_index"][idx] = bbox["frame_index"]
            bboxes_group["class"][idx] = bbox["class_id"]
            bboxes_group["color_name"][idx] = bbox["color_name"]

    def get_features(self, frame_indices: List[int], model_name: str) -> np.ndarray:
        """Retrieve features for specific frames"""
        if self._file is None:
            raise RuntimeError("HDF5 file not opened")

        features_group = self._file["features"]
        if model_name not in features_group:
            raise KeyError(f"Feature type {model_name} not found")

        return features_group[model_name][frame_indices]

    def get_metadata(self, frame_indices: List[int]) -> Dict[str, np.ndarray]:
        """Retrieve metadata for specific frames"""
        if self._file is None:
            raise RuntimeError("HDF5 file not opened")

        meta_group = self._file["meta"]
        return {
            "video_ids": meta_group["video_ids"][frame_indices],
            "frame_ids": meta_group["frame_ids"][frame_indices],
            "shot_ids": meta_group["shot_ids"][frame_indices],
        }

    def get_bboxes_for_frame(self, frame_index: int) -> List[Dict]:
        """Get all bounding boxes for a specific frame"""
        if self._file is None:
            raise RuntimeError("HDF5 file not opened")

        bboxes_group = self._file["bboxes"]
        frame_bbox_indices = np.where(bboxes_group["frame_index"][:] == frame_index)[0]

        bboxes = []
        for idx in frame_bbox_indices:
            bboxes.append(
                {
                    "bbox": bboxes_group["indices"][idx].tolist(),
                    "class_id": int(bboxes_group["class"][idx]),
                    "color_name": (
                        bboxes_group["color_name"][idx].decode()
                        if isinstance(bboxes_group["color_name"][idx], bytes)
                        else bboxes_group["color_name"][idx]
                    ),
                }
            )

        return bboxes

    def get_stats(self) -> Dict:
        """Get storage statistics"""
        if self._file is None:
            raise RuntimeError("HDF5 file not opened")

        features_group = self._file["features"]
        meta_group = self._file["meta"]
        bboxes_group = self._file["bboxes"]

        stats = {
            "total_frames": meta_group["video_ids"].shape[0],
            "feature_types": {},
            "total_bboxes": bboxes_group["indices"].shape[0],
        }

        for model_name in features_group.keys():
            stats["feature_types"][model_name] = {
                "shape": features_group[model_name].shape,
                "dtype": str(features_group[model_name].dtype),
            }

        return stats


def create_hdf5_file(
    file_path: str, num_frames: int, feature_dims: Dict[str, int]
) -> HDF5Storage:
    """Create a new HDF5 file with proper schema"""
    storage = HDF5Storage(file_path, mode="w")
    storage._file = h5py.File(file_path, "w")
    storage.create_schema(num_frames, feature_dims)
    return storage
