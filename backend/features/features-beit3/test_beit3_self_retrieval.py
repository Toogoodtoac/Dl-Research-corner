# we dont need to care about this file
# test_beit3_text2img_single_video.py
import argparse
import json
import os
import sys

import numpy as np
import torch

# ===============================
# 1) IMPORT BEiT3 WRAPPER
# ===============================
CUR_DIR = os.path.dirname(os.path.abspath(__file__))
if CUR_DIR not in sys.path:
    sys.path.insert(0, CUR_DIR)

from beit3_wrapper import BEiT3Wrapper  # dùng bản wrapper đã fix


# ===============================
# 2) UTILITIES
# ===============================
def l2_normalize(x: np.ndarray, eps: float = 1e-12) -> np.ndarray:
    if x.ndim == 1:
        denom = np.sqrt((x * x).sum()) + eps
        return x / denom
    else:
        denom = np.sqrt((x * x).sum(axis=1, keepdims=True)) + eps
        return x / denom


def build_frame_paths(keyframe_dir: str, idxs: np.ndarray):
    """
    keyframe_dir: thư mục chứa các ảnh frame .jpg (tên dạng 001.jpg, 002.jpg, ...)
    idxs: chỉ số 0-based của frame (0 -> 001.jpg)
    """
    paths = []
    for i in idxs:
        fname = f"{int(i)+1:03d}.jpg"
        paths.append(os.path.join(keyframe_dir, fname))
    return paths


# ===============================
# 3) MAIN
# ===============================
def main():
    parser = argparse.ArgumentParser(
        description="Text->Image Retrieval test trên 1 file features .npy (BEiT-3)"
    )
    parser.add_argument(
        "--feature_npy",
        required=True,
        type=str,
        help="Đường dẫn .npy features của 1 video, ví dụ: E:\\AI_Competition\\AIC2025\\features\\features-beit3\\features\\L21_V001.npy",
    )
    parser.add_argument(
        "--text",
        required=True,
        type=str,
        help="Câu query tiếng Anh (hoặc đã dịch sang EN)",
    )
    parser.add_argument(
        "--checkpoint",
        required=True,
        type=str,
        help="Đường dẫn .pth BEiT3, ví dụ: ...\\checkpoints\\beit3_large_patch16_384_coco_retrieval.pth",
    )
    parser.add_argument("--spm", required=True, type=str, help="Đường dẫn beit3.spm")
    parser.add_argument(
        "--device", default="cuda" if torch.cuda.is_available() else "cpu"
    )
    parser.add_argument("--topk", type=int, default=10)

    # Tuỳ chọn: gốc thư mục keyframes để in path ảnh kết quả
    # Ví dụ: E:\AI_Competition\AIC2025\keyframe_btc\Keyframes_L21\keyframes\L21_V001
    parser.add_argument(
        "--keyframe_dir",
        type=str,
        default="",
        help="(Optional) Thư mục chứa các frame .jpg để map kết quả -> đường dẫn ảnh",
    )

    args = parser.parse_args()
    print("==> Device:", args.device)

    # 3.1 Load features của video (N, D)
    if not os.path.isfile(args.feature_npy):
        raise FileNotFoundError(f"Không tìm thấy file features: {args.feature_npy}")
    feats = np.load(args.feature_npy).astype(np.float32)  # (N, D)
    if feats.ndim == 3 and feats.shape[1] == 1:
        print(f"⚠️ Fixing shape from {feats.shape} → {(feats.shape[0], feats.shape[2])}")
        feats = feats[:, 0, :]  # (N, 1024)
    feats = l2_normalize(feats)  # đảm bảo chuẩn hoá

    N, D = feats.shape
    print(f"==> Loaded features: shape={feats.shape} (N={N}, D={D})")

    # 3.2 Khởi tạo BEiT3
    beit3 = BEiT3Wrapper(
        checkpoint_path=args.checkpoint, spm_path=args.spm, device=args.device
    )

    # 3.3 Encode text -> (1, D)
    txt = args.text.strip()
    txt_emb = beit3.encode_text(txt)  # (1, D) float32, đã L2-normalized trong wrapper
    if txt_emb.ndim != 2 or txt_emb.shape[1] != D:
        raise ValueError(
            f"Dim mismatch: text_emb has shape {txt_emb.shape}, features have D={D}"
        )

    # 3.4 Tính cosine similarity (feats & txt_emb đều đã L2-normalized)
    # sim = feats @ txt_emb.T -> (N, 1)
    sim = feats @ txt_emb[0].reshape(-1, 1)  # (N,1)
    sim = sim[:, 0]  # (N,)

    # 3.5 Lấy Top-K
    k = min(args.topk, N)
    top_idx = np.argpartition(-sim, k - 1)[:k]
    # Sắp xếp theo score giảm dần
    top_idx = top_idx[np.argsort(-sim[top_idx])]

    print(f"\n==> Query: {txt}")
    print(f"==> Top-{k} frames:")
    for rank, i in enumerate(top_idx, start=1):
        score = float(sim[i])
        if args.keyframe_dir:
            path = os.path.join(args.keyframe_dir, f"{int(i)+1:03d}.jpg")
            print(f"[{rank}] frame_idx={int(i)}  score={score:.6f}  path={path}")
        else:
            print(f"[{rank}] frame_idx={int(i)}  score={score:.6f}")

    print("\nNOTE:")
    print(
        "- Nếu kết quả không hợp lý, thường do tokenizer/model khi encode text KHÔNG TRÙNG với pipeline lúc trích features."
    )
    print(
        "- Hãy chắc dùng đúng beit3.spm và checkpoint tương ứng; cùng resize 384, cùng mean/std."
    )


if __name__ == "__main__":
    main()
