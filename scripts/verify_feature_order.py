#!/usr/bin/env python3
"""
Verify the exact order of features and ID mapping
"""

import glob
import json
import os
import sys

import numpy as np


def verify_feature_order():
    """Verify the exact order of features and ID mapping"""
    print("Verifying feature order...")

    # Load ID mapping
    with open("data/indexes/faiss/id2img.json", "r") as f:
        id2img = json.load(f)

    print(f"ID mapping has {len(id2img)} entries")

    # Check first few entries
    print("\nFirst 10 ID mappings:")
    for i in range(10):
        if str(i) in id2img:
            print(f"  ID {i}: {id2img[str(i)]}")
        else:
            print(f"  ID {i}: NOT_FOUND")

    # Check last few entries
    print("\nLast 10 ID mappings:")
    for i in range(7790, 7800):
        if str(i) in id2img:
            print(f"  ID {i}: {id2img[str(i)]}")
        else:
            print(f"  ID {i}: NOT_FOUND")

    # Load features
    features = np.load("data/features-longclip/all_features.npy")
    print(f"\nFeatures loaded: {features.shape}")

    # Check if the number of features matches the ID mapping
    if len(features) == len(id2img):
        print("✅ Feature count matches ID mapping count")
    else:
        print(
            f"❌ Feature count ({len(features)}) doesn't match ID mapping count ({len(id2img)})"
        )

    # Check the actual keyframe files to see the order
    print("\nChecking actual keyframe file order...")
    keyframe_pattern = "data/raw/keyframes/Keyframes_L21/keyframes/*"
    video_dirs = sorted(glob.glob(keyframe_pattern))

    print(f"Found {len(video_dirs)} video directories")

    # Check first few video directories
    for i, video_dir in enumerate(video_dirs[:5]):
        video_id = os.path.basename(video_dir)
        image_pattern = os.path.join(video_dir, "*.jpg")
        image_files = sorted(glob.glob(image_pattern))
        print(f"  {video_id}: {len(image_files)} keyframes")
        if image_files:
            print(f"    First: {os.path.basename(image_files[0])}")
            print(f"    Last: {os.path.basename(image_files[-1])}")

    # Check if the ID mapping matches the actual file order
    print("\nVerifying ID mapping against actual files...")
    correct_count = 0
    total_count = 0

    for i in range(min(20, len(id2img))):  # Check first 20
        if str(i) in id2img:
            expected_path = id2img[str(i)]
            full_path = os.path.join("data", expected_path)
            if os.path.exists(full_path):
                correct_count += 1
            else:
                print(f"  ❌ ID {i}: {expected_path} -> FILE_NOT_FOUND")
            total_count += 1

    print(f"✅ {correct_count}/{total_count} ID mappings point to existing files")

    return True


def main():
    """Run verification"""
    print("🔍 Feature Order Verification")
    print("=" * 40)

    verify_feature_order()


if __name__ == "__main__":
    main()
