#!/usr/bin/env python3
"""
Test direct FAISS access to verify search functionality
"""

import json
import os
import sys

import faiss
import numpy as np

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))


def test_faiss_direct():
    """Test direct FAISS access"""
    print("Testing direct FAISS access...")

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

        # Test search with random query
        print("\nTesting search with random query...")
        query_features = np.random.randn(1, 512).astype(np.float32)

        # Search
        scores, idxs = index.search(query_features, 5)

        print(f"Search results:")
        for i, (score, idx) in enumerate(zip(scores[0], idxs[0])):
            if int(idx) in id2img:
                path = id2img[int(idx)]
                print(f"  {i+1}. Score: {score:.4f}, ID: {idx}, Path: {path}")
            else:
                print(f"  {i+1}. Score: {score:.4f}, ID: {idx}, Path: NOT_FOUND")

        return True

    except Exception as e:
        print(f"❌ FAISS test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_search_service_direct():
    """Test search service directly"""
    print("\nTesting search service directly...")

    try:
        import asyncio

        from services.search_service import SearchService

        service = SearchService()
        print("✅ Search service created")

        # Test search
        async def test_search():
            results = await service.text_search("test query", limit=5)
            print(f"✅ Search completed: {len(results)} results")

            # Show first few results
            for i, result in enumerate(results[:3]):
                print(
                    f"  {i+1}. {result.image_id}: {result.link} (score: {result.score:.4f})"
                )

            return results

        results = asyncio.run(test_search())
        return True

    except Exception as e:
        print(f"❌ Search service test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Run tests"""
    print("🧪 Direct FAISS Test")
    print("=" * 30)

    tests = [test_faiss_direct, test_search_service_direct]

    passed = 0
    total = len(tests)

    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")

    print(f"\n📊 Test Results: {passed}/{total} passed")

    if passed == total:
        print("🎉 All tests passed! FAISS is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Check the output above.")
        return False


if __name__ == "__main__":
    main()
