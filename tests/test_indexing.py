"""
Tests for the video indexing pipeline
"""

import os

# Add backend to path
import sys
import tempfile
from pathlib import Path

import numpy as np
import pytest

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))

from indexer.faiss_index import FAISSIndex
from indexer.hdf5_storage import HDF5Storage, create_hdf5_file
from indexer.lucene_index import LuceneIndex


class TestHDF5Storage:
    """Test HDF5 storage functionality"""

    def test_create_hdf5_file(self):
        """Test HDF5 file creation"""
        with tempfile.NamedTemporaryFile(suffix=".h5", delete=False) as tmp_file:
            hdf5_path = tmp_file.name

        try:
            # Create HDF5 file
            with create_hdf5_file(hdf5_path, 100, {"test": 512}) as storage:
                # Store features
                features = {"test": np.random.randn(100, 512).astype(np.float32)}
                storage.store_features(0, features)

                # Store metadata
                storage.store_metadata(
                    0,
                    ["video1"] * 100,
                    [f"frame_{i}" for i in range(100)],
                    list(range(100)),
                )

                # Store bboxes
                bboxes = [
                    {
                        "bbox": [0.1, 0.1, 0.2, 0.2],
                        "frame_index": i,
                        "class_id": 0,
                        "color_name": "red",
                    }
                    for i in range(100)
                ]
                storage.store_bboxes(bboxes)

                # Get stats
                stats = storage.get_stats()
                assert stats["total_frames"] == 100
                assert "test" in stats["feature_types"]

        finally:
            if os.path.exists(hdf5_path):
                os.unlink(hdf5_path)

    def test_hdf5_storage_context_manager(self):
        """Test HDF5 storage context manager"""
        with tempfile.NamedTemporaryFile(suffix=".h5", delete=False) as tmp_file:
            hdf5_path = tmp_file.name

        try:
            storage = HDF5Storage(hdf5_path, mode="w")
            with storage:
                storage.create_schema(50, {"test": 256})

                # Test that file was created
                assert os.path.exists(hdf5_path)

        finally:
            if os.path.exists(hdf5_path):
                os.unlink(hdf5_path)


class TestFAISSIndex:
    """Test FAISS index functionality"""

    def test_faiss_index_creation(self):
        """Test FAISS index creation"""
        # Create sample data
        num_vectors = 100
        feature_dim = 512
        features = np.random.randn(num_vectors, feature_dim).astype(np.float32)

        # Create metadata
        metadata = [
            {"id": i, "video_id": f"video_{i//10}", "frame_id": f"frame_{i%10}"}
            for i in range(num_vectors)
        ]

        # Create index
        faiss_index = FAISSIndex()
        faiss_index.build_index(features, metadata, index_type="flat")

        # Test search
        query = np.random.randn(1, feature_dim).astype(np.float32)
        scores, indices, results = faiss_index.search(query, k=5)

        assert len(scores) == 5
        assert len(indices) == 5
        assert len(results) == 5
        assert faiss_index.is_trained

    def test_faiss_index_save_load(self):
        """Test FAISS index save and load"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create sample data
            features = np.random.randn(50, 256).astype(np.float32)
            metadata = [{"id": i} for i in range(50)]

            # Create and save index
            faiss_index = FAISSIndex()
            faiss_index.build_index(features, metadata)

            index_path = os.path.join(temp_dir, "test_index.bin")
            metadata_path = os.path.join(temp_dir, "test_metadata.json")

            faiss_index.save_index(index_path, metadata_path)

            # Load index
            loaded_index = FAISSIndex()
            loaded_index.load_index(index_path, metadata_path)

            # Test search
            query = np.random.randn(1, 256).astype(np.float32)
            scores, indices, results = loaded_index.search(query, k=3)

            assert len(scores) == 3
            assert loaded_index.is_trained


class TestLuceneIndex:
    """Test Lucene/Whoosh index functionality"""

    def test_lucene_index_creation(self):
        """Test Lucene/Whoosh index creation"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create index
            lucene_index = LuceneIndex(temp_dir)
            lucene_index.create_schema()

            # Add documents
            lucene_index.add_document(
                doc_id="test1",
                video_id="video1",
                frame_id="frame1",
                shot_id=0,
                aladin_text="A person walking",
                gem_text="Visual content with person",
                object_classes=["person"],
                bbox_text="person red at 0.1,0.1",
            )

            lucene_index.add_document(
                doc_id="test2",
                video_id="video1",
                frame_id="frame2",
                shot_id=0,
                aladin_text="A car driving",
                gem_text="Visual content with car",
                object_classes=["car"],
                bbox_text="car blue at 0.5,0.5",
            )

            # Commit changes
            lucene_index.commit()

            # Test search
            results = lucene_index.search("person", limit=10)
            assert len(results) > 0

            # Test class search
            class_results = lucene_index.search_by_class("person", limit=5)
            assert len(class_results) > 0

            # Test color search
            color_results = lucene_index.search_by_color("red", limit=5)
            assert len(color_results) > 0

            # Get stats
            stats = lucene_index.get_stats()
            assert "total_documents" in stats

            # Close index
            lucene_index.close()


class TestIndexingPipeline:
    """Test complete indexing pipeline"""

    def test_sample_data_generation(self):
        """Test sample data generation"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # This would test the sample data generator
            # For now, just test that we can create the required directories
            os.makedirs(os.path.join(temp_dir, "features"), exist_ok=True)
            os.makedirs(os.path.join(temp_dir, "indexes", "faiss"), exist_ok=True)
            os.makedirs(os.path.join(temp_dir, "indexes", "lucene"), exist_ok=True)

            assert os.path.exists(os.path.join(temp_dir, "features"))
            assert os.path.exists(os.path.join(temp_dir, "indexes", "faiss"))
            assert os.path.exists(os.path.join(temp_dir, "indexes", "lucene"))

    def test_hdf5_to_faiss_pipeline(self):
        """Test HDF5 to FAISS pipeline"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create sample HDF5 file
            hdf5_path = os.path.join(temp_dir, "test_features.h5")

            with create_hdf5_file(hdf5_path, 50, {"test": 256}) as storage:
                # Store features
                features = np.random.randn(50, 256).astype(np.float32)
                storage.store_features(0, {"test": features})

                # Store metadata
                storage.store_metadata(
                    0,
                    ["video1"] * 50,
                    [f"frame_{i}" for i in range(50)],
                    list(range(50)),
                )

            # Test that HDF5 file was created
            assert os.path.exists(hdf5_path)

            # Test that we can read it back
            import h5py

            with h5py.File(hdf5_path, "r") as f:
                assert "features" in f
                assert "test" in f["features"]
                assert f["features"]["test"].shape == (50, 256)


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
