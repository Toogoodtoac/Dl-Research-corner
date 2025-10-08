#!/usr/bin/env python3
"""
Validate data sources and diagnose search issues
"""

import os
import sys
from pathlib import Path

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))


def validate_data_sources():
    """Validate all data sources and their availability"""

    print("🔍 Data Source Validation")
    print("=" * 50)

    # Check environment
    env = os.getenv("AIC_ENV", "dev")
    print(f"🌍 Environment: {env}")

    # Check local data
    print(f"\n📁 Local Data Sources:")
    local_data_root = Path("data")
    if local_data_root.exists():
        print(f"   ✅ Local data directory exists: {local_data_root.absolute()}")

        # Check indexes
        indexes_dir = local_data_root / "indexes" / "faiss"
        if indexes_dir.exists():
            print(f"   ✅ FAISS indexes directory exists: {indexes_dir}")

            # Check specific index files
            index_files = {
                "faiss_clip_vitb32.bin": indexes_dir / "faiss_clip_vitb32.bin",
                "faiss_longclip.bin": indexes_dir / "faiss_longclip.bin",
                "faiss_clip2video.bin": indexes_dir / "faiss_clip2video.bin",
                "id2img.json": indexes_dir / "id2img.json",
            }

            for name, path in index_files.items():
                if path.exists():
                    size = path.stat().st_size
                    print(f"      ✅ {name}: {size:,} bytes")
                else:
                    print(f"      ❌ {name}: Missing")
        else:
            print(f"   ❌ FAISS indexes directory missing: {indexes_dir}")

        # Check features
        features_dir = local_data_root / "features-longclip"
        if features_dir.exists():
            print(f"   ✅ Features directory exists: {features_dir}")

            # Check feature files
            feature_files = list(features_dir.glob("*.npy"))
            if feature_files:
                print(f"      ✅ Found {len(feature_files)} feature files")
                for f in feature_files[:3]:  # Show first 3
                    size = f.stat().st_size
                    print(f"         - {f.name}: {size:,} bytes")
            else:
                print(f"      ❌ No feature files found")
        else:
            print(f"   ❌ Features directory missing: {features_dir}")

        # Check raw data
        raw_data_dir = local_data_root / "raw" / "keyframes"
        if raw_data_dir.exists():
            print(f"   ✅ Raw keyframes directory exists: {raw_data_dir}")

            # Count keyframe directories
            keyframe_dirs = list(raw_data_dir.glob("Keyframes_L*"))
            if keyframe_dirs:
                print(f"      ✅ Found {len(keyframe_dirs)} keyframe directories")
                for d in keyframe_dirs[:3]:  # Show first 3
                    print(f"         - {d.name}")
            else:
                print(f"      ❌ No keyframe directories found")
        else:
            print(f"   ❌ Raw keyframes directory missing: {raw_data_dir}")

    else:
        print(f"   ❌ Local data directory missing: {local_data_root.absolute()}")

    # Check Google Drive data
    print(f"\n☁️  Google Drive Data Sources:")
    gdrive_path = Path(
        "/Users/tranlynhathao/Library/CloudStorage/GoogleDrive-haotran04022005@gmail.com/.shortcut-targets-by-id/1fXA9wu7HLdKxI0-yJ-n66eq2JV0d6j-H/AIC2025_data"
    )

    if gdrive_path.exists():
        print(f"   ✅ Google Drive path accessible: {gdrive_path}")

        # Check keyframe_btc directory
        keyframe_dir = gdrive_path / "keyframe_btc"
        if keyframe_dir.exists():
            print(f"   ✅ Keyframe directory exists: {keyframe_dir}")

            # Check for indexes
            gdrive_indexes = keyframe_dir / "indexes" / "faiss"
            if gdrive_indexes.exists():
                print(f"      ✅ FAISS indexes available in Google Drive")

                # Check specific files
                gdrive_files = {
                    "faiss_clip_vitb32.bin": gdrive_indexes / "faiss_clip_vitb32.bin",
                    "faiss_longclip.bin": gdrive_indexes / "faiss_longclip.bin",
                    "faiss_clip2video.bin": gdrive_indexes / "faiss_clip2video.bin",
                    "id2img.json": gdrive_indexes / "id2img.json",
                }

                for name, path in gdrive_files.items():
                    if path.exists():
                        size = path.stat().st_size
                        print(f"         ✅ {name}: {size:,} bytes")
                    else:
                        print(f"         ❌ {name}: Missing")
            else:
                print(f"      ❌ No FAISS indexes in Google Drive")
        else:
            print(f"   ❌ Keyframe directory missing in Google Drive")
    else:
        print(f"   ❌ Google Drive path not accessible: {gdrive_path}")

    # Check support models
    print(f"\n🤖 Support Models:")
    support_models_dir = Path("support_models")
    if support_models_dir.exists():
        print(f"   ✅ Support models directory exists: {support_models_dir}")

        # Check LongCLIP
        longclip_dir = support_models_dir / "Long-CLIP" / "checkpoints"
        if longclip_dir.exists():
            pt_files = list(longclip_dir.glob("*.pt"))
            if pt_files:
                print(f"   ✅ LongCLIP checkpoints found: {len(pt_files)} files")
                for f in pt_files:
                    size = f.stat().st_size
                    print(f"      - {f.name}: {size:,} bytes")
            else:
                print(f"   ❌ No LongCLIP checkpoints found")
        else:
            print(f"   ❌ LongCLIP checkpoints directory missing")

        # Check CLIP2Video
        clip2video_dir = support_models_dir / "CLIP2Video" / "checkpoints"
        if clip2video_dir.exists():
            print(f"   ✅ CLIP2Video checkpoints directory exists")
        else:
            print(f"   ❌ CLIP2Video checkpoints directory missing")
    else:
        print(f"   ❌ Support models directory missing: {support_models_dir}")

    # Summary and recommendations
    print(f"\n📋 Summary & Recommendations:")
    print("=" * 50)

    # Check if we have the minimum required data
    has_local_indexes = (
        local_data_root / "indexes" / "faiss" / "faiss_clip_vitb32.bin"
    ).exists()
    has_gdrive_indexes = (
        gdrive_path / "keyframe_btc" / "indexes" / "faiss" / "faiss_clip_vitb32.bin"
    ).exists()

    if has_local_indexes:
        print("✅ Local FAISS indexes available - search should work")
    elif has_gdrive_indexes:
        print("⚠️  Only Google Drive indexes available - search may be slower")
        print("   Consider downloading indexes locally for better performance")
    else:
        print("❌ No FAISS indexes available - search will not work")
        print("   Need to either:")
        print("   1. Download indexes to local data/ directory")
        print("   2. Ensure Google Drive indexes are accessible")

    # Check if we have models
    has_longclip = (support_models_dir / "Long-CLIP" / "checkpoints").exists() and any(
        (support_models_dir / "Long-CLIP" / "checkpoints").glob("*.pt")
    )
    has_clip2video = (support_models_dir / "CLIP2Video" / "checkpoints").exists()

    if has_longclip:
        print("✅ LongCLIP models available")
    else:
        print("❌ LongCLIP models missing - will fallback to CLIP")

    if has_clip2video:
        print("✅ CLIP2Video models available")
    else:
        print("❌ CLIP2Video models missing - CLIP2Video search won't work")


if __name__ == "__main__":
    validate_data_sources()
