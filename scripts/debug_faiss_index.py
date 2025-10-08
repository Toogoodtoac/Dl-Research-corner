#!/usr/bin/env python3
"""
Debug script to test FAISS index directly
"""

import os
import sys

import faiss
import numpy as np

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))


def test_faiss_index():
    """Test FAISS index directly"""

    print("=== Testing FAISS Index Directly ===")

    # Paths
    faiss_clip_path = "data/indexes/faiss/faiss_clip_vitb32.bin"
    faiss_longclip_path = "data/indexes/faiss/faiss_longclip.bin"
    id2img_path = "data/indexes/faiss/id2img.json"

    # Check if files exist
    print(f"FAISS CLIP path exists: {os.path.exists(faiss_clip_path)}")
    print(f"FAISS LongCLIP path exists: {os.path.exists(faiss_longclip_path)}")
    print(f"ID2IMG path exists: {os.path.exists(id2img_path)}")

    # Load CLIP index
    if os.path.exists(faiss_clip_path):
        print(f"\n--- Testing CLIP Index ---")
        try:
            index_clip = faiss.read_index(faiss_clip_path)
            print(f"CLIP Index loaded successfully")
            print(f"  - Total vectors: {index_clip.ntotal}")
            print(f"  - Dimension: {index_clip.d}")
            print(f"  - Index type: {type(index_clip)}")

            # Test a random query
            if index_clip.ntotal > 0:
                # Create a random query vector
                query_dim = index_clip.d
                query_vector = np.random.randn(1, query_dim).astype("float32")
                query_vector = query_vector / np.linalg.norm(query_vector)

                # Search
                k = 5
                scores, indices = index_clip.search(query_vector, k)

                print(f"  - Random query search results:")
                for i in range(min(k, len(scores[0]))):
                    print(
                        f"    {i+1}. Index: {indices[0][i]}, Score: {scores[0][i]:.4f}"
                    )

        except Exception as e:
            print(f"Failed to load CLIP index: {e}")

    # Load LongCLIP index
    if os.path.exists(faiss_longclip_path):
        print(f"\n--- Testing LongCLIP Index ---")
        try:
            index_longclip = faiss.read_index(faiss_longclip_path)
            print(f"LongCLIP Index loaded successfully")
            print(f"  - Total vectors: {index_longclip.ntotal}")
            print(f"  - Dimension: {index_longclip.d}")
            print(f"  - Index type: {type(index_longclip)}")

            # Test a random query
            if index_longclip.ntotal > 0:
                # Create a random query vector
                query_dim = index_longclip.d
                query_vector = np.random.randn(1, query_dim).astype("float32")
                query_vector = query_vector / np.linalg.norm(query_vector)

                # Search
                k = 5
                scores, indices = index_longclip.search(query_vector, k)

                print(f"  - Random query search results:")
                for i in range(min(k, len(scores[0]))):
                    print(
                        f"    {i+1}. Index: {indices[0][i]}, Score: {scores[0][i]:.4f}"
                    )

        except Exception as e:
            print(f"Failed to load LongCLIP index: {e}")

    # Check ID2IMG mapping
    if os.path.exists(id2img_path):
        print(f"\n--- Testing ID2IMG Mapping ---")
        try:
            import json

            with open(id2img_path, "r") as f:
                id2img = json.load(f)

            print(f"ID2IMG loaded successfully")
            print(f"  - Total mappings: {len(id2img)}")

            # Check first few mappings
            print(f"  - First 5 mappings:")
            for i in range(min(5, len(id2img))):
                print(f"    {i}: {id2img[str(i)]}")

            # Check if paths exist
            print(f"  - Checking if first 5 image paths exist:")
            for i in range(min(5, len(id2img))):
                img_path = id2img[str(i)]
                full_path = os.path.join("data", img_path)
                exists = os.path.exists(full_path)
                print(f"    {i}: {full_path} -> {'EXISTS' if exists else 'MISSING'}")

        except Exception as e:
            print(f"Failed to load ID2IMG: {e}")


if __name__ == "__main__":
    test_faiss_index()
