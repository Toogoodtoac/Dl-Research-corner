#!/usr/bin/env python3
"""
Debug FAISS search to understand the ID mismatch
"""

import json
import os
import sys

import faiss
import numpy as np

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))


def debug_faiss_search():
    """Debug FAISS search to understand ID mismatch"""
    print("Debugging FAISS search...")

    try:
        from core.config import settings

        # Load FAISS index
        print(f"Loading FAISS index from: {settings.FAISS_LONGCLIP_PATH}")
        index = faiss.read_index(settings.FAISS_LONGCLIP_PATH)
        print(f"✅ FAISS index loaded: {index.ntotal} vectors, {index.d} dimensions")

        # Load ID mapping
        print(f"Loading ID mapping from: {settings.ID2IMG_JSON_PATH}")
        with open(settings.ID2IMG_JSON_PATH, "r") as f:
            id2img = json.load(f)
        print(f"✅ ID mapping loaded: {len(id2img)} entries")

        # Check ID mapping range
        id_keys = [int(k) for k in id2img.keys()]
        print(f"ID mapping range: {min(id_keys)} to {max(id_keys)}")

        # Test multiple searches to see the pattern
        print("\nTesting multiple searches...")
        for search_num in range(3):
            print(f"\nSearch {search_num + 1}:")
            query_features = np.random.randn(1, 512).astype(np.float32)

            # Search
            scores, idxs = index.search(query_features, 5)

            print(f"  Query features shape: {query_features.shape}")
            print(f"  Scores: {scores[0]}")
            print(f"  IDs: {idxs[0]}")

            # Check which IDs are in the mapping
            valid_results = 0
            for i, (score, idx) in enumerate(zip(scores[0], idxs[0])):
                idx_int = int(idx)
                if idx_int in id2img:
                    path = id2img[idx_int]
                    print(f"    {i+1}. Score: {score:.4f}, ID: {idx_int} ✅ -> {path}")
                    valid_results += 1
                else:
                    print(
                        f"    {i+1}. Score: {score:.4f}, ID: {idx_int} ❌ -> NOT_FOUND"
                    )

            print(f"  Valid results: {valid_results}/5")

        # Check if the issue is with the index itself
        print(f"\nChecking FAISS index properties:")
        print(f"  Index type: {type(index)}")
        print(f"  Index ntotal: {index.ntotal}")
        print(f"  Index d: {index.d}")

        # Try to get a specific vector by ID
        print(f"\nTrying to get vector by ID 0:")
        try:
            vector_0 = index.reconstruct(0)
            print(f"  ✅ Vector 0 shape: {vector_0.shape}")
        except Exception as e:
            print(f"  ❌ Failed to get vector 0: {e}")

        # Try to get vector by ID 1000
        print(f"Trying to get vector by ID 1000:")
        try:
            vector_1000 = index.reconstruct(1000)
            print(f"  ✅ Vector 1000 shape: {vector_1000.shape}")
        except Exception as e:
            print(f"  ❌ Failed to get vector 1000: {e}")

        return True

    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Run debug"""
    print("🔍 FAISS Search Debug")
    print("=" * 30)

    debug_faiss_search()


if __name__ == "__main__":
    main()
