"""
FAISS index management for video retrieval
"""

import json
import os
import pickle
from typing import Dict, List, Optional, Tuple, Union

import faiss
import numpy as np
import structlog

logger = structlog.get_logger()


class FAISSIndex:
    """FAISS index management for video features"""

    def __init__(self, index_path: str = None, metadata_path: str = None):
        self.index_path = index_path
        self.metadata_path = metadata_path
        self.index = None
        self.metadata = {}
        self.feature_dim = None
        self.is_trained = False

    def build_index(
        self,
        features: np.ndarray,
        metadata: List[Dict],
        index_type: str = "flat",
        use_gpu: bool = False,
        **kwargs,
    ) -> None:
        """Build FAISS index from features"""
        if features.size == 0:
            raise ValueError("Features array is empty")

        self.feature_dim = features.shape[1]
        num_vectors = features.shape[0]

        logger.info(
            f"Building {index_type} FAISS index with {num_vectors} vectors of dimension {self.feature_dim}"
        )

        # Normalize features for cosine similarity
        faiss.normalize_L2(features)

        if index_type == "flat":
            self.index = faiss.IndexFlatIP(self.feature_dim)
        elif index_type == "ivf":
            nlist = kwargs.get("nlist", min(4096, num_vectors // 30))
            self.index = faiss.IndexIVFFlat(
                faiss.IndexFlatIP(self.feature_dim), self.feature_dim, nlist
            )
            self.index.train(features)
        elif index_type == "ivfpq":
            nlist = kwargs.get("nlist", min(4096, num_vectors // 30))
            m = kwargs.get("m", 8)  # number of subquantizers
            bits = kwargs.get("bits", 8)  # bits per subquantizer
            self.index = faiss.IndexIVFPQ(
                faiss.IndexFlatIP(self.feature_dim), self.feature_dim, nlist, m, bits
            )
            self.index.train(features)
        else:
            raise ValueError(f"Unsupported index type: {index_type}")

        # Add vectors to index
        self.index.add(features)
        self.is_trained = True

        # Store metadata
        self.metadata = {str(i): meta for i, meta in enumerate(metadata)}

        logger.info(
            f"FAISS index built successfully. Index type: {type(self.index).__name__}"
        )

    def search(
        self, query_features: np.ndarray, k: int = 10, return_metadata: bool = True
    ) -> Tuple[np.ndarray, np.ndarray, List[Dict]]:
        """Search for similar vectors"""
        if self.index is None:
            raise RuntimeError("FAISS index not built or loaded")

        if not self.is_trained:
            raise RuntimeError("FAISS index not trained")

        # Normalize query features
        if query_features.ndim == 1:
            query_features = query_features.reshape(1, -1)
        faiss.normalize_L2(query_features)

        # Perform search
        scores, indices = self.index.search(query_features, min(k, self.index.ntotal))

        # Get metadata for returned indices
        metadata_results = []
        if return_metadata:
            for idx in indices[0]:
                if str(idx) in self.metadata:
                    metadata_results.append(self.metadata[str(idx)])
                else:
                    metadata_results.append(
                        {"error": f"Metadata not found for index {idx}"}
                    )

        return scores[0], indices[0], metadata_results

    def save_index(self, index_path: str = None, metadata_path: str = None) -> None:
        """Save FAISS index and metadata to disk"""
        if self.index is None:
            raise RuntimeError("No index to save")

        index_path = index_path or self.index_path
        metadata_path = metadata_path or self.metadata_path

        if not index_path or not metadata_path:
            raise ValueError("Both index_path and metadata_path must be provided")

        # Save FAISS index
        faiss.write_index(self.index, index_path)
        logger.info(f"Saved FAISS index to {index_path}")

        # Save metadata
        with open(metadata_path, "w") as f:
            json.dump(self.metadata, f, indent=2)
        logger.info(f"Saved metadata to {metadata_path}")

    def load_index(self, index_path: str = None, metadata_path: str = None) -> None:
        """Load FAISS index and metadata from disk"""
        index_path = index_path or self.index_path
        metadata_path = metadata_path or self.metadata_path

        if not index_path or not metadata_path:
            raise ValueError("Both index_path and metadata_path must be provided")

        if not os.path.exists(index_path):
            raise FileNotFoundError(f"FAISS index file not found: {index_path}")

        if not os.path.exists(metadata_path):
            raise FileNotFoundError(f"Metadata file not found: {metadata_path}")

        # Load FAISS index
        self.index = faiss.read_index(index_path)
        self.feature_dim = self.index.d
        self.is_trained = True

        # Load metadata
        with open(metadata_path, "r") as f:
            self.metadata = json.load(f)

        logger.info(
            f"Loaded FAISS index from {index_path} with {self.index.ntotal} vectors"
        )
        logger.info(
            f"Loaded metadata from {metadata_path} with {len(self.metadata)} entries"
        )

    def get_stats(self) -> Dict:
        """Get index statistics"""
        if self.index is None:
            return {"error": "Index not loaded"}

        stats = {
            "index_type": type(self.index).__name__,
            "total_vectors": self.index.ntotal,
            "feature_dimension": self.feature_dim,
            "is_trained": self.is_trained,
            "metadata_entries": len(self.metadata),
        }

        # Add index-specific stats
        if hasattr(self.index, "nlist"):
            stats["nlist"] = self.index.nlist

        return stats

    def add_vectors(self, new_features: np.ndarray, new_metadata: List[Dict]) -> None:
        """Add new vectors to existing index"""
        if self.index is None:
            raise RuntimeError("Index not loaded")

        if new_features.shape[1] != self.feature_dim:
            raise ValueError(
                f"Feature dimension mismatch: expected {self.feature_dim}, got {new_features.shape[1]}"
            )

        # Normalize new features
        faiss.normalize_L2(new_features)

        # Add to index
        start_id = self.index.ntotal
        self.index.add(new_features)

        # Add metadata
        for i, meta in enumerate(new_metadata):
            self.metadata[str(start_id + i)] = meta

        logger.info(f"Added {len(new_features)} new vectors to index")

    def remove_vectors(self, vector_ids: List[int]) -> None:
        """Remove vectors from index (if supported)"""
        if self.index is None:
            raise RuntimeError("Index not loaded")

        if not hasattr(self.index, "remove_ids"):
            logger.warning("This index type doesn't support vector removal")
            return

        # Remove from index
        faiss_vector_ids = faiss.IDSelectorArray(vector_ids)
        self.index.remove_ids(faiss_vector_ids)

        # Remove from metadata
        for vid in vector_ids:
            self.metadata.pop(str(vid), None)

        logger.info(f"Removed {len(vector_ids)} vectors from index")


def build_faiss_index_from_hdf5(
    hdf5_path: str,
    output_dir: str,
    index_type: str = "flat",
    use_gpu: bool = False,
    **kwargs,
) -> FAISSIndex:
    """Build FAISS index from HDF5 file"""
    import h5py

    if not os.path.exists(hdf5_path):
        raise FileNotFoundError(f"HDF5 file not found: {hdf5_path}")

    os.makedirs(output_dir, exist_ok=True)

    # Load features from HDF5
    with h5py.File(hdf5_path, "r") as f:
        features_group = f["features"]
        meta_group = f["meta"]

        # Get feature dimensions
        feature_dims = {}
        for model_name in features_group.keys():
            feature_dims[model_name] = features_group[model_name].shape[1]

        # Use first feature type for now (can be extended to multi-modal)
        first_model = list(features_group.keys())[0]
        features = features_group[first_model][:]

        # Prepare metadata
        metadata = []
        for i in range(len(features)):
            metadata.append(
                {
                    "video_id": (
                        meta_group["video_ids"][i].decode()
                        if isinstance(meta_group["video_ids"][i], bytes)
                        else meta_group["video_ids"][i]
                    ),
                    "frame_id": (
                        meta_group["frame_ids"][i].decode()
                        if isinstance(meta_group["frame_ids"][i], bytes)
                        else meta_group["frame_ids"][i]
                    ),
                    "shot_id": int(meta_group["shot_ids"][i]),
                    "global_index": i,
                }
            )

    # Build index
    faiss_index = FAISSIndex()
    faiss_index.build_index(features, metadata, index_type, use_gpu, **kwargs)

    # Save index
    index_path = os.path.join(output_dir, f"faiss_{first_model}.bin")
    metadata_path = os.path.join(output_dir, f"metadata_{first_model}.json")
    faiss_index.save_index(index_path, metadata_path)

    return faiss_index
