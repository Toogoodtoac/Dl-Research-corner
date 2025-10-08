#!/usr/bin/env python3
"""
Simple backend test without loading problematic models
"""

import os
import sys

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))


def test_config():
    """Test configuration loading"""
    print("Testing configuration...")
    try:
        from core.config import settings

        print(f"✅ Config loaded successfully")
        print(f"   FAISS_LONGCLIP_PATH: {settings.FAISS_LONGCLIP_PATH}")
        print(f"   ID2IMG_JSON_PATH: {settings.ID2IMG_JSON_PATH}")
        print(f"   DATA_ROOT: {settings.DATA_ROOT}")
        return True
    except Exception as e:
        print(f"❌ Config loading failed: {e}")
        return False


def test_paths():
    """Test if required files exist"""
    print("\nTesting file paths...")
    try:
        import os

        from core.config import settings

        paths_to_check = [
            settings.FAISS_LONGCLIP_PATH,
            settings.ID2IMG_JSON_PATH,
            settings.DATA_ROOT,
        ]

        for path in paths_to_check:
            exists = os.path.exists(path)
            print(f"   {path}: {'✅' if exists else '❌'}")

        return True
    except Exception as e:
        print(f"❌ Path testing failed: {e}")
        return False


def test_search_service():
    """Test search service initialization"""
    print("\nTesting search service...")
    try:
        from services.search_service import SearchService

        service = SearchService()
        print("✅ Search service initialized")

        # Test mock search
        import asyncio

        async def test_mock():
            results = await service.text_search("test", limit=3)
            print(f"✅ Mock search returned {len(results)} results")
            return results

        results = asyncio.run(test_mock())
        return True

    except Exception as e:
        print(f"❌ Search service test failed: {e}")
        return False


def test_faiss_loading():
    """Test FAISS index loading"""
    print("\nTesting FAISS index loading...")
    try:
        import faiss
        from core.config import settings

        # Try to load the index
        index = faiss.read_index(settings.FAISS_LONGCLIP_PATH)
        print(f"✅ FAISS index loaded successfully")
        print(f"   Index contains {index.ntotal} vectors")
        print(f"   Index dimension: {index.d}")
        return True

    except Exception as e:
        print(f"❌ FAISS loading failed: {e}")
        return False


def test_id_mapping():
    """Test ID to image mapping"""
    print("\nTesting ID mapping...")
    try:
        import json

        from core.config import settings

        with open(settings.ID2IMG_JSON_PATH, "r") as f:
            mapping = json.load(f)

        print(f"✅ ID mapping loaded successfully")
        print(f"   Contains {len(mapping)} mappings")

        # Show a few examples
        for i, (key, value) in enumerate(list(mapping.items())[:5]):
            print(f"   {key}: {value}")

        return True

    except Exception as e:
        print(f"❌ ID mapping test failed: {e}")
        return False


def main():
    """Run all tests"""
    print("🧪 Simple Backend Test")
    print("=" * 30)

    tests = [
        test_config,
        test_paths,
        test_faiss_loading,
        test_id_mapping,
        test_search_service,
    ]

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
        print("🎉 All tests passed! Backend is ready.")
        return True
    else:
        print("⚠️  Some tests failed. Check the output above.")
        return False


if __name__ == "__main__":
    main()
