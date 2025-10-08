# extract.py
import os
import sys

sys.path.append("/home")

from clip2video_extractor import CLIP2VideoFeatureExtraction

import env_path_manager as pm

ROOT_DIR = pm.root_dir
ROOT_DATA = pm.root_data

# ======= EDIT PATH =======
CHECKPOINT_DIR = os.path.join(ROOT_DIR, "checkpoints")
# CLIP_WEIGHTS = os.path.join(ROOT_DIR, "checkpoints/ViT-B-32.pt")

CLIP_WEIGHTS = r"/home/checkpoints/ViT-B-32.pt"
VIDEOS_DIR = os.path.join(ROOT_DATA, "videos")
SHOTS_DIR = os.path.join(ROOT_DIR, "dict/Shots_PSD")

OUTPUT_DIR = os.path.join(ROOT_DIR, "features/features-clip2video")
FEATURES_DIR = os.path.join(OUTPUT_DIR, "features")


# ALL_VIDEOS = []
# for folder in sorted(os.listdir(VIDEOS_DIR)):
#     folder_path = os.path.join(VIDEOS_DIR, folder)
#     for video in sorted(os.listdir(folder_path)):
#         ALL_VIDEOS.append(video)

# VIDEO_BATCH = ALL_VIDEOS[:5]

ALL_VIDEOS = [
    "L25_V054",
    "L25_V055",
    "L25_V056",
    "L25_V057",
    "L25_V058",
    "L25_V059",
    "L25_V060",
    "L25_V061",
    "L25_V062",
    "L25_V063",
    "L25_V064",
    "L25_V065",
    "L25_V066",
    "L25_V067",
    "L25_V068",
    "L25_V069",
    "L25_V070",
    "L25_V071",
    "L25_V072",
]


if __name__ == "__main__":
    os.makedirs(FEATURES_DIR, exist_ok=True)
    print(CHECKPOINT_DIR)
    extractor = CLIP2VideoFeatureExtraction(
        checkpoint_dir=CHECKPOINT_DIR,
        clip_weights_path=CLIP_WEIGHTS,
        device="cuda",  # 'cpu' nếu không có GPU
    )

    # encode NPY per-video và build lại FAISS + id2shot.json
    extractor.process_video_batch(
        video_names=ALL_VIDEOS,
        videos_dir=VIDEOS_DIR,
        shots_dir=SHOTS_DIR,
        features_dir=FEATURES_DIR,
        output_dir=OUTPUT_DIR,
    )

    print("\n=== DONE ===")
