#!/usr/bin/env python3
"""
Rebuild FAISS index using CLIP features instead of corrupted LongCLIP features
"""

import json
import os
import sys
from pathlib import Path

import clip
import faiss
import numpy as np
import torch
from PIL import Image

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))


def load_clip_model():
    """Load CLIP model"""
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model, preprocess = clip.load("ViT-B/32", device=device)
    return model, preprocess, device


def extract_clip_features(image_path, model, preprocess, device):
    """Extract CLIP features from an image"""
    try:
        # Load and preprocess image
        image = Image.open(image_path).convert("RGB")
        image_tensor = preprocess(image).unsqueeze(0).to(device)

        # Extract features
        with torch.no_grad():
            features = model.encode_image(image_tensor)
            features = features.cpu().numpy().flatten().astype(np.float32)

            # Normalize features (important for FAISS IndexFlatIP)
            features = features / (np.linalg.norm(features) + 1e-8)

        return features
    except Exception as e:
        print(f"Failed to extract features from {image_path}: {e}")
        return None


def rebuild_faiss_index():
    """Rebuild FAISS index with CLIP features"""
    print("🔧 Rebuilding FAISS Index with CLIP Features")
    print("=" * 50)

    # Load CLIP model
    print("📥 Loading CLIP model...")
    model, preprocess, device = load_clip_model()
    print(f"✅ CLIP model loaded on {device}")

    # Load ID2IMG mapping
    id2img_path = "data/indexes/faiss/id2img.json"
    with open(id2img_path, "r") as f:
        id2img = json.load(f)

    print(f"📋 Loaded {len(id2img)} image mappings")

    # Initialize feature array
    total_images = len(id2img)
    feature_dim = 512
    features = np.zeros((total_images, feature_dim), dtype=np.float32)

    # Extract features from each image
    print("🔄 Extracting CLIP features...")
    successful_extractions = 0

    for idx in range(total_images):
        if idx % 100 == 0:
            print(f"   Processing {idx}/{total_images}...")

        image_path = id2img[str(idx)]
        full_path = os.path.join("data", image_path)

        if os.path.exists(full_path):
            feature = extract_clip_features(full_path, model, preprocess, device)
            if feature is not None:
                features[idx] = feature
                successful_extractions += 1
            else:
                # Use zero vector for failed extractions
                features[idx] = np.zeros(feature_dim, dtype=np.float32)
        else:
            print(f"⚠️  Image not found: {full_path}")
            features[idx] = np.zeros(feature_dim, dtype=np.float32)

    print(
        f"✅ Successfully extracted features from {successful_extractions}/{total_images} images"
    )

    # Create FAISS index
    print("🏗️  Creating FAISS index...")
    index = faiss.IndexFlatIP(feature_dim)  # Inner Product for normalized vectors

    # Add vectors to index
    index.add(features)

    print(f"✅ FAISS index created with {index.ntotal} vectors")
    print(f"   Index type: {type(index)}")
    print(f"   Dimension: {index.d}")

    # Test the index
    print("🧪 Testing index...")
    test_query = np.random.randn(1, feature_dim).astype(np.float32)
    test_query = test_query / (np.linalg.norm(test_query, axis=1, keepdims=True) + 1e-8)

    scores, indices = index.search(test_query, k=5)
    print(f"   Test query scores: {scores[0]}")
    print(f"   Test query indices: {indices[0]}")

    # Save the index
    output_path = "data/indexes/faiss/faiss_clip_vitb32_rebuilt.bin"
    faiss.write_index(index, output_path)
    print(f"💾 Index saved to: {output_path}")

    # Save features for backup
    features_path = "data/features-longclip/clip_features_rebuilt.npy"
    np.save(features_path, features)
    print(f"💾 Features saved to: {features_path}")

    print("\n🎉 FAISS index rebuilt successfully!")
    print("   - Use the new index for better search results")
    print("   - Features are properly normalized for IndexFlatIP")
    print("   - Search scores should now be meaningful")


if __name__ == "__main__":
    rebuild_faiss_index()
