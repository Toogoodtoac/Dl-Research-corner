#!/usr/bin/env python3
"""
Test CLIP text encoding to debug search issues
"""

import os
import sys

import clip
import faiss
import numpy as np
import torch

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))


def test_clip_encoding():
    """Test CLIP text encoding"""

    print("=== Testing CLIP Text Encoding ===")

    # Test queries
    test_queries = [
        "man",
        "bird",
        "decoration",
        "purple",
        "festival",
        "behind this man is a decoration with a purple bird",
        "a person standing",
        "a bird flying",
        "a purple object",
        "a man wearing a shirt",
    ]

    # Load CLIP model
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")

    try:
        model, preprocess = clip.load("ViT-B/32", device=device)
        model.eval()
        print("CLIP model loaded successfully")

        # Load FAISS index
        faiss_path = "data/indexes/faiss/faiss_clip_vitb32.bin"
        if os.path.exists(faiss_path):
            index = faiss.read_index(faiss_path)
            print(f"FAISS index loaded: {index.ntotal} vectors, {index.d} dimensions")

            # Test each query
            for query in test_queries:
                print(f"\n--- Testing query: '{query}' ---")

                try:
                    # Encode text
                    with torch.no_grad():
                        tokens = clip.tokenize([query]).to(device)
                        text_features = model.encode_text(tokens)
                        text_features /= text_features.norm(dim=-1, keepdim=True)
                        text_features = (
                            text_features.cpu().detach().numpy().astype(np.float32)
                        )

                    print(f"  Text encoded successfully, shape: {text_features.shape}")
                    print(f"  Feature norm: {np.linalg.norm(text_features):.6f}")

                    # Search in FAISS
                    scores, indices = index.search(text_features, k=5)

                    print(f"  Top 5 results:")
                    for i in range(5):
                        print(
                            f"    {i+1}. Index: {indices[0][i]}, Score: {scores[0][i]:.4f}"
                        )

                    # Check if scores are reasonable
                    max_score = np.max(scores)
                    if max_score < 0.2:
                        print(f"  ⚠️  WARNING: Very low scores (max: {max_score:.4f})")
                    elif max_score < 0.3:
                        print(f"  ⚠️  WARNING: Low scores (max: {max_score:.4f})")
                    else:
                        print(f"  ✅ Good scores (max: {max_score:.4f})")

                except Exception as e:
                    print(f"  ❌ Failed to process query: {e}")

        else:
            print("FAISS index not found")

    except Exception as e:
        print(f"Failed to load CLIP model: {e}")


if __name__ == "__main__":
    test_clip_encoding()
