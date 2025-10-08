#!/usr/bin/env python3
"""
Debug script to test search functionality and identify issues
"""

import asyncio
import json
import os
import sys

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))

from schemas.common import ModelType
from services.search_service import SearchService


async def test_search():
    """Test the search service with various queries"""

    print("=== Testing Search Service ===")

    # Initialize the search service
    search_service = SearchService()

    # Test queries
    test_queries = [
        "ễ hội. Phía sau người đàn ông này là một vật trang trí có hình dáng con chim màu tím.",
        "người đàn ông",
        "con chim",
        "vật trang trí",
        "màu tím",
    ]

    for query in test_queries:
        print(f"\n--- Testing query: {query} ---")

        try:
            # Test with LongCLIP model
            results = await search_service.text_search(
                query=query, model_type=ModelType.LONGCLIP, limit=5
            )

            print(f"LongCLIP results ({len(results)}):")
            for i, result in enumerate(results):
                print(
                    f"  {i+1}. ID: {result.image_id}, Score: {result.score:.4f}, Path: {result.link}"
                )

        except Exception as e:
            print(f"LongCLIP search failed: {e}")

        try:
            # Test with CLIP model
            results = await search_service.text_search(
                query=query, model_type=ModelType.CLIP, limit=5
            )

            print(f"CLIP results ({len(results)}):")
            for i, result in enumerate(results):
                print(
                    f"  {i+1}. ID: {result.image_id}, Score: {result.score:.4f}, Path: {result.link}"
                )

        except Exception as e:
            print(f"CLIP search failed: {e}")

    # Test image search with a known image ID
    print(f"\n--- Testing neighbor search ---")
    try:
        results = await search_service.neighbor_search(
            image_id="longclip_0", model_type=ModelType.LONGCLIP, limit=5
        )

        print(f"Neighbor search results ({len(results)}):")
        for i, result in enumerate(results):
            print(
                f"  {i+1}. ID: {result.image_id}, Score: {result.score:.4f}, Path: {result.link}"
            )

    except Exception as e:
        print(f"Neighbor search failed: {e}")

    # Cleanup
    await search_service.cleanup()


if __name__ == "__main__":
    asyncio.run(test_search())
