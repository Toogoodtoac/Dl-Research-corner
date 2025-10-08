#!/usr/bin/env python3
"""
Test API search to see what's happening
"""

import json

import requests


def test_api_search():
    """Test the API search endpoint"""
    print("Testing API search...")

    # Test 1: Simple search
    print("\nTest 1: Simple search")
    try:
        response = requests.post(
            "http://localhost:8000/api/search/text",
            headers={"Content-Type": "application/json"},
            json={"query": "test query", "model_type": "longclip", "limit": 3},
        )

        print(f"Status code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")

            # Check if we got real results or mock results
            results = data.get("data", {}).get("results", [])
            if results:
                first_result = results[0]
                if "mock" in first_result.get("image_id", ""):
                    print("❌ Got mock results instead of real FAISS results")
                else:
                    print("✅ Got real FAISS results")
            else:
                print("❌ No results returned")
        else:
            print(f"Error response: {response.text}")

    except Exception as e:
        print(f"❌ Request failed: {e}")

    # Test 2: Check server health
    print("\nTest 2: Server health")
    try:
        response = requests.get("http://localhost:8000/health")
        print(f"Health status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Server is healthy")
        else:
            print(f"❌ Server health check failed: {response.text}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")

    # Test 3: Check server root
    print("\nTest 3: Server root")
    try:
        response = requests.get("http://localhost:8000/")
        print(f"Root status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Server info: {json.dumps(data, indent=2)}")
        else:
            print(f"❌ Root endpoint failed: {response.text}")
    except Exception as e:
        print(f"❌ Root check failed: {e}")


if __name__ == "__main__":
    test_api_search()
