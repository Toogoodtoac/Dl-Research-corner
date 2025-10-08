# extract.py

import argparse
import os
import sys
from pathlib import Path
from typing import List

import numpy as np
from beit3_wrapper import Beit3Wrapper
from PIL import Image
from tqdm import tqdm

VALID_EXTS = (".jpg", ".jpeg", ".png", ".bmp", ".webp")


def list_video_dirs(root: Path, level: str) -> List[Path]:
    base = root / level / "keyframes"
    if not base.exists():
        return []
    return sorted([p for p in base.iterdir() if p.is_dir()])


def list_images(video_dir: Path) -> List[Path]:
    imgs = [
        p for p in video_dir.iterdir() if p.is_file() and p.suffix.lower() in VALID_EXTS
    ]

    def key_fn(p: Path):
        try:
            return (0, int(p.stem))
        except:
            return (1, p.stem)

    return sorted(imgs, key=key_fn)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=str, default="/home/data/keyframe_btc")
    ap.add_argument(
        "--levels", nargs="*", default=[f"Keyframes_L{i}" for i in range(21, 30 + 1)]
    )
    ap.add_argument("--out", type=str, default="./features_beit3")
    ap.add_argument("--device", type=str, default="cuda")
    ap.add_argument("--batch", type=int, default=128)  # chỉ batching ở đây
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()

    root = Path(args.root)
    out_root = Path(args.out)
    out_root.mkdir(parents=True, exist_ok=True)
    for lv in args.levels:
        (out_root / lv).mkdir(parents=True, exist_ok=True)

    wrapper = Beit3Wrapper(device=args.device)

    for lv in args.levels:
        vdirs = list_video_dirs(root, lv)
        print(f"[{lv}] Found {len(vdirs)} video folders.")
        for vdir in tqdm(vdirs, desc=f"Encoding {lv}", unit="video"):
            vid = vdir.name  # ví dụ: L21_V001
            out_path = out_root / lv / f"{vid}.npy"
            if out_path.exists() and not args.overwrite:
                continue

            img_paths = list_images(vdir)
            if not img_paths:
                np.save(out_path, np.zeros((0, 768), dtype=np.float32))
                continue

            feats_chunks = []
            # batching tại đây: mỗi batch encode từng ảnh
            for i in range(0, len(img_paths), args.batch):
                batch_paths = img_paths[i : i + args.batch]
                batch_feats = []
                for p in batch_paths:
                    try:
                        im = Image.open(p).convert("RGB")
                    except Exception as e:
                        print(f"[WARN] cannot read {p}: {e}")
                        continue
                    feat = wrapper.encode_image(im)  # (768,)
                    batch_feats.append(feat)
                if batch_feats:
                    feats_chunks.append(np.vstack(batch_feats))  # (B,768)

            feats = (
                np.vstack(feats_chunks)
                if feats_chunks
                else np.zeros((0, 768), dtype=np.float32)
            )
            np.save(out_path, feats)
            print(f"[save] {out_path}  shape={feats.shape}")

    print("[DONE]")


if __name__ == "__main__":
    main()
