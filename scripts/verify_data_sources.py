#!/usr/bin/env python3
"""
Data Source Verification Script

This script helps you verify which data sources your backend is using.
Run this script to check if you're loading from Google Drive or local data.
"""

import os
import sys

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))

from core.config import settings

import env_path_manager as pm


def verify_data_sources():
    """Verify which data sources are being used"""

    print("🔍 DATA SOURCE VERIFICATION")
    print("=" * 60)

    # Environment info
    print(f"🌍 Environment: {pm.detect_env()}")
    print(f"📁 Repo root: {pm.REPO_ROOT}")
    print(f"💾 Data root: {pm.path_manager.get_data_root()}")
    print()

    # Check available sources
    print("📊 Available Data Sources:")
    sources = pm.path_manager.list_available_sources()
    for source, available in sources.items():
        status = "✅ Available" if available else "❌ Not Available"
        print(f"   {source}: {status}")
    print()

    # Check specific paths
    print("🎯 Backend Configuration Paths:")

    # Video data
    video_path = settings.VIDEO_DATA_DIR
    video_exists = os.path.exists(video_path)
    video_source = "Google Drive" if "GoogleDrive" in video_path else "Local"
    print(f"   📹 Video data: {video_source}")
    print(f"      Path: {video_path}")
    print(f"      Exists: {'✅ Yes' if video_exists else '❌ No'}")
    if video_exists:
        try:
            files = os.listdir(video_path)[:3]
            print(f"      Sample files: {files}")
        except:
            print(f"      Sample files: (cannot list)")

    # Keyframe data
    keyframe_path = settings.KEYFRAME_DATA_DIR
    keyframe_exists = os.path.exists(keyframe_path)
    keyframe_source = "Google Drive" if "GoogleDrive" in keyframe_path else "Local"
    print(f"   🖼️  Keyframe data: {keyframe_source}")
    print(f"      Path: {keyframe_path}")
    print(f"      Exists: {'✅ Yes' if keyframe_exists else '❌ No'}")
    if keyframe_exists:
        try:
            files = os.listdir(keyframe_path)[:3]
            print(f"      Sample files: {files}")
        except:
            print(f"      Sample files: (cannot list)")

    # Dict files (should always be local)
    dict_path = settings.ID2IMG_JSON_PATH
    dict_exists = os.path.exists(dict_path)
    dict_source = "Google Drive" if "GoogleDrive" in dict_path else "Local"
    print(f"   📋 Dict files: {dict_source}")
    print(f"      Path: {dict_path}")
    print(f"      Exists: {'✅ Yes' if dict_exists else '❌ No'}")

    # Features (should always be local)
    features_path = settings.FAISS_LONGCLIP_PATH
    features_exists = os.path.exists(features_path)
    features_source = "Google Drive" if "GoogleDrive" in features_path else "Local"
    print(f"   🧠 Features: {features_source}")
    print(f"      Path: {features_path}")
    print(f"      Exists: {'✅ Yes' if features_exists else '❌ No'}")

    print()

    # Summary
    print("📋 SUMMARY:")
    if "GoogleDrive" in video_path and "GoogleDrive" in keyframe_path:
        print("   ✅ CORRECT: Loading video and keyframe data from Google Drive")
    else:
        print("   ❌ INCORRECT: Not loading from Google Drive")

    if "GoogleDrive" not in dict_path and "GoogleDrive" not in features_path:
        print("   ✅ CORRECT: Loading dict and features from repo root")
    else:
        print("   ❌ INCORRECT: Dict/features should be from repo root")

    print()
    print("💡 To switch environments:")
    print("   Local:  make dev-backend")
    print("   Google Drive: AIC_ENV=prod make dev-backend")


if __name__ == "__main__":
    verify_data_sources()
