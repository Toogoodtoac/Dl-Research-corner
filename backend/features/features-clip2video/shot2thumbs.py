# -*- coding: utf-8 -*-
"""
shot2thumbs.py (v2)
- Tạo thumbnail giữa mỗi shot HOẶC tái tổ chức cấu trúc thumbnails theo yêu cầu.
- Cấu trúc mới:
  F:\My Drive\AIC2025_data\thumbnails\Videos_Lxx\{video_id}\{shot_ordinal_3digits}.jpg
    ví dụ: ...\thumbnails\Videos_L21\L21_V001\001.jpg

- id2shot.json được cập nhật in-place: trường "thumb_path" trỏ đến đường dẫn mới.

Chạy:
  python shot2thumbs.py                  # xử lý toàn bộ
  python shot2thumbs.py --limit 50       # test 50 entries đầu

Yêu cầu:
- ffmpeg trong PATH (đã cài qua conda-forge)
"""

import argparse
import csv
import json
import os
import shutil
import subprocess
import sys
import time
from typing import Optional, Tuple

# =======================
# CẤU HÌNH MẶC ĐỊNH
# =======================
ID2SHOT_JSON = r"E:\AI_Competition\AIC2025\dict\id2shot.json"
CSV_ROOT = r"E:\AI_Competition\AIC2025\dict\shots_PSD"  # ...\Videos_L21\L21_V001.csv
VIDEO_ROOT = r"F:\My Drive\AIC2025_data\video_btc"  # ...\Videos_L21\video\L21_V001.mp4
OUT_ROOT = r"F:\My Drive\AIC2025_data\thumbnails"  # gốc của thumbnails

THUMB_WIDTH = 480
JPEG_QUALITY = "3"
FFMPEG_LOGLV = "error"  # "quiet"/"error"/"warning"/"info"


# =======================
# TIỆN ÍCH
# =======================
def ensure_dir(p: str):
    os.makedirs(p, exist_ok=True)


def backup_json(path: str) -> str:
    ts = time.strftime("%Y%m%d-%H%M%S")
    bak = f"{os.path.splitext(path)[0]}.backup.{ts}.json"
    shutil.copy2(path, bak)
    return bak


def read_json(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: str, obj: dict):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def safe_float(v) -> Optional[float]:
    try:
        return float(str(v).strip())
    except Exception:
        return None


def csv_path_for_video(csv_root: str, video_id: str) -> Optional[str]:
    batch = video_id.split("_")[0]  # "L21"
    folder = f"Videos_{batch}"
    candidate = os.path.join(csv_root, folder, f"{video_id}.csv")
    return candidate if os.path.exists(candidate) else None


def read_psd_row_bounds(
    csv_file: str, shot_index: int
) -> Optional[Tuple[float, float]]:
    try:
        rows = []
        with open(csv_file, "r", encoding="utf-8", newline="") as f:
            rdr = csv.DictReader(f)
            for r in rdr:
                s = safe_float(r.get("Start Time (seconds)"))
                e = safe_float(r.get("End Time (seconds)"))
                if s is None or e is None:
                    continue
                rows.append((s, e))
        if 0 <= shot_index < len(rows):
            return rows[shot_index]
    except Exception:
        pass
    return None


def mid_time_from_meta(meta: dict, csv_root: str) -> Optional[float]:
    # 1) ưu tiên JSON
    t0 = safe_float(meta.get("start_seconds"))
    t1 = safe_float(meta.get("end_seconds"))
    if t0 is not None and t1 is not None and t1 >= t0:
        return t0 + (t1 - t0) / 2.0
    # 2) fallback CSV
    video_id = str(meta["video_id"])
    sid = int(meta["shot_index"])
    csv_file = csv_path_for_video(csv_root, video_id)
    if csv_file:
        bounds = read_psd_row_bounds(csv_file, sid)
        if bounds:
            s, e = bounds
            return s + max(0.0, e - s) / 2.0
    return None


