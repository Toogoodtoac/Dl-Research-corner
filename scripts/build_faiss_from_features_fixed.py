#!/usr/bin/env python3
"""
Fixed FAISS index building script with proper feature processing
"""

import argparse
import json
import os
import sys

import faiss
import numpy as np
import structlog

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


class FAISSIndexBuilder:
    """Build FAISS index from extracted features with proper processing"""

    def __init__(self, index_type: str = "flat", use_gpu: bool = False):
        self.index_type = index_type
        self.use_gpu = use_gpu

    def build_index(self, features: np.ndarray, output_path: str) -> faiss.Index:
        """Build FAISS index from features with proper processing"""
        logger.info(
            f"Building {self.index_type} FAISS index for {features.shape[0]} features"
        )

        # Check feature properties
        logger.info(
            f"Feature stats - min: {features.min():.4f}, max: {features.max():.4f}, mean: {features.mean():.4f}, std: {features.std():.4f}"
        )

        # Normalize features to unit length (L2 normalization)
        logger.info("Normalizing features to unit length...")
        features_normalized = features.copy().astype(np.float32)
        faiss.normalize_L2(features_normalized)

        # Check normalized feature properties
        norms = np.linalg.norm(features_normalized, axis=1)
        logger.info(
            f"Normalized feature norms - min: {norms.min():.4f}, max: {norms.max():.4f}, mean: {norms.mean():.4f}"
        )

        # Create index
        if self.index_type == "flat":
            # Use IndexFlatIP for inner product similarity with normalized vectors
            index = faiss.IndexFlatIP(features.shape[1])
        elif self.index_type == "ivf":
            nlist = min(100, features.shape[0] // 10)  # Number of clusters
            quantizer = faiss.IndexFlatIP(features.shape[1])
            index = faiss.IndexIVFFlat(
                quantizer, features.shape[1], nlist, faiss.METRIC_INNER_PRODUCT
            )
            # Train the index
            logger.info("Training IVF index...")
            index.train(features_normalized)
        else:
            raise ValueError(f"Unsupported index type: {self.index_type}")

        # Add vectors to index
        logger.info("Adding vectors to index...")
        index.add(features_normalized)

        # Verify index
        logger.info(f"Index verification - ntotal: {index.ntotal}, d: {index.d}")

        # Test search to verify index works correctly
        logger.info("Testing index with sample queries...")
        test_queries = [
            np.zeros((1, features.shape[1]), dtype=np.float32),  # Zero vector
            np.ones((1, features.shape[1]), dtype=np.float32),  # Ones vector
            np.random.randn(1, features.shape[1]).astype(np.float32),  # Random vector
        ]

        for i, query in enumerate(test_queries):
            # Normalize query
            faiss.normalize_L2(query)
            scores, idxs = index.search(query, 3)
            logger.info(f"Test query {i+1}: scores={scores[0][:3]}, IDs={idxs[0][:3]}")

            # Verify IDs are in valid range
            valid_ids = [idx for idx in idxs[0] if 0 <= idx < features.shape[0]]
            logger.info(f"  Valid IDs: {len(valid_ids)}/3")

        # Save index
        faiss.write_index(index, output_path)
        logger.info(f"FAISS index saved to {output_path}")
        logger.info(f"Index contains {index.ntotal} vectors")

        return index


def main():
    parser = argparse.ArgumentParser(
        description="Build FAISS index from features (fixed version)"
    )
    parser.add_argument(
        "--features-dir",
        default="data/features-longclip",
        help="Directory containing features",
    )
    parser.add_argument(
        "--output-dir",
        default="data/indexes/faiss",
        help="Output directory for indexes",
    )
    parser.add_argument(
        "--index-type", default="flat", choices=["flat", "ivf"], help="FAISS index type"
    )
    parser.add_argument(
        "--use-gpu", action="store_true", help="Use GPU for index building"
    )

    args = parser.parse_args()

    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)

    # Load features
    features_path = os.path.join(args.features_dir, "all_features.npy")
    if not os.path.exists(features_path):
        logger.error(f"Features file not found: {features_path}")
        logger.info("Please run extract_features.py first")
        return

    features = np.load(features_path)
    logger.info(f"Loaded features: {features.shape}")

    # Load ID mapping
    mapping_path = os.path.join(args.features_dir, "id2img.json")
    if not os.path.exists(mapping_path):
        logger.error(f"ID mapping file not found: {mapping_path}")
        return

    with open(mapping_path, "r") as f:
        id2img_mapping = json.load(f)

    logger.info(f"Loaded ID mapping with {len(id2img_mapping)} entries")

    # Verify feature count matches ID mapping
    if len(features) != len(id2img_mapping):
        logger.error(
            f"Feature count ({len(features)}) doesn't match ID mapping count ({len(id2img_mapping)})"
        )
        return

    # Build FAISS index
    builder = FAISSIndexBuilder(index_type=args.index_type, use_gpu=args.use_gpu)

    # Build LongCLIP index
    longclip_index_path = os.path.join(args.output_dir, "faiss_longclip.bin")
    longclip_index = builder.build_index(features, longclip_index_path)

    # Build CLIP index (using same features for now)
    clip_index_path = os.path.join(args.output_dir, "faiss_clip_vitb32.bin")
    clip_index = builder.build_index(features, clip_index_path)

    # Copy ID mapping to indexes directory
    indexes_mapping_path = os.path.join(args.output_dir, "id2img.json")
    with open(indexes_mapping_path, "w") as f:
        json.dump(id2img_mapping, f, indent=2)

    logger.info("FAISS index building completed!")
    logger.info(f"LongCLIP index: {longclip_index_path}")
    logger.info(f"CLIP index: {clip_index_path}")
    logger.info(f"ID mapping: {indexes_mapping_path}")


if __name__ == "__main__":
    main()
