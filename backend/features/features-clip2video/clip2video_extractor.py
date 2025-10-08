import csv
import json
import os
import subprocess
import sys
from typing import List, Optional, Tuple

import faiss
import numpy as np
import torch
from config import Config
from torchvision import transforms as T

# ==== Thêm CLIP2Video repo vào sys.path ====
CLIP2VIDEO_PATH = os.path.join(
    os.path.dirname(__file__), "../../..", "support_models", "CLIP2Video"
)
CLIP2VIDEO_PATH = os.path.abspath(CLIP2VIDEO_PATH)
if CLIP2VIDEO_PATH not in sys.path:
    sys.path.insert(0, CLIP2VIDEO_PATH)

from modules.modeling import CLIP2Video  # type: ignore
from modules.tokenization_clip import SimpleTokenizer as ClipTokenizer  # type: ignore


# ========================================
# CSV loader
# ========================================
def load_shots_from_csv(csv_path: str, video_path: str) -> List[Tuple]:
    """
    CSV PySceneDetect columns:
      Scene Number, Start Frame, Start Time (seconds), End Frame, End Time (seconds), Length (frames), Length (timecode), Length (seconds)
    Returns: (vid, sid, path, sf, st, ef, et)
    """
    shots: List[Tuple] = []
    with open(csv_path, "r", newline="") as f:
        reader = csv.DictReader(f)
        basename = os.path.splitext(os.path.basename(video_path))[0]
        for r in reader:
            shots.append(
                (
                    basename,
                    int(r["Scene Number"]),
                    video_path,
                    int(r["Start Frame"]),
                    float(r["Start Time (seconds)"]),
                    int(r["End Frame"]),
                    float(r["End Time (seconds)"]),
                )
            )
    return shots


# ========================================
# ffmpeg -> tensor
# ========================================
def extract_video_tensor(
    video_path: str,
    start_time: float,
    end_time: float,
    fps: int,
    size: int,
    max_frames: int,
):
    """
    Trích xuất tensor video (T,3,H,W) đã normalize giống CLIP.
    Trả về (video[1,1,1,T,3,H,W], mask[1,T]) hoặc (None, None) nếu lỗi.
    """
    duration = end_time - start_time
    if duration == 0 or (end_time - start_time) <= 1 / max(fps, 1):
        start_time = max(0, start_time - 0.25)
        end_time = start_time + 0.5
        duration = 0.5

    cmd = [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-threads",
        "2",
        "-ss",
        f"{start_time:.2f}",
        "-i",
        video_path,
        "-t",
        f"{duration:.2f}",
        "-r",
        str(fps),
        "-vf",
        f"scale={size}x{size}",
        "-pix_fmt",
        "rgb24",
        "-f",
        "rawvideo",
        "pipe:",
    ]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = proc.communicate()
    if proc.returncode != 0:
        print(f"[ffmpeg] error: {video_path}\n{err.decode().strip()}")
        return None, None

    frame_size = size * size * 3
    num_frames = len(out) // frame_size
    if num_frames <= 0:
        print(f"[ffmpeg] no frames: {video_path} [{start_time:.2f}-{end_time:.2f}]")
        return None, None

    try:
        frames = np.frombuffer(out, dtype=np.uint8).reshape((num_frames, size, size, 3))
    except ValueError:
        print(f"[ffmpeg] reshape error: {video_path}")
        return None, None

    frames = torch.tensor(frames).permute(0, 3, 1, 2).float() / 255.0
    transform = T.Normalize(
        (0.48145466, 0.4578275, 0.40821073), (0.26862954, 0.26130258, 0.27577711)
    )
    frames = torch.stack([transform(f) for f in frames])

    original_len = frames.size(0)
    if original_len > max_frames:
        idx = torch.linspace(0, original_len - 1, steps=max_frames).long()
        frames = frames[idx]
    elif original_len < max_frames:
        pad = torch.zeros((max_frames - original_len, 3, size, size))
        frames = torch.cat([frames, pad], dim=0)

    video = frames.unsqueeze(0).unsqueeze(0).unsqueeze(2)  # (1,1,1,T,3,H,W)
    mask = torch.zeros(1, max_frames, dtype=torch.long)
    mask[0, : min(original_len, max_frames)] = 1
    return video, mask