def video_file_for_id(video_root: str, video_id: str) -> Optional[str]:
    batch = video_id.split("_")[0]  # "L21"
    base_dir = os.path.join(video_root, f"Videos_{batch}", "video")
    candidates = [
        os.path.join(base_dir, f"{video_id}.mp4"),
        os.path.join(base_dir, f"{video_id}.mkv"),
        os.path.join(base_dir, f"{video_id}.mov"),
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return None


def out_path_for_shot(out_root: str, video_id: str, shot_index: int) -> str:
    """Tạo đường dẫn mới theo chuẩn yêu cầu."""
    batch = video_id.split("_")[0]  # "L21"
    folder = os.path.join(out_root, f"Videos_{batch}", video_id)
    ensure_dir(folder)
    # tên file 3-digit theo thứ tự shot (1-based)
    name = f"{shot_index + 1:03d}.jpg"
    return os.path.join(folder, name)


def make_thumb(video_path: str, mid_sec: float, out_path: str) -> bool:
    """
    Thử 2 chiến lược:
    1) Fast seek: -ss trước -i (nhanh)
    2) Accurate seek (fallback): -ss sau -i + bỏ qua lỗi nhẹ
    """
    # 1) Fast seek (nhanh)
    cmd_fast = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        FFMPEG_LOGLV,  # ví dụ: "error" hoặc "warning" để xem thêm log
        "-ss",
        f"{mid_sec}",
        "-i",
        video_path,
        "-frames:v",
        "1",
        "-vf",
        f"scale='min({THUMB_WIDTH},iw)':-2",
        "-q:v",
        JPEG_QUALITY,
        "-y",
        out_path,
    ]
    try:
        subprocess.run(cmd_fast, check=True)
        return os.path.exists(out_path)
    except subprocess.CalledProcessError:
        pass  # thử fallback

    # 2) Accurate seek (chậm hơn nhưng bền)
    #   - đặt -ss sau -i để ffmpeg giải mã tuần tự đến thời điểm mong muốn
    #   - thêm cờ bỏ qua lỗi giải mã nhẹ
    cmd_accurate = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        FFMPEG_LOGLV,
        "-err_detect",
        "ignore_err",  # bỏ qua lỗi giải mã nhẹ
        "-fflags",
        "+discardcorrupt+genpts",  # bỏ frame hỏng, tự sinh PTS nếu cần
        "-i",
        video_path,
        "-ss",
        f"{mid_sec}",
        "-frames:v",
        "1",
        "-vf",
        f"scale='min({THUMB_WIDTH},iw)':-2",
        "-q:v",
        JPEG_QUALITY,
        "-y",
        out_path,
    ]
    try:
        subprocess.run(cmd_accurate, check=True)
        return os.path.exists(out_path)
    except subprocess.CalledProcessError:
        return False


# =======================
# MAIN
# =======================
def main():
    parser = argparse.ArgumentParser(
        description="Generate/reorganize shot thumbnails and update id2shot.json in-place."
    )
    parser.add_argument("--id2shot", default=ID2SHOT_JSON)
    parser.add_argument("--csv-root", default=CSV_ROOT)
    parser.add_argument("--video-root", default=VIDEO_ROOT)
    parser.add_argument("--out-root", default=OUT_ROOT)
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    id2shot_path = args.id2shot
    csv_root = args.csv_root
    video_root = args.video_root
    out_root = args.out_root

    if not os.path.exists(id2shot_path):
        print("ERR: Not found:", id2shot_path)
        sys.exit(1)

    data = read_json(id2shot_path)
    keys = sorted(data.keys(), key=lambda x: int(x))
    if args.limit is not None:
        keys = keys[: args.limit]

    # backup trước khi sửa
    bak = backup_json(id2shot_path)
    print(f"[+] Backed up to: {bak}")

    total = made = moved = skipped = missing_video = failed_ffmpeg = no_time = 0

    for k in keys:
        meta = data[k]
        video_id = str(meta["video_id"])
        shot_idx = int(meta["shot_index"])

        # đích mới theo cấu trúc yêu cầu
        new_path = out_path_for_shot(out_root, video_id, shot_idx)

        # nếu đã đúng vị trí mới → cập nhật và bỏ qua
        if os.path.exists(new_path):
            meta["thumb_path"] = new_path
            skipped += 1
            total += 1
            continue

        # nếu có thumb cũ (đường dẫn phẳng) → move sang vị trí mới
        old_path = meta.get("thumb_path")
        if (
            old_path
            and os.path.exists(old_path)
            and os.path.abspath(old_path) != os.path.abspath(new_path)
        ):
            ensure_dir(os.path.dirname(new_path))
            try:
                shutil.move(old_path, new_path)
                meta["thumb_path"] = new_path
                moved += 1
                total += 1
                continue
            except Exception:
                # nếu move lỗi, sẽ thử tạo lại bằng ffmpeg
                pass

        # Nếu chưa có file → tạo mới bằng ffmpeg
        mid = mid_time_from_meta(meta, csv_root)
        if mid is None:
            no_time += 1
            total += 1
            continue

        vpath = video_file_for_id(video_root, video_id)
        if not vpath:
            missing_video += 1
            total += 1
            continue

        ok = make_thumb(vpath, mid, new_path)
        if ok:
            meta["thumb_path"] = new_path
            made += 1
        else:
            failed_ffmpeg += 1

        total += 1

    write_json(id2shot_path, data)

    print("\n=== SUMMARY ===")
    print("Total entries     :", total)
    print("Created thumbnails:", made)
    print("Moved thumbnails  :", moved)
    print("Skipped (exists)  :", skipped)
    print("Missing video     :", missing_video)
    print("No mid time       :", no_time)
    print("ffmpeg failed     :", failed_ffmpeg)
    print("Updated JSON      :", id2shot_path)
    print("Output root       :", out_root)


if __name__ == "__main__":
    main()
