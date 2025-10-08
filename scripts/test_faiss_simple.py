#!/usr/bin/env python3
"""
Simple FAISS test to understand the search issue
"""

import json

import faiss
import numpy as np


def test_faiss_simple():
    """Simple FAISS test"""
    print("Testing FAISS search...")

    # Load FAISS index
    index = faiss.read_index("data/indexes/faiss/faiss_longclip.bin")
    print(f"Index loaded: {index.ntotal} vectors, {index.d} dimensions")

    # Load ID mapping
    with open("data/indexes/faiss/id2img.json", "r") as f:
        id2img = json.load(f)
    print(f"ID mapping loaded: {len(id2img)} entries")

    # Test 1: Search with random query
    print("\nTest 1: Random query search")
    query = np.random.randn(1, 512).astype(np.float32)
    scores, idxs = index.search(query, 5)
    print(f"Query shape: {query.shape}")
    print(f"Scores: {scores[0]}")
    print(f"IDs: {idxs[0]}")
    print(f"ID types: {[type(idx) for idx in idxs[0]]}")

    # Test 2: Search with specific query (all zeros)
    print("\nTest 2: Zero query search")
    query = np.zeros((1, 512), dtype=np.float32)
    scores, idxs = index.search(query, 5)
    print(f"Query shape: {query.shape}")
    print(f"Scores: {scores[0]}")
    print(f"IDs: {idxs[0]}")

    # Test 3: Search with specific query (all ones)
    print("\nTest 3: Ones query search")
    query = np.ones((1, 512), dtype=np.float32)
    scores, idxs = index.search(query, 5)
    print(f"Query shape: {query.shape}")
    print(f"Scores: {scores[0]}")
    print(f"IDs: {idxs[0]}")

    # Test 4: Check if the issue is with the index type
    print(f"\nIndex type: {type(index)}")
    print(f"Index properties:")
    print(f"  - ntotal: {index.ntotal}")
    print(f"  - d: {index.d}")
    print(f"  - is_trained: {getattr(index, 'is_trained', 'N/A')}")

    # Test 5: Try to get a specific vector and search with it
    print("\nTest 5: Search with reconstructed vector")
    try:
        # Get vector 0
        vector_0 = index.reconstruct(0)
        print(f"Vector 0 shape: {vector_0.shape}")

        # Search with this vector
        query = vector_0.reshape(1, -1).astype(np.float32)
        scores, idxs = index.search(query, 5)
        print(f"Scores: {scores[0]}")
        print(f"IDs: {idxs[0]}")

        # The first result should be ID 0 with score close to 1.0
        print(f"First result should be ID 0: {idxs[0][0] == 0}")
        print(f"First score should be close to 1.0: {scores[0][0]:.4f}")

    except Exception as e:
        print(f"Failed to reconstruct vector: {e}")

    return True


if __name__ == "__main__":
    test_faiss_simple()
