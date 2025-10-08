#!/usr/bin/env python3
"""
Check feature files to understand their structure and quality
"""

import os
import sys

import numpy as np

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))


def check_features():
    """Check feature files"""

    print("=== Checking Feature Files ===")

    # Check all_features.npy
    all_features_path = "data/features-longclip/all_features.npy"
    if os.path.exists(all_features_path):
        print(f"\n--- Checking {all_features_path} ---")
        try:
            features = np.load(all_features_path)
            print(f"  Shape: {features.shape}")
            print(f"  Data type: {features.dtype}")
            print(f"  Min value: {np.min(features):.6f}")
            print(f"  Max value: {np.max(features):.6f}")
            print(f"  Mean value: {np.mean(features):.6f}")
            print(f"  Std value: {np.std(features):.6f}")

            # Check norms
            norms = np.linalg.norm(features, axis=1)
            print(
                f"  Feature norms - Min: {np.min(norms):.6f}, Max: {np.max(norms):.6f}, Mean: {np.mean(norms):.6f}"
            )

            # Check if features are normalized
            if np.allclose(norms, 1.0, atol=1e-6):
                print("  ✅ Features are properly normalized (norm ≈ 1.0)")
            else:
                print("  ⚠️  Features are NOT properly normalized")

        except Exception as e:
            print(f"  ❌ Failed to load features: {e}")

    # Check individual feature files
    features_dir = "data/features-longclip/features"
    if os.path.exists(features_dir):
        print(f"\n--- Checking individual feature files in {features_dir} ---")

        # Check first few files
        feature_files = [f for f in os.listdir(features_dir) if f.endswith(".npy")]
        feature_files.sort()

        for i, filename in enumerate(feature_files[:5]):  # Check first 5 files
            filepath = os.path.join(features_dir, filename)
            try:
                features = np.load(filepath)
                print(f"  {filename}: shape={features.shape}, dtype={features.dtype}")

                # Check norms for this file
                if features.size > 0:
                    norms = np.linalg.norm(features, axis=1)
                    print(
                        f"    Norms - Min: {np.min(norms):.6f}, Max: {np.max(norms):.6f}, Mean: {np.mean(norms):.6f}"
                    )

            except Exception as e:
                print(f"  {filename}: ❌ Failed to load - {e}")

    # Check if there's a mismatch between features and FAISS index
    print(f"\n--- Checking FAISS Index vs Features ---")

    # Load FAISS index
    try:
        import faiss

        faiss_path = "data/indexes/faiss/faiss_clip_vitb32.bin"
        if os.path.exists(faiss_path):
            index = faiss.read_index(faiss_path)
            print(f"  FAISS index: {index.ntotal} vectors, {index.d} dimensions")

            # Try to reconstruct a few vectors
            try:
                for i in range(min(3, index.ntotal)):
                    vector = index.reconstruct(i)
                    norm = np.linalg.norm(vector)
                    print(f"    Vector {i}: norm = {norm:.6f}")
            except Exception as e:
                print(f"    Cannot reconstruct vectors: {e}")

    except Exception as e:
        print(f"  ❌ Failed to load FAISS index: {e}")


if __name__ == "__main__":
    check_features()
