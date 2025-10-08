#!/usr/bin/env python3
"""
Script to download LongCLIP models from Hugging Face
"""

import os
import sys
from pathlib import Path

import requests

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))


def download_file(url: str, filepath: str):
    """Download a file from URL to filepath"""
    print(f"Downloading {url} to {filepath}")

    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    response = requests.get(url, stream=True)
    response.raise_for_status()

    total_size = int(response.headers.get("content-length", 0))
    downloaded = 0

    with open(filepath, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
                downloaded += len(chunk)
                if total_size > 0:
                    percent = (downloaded / total_size) * 100
                    print(
                        f"\rProgress: {percent:.1f}% ({downloaded}/{total_size} bytes)",
                        end="",
                    )

    print(f"\nDownloaded: {filepath}")


def main():
    """Download LongCLIP models"""

    # Model URLs from the model zoo
    models = {
        "longclip-B": "https://huggingface.co/BeichenZhang/LongCLIP-B/resolve/main/pytorch_model.bin",
        "longclip-L": "https://huggingface.co/BeichenZhang/LongCLIP-L/resolve/main/pytorch_model.bin",
    }

    # Download directory
    download_dir = Path("../support_models/Long-CLIP/checkpoints")

    print("Downloading LongCLIP models...")

    for model_name, url in models.items():
        try:
            # For now, let's try to download the B model first
            if model_name == "longclip-B":
                filepath = download_dir / "longclip-B.pt"
                download_file(url, str(filepath))
                print(f"Successfully downloaded {model_name}")
                break  # Just download one for now
        except Exception as e:
            print(f"Failed to download {model_name}: {e}")
            continue

    print("Download completed!")


if __name__ == "__main__":
    main()
