#!/usr/bin/env python3
"""
Test server startup to identify issues
"""

import os
import sys

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))


def test_imports():
    """Test if all required modules can be imported"""
    print("Testing imports...")

    try:
        print("  Importing core.config...")
        from core.config import settings

        print("  ✅ core.config imported successfully")

        print("  Importing core.logging...")
        from core.logging import setup_logging

        print("  ✅ core.logging imported successfully")

        print("  Importing api modules...")
        from api import health, search

        print("  ✅ api modules imported successfully")

        print("  Importing services...")
        from services.model_manager import ModelManager

        print("  ✅ ModelManager imported successfully")

        print("  Importing search service...")
        from services.search_service import SearchService

        print("  ✅ SearchService imported successfully")

        return True

    except Exception as e:
        print(f"  ❌ Import failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_model_manager():
    """Test ModelManager initialization"""
    print("\nTesting ModelManager...")

    try:
        from services.model_manager import ModelManager

        manager = ModelManager()
        print("  ✅ ModelManager initialized successfully")

        # Test search service access
        search_service = manager.search_service
        print(f"  ✅ Search service accessible: {type(search_service)}")

        return True

    except Exception as e:
        print(f"  ❌ ModelManager test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_search_service():
    """Test SearchService initialization"""
    print("\nTesting SearchService...")

    try:
        from services.search_service import SearchService

        service = SearchService()
        print("  ✅ SearchService initialized successfully")

        # Test async search
        import asyncio

        async def test_search():
            results = await service.text_search("test", limit=3)
            print(f"  ✅ Search test completed: {len(results)} results")
            return results

        results = asyncio.run(test_search())
        return True

    except Exception as e:
        print(f"  ❌ SearchService test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("🧪 Server Startup Test")
    print("=" * 30)

    tests = [test_imports, test_model_manager, test_search_service]

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
        print("🎉 All tests passed! Server should start successfully.")
        return True
    else:
        print("⚠️  Some tests failed. Check the output above.")
        return False


if __name__ == "__main__":
    main()
