#!/usr/bin/env python3
"""
Setup and test script for the MM-Data Intelligent Agent
"""

import json
import os
import subprocess
import sys
from pathlib import Path


def check_dependencies():
    """Check if required dependencies are installed"""
    print("🔍 Checking dependencies...")

    required_packages = [
        "numpy",
        "faiss-cpu",
        "torch",
        "PIL",
        "structlog",
        "fastapi",
        "uvicorn",
    ]

    missing_packages = []
    for package in required_packages:
        try:
            if package == "PIL":
                import PIL
            elif package == "faiss-cpu":
                import faiss
            else:
                __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - MISSING")
            missing_packages.append(package)

    if missing_packages:
        print(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
        print("Please install them with: pip install " + " ".join(missing_packages))
        return False

    print("✅ All dependencies are available")
    return True


def check_data_structure():
    """Check if the data structure is correct"""
    print("\n📁 Checking data structure...")

    data_root = Path("data")
    required_dirs = [
        "raw/videos/Videos_L21/video",
        "raw/keyframes/Keyframes_L21/keyframes",
        "features-longclip/features",
        "indexes/faiss",
    ]

    missing_dirs = []
    for dir_path in required_dirs:
        full_path = data_root / dir_path
        if full_path.exists():
            print(f"✅ {dir_path}")
        else:
            print(f"❌ {dir_path} - MISSING")
            missing_dirs.append(dir_path)

    if missing_dirs:
        print(f"\n⚠️  Missing directories: {', '.join(missing_dirs)}")
        return False

    print("✅ Data structure is correct")
    return True


def check_keyframes():
    """Check if keyframes exist"""
    print("\n🖼️  Checking keyframes...")

    keyframe_dir = Path("data/raw/keyframes/Keyframes_L21/keyframes")
    if not keyframe_dir.exists():
        print("❌ Keyframes directory not found")
        return False

    video_dirs = list(keyframe_dir.glob("L21_V*"))
    print(f"✅ Found {len(video_dirs)} video directories")

    total_keyframes = 0
    for video_dir in video_dirs:
        keyframes = list(video_dir.glob("*.jpg"))
        total_keyframes += len(keyframes)
        print(f"  {video_dir.name}: {len(keyframes)} keyframes")

    print(f"✅ Total keyframes: {total_keyframes}")
    return True


def check_videos():
    """Check if videos exist"""
    print("\n🎥 Checking videos...")

    video_dir = Path("data/raw/videos/Videos_L21/video")
    if not video_dir.exists():
        print("❌ Videos directory not found")
        return False

    videos = list(video_dir.glob("*.mp4"))
    print(f"✅ Found {len(videos)} videos")

    for video in videos:
        size_mb = video.stat().st_size / (1024 * 1024)
        print(f"  {video.name}: {size_mb:.1f} MB")

    return True


def create_directories():
    """Create missing directories"""
    print("\n📂 Creating missing directories...")

    dirs_to_create = [
        "data/features-longclip/features",
        "data/indexes/faiss",
        "data/hdf5_features",
    ]

    for dir_path in dirs_to_create:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created {dir_path}")


def run_feature_extraction():
    """Run feature extraction"""
    print("\n🚀 Running feature extraction...")

    try:
        result = subprocess.run(
            [
                sys.executable,
                "scripts/extract_features.py",
                "--data-root",
                "data",
                "--output-dir",
                "data/features-longclip",
            ],
            capture_output=True,
            text=True,
            cwd=os.getcwd(),
        )

        if result.returncode == 0:
            print("✅ Feature extraction completed successfully")
            print(result.stdout)
        else:
            print("❌ Feature extraction failed")
            print(result.stderr)
            return False

    except Exception as e:
        print(f"❌ Failed to run feature extraction: {e}")
        return False

    return True


def run_faiss_building():
    """Run FAISS index building"""
    print("\n🔍 Building FAISS indexes...")

    try:
        result = subprocess.run(
            [
                sys.executable,
                "scripts/build_faiss_from_features.py",
                "--features-dir",
                "data/features-longclip",
                "--output-dir",
                "data/indexes/faiss",
            ],
            capture_output=True,
            text=True,
            cwd=os.getcwd(),
        )

        if result.returncode == 0:
            print("✅ FAISS index building completed successfully")
            print(result.stdout)
        else:
            print("❌ FAISS index building failed")
            print(result.stderr)
            return False

    except Exception as e:
        print(f"❌ Failed to build FAISS indexes: {e}")
        return False

    return True


def test_backend():
    """Test if the backend can start"""
    print("\n🧪 Testing backend...")

    try:
        # Try to import and initialize the search service
        sys.path.append("backend")
        from services.search_service import SearchService

        service = SearchService()
        print("✅ Search service initialized successfully")

        # Test mock search
        import asyncio

        async def test_search():
            results = await service.text_search("test query", limit=5)
            print(f"✅ Mock search returned {len(results)} results")

        asyncio.run(test_search())

    except Exception as e:
        print(f"❌ Backend test failed: {e}")
        return False

    return True


def main():
    """Main setup and test function"""
    print("🚀 MM-Data Intelligent Agent Setup and Test")
    print("=" * 50)

    # Check dependencies
    if not check_dependencies():
        print("\n❌ Setup failed: Missing dependencies")
        return False

    # Check data structure
    if not check_data_structure():
        print("\n⚠️  Creating missing directories...")
        create_directories()

    # Check keyframes and videos
    if not check_keyframes() or not check_videos():
        print("\n❌ Setup failed: Missing data files")
        return False

    # Run feature extraction
    if not run_feature_extraction():
        print("\n❌ Setup failed: Feature extraction failed")
        return False

    # Build FAISS indexes
    if not run_faiss_building():
        print("\n❌ Setup failed: FAISS index building failed")
        return False

    # Test backend
    if not test_backend():
        print("\n❌ Setup failed: Backend test failed")
        return False

    print("\n🎉 Setup completed successfully!")
    print("\nNext steps:")
    print("1. Start the backend: cd backend && python run.py")
    print("2. Start the frontend: cd frontend && npm run dev")
    print("3. Test search functionality in the webapp")

    return True


if __name__ == "__main__":
    main()
