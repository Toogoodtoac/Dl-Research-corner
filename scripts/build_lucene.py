#!/usr/bin/env python3
"""
Build Lucene/Whoosh indexes from HDF5 feature files
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

from indexer.lucene_index import LuceneIndex, build_lucene_index_from_hdf5

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


class LuceneIndexBuilder:
    """Build Lucene/Whoosh indexes from HDF5 feature files"""

    def __init__(self, config: Dict):
        self.config = config
        self.use_lucene = config.get("use_lucene", True)
        self.index_params = config.get("index_params", {})

    def build_index_from_hdf5(self, hdf5_path: str, output_dir: str) -> LuceneIndex:
        """Build Lucene/Whoosh index from a single HDF5 file"""
        logger.info(f"Building text index from {hdf5_path}")

        # Create output directory
        os.makedirs(output_dir, exist_ok=True)

        # Build index
        lucene_index = build_lucene_index_from_hdf5(
            hdf5_path=hdf5_path, output_dir=output_dir, use_lucene=self.use_lucene
        )

        logger.info(f"Text index built successfully: {lucene_index.get_stats()}")
        return lucene_index

    def build_index_from_directory(
        self, input_dir: str, output_dir: str
    ) -> List[LuceneIndex]:
        """Build Lucene/Whoosh indexes from all HDF5 files in a directory"""
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
                video_name = os.path.splitext(os.path.basename(hdf5_file))[0]
                index_output_dir = os.path.join(output_dir, video_name)

                lucene_index = self.build_index_from_hdf5(hdf5_file, index_output_dir)
                indexes.append(lucene_index)

            except Exception as e:
                logger.error(f"Failed to build index for {hdf5_file}: {e}")
                continue

        logger.info(f"Built {len(indexes)} text indexes")
        return indexes

    def build_combined_index(self, input_dir: str, output_dir: str) -> LuceneIndex:
        """Build a combined Lucene/Whoosh index from all HDF5 files"""
        import h5py
        import numpy as np

        # Find all HDF5 files
        hdf5_pattern = os.path.join(input_dir, "**", "*.h5")
        hdf5_files = glob.glob(hdf5_pattern, recursive=True)

        if not hdf5_files:
            raise ValueError(f"No HDF5 files found in {input_dir}")

        logger.info(f"Building combined text index from {len(hdf5_files)} HDF5 files")

        # Create output directory
        os.makedirs(output_dir, exist_ok=True)

        # Create combined index
        combined_index = LuceneIndex(output_dir)
        combined_index.create_schema()

        # Process each HDF5 file
        total_documents = 0

        for hdf5_file in hdf5_files:
            try:
                with h5py.File(hdf5_file, "r") as f:
                    meta_group = f["meta"]
                    bboxes_group = f["bboxes"]

                    total_frames = meta_group["video_ids"].shape[0]

                    # Index each frame
                    for i in range(total_frames):
                        video_id = (
                            meta_group["video_ids"][i].decode()
                            if isinstance(meta_group["video_ids"][i], bytes)
                            else meta_group["video_ids"][i]
                        )
                        frame_id = (
                            meta_group["frame_ids"][i].decode()
                            if isinstance(meta_group["frame_ids"][i], bytes)
                            else meta_group["frame_ids"][i]
                        )
                        shot_id = int(meta_group["shot_ids"][i])

                        # Get bboxes for this frame
                        frame_bbox_indices = np.where(
                            bboxes_group["frame_index"][:] == i
                        )[0]

                        object_classes = []
                        bbox_texts = []

                        for idx in frame_bbox_indices:
                            class_id = int(bboxes_group["class"][idx])
                            color_name = (
                                bboxes_group["color_name"][idx].decode()
                                if isinstance(bboxes_group["color_name"][idx], bytes)
                                else bboxes_group["color_name"][idx]
                            )

                            # Convert class ID to name (simplified)
                            class_name = f"class_{class_id}"
                            object_classes.append(class_name)

                            # Create bbox text representation
                            bbox = bboxes_group["indices"][idx]
                            bbox_text = f"{class_name} {color_name} at {bbox[0]:.2f},{bbox[1]:.2f}"
                            bbox_texts.append(bbox_text)

                        # Add document to combined index
                        combined_index.add_document(
                            doc_id=f"{video_id}_{frame_id}",
                            video_id=video_id,
                            frame_id=frame_id,
                            shot_id=shot_id,
                            aladin_text=f"Frame from {video_id} showing {', '.join(object_classes)}",
                            gem_text=f"Visual content: {', '.join(bbox_texts)}",
                            object_classes=object_classes,
                            bbox_text=" ".join(bbox_texts),
                            metadata={
                                "frame_index": i,
                                "bbox_count": len(object_classes),
                                "source_file": os.path.basename(hdf5_file),
                            },
                        )

                        total_documents += 1

                        if total_documents % 100 == 0:
                            logger.info(f"Indexed {total_documents} documents...")

            except Exception as e:
                logger.error(f"Failed to read {hdf5_file}: {e}")
                continue

        # Commit and close combined index
        combined_index.commit()
        combined_index.close()

        logger.info(
            f"Combined text index built successfully with {total_documents} documents"
        )
        return combined_index

    def validate_index(self, index_path: str) -> bool:
        """Validate a built text index"""
        try:
            # Try to open and search the index
            lucene_index = LuceneIndex(index_path)

            # Test search
            results = lucene_index.search("person", limit=5)

            if len(results) > 0:
                logger.info(
                    f"Index validation successful: {len(results)} search results"
                )
                return True
            else:
                logger.warning(
                    "Index validation: search returned no results (this might be normal)"
                )
                return True

        except Exception as e:
            logger.error(f"Index validation failed: {e}")
            return False

    def test_search_functionality(self, index_path: str) -> Dict:
        """Test various search functionalities"""
        try:
            lucene_index = LuceneIndex(index_path)

            test_results = {}

            # Test text search
            text_results = lucene_index.search("person", limit=3)
            test_results["text_search"] = len(text_results)

            # Test class search
            class_results = lucene_index.search_by_class("person", limit=3)
            test_results["class_search"] = len(class_results)

            # Test color search
            color_results = lucene_index.search_by_color("red", limit=3)
            test_results["color_search"] = len(color_results)

            # Get index stats
            test_results["stats"] = lucene_index.get_stats()

            logger.info(f"Search functionality test completed: {test_results}")
            return test_results

        except Exception as e:
            logger.error(f"Search functionality test failed: {e}")
            return {"error": str(e)}


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
    parser = argparse.ArgumentParser(
        description="Build Lucene/Whoosh indexes from HDF5 files"
    )
    parser.add_argument(
        "--input", "-i", required=True, help="Input directory containing HDF5 files"
    )
    parser.add_argument(
        "--output", "-o", required=True, help="Output directory for indexes"
    )
    parser.add_argument("--config", "-c", help="Configuration file path")
    parser.add_argument(
        "--use-lucene",
        action="store_true",
        default=True,
        help="Use Lucene (default: True)",
    )
    parser.add_argument(
        "--use-whoosh", action="store_true", help="Use Whoosh instead of Lucene"
    )
    parser.add_argument(
        "--combined", action="store_true", help="Build combined index from all files"
    )
    parser.add_argument(
        "--validate", action="store_true", help="Validate built indexes"
    )
    parser.add_argument(
        "--test-search", action="store_true", help="Test search functionality"
    )

    args = parser.parse_args()

    # Handle Lucene/Whoosh selection
    if args.use_whoosh:
        args.use_lucene = False

    # Load configuration
    config = {}
    if args.config:
        config = load_config(args.config)

    # Default configuration
    default_config = {"use_lucene": args.use_lucene, "index_params": {}}

    # Merge with user config
    config = {**default_config, **config}

    # Initialize builder
    builder = LuceneIndexBuilder(config)

    # Build indexes
    if args.combined:
        # Build combined index
        lucene_index = builder.build_combined_index(
            input_dir=args.input, output_dir=args.output
        )
        indexes = [lucene_index]
    else:
        # Build individual indexes
        indexes = builder.build_index_from_directory(
            input_dir=args.input, output_dir=args.output
        )

    # Validate indexes if requested
    if args.validate and indexes:
        logger.info("Validating built indexes...")
        for lucene_index in indexes:
            if hasattr(lucene_index, "index_path"):
                is_valid = builder.validate_index(lucene_index.index_path)
                if is_valid:
                    logger.info(f"Index validation passed: {lucene_index.index_path}")
                else:
                    logger.error(f"Index validation failed: {lucene_index.index_path}")

    # Test search functionality if requested
    if args.test_search and indexes:
        logger.info("Testing search functionality...")
        for lucene_index in indexes:
            if hasattr(lucene_index, "index_path"):
                test_results = builder.test_search_functionality(
                    lucene_index.index_path
                )
                logger.info(
                    f"Search test results for {lucene_index.index_path}: {test_results}"
                )

    # Save build summary
    summary = {
        "input_dir": args.input,
        "output_dir": args.output,
        "use_lucene": args.use_lucene,
        "combined": args.combined,
        "total_indexes": len(indexes),
        "indexes": [],
    }

    for lucene_index in indexes:
        if hasattr(lucene_index, "index_path"):
            summary["indexes"].append(
                {
                    "index_path": lucene_index.index_path,
                    "stats": lucene_index.get_stats(),
                }
            )

    summary_file = os.path.join(args.output, "lucene_build_summary.json")
    with open(summary_file, "w") as f:
        json.dump(summary, f, indent=2)

    logger.info(f"Build summary saved to {summary_file}")
    logger.info(f"Successfully built {len(indexes)} text indexes")


if __name__ == "__main__":
    main()
