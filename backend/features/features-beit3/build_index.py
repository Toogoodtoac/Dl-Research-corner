# dung de chay rieng build FAISS Index

import os
import sys

import faiss
import numpy as np

features_dir = r"E:\AI_Competition\AIC2025\features\features-beit3\features"
index_out = r"E:\AI_Competition\AIC2025\features\features-beit3\faiss_beit3.bin"

npy_paths = [
    os.path.join(features_dir, f)
    for f in sorted(os.listdir(features_dir))
    if f.endswith(".npy")
]
print(f"[faiss] found {len(npy_paths)} npy files")

all_blocks = []

for npy_path in sorted(npy_paths):
    video_id = os.path.splitext(os.path.basename(npy_path))[0]  # e.g., L21_V001
    print(f"Processing {video_id}")

    feats = np.load(npy_path).astype("float32", copy=False)  # shape: (N, D)
    N = feats.shape[0]
    all_blocks.append(feats)

# === Build FAISS index ===
X = np.vstack(all_blocks)  # (total_vectors, D)
faiss.normalize_L2(X)
index = faiss.IndexFlatIP(X.shape[1])
index.add(X)

# === Save ===
faiss.write_index(index, index_out)

print(f"[faiss] saved index -> {index_out}")
print(f"[faiss] total vecs  = {index.ntotal}")