# ========================================
# CLIP2Video Wrapper Class
# ========================================
class CLIP2VideoFeatureExtraction:
    def __init__(
        self, checkpoint_dir: str, clip_weights_path: str, device: str = "cuda"
    ):
        self.args = Config(checkpoint=checkpoint_dir, clip_path=clip_weights_path)
        self.device = torch.device(device if torch.cuda.is_available() else "cpu")

        model_path = os.path.join(
            self.args.checkpoint, f"pytorch_model.bin.{self.args.model_num}"
        )

        print(f"[init] device: {self.device}")
        print(
            f"[init] load state_dict: {model_path} (exists={os.path.exists(model_path)})"
        )

        state_dict = (
            torch.load(model_path, map_location="cpu")
            if os.path.exists(model_path)
            else None
        )
        self.model = CLIP2Video.from_pretrained(
            self.args.cross_model, state_dict=state_dict, task_config=self.args
        )
        self.model.eval().to(self.device)

        # check if model is loaded on to GPU
        param_device = next(self.model.parameters()).device
        print(f"[check] model is on device: {param_device}")
        print("[init] model ready.")

    def get_video_features(
        self, visual_output: torch.Tensor, video_mask: torch.Tensor, shaped=False
    ):
        if shaped is False:
            video_mask = video_mask.view(-1, video_mask.shape[-1])

        if self.model.sim_type == "seqTransf" and self.model.temporal_type == "TDB":
            visual_output = visual_output.contiguous()
            visual_output_original = visual_output

            (
                visual_output,
                frame_position_embeddings,
                type_embedding,
                temporal_video_mask,
            ) = self.model.temporal_difference_block(visual_output, video_mask)

            visual_output = visual_output + frame_position_embeddings + type_embedding
            extended_video_mask = (1.0 - temporal_video_mask.unsqueeze(1)) * -1000000.0
            extended_video_mask = extended_video_mask.expand(
                -1, temporal_video_mask.size(1), -1
            )
            visual_output = visual_output.permute(1, 0, 2)
            visual_output = self.model.transformerClip(
                visual_output, extended_video_mask
            )
            visual_output = visual_output.permute(1, 0, 2)

            frame_position_id = torch.arange(
                start=0,
                end=visual_output.size()[1],
                step=2,
                dtype=torch.long,
                device=visual_output.device,
            )
            visual_output = visual_output[:, frame_position_id, :]
            visual_output = visual_output + visual_output_original
            visual_output = visual_output / visual_output.norm(dim=-1, keepdim=True)

            video_mask_un = video_mask.to(dtype=torch.float).unsqueeze(-1)
            visual_output = visual_output * video_mask_un
            video_mask_un_sum = torch.sum(video_mask_un, dim=1, dtype=torch.float)
            video_mask_un_sum[video_mask_un_sum == 0.0] = 1.0
            visual_output = torch.sum(visual_output, dim=1) / video_mask_un_sum
            visual_output = visual_output / visual_output.norm(dim=-1, keepdim=True)
            return visual_output
        else:
            raise NotImplementedError("Only TDB + seqTransf is implemented.")

    def extract_features(
        self,
        shots,
        features_dir: str,
        fps: int = 5,
        size: int = 224,
        max_frames: int = 12,
    ):
        """
        Encode tất cả shot của 1 video và lưu 1 file .npy:
        {features_dir}/{FOLDER}/{VIDEO}.npy -> (num_shots, 512) float32
        Trong đó FOLDER = phần trước dấu '_' của VIDEO (vd: L21_V001 -> L21)
        """
        if not shots:
            print("[extract] no shots.")
            return

        video_name = shots[0][0]  # (vid, sid, path, sf, st, ef, et)
        folder_name = video_name.split("_")[0] if "_" in video_name else video_name

        feats_list = []
        ok, fail = 0, 0

        # (muốn đồng bộ config thì bật 2 dòng dưới)
        # fps = self.args.feature_framerate
        # max_frames = self.args.max_frames

        for i, (vid, sid, path, sf, st, ef, et) in enumerate(shots):
            video, mask = extract_video_tensor(
                path, st, et, fps=fps, size=size, max_frames=max_frames
            )
            if video is None:
                fail += 1
                continue

            with torch.no_grad():
                visual_output = self.model.get_visual_output(
                    video.to(self.device), mask.to(self.device)
                )
                feature = (
                    self.get_video_features(visual_output, mask.to(self.device))
                    .cpu()
                    .numpy()
                )  # (1,512)

            feats_list.append(feature.squeeze().astype("float32", copy=False))
            ok += 1

            if (i + 1) % 10 == 0 or i == len(shots) - 1:
                print(
                    f"[extract] {video_name}: {i+1}/{len(shots)}  ok={ok}  fail={fail}"
                )

        if ok == 0:
            print(f"[extract] no valid features for {video_name}.")
            return

        feats = np.vstack(feats_list)  # (N, 512)
        out_path = os.path.join(features_dir, video_name + ".npy")
        np.save(out_path, feats)

        print(f"[extract] saved -> {out_path}   shape={feats.shape}")
        print(f"[extract] done: {video_name}  ok={ok}  fail={fail}")

    def build_faiss_index(self, features_dir: str, shots_dir: str, output_dir: str):
        """
        Build lại FAISS index từ tất cả .npy trong cây thư mục features_dir
        và lưu:
        - {output_dir}/faiss_clip2video.bin
        - {output_dir}/id2shot.json  (dict: "global_id" -> {video_id, shot_index, boundary})
        Boundary lấy từ CSV: Start Frame / End Frame (nếu có).
        """
        os.makedirs(output_dir, exist_ok=True)
        index_path = os.path.join(output_dir, "faiss_clip2video.bin")
        meta_path = os.path.join(output_dir, "id2shot.json")

        # Thu thập tất cả .npy (recursive)
        npy_paths = []
        for root, _, files in os.walk(features_dir):
            for f in files:
                if f.endswith(".npy"):
                    npy_paths.append(os.path.join(root, f))
        npy_paths.sort()
        print(f"[faiss] found {len(npy_paths)} npy files (recursive)")

        if not npy_paths:
            print("[faiss] no features found.")
            return

        all_blocks = []
        id2shot = {}
        gid = 0

        for npy_path in npy_paths:
            video_id = os.path.splitext(os.path.basename(npy_path))[
                0
            ]  # .../L21/L21_V001.npy -> L21_V001
            feats = np.load(npy_path).astype("float32", copy=False)  # (N, 512)

            # đọc boundary từ CSV tương ứng
            folder_name = video_id.split("_")[0]  # -> L21
            csv_path = os.path.join(shots_dir, f"Videos_{folder_name}/{video_id}.csv")
            starts, ends = None, None
            if os.path.exists(csv_path):
                starts, ends = [], []
                with open(csv_path, "r", newline="") as f:
                    reader = csv.DictReader(f)
                    for r in reader:
                        starts.append(int(r["Start Frame"]))
                        ends.append(int(r["End Frame"]))
                n = feats.shape[0]
                if len(starts) != n:
                    m = min(len(starts), n)
                    print(
                        f"[warn] {video_id}: CSV shots={len(starts)}, feats={n} -> truncate to {m}"
                    )
                    starts, ends = starts[:m], ends[:m]
                    feats = feats[:m]

            # metadata
            N = feats.shape[0]
            for i in range(N):
                entry = {"video_id": video_id, "shot_index": i}
                if starts is not None and ends is not None:
                    entry["boundary"] = [int(starts[i]), int(ends[i])]
                id2shot[str(gid)] = entry
                gid += 1

            all_blocks.append(feats)

        X = np.vstack(all_blocks)  # (M, 512)
        faiss.normalize_L2(X)
        index = faiss.IndexFlatIP(X.shape[1])
        index.add(X)

        faiss.write_index(index, index_path)
        with open(meta_path, "w") as f:
            json.dump(id2shot, f, indent=2)

        print(f"[faiss] saved index -> {index_path}")
        print(f"[faiss] saved meta  -> {meta_path}")
        print(f"[faiss] total vecs  = {index.ntotal}")

    def process_video_batch(
        self,
        video_names: List[str],
        videos_dir: str,
        shots_dir: str,
        features_dir: str,
        output_dir: Optional[str] = None,
    ):
        """
        1) Encode từng video -> lưu {features_dir}/{FOLDER}/{VIDEO}.npy
        2) Build lại toàn bộ FAISS + id2shot.json (không append)
        """
        if output_dir is None:
            output_dir = os.path.dirname(features_dir)

        # 1) encode npy per-video theo thư mục con
        for name in video_names:
            folder_name = name.split("_")[0]
            video_path = os.path.join(
                videos_dir, f"Videos_{folder_name}/video/{name}.mp4"
            )
            csv_path = os.path.join(shots_dir, f"Videos_{folder_name}/{name}.csv")

            if not os.path.exists(csv_path):
                print(f"[batch] missing CSV -> {csv_path}")
                continue
            if not os.path.exists(video_path):
                print(f"[batch] missing video -> {video_path}")
                continue

            shots = load_shots_from_csv(csv_path, video_path)
            print(f"[batch] {name}: {len(shots)} shots")
            self.extract_features(
                shots, features_dir
            )  # sẽ tự tạo {features_dir}/{folder}/{name}.npy

        # # 2) build lại FAISS index + metadata (rebuild all)
        # self.build_faiss_index(
        #     features_dir=features_dir, shots_dir=shots_dir, output_dir=output_dir
        # )
