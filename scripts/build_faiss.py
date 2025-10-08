#!/usr/bin/env python3
"""
Build FAISS indexes from HDF5 feature files
"""

import argparse
import glob
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

import structlog

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))

from indexer.faiss_index import FAISSIndex, build_faiss_index_from_hdf5

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
    """Build FAISS indexes from HDF5 feature files"""

    def __init__(self, config: Dict):
        self.config = config
        self.index_type = config.get("index_type", "flat")
        self.use_gpu = config.get("use_gpu", False)
        self.index_params = config.get("index_params", {})

    def build_index_from_hdf5(
        self, hdf5_path: str, output_dir: str, feature_type: str = None
    ) -> FAISSIndex:
        """Build FAISS index from a single HDF5 file"""
        logger.info(f"Building FAISS index from {hdf5_path}")

        # Create output directory
        os.makedirs(output_dir, exist_ok=True)

        # Build index
        faiss_index = build_faiss_index_from_hdf5(
            hdf5_path=hdf5_path,
            output_dir=output_dir,
            index_type=self.index_type,
            use_gpu=self.use_gpu,
            **self.index_params,
        )

        logger.info(f"FAISS index built successfully: {faiss_index.get_stats()}")
        return faiss_index

    def build_index_from_directory(
        self, input_dir: str, output_dir: str, feature_type: str = None
    ) -> List[FAISSIndex]:
        """Build FAISS indexes from all HDF5 files in a directory"""
        # Find all HDF5 files
        hdf5_pattern = os.path.join(input_dir, "**", "*.h5")
        hdf5_files = glob.glob(hdf5_pattern, recursive=True)

        if not hdf5_files:
            logger.warning(f"No HDF5 files found in {input_dir}")
            return []

        logger.info(f"Found {len(hdf5_files)} HDF5 files")

        # Build indexes
        indexes = []
        for hdf5_file in hdf5_files:
            try:
                # Create subdirectory for this index
                relative_path = os.path.relpath(hdf5_file, input_dir)
                video_name = os.path.splitext(os.path.basename(hdf5_file))[0]
                index_output_dir = os.path.join(output_dir, video_name)

                faiss_index = self.build_index_from_hdf5(
                    hdf5_file, index_output_dir, feature_type
                )
                indexes.append(faiss_index)

            except Exception as e:
                logger.error(f"Failed to build index for {hdf5_file}: {e}")
                continue

        logger.info(f"Built {len(indexes)} FAISS indexes")
        return indexes

    def build_combined_index(
        self, input_dir: str, output_dir: str, feature_type: str = None
    ) -> FAISSIndex:
        """Build a combined FAISS index from all HDF5 files"""
        import h5py
        import numpy as np

        # Find all HDF5 files
        hdf5_pattern = os.path.join(input_dir, "**", "*.h5")
        hdf5_files = glob.glob(hdf5_pattern, recursive=True)

        if not hdf5_files:
            raise ValueError(f"No HDF5 files found in {input_dir}")

        logger.info(f"Building combined index from {len(hdf5_files)} HDF5 files")

        # Create output directory
        os.makedirs(output_dir, exist_ok=True)

        # Collect all features and metadata
        all_features = []
        all_metadata = []

        for hdf5_file in hdf5_files:
            try:
                with h5py.File(hdf5_file, "r") as f:
                    # Get feature type
                    if feature_type is None:
                        feature_type = list(f["features"].keys())[0]

                    if feature_type not in f["features"]:
                        logger.warning(
                            f"Feature type {feature_type} not found in {hdf5_file}"
                        )
                        continue

                    # Load features
                    features = f["features"][feature_type][:]
                    all_features.append(features)

                    # Load metadata
                    video_ids = f["meta"]["video_ids"][:]
                    frame_ids = f["meta"]["frame_ids"][:]
                    shot_ids = f["meta"]["shot_ids"][:]

                    # Convert to list format
                    for i in range(len(features)):
                        metadata = {
                            "video_id": (
                                video_ids[i].decode()
                                if isinstance(video_ids[i], bytes)
                                else video_ids[i]
                            ),
                            "frame_id": (
                                frame_ids[i].decode()
                                if isinstance(frame_ids[i], bytes)
                                else frame_ids[i]
                            ),
                            "shot_id": int(shot_ids[i]),
                            "source_file": os.path.basename(hdf5_file),
                            "global_index": len(all_metadata),
                        }
                        all_metadata.append(metadata)

            except Exception as e:
                logger.error(f"Failed to read {hdf5_file}: {e}")
                continue

        if not all_features:
            raise ValueError("No features found in any HDF5 files")

        # Combine all features
        combined_features = np.vstack(all_features)
        logger.info(f"Combined features shape: {combined_features.shape}")

        # Create FAISS index
        faiss_index = FAISSIndex()
        faiss_index.build_index(
            features=combined_features,
            metadata=all_metadata,
            index_type=self.index_type,
            use_gpu=self.use_gpu,
            **self.index_params,
        )

        # Save combined index
        index_path = os.path.join(output_dir, f"faiss_{feature_type}_combined.bin")
        metadata_path = os.path.join(
            output_dir, f"metadata_{feature_type}_combined.json"
        )
        faiss_index.save_index(index_path, metadata_path)

        logger.info(
            f"Combined FAISS index built successfully: {faiss_index.get_stats()}"
        )
        return faiss_index

    def validate_index(self, index_path: str, metadata_path: str) -> bool:
        """Validate a built FAISS index"""
        try:
            faiss_index = FAISSIndex()
            faiss_index.load_index(index_path, metadata_path)

            stats = faiss_index.get_stats()
            logger.info(f"Index validation successful: {stats}")

            # Test search
            test_query = np.random.randn(1, stats["feature_dimension"]).astype(
                np.float32
            )
            scores, indices, metadata = faiss_index.search(test_query, k=5)

            if len(metadata) > 0:
                logger.info("Search test successful")
                return True
            else:
                logger.error("Search test failed - no results returned")
                return False

        except Exception as e:
            logger.error(f"Index validation failed: {e}")
            return False


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
    parser = argparse.ArgumentParser(description="Build FAISS indexes from HDF5 files")
    parser.add_argument(
        "--input", "-i", required=True, help="Input directory containing HDF5 files"
    )
    parser.add_argument(
        "--output", "-o", required=True, help="Output directory for indexes"
    )
    parser.add_argument("--config", "-c", help="Configuration file path")
    parser.add_argument(
        "--feature-type", help="Feature type to index (e.g., clip2video, longclip)"
    )
    parser.add_argument(
        "--index-type",
        choices=["flat", "ivf", "ivfpq"],
        default="flat",
        help="FAISS index type",
    )
    parser.add_argument(
        "--use-gpu", action="store_true", help="Use GPU for index building"
    )
    parser.add_argument(
        "--combined", action="store_true", help="Build combined index from all files"
    )
    parser.add_argument(
        "--validate", action="store_true", help="Validate built indexes"
    )

    args = parser.parse_args()

    # Load configuration
    config = {}
    if args.config:
        config = load_config(args.config)

    # Default configuration
    default_config = {
        "index_type": args.index_type,
        "use_gpu": args.use_gpu,
        "index_params": {},
    }

    # Merge with user config
    config = {**default_config, **config}

    # Initialize builder
    builder = FAISSIndexBuilder(config)

    # Build indexes
    if args.combined:
        # Build combined index
        faiss_index = builder.build_combined_index(
            input_dir=args.input, output_dir=args.output, feature_type=args.feature_type
        )
        indexes = [faiss_index]
    else:
        # Build individual indexes
        indexes = builder.build_index_from_directory(
            input_dir=args.input, output_dir=args.output, feature_type=args.feature_type
        )

    # Validate indexes if requested
    if args.validate and indexes:
        logger.info("Validating built indexes...")
        for faiss_index in indexes:
            if hasattr(faiss_index, "index_path") and hasattr(
                faiss_index, "metadata_path"
            ):
                is_valid = builder.validate_index(
                    faiss_index.index_path, faiss_index.metadata_path
                )
                if is_valid:
                    logger.info(f"Index validation passed: {faiss_index.index_path}")
                else:
                    logger.error(f"Index validation failed: {faiss_index.index_path}")

    # Save build summary
    summary = {
        "input_dir": args.input,
        "output_dir": args.output,
        "index_type": args.index_type,
        "use_gpu": args.use_gpu,
        "combined": args.combined,
        "total_indexes": len(indexes),
        "indexes": [],
    }

    for faiss_index in indexes:
        if hasattr(faiss_index, "index_path") and hasattr(faiss_index, "metadata_path"):
            summary["indexes"].append(
                {
                    "index_path": faiss_index.index_path,
                    "metadata_path": faiss_index.metadata_path,
                    "stats": faiss_index.get_stats(),
                }
            )

    summary_file = os.path.join(args.output, "faiss_build_summary.json")
    with open(summary_file, "w") as f:
        json.dump(summary, f, indent=2)

    logger.info(f"Build summary saved to {summary_file}")
    logger.info(f"Successfully built {len(indexes)} FAISS indexes")


if __name__ == "__main__":
    main()
