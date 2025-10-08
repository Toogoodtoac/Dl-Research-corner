#!/usr/bin/env python3
"""
Deep FAISS test to understand the search issue
"""

import json

import faiss
import numpy as np


def test_faiss_deep():
    """Deep FAISS test"""
    print("Deep FAISS testing...")

    # Load FAISS index
    index = faiss.read_index("data/indexes/faiss/faiss_longclip.bin")
    print(f"Index loaded: {index.ntotal} vectors, {index.d} dimensions")

    # Load ID mapping
    with open("data/indexes/faiss/id2img.json", "r") as f:
        id2img = json.load(f)
    print(f"ID mapping loaded: {len(id2img)} entries")

    # Check if the issue is with the index type
    print(f"\nIndex details:")
    print(f"  Type: {type(index)}")
    print(f"  ntotal: {index.ntotal}")
    print(f"  d: {index.d}")
    print(f"  is_trained: {getattr(index, 'is_trained', 'N/A')}")

    # Test 1: Try to get all vectors and see their properties
    print(f"\nTest 1: Vector properties")
    try:
        # Get first few vectors
        for i in range(5):
            vector = index.reconstruct(i)
            norm = np.linalg.norm(vector)
            print(f"  Vector {i}: shape={vector.shape}, norm={norm:.4f}")
    except Exception as e:
        print(f"  Failed to reconstruct vectors: {e}")

    # Test 2: Try different search strategies
    print(f"\nTest 2: Different search strategies")

    # Strategy 1: Search with zero vector
    print(f"  Strategy 1: Zero vector search")
    query = np.zeros((1, index.d), dtype=np.float32)
    scores, idxs = index.search(query, 5)
    print(f"    Scores: {scores[0]}")
    print(f"    IDs: {idxs[0]}")
    print(f"    Valid IDs: {[idx for idx in idxs[0] if 0 <= idx < index.ntotal]}")

    # Strategy 2: Search with first vector
    print(f"  Strategy 2: First vector search")
    try:
        query = index.reconstruct(0).reshape(1, -1).astype(np.float32)
        scores, idxs = index.search(query, 5)
        print(f"    Scores: {scores[0]}")
        print(f"    IDs: {idxs[0]}")
        print(f"    Valid IDs: {[idx for idx in idxs[0] if 0 <= idx < index.ntotal]}")
    except Exception as e:
        print(f"    Failed: {e}")

    # Strategy 3: Search with random normalized vector
    print(f"  Strategy 3: Random normalized vector search")
    query = np.random.randn(1, index.d).astype(np.float32)
    faiss.normalize_L2(query)
    scores, idxs = index.search(query, 5)
    print(f"    Scores: {scores[0]}")
    print(f"    IDs: {idxs[0]}")
    print(f"    Valid IDs: {[idx for idx in idxs[0] if 0 <= idx < index.ntotal]}")

    # Test 3: Check if the issue is with the search method
    print(f"\nTest 3: Search method analysis")

    # Try to understand what the search method is doing
    print(f"  Search method: {index.search.__name__}")
    print(f"  Search signature: {index.search.__doc__}")

    # Test 4: Check if there's a mismatch between index and features
    print(f"\nTest 4: Index vs Features consistency")

    # Load features
    features = np.load("data/features-longclip/all_features.npy")
    print(f"  Features shape: {features.shape}")

    # Check if the index size matches features
    if index.ntotal == len(features):
        print(f"  ✅ Index size matches features")
    else:
        print(
            f"  ❌ Index size ({index.ntotal}) doesn't match features ({len(features)})"
        )

    # Test 5: Try to understand the ID assignment
    print(f"\nTest 5: ID assignment analysis")

    # Check if the issue is with the ID mapping keys
    id_keys = [int(k) for k in id2img.keys()]
    print(
        f"  ID mapping keys: min={min(id_keys)}, max={max(id_keys)}, count={len(id_keys)}"
    )

    # Check if there are any gaps in the ID sequence
    expected_ids = set(range(len(id_keys)))
    actual_ids = set(id_keys)
    missing_ids = expected_ids - actual_ids
    extra_ids = actual_ids - expected_ids

    if missing_ids:
        print(f"  ❌ Missing IDs: {sorted(missing_ids)[:10]}...")
    else:
        print(f"  ✅ No missing IDs")

    if extra_ids:
        print(f"  ❌ Extra IDs: {sorted(extra_ids)[:10]}...")
    else:
        print(f"  ✅ No extra IDs")

    return True


if __name__ == "__main__":
    test_faiss_deep()
