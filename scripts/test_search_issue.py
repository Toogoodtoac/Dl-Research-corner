#!/usr/bin/env python3
"""
Test script to demonstrate the current search issue
"""

import os
import sys

import numpy as np

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))


def test_current_search_issue():
    """Test the current search issue"""
    print("🔍 Testing Current Search Issue")
    print("=" * 50)

    # Check if features are random
    features_path = "data/features-longclip/all_features.npy"
    if os.path.exists(features_path):
        features = np.load(features_path)
        print(f"📊 Features loaded: {features.shape}")

        # Check if features are random
        first_feature = features[0]
        feature_norm = np.linalg.norm(first_feature)
        feature_variance = np.var(first_feature)

        print(f"   First feature norm: {feature_norm:.4f}")
        print(f"   First feature variance: {feature_variance:.4f}")
        print(f"   First 5 values: {first_feature[:5]}")

        # Random features have variance ≈ 1.0
        if 0.9 < feature_variance < 1.1:
            print("❌ PROBLEM: Features are random numbers!")
            print("   This explains why search results are wrong.")
            print("   The FAISS index contains no semantic information.")
        else:
            print("✅ Features appear to be real (not random)")

    # Check FAISS index
    faiss_path = "data/indexes/faiss/faiss_clip_vitb32.bin"
    if os.path.exists(faiss_path):
        print(f"\n📁 FAISS index exists: {faiss_path}")
        print("   But it was built with random features!")

    # Check LongCLIP model
    longclip_path = "support_models/Long-CLIP/checkpoints/longclip-B.pt"
    if os.path.exists(longclip_path):
        print(f"✅ LongCLIP model exists: {longclip_path}")
    else:
        print(f"❌ LongCLIP model missing: {longclip_path}")
        print("   This is why features are random!")

    print("\n🔧 SOLUTION:")
    print("   1. Download LongCLIP models, OR")
    print("   2. Rebuild index with CLIP features using:")
    print("      python scripts/rebuild_clip_index.py")


if __name__ == "__main__":
    test_current_search_issue()
