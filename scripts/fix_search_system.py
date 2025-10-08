#!/usr/bin/env python3
"""
Comprehensive script to fix the search system
"""

import os
import subprocess
import sys
from pathlib import Path

import requests


def download_longclip_models():
    """Download LongCLIP models from Hugging Face"""
    print("=== Downloading LongCLIP Models ===")

    # Model URLs (these need to be verified)
    models = {
        "longclip-B": "https://huggingface.co/BeichenZhang/LongCLIP-B/resolve/main/pytorch_model.bin",
        "longclip-L": "https://huggingface.co/BeichenZhang/LongCLIP-L/resolve/main/pytorch_model.bin",
    }

    # Download directory
    download_dir = Path("support_models/Long-CLIP/checkpoints")
    download_dir.mkdir(parents=True, exist_ok=True)

    print("Note: Direct download may not work due to Hugging Face restrictions.")
    print("Please manually download the models from:")
    print("  - https://huggingface.co/BeichenZhang/LongCLIP-B")
    print("  - https://huggingface.co/BeichenZhang/LongCLIP-L")
    print(f"\nPlace the downloaded .pt files in: {download_dir.absolute()}")

    return False


def check_models():
    """Check if models are available"""
    print("\n=== Checking Model Availability ===")

    checkpoint_dir = Path("support_models/Long-CLIP/checkpoints")
    pt_files = list(checkpoint_dir.glob("*.pt"))

    if pt_files:
        print(f"✅ Found {len(pt_files)} model files:")
        for pt_file in pt_files:
            print(f"  - {pt_file.name}")
        return True
    else:
        print("❌ No .pt model files found")
        print(f"Expected location: {checkpoint_dir.absolute()}")
        return False


def reinstall_dependencies():
    """Reinstall dependencies to ensure proper model loading"""
    print("\n=== Reinstalling Dependencies ===")

    try:
        # Install deep-translator for better translation
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "deep-translator"], check=True
        )
        print("✅ deep-translator installed")

        # Install CLIP
        subprocess.run([sys.executable, "-m", "pip", "install", "clip"], check=True)
        print("✅ CLIP installed")

    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

    return True


def rebuild_features():
    """Rebuild features with real models"""
    print("\n=== Rebuilding Features ===")

    if not check_models():
        print("❌ Cannot rebuild features without models")
        return False

    try:
        # Run feature extraction
        cmd = [sys.executable, "scripts/extract_features.py", "--device", "cpu"]
        print(f"Running: {' '.join(cmd)}")

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            print("✅ Features rebuilt successfully")
            print("Output:", result.stdout)
        else:
            print("❌ Feature extraction failed")
            print("Error:", result.stderr)
            return False

    except Exception as e:
        print(f"❌ Failed to rebuild features: {e}")
        return False

    return True


def rebuild_faiss_index():
    """Rebuild FAISS index with new features"""
    print("\n=== Rebuilding FAISS Index ===")

    try:
        # Run FAISS building
        cmd = [sys.executable, "scripts/build_faiss_from_features_fixed.py"]
        print(f"Running: {' '.join(cmd)}")

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            print("✅ FAISS index rebuilt successfully")
            print("Output:", result.stdout)
        else:
            print("❌ FAISS index building failed")
            print("Error:", result.stderr)
            return False

    except Exception as e:
        print(f"❌ Failed to rebuild FAISS index: {e}")
        return False

    return True


def test_search():
    """Test the search system after fixes"""
    print("\n=== Testing Search System ===")

    try:
        # Run search test
        cmd = [sys.executable, "scripts/debug_search.py"]
        print(f"Running: {' '.join(cmd)}")

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            print("✅ Search test completed")
            print("Check the output above for search quality")
        else:
            print("❌ Search test failed")
            print("Error:", result.stderr)

    except Exception as e:
        print(f"❌ Failed to test search: {e}")


def main():
    """Main fix process"""
    print("🔧 Fixing Search System Issues")
    print("=" * 50)

    # Step 1: Check current state
    print("\n📋 Current Status:")
    print("  - Translation: ✅ Working (with deep-translator)")
    print("  - LongCLIP Models: ❌ Missing")
    print("  - Features: ❌ Mock/random")
    print("  - FAISS Index: ⚠️  Built with mock features")
    print("  - Search Quality: ❌ Very poor (random results)")

    # Step 2: Install dependencies
    if not reinstall_dependencies():
        print("❌ Failed to install dependencies")
        return

    # Step 3: Download models (manual step)
    download_longclip_models()

    # Step 4: Check if models are now available
    if not check_models():
        print("\n❌ Models still not available.")
        print("Please manually download the LongCLIP models and try again.")
        print("\nManual steps:")
        print("1. Go to https://huggingface.co/BeichenZhang/LongCLIP-B")
        print("2. Download the model files (.pt)")
        print("3. Place them in support_models/Long-CLIP/checkpoints/")
        print("4. Run this script again")
        return

    # Step 5: Rebuild features
    if not rebuild_features():
        print("❌ Failed to rebuild features")
        return

    # Step 6: Rebuild FAISS index
    if not rebuild_faiss_index():
        print("❌ Failed to rebuild FAISS index")
        return

    # Step 7: Test search
    test_search()

    print("\n🎉 Search system fix completed!")
    print("\nNext steps:")
    print("1. Test the search in the web interface")
    print("2. Check if results are now relevant")
    print("3. If issues persist, check the logs for errors")


if __name__ == "__main__":
    main()
