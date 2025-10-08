#!/usr/bin/env python3
"""
Debug search service initialization
"""

import os
import sys

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))


def test_search_service_debug():
    """Debug search service initialization"""
    print("Debugging search service initialization...")

    try:
        import asyncio

        from services.search_service import SearchService

        print("✅ SearchService imported successfully")

        # Create search service
        service = SearchService()
        print("✅ SearchService created successfully")

        # Check initial state
        print(f"Initial state:")
        print(f"  _faiss_engine: {service._faiss_engine}")
        print(f"  _faiss_index: {service._faiss_index}")
        print(f"  _id2img_mapping: {service._id2img_mapping}")
        print(f"  _models_loaded: {service._models_loaded}")

        # Try to load models
        print(f"\nLoading models...")

        async def load_models():
            await service._ensure_models_loaded()
            return service._faiss_engine, service._faiss_index, service._id2img_mapping

        engine, index, mapping = asyncio.run(load_models())

        print(f"After loading:")
        print(f"  _faiss_engine: {engine}")
        print(f"  _faiss_index: {index}")
        print(f"  _id2img_mapping: {mapping}")
        print(f"  _models_loaded: {service._models_loaded}")

        if engine == "direct":
            print("✅ FAISS engine is in direct mode")
            if index is not None:
                print(f"✅ FAISS index loaded: {index.ntotal} vectors")
            else:
                print("❌ FAISS index is None")

            if mapping is not None:
                print(f"✅ ID mapping loaded: {len(mapping)} entries")
            else:
                print("❌ ID mapping is None")
        else:
            print("❌ FAISS engine is not in direct mode")

        # Test search
        print(f"\nTesting search...")

        async def test_search():
            results = await service.text_search("test", limit=3)
            return results

        results = asyncio.run(test_search())
        print(f"Search results: {len(results)}")

        if results:
            first_result = results[0]
            if "mock" in first_result.image_id:
                print("❌ Got mock results")
            else:
                print("✅ Got real results")
                print(f"First result: {first_result.image_id} -> {first_result.link}")
        else:
            print("❌ No results returned")

        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_search_service_debug()
