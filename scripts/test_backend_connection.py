#!/usr/bin/env python3
"""
Simple test script to verify backend data connection
"""

import json
import os
import sys

# Add backend to path
backend_dir = os.path.join(os.path.dirname(__file__), "backend")
sys.path.insert(0, backend_dir)


def test_data_access():
    """Test if we can access the data files"""
    print("Testing data access...")

    # Test data directory structure
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    if not os.path.exists(data_dir):
        print(f"❌ Data directory not found: {data_dir}")
        return False

    print(f"✅ Data directory found: {data_dir}")

    # Test FAISS indexes
    faiss_dir = os.path.join(data_dir, "indexes", "faiss")
    if not os.path.exists(faiss_dir):
        print(f"❌ FAISS directory not found: {faiss_dir}")
        return False

    print(f"✅ FAISS directory found: {faiss_dir}")

    # Test specific files
    required_files = ["faiss_clip_vitb32.bin", "faiss_longclip.bin", "id2img.json"]

    for file in required_files:
        file_path = os.path.join(faiss_dir, file)
        if not os.path.exists(file_path):
            print(f"❌ Required file not found: {file_path}")
            return False
        print(f"✅ Found: {file}")

    # Test id2img.json content
    id2img_path = os.path.join(faiss_dir, "id2img.json")
    try:
        with open(id2img_path, "r") as f:
            id2img = json.load(f)
        print(f"✅ id2img.json loaded successfully with {len(id2img)} entries")

        # Show first few entries
        print("First 5 entries:")
        for i in range(min(5, len(id2img))):
            print(f"  {i}: {id2img[str(i)]}")

    except Exception as e:
        print(f"❌ Failed to load id2img.json: {e}")
        return False

    # Test keyframes directory
    keyframes_dir = os.path.join(
        data_dir, "raw", "keyframes", "Keyframes_L21", "keyframes"
    )
    if not os.path.exists(keyframes_dir):
        print(f"❌ Keyframes directory not found: {keyframes_dir}")
        return False

    print(f"✅ Keyframes directory found: {keyframes_dir}")

    # Test if we can access some actual image files
    video_dirs = [
        d
        for d in os.listdir(keyframes_dir)
        if d.startswith("L21_V") and os.path.isdir(os.path.join(keyframes_dir, d))
    ]
    print(f"✅ Found {len(video_dirs)} video directories")

    if video_dirs:
        first_video = video_dirs[0]
        first_video_path = os.path.join(keyframes_dir, first_video)
        image_files = [f for f in os.listdir(first_video_path) if f.endswith(".jpg")]
        print(f"✅ First video {first_video} has {len(image_files)} images")

        if image_files:
            first_image = image_files[0]
            first_image_path = os.path.join(first_video_path, first_image)
            if os.path.exists(first_image_path):
                print(f"✅ Can access first image: {first_image_path}")
            else:
                print(f"❌ Cannot access first image: {first_image_path}")

    return True


def test_faiss_loading():
    """Test if we can load FAISS indexes"""
    print("\nTesting FAISS loading...")

    try:
        import faiss

        print("✅ FAISS imported successfully")
    except ImportError as e:
        print(f"❌ FAISS import failed: {e}")
        return False

    try:
        # Test loading a small index
        faiss_dir = os.path.join(os.path.dirname(__file__), "data", "indexes", "faiss")
        clip_index_path = os.path.join(faiss_dir, "faiss_clip_vitb32.bin")

        if os.path.exists(clip_index_path):
            index = faiss.read_index(clip_index_path)
            print(f"✅ FAISS CLIP index loaded successfully: {index.ntotal} vectors")
        else:
            print(f"❌ FAISS CLIP index not found: {clip_index_path}")
            return False

    except Exception as e:
        print(f"❌ FAISS index loading failed: {e}")
        return False

    return True


def test_path_manager():
    """Test if path manager works correctly"""
    print("\nTesting path manager...")

    try:
        import env_path_manager as pm

        print(f"✅ Path manager imported successfully")
        print(f"   Environment: {pm.ENV}")
        print(f"   Root directory: {pm.root_dir}")
        print(f"   Data directory: {pm.root_data}")

        # Test if data directory exists
        if os.path.exists(pm.root_data):
            print(f"✅ Data directory exists: {pm.root_data}")
        else:
            print(f"❌ Data directory does not exist: {pm.root_data}")
            return False

    except Exception as e:
        print(f"❌ Path manager test failed: {e}")
        return False

    return True


def main():
    """Run all tests"""
    print("🔍 Testing Backend Data Connection")
    print("=" * 50)

    tests = [
        ("Data Access", test_data_access),
        ("FAISS Loading", test_faiss_loading),
        ("Path Manager", test_path_manager),
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n🧪 Running {test_name} test...")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary")
    print("=" * 50)

    passed = 0
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1

    print(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Backend should be able to connect to data.")
    else:
        print("⚠️  Some tests failed. Check the issues above.")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
