import base64
import io
import json
import os
import sys
from pathlib import Path
from urllib.parse import urlparse

import clip
import faiss
import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image

# Add the current directory to the path for local imports
current_dir = os.path.dirname(__file__)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Add the project root to the path for env_path_manager
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from translate_vi2en import Translation

from env_path_manager import get_path_manager

# Get the path manager instance
path_manager = get_path_manager()
DATA_ROOT = path_manager.get_data_root()  # Use the env path manager

# Updated path for LongCLIP wrapper - located in backend features folder
LONGCLIP_WRAPPER_PATH = os.path.join(ROOT_DIR, "backend/features/features-longclip")
if LONGCLIP_WRAPPER_PATH not in sys.path:
    sys.path.insert(1, LONGCLIP_WRAPPER_PATH)

from longclip_wrapper import LongCLIPModel

# Add BEIT3 wrapper
BEIT3_WRAPPER_PATH = os.path.join(ROOT_DIR, "backend/features/features-beit3")
if BEIT3_WRAPPER_PATH not in sys.path:
    sys.path.insert(1, BEIT3_WRAPPER_PATH)

from beit3_wrapper import BEiT3Wrapper


class MyFaiss:
    def __init__(
        self,
        checkpoint_dir: str = None,
        dict_dir: str = None,
        # Legacy parameters for backward compatibility
        longclip_ckpt_path: str = None,
        bin_clip_file: str = None,
        bin_longclip_file: str = None,
        id2img_json: str = None,
        clip_ckpt_path: str = None,
    ):
        # Support new interface with checkpoint_dir and dict_dir
        if checkpoint_dir and dict_dir:
            # New interface - construct paths from directories
            longclip_ckpt_path = os.path.join(checkpoint_dir, "longclip-B.pt")
            clip_ckpt_path = os.path.join(checkpoint_dir, "ViT-B-32.pt")
            bin_clip_file = os.path.join(dict_dir, "faiss_clip_vitb32.bin")
            bin_longclip_file = os.path.join(dict_dir, "faiss_longclip.bin")
            bin_beit3_file = os.path.join(dict_dir, "faiss_beit3.bin")
            id2img_json = os.path.join(dict_dir, "id2img.json")
        
        # Load FAISS indexes
        self.index_clip = self.load_bin_file(bin_clip_file)
        self.index_longclip = self.load_bin_file(bin_longclip_file)
        self.index_beit3 = self.load_bin_file(bin_beit3_file)
        # self.index_clip2video =

        self.id2img = self.load_json_file(id2img_json)

        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        ##### Load CLIP ViT-B/32 #####
        print("Loading CLIP model...")
        if clip_ckpt_path and os.path.exists(clip_ckpt_path):
            # Load from custom checkpoint
            self.clip_model, _ = clip.load(clip_ckpt_path, device=self.device)
        else:
            # Load default CLIP model
            self.clip_model, _ = clip.load("ViT-B/32", device=self.device)
        self.clip_model.eval()
        print("CLIP model loaded:", type(self.clip_model))

        ##### Load LongCLIP #####
        self.longclip_model = None
        if longclip_ckpt_path and longclip_ckpt_path != "clip_fallback":
            try:
                self.longclip_model = LongCLIPModel(
                    longclip_ckpt_path, device=self.device
                )
                print("LongCLIP model loaded:", type(self.longclip_model))
            except Exception as e:
                print(f"Failed to load LongCLIP model: {e}")
                print("Falling back to CLIP-only mode")
                self.longclip_model = None
        else:
            print("LongCLIP checkpoint not available, using CLIP-only mode")

        ##### Load BEIT3 #####
        self.beit3_model = None
        beit3_ckpt_path = os.path.join(checkpoint_dir, "beit3_large_patch16_384_coco_retrieval.pth") if checkpoint_dir else None
        beit3_spm_path = os.path.join(checkpoint_dir, "beit3.spm") if checkpoint_dir else None
        
        if beit3_ckpt_path and beit3_spm_path and os.path.exists(beit3_ckpt_path) and os.path.exists(beit3_spm_path):
            try:
                self.beit3_model = BEiT3Wrapper(
                    beit3_ckpt_path, beit3_spm_path, device=self.device
                )
                print("BEIT3 model loaded:", type(self.beit3_model))
            except Exception as e:
                print(f"Failed to load BEIT3 model: {e}")
                print("BEIT3 will not be available")
                self.beit3_model = None
        else:
            print("BEIT3 checkpoints not available, BEIT3 will not be available")

        # self.clip2video_model

        self.translator = Translation()

    def clip_preprocess(self, image):
        """CLIP image preprocessing"""
        # Use the standard CLIP preprocessing
        _, preprocess = clip.load("ViT-B/32", device=self.device)
        return preprocess(image)

    def load_image_source(self, image_source):
        """Load image from various sources (URL, local path, bytes, file-like)"""
        if isinstance(image_source, str):
            if image_source.startswith(("http://", "https://")):
                # URL
                import requests

                response = requests.get(image_source)
                response.raise_for_status()
                image = Image.open(io.BytesIO(response.content)).convert("RGB")
            else:
                # Local file path
                image = Image.open(image_source).convert("RGB")
        elif isinstance(image_source, bytes):
            # Bytes
            image = Image.open(io.BytesIO(image_source)).convert("RGB")
        elif hasattr(image_source, "read"):
            # File-like object
            image = Image.open(image_source).convert("RGB")
        elif isinstance(image_source, Image.Image):
            # Already a PIL Image
            image = image_source.convert("RGB")
        else:
            raise ValueError(f"Unsupported image source type: {type(image_source)}")

        return image

    # ==================================================
    # HELPER FUNCTIONS
    # ==================================================
    def load_json_file(self, json_path: str):
        with open(json_path, "r") as f:
            js = json.load(f)
        return {int(k): v for k, v in js.items()}

    def load_bin_file(self, bin_file: str):
        return faiss.read_index(bin_file)

    def load_video_features(self, model_type: str, video_id: str):
        if model_type == "clip":
            feature_path = os.path.join(
                DATA_ROOT, f"features/features_clip/features/{video_id}.npy"
            )
        if model_type == "longclip":
            feature_path = os.path.join(
                DATA_ROOT,
                f"features/features-longclip/features/{video_id}.npy",
            )

        arr = np.load(feature_path).astype(np.float32)
        features = torch.from_numpy(arr).to(self.device)
        features = F.normalize(features, dim=-1)
        return features

    def load_image_source(self, source):
        """source: local path | http(s) URL | bytes | file-like | data URL -> PIL.Image(RGB)"""
        if hasattr(source, "read"):  # file-like
            img = Image.open(source)
            return img.convert("RGB")

        if isinstance(source, (bytes, bytearray)):  # raw bytes
            img = Image.open(io.BytesIO(source))
            return img.convert("RGB")

        if isinstance(source, str):
            # data URL
            if source.startswith("data:image/"):
                header, b64 = source.split(",", 1)
                raw = base64.b64decode(b64)
                img = Image.open(io.BytesIO(raw))
                return img.convert("RGB")

            # http(s) URL
            parsed = urlparse(source)
            if parsed.scheme in ("http", "https"):
                import requests

                r = requests.get(source, timeout=10)
                r.raise_for_status()
                img = Image.open(io.BytesIO(r.content))
                return img.convert("RGB")

            # local path
            if os.path.exists(source):
                img = Image.open(source)
                return img.convert("RGB")

        raise ValueError("Unsupported image source format.")

    # ==================================================
    # SEARCHING FUNCTIONS
    # ==================================================

    def image_search(self, k: int, model_type: str, image_id: int, image_source=None):
        """
        Args:
            k: topk to return
            model_type: 'clip' | 'longclip'
            image_id: FAISS index of image (for search similar images)
            image_source:

        Return:
            scores (list): score calculated by FAISS
            idxs (list): the index of the candidate in FAISS Index
            image_paths (list): Paths of images mapped from Faiss Index to Image
                                (E.g., "keyframe_btc/Keyframes_L21/keyframes/L21_V001/001.jpg")
        """
        # ================================
        # 1. CHOOSING INDEX
        # ================================
        if model_type == "clip":
            index = self.index_clip
        elif model_type == "longclip":
            index = self.index_longclip
        else:
            raise NotImplementedError(f"{model_type} not supported")

        # ================================
        # 2. CHECK INPUT & SEARCH
        # ================================
        if (image_id is None) and (image_source is None):
            raise ValueError("Provide either image_id or image_source.")
        if (image_id is not None) and (image_source is not None):
            raise ValueError("Provide only one of image_id or image_source, not both.")

        if image_id is not None:
            # reconstruct từ index
            try:
                q = (
                    index.reconstruct(int(image_id))
                    .reshape(1, -1)
                    .astype("float32", copy=False)
                )
            except Exception:
                if (
                    hasattr(self, "features_store")
                    and model_type in self.features_store
                ):
                    q = np.asarray(
                        self.features_store[model_type][int(image_id)], dtype="float32"
                    ).reshape(1, -1)
                else:
                    raise RuntimeError("Index không hỗ trợ reconstruct().")
        else:
            # encode từ ảnh (URL/local/bytes/file-like)
            pil_img = self.load_image_source(image_source)
            if model_type == "clip":
                with torch.no_grad():
                    img_tensor = (
                        self.clip_preprocess(pil_img).unsqueeze(0).to(self.device)
                    )
                    q = self.clip_model.encode_image(img_tensor).float().cpu().numpy()
            else:
                # LongCLIP: truyền kiểu phù hợp cho wrapper (str | file-like | bytes)
                src = image_source
                if (
                    isinstance(src, str)
                    or hasattr(src, "read")
                    or isinstance(src, (bytes, bytearray))
                ):
                    pass  # dùng src như hiện tại
                else:
                    # trường hợp mình chỉ có PIL.Image -> convert sang BytesIO (file-like)
                    import io

                    buf = io.BytesIO()
                    pil_img.save(buf, format="PNG")
                    buf.seek(0)
                    src = buf

                q = self.longclip_model.encode_image(src).astype("float32", copy=False)
                if q.ndim == 1:
                    q = q[None, :]

        # normalize & search
        q = q / (np.linalg.norm(q, axis=-1, keepdims=True) + 1e-12)
        scores, idxs = index.search(q, k=k)
        scores = scores.flatten()
        idxs = idxs.flatten()

        image_paths = [self.id2img.get(int(i)) for i in idxs if int(i) in self.id2img]
        return scores, idxs, image_paths

    def _truncate_text_for_clip(self, text: str, max_tokens: int = 77) -> str:
        """
        Intelligently truncate text to fit within CLIP's token limit.
        Tries to keep the most important parts of the query.
        """
        # Simple approach: split by sentences and keep the most relevant parts
        # For Vietnamese queries, we'll keep the beginning and end parts

        # If text is short enough, return as is
        if len(text) <= max_tokens * 4:  # Rough estimate: 4 chars per token
            return text

        # Split into sentences (roughly by periods and common Vietnamese sentence endings)
        sentences = []
        current = ""
        for char in text:
            current += char
            if char in [".", "!", "?", ":", ";"]:
                sentences.append(current.strip())
                current = ""
        if current.strip():
            sentences.append(current.strip())

        # If we have sentences, prioritize the first and last ones
        if len(sentences) > 1:
            # Keep first sentence and last sentence if they fit
            first = sentences[0]
            last = sentences[-1]

            # If first + last fits, use that
            if len(first + " " + last) <= max_tokens * 4:
                return first + " " + last

            # Otherwise, just use first sentence
            if len(first) <= max_tokens * 4:
                return first

        # Fallback: truncate to max length, trying to keep meaningful parts
        # For Vietnamese, try to keep the beginning and end
        if len(text) > max_tokens * 4:
            # Keep first 60% and last 40% of allowed length
            first_part = int(max_tokens * 2.4)  # 60% of max_tokens * 4
            last_part = int(max_tokens * 1.6)  # 40% of max_tokens * 4

            if len(text) > first_part + last_part:
                truncated = text[:first_part] + "..." + text[-last_part:]
                return truncated

        return text

    def text_search(self, text, k, model_type):
        """
        Args:
            ...

        Returns:
            scores (list): score calculated by FAISS
            idx_image (list): the index of the candidate in FAISS Index
            image_paths (list): Paths of images mapped from Faiss Index to Image (E.g., "keyframe_btc/Keyframes_L21/keyframes/L21_V001/001.jpg")
        """

        text = self.translator(text)
        print(f"Text after translate: {text}")

        # Truncate text if it's too long for CLIP
        original_text = text
        text = self._truncate_text_for_clip(text)
        if text != original_text:
            print(
                f"Text truncated from {len(original_text)} to {len(text)} chars: {text}"
            )

        ##### TEXT FEATURES EXTRACTING #####
        if model_type == "clip":
            try:
                tokens = clip.tokenize([text]).to(self.device)
                text_features = self.clip_model.encode_text(tokens)
                text_features /= text_features.norm(dim=-1, keepdim=True)
                text_features = text_features.cpu().detach().numpy().astype(np.float32)
            except Exception as e:
                print(f"CLIP tokenization failed: {e}")
                # Try with even shorter text
                text = text[:50] if len(text) > 50 else text
                print(f"Retrying with shorter text: {text}")
                tokens = clip.tokenize([text]).to(self.device)
                text_features = self.clip_model.encode_text(tokens)
                text_features /= text_features.norm(dim=-1, keepdim=True)
                text_features = text_features.cpu().detach().numpy().astype(np.float32)
        elif model_type == "longclip":
            # Check if LongCLIP model is available
            if self.longclip_model is not None:
                # class LongCLIP trong features-longclip/model.py đã có sẵn encode_text
                text_features = self.longclip_model.encode_text(text)
                print(
                    f"LongCLIP text encoding successful, features shape: {text_features.shape}"
                )
            else:
                # Fallback to CLIP if LongCLIP is not available
                print(
                    "LongCLIP model not available due to dependency conflicts, falling back to CLIP"
                )
                print(
                    "Note: This will use CLIP encoding with LongCLIP index, which may not work optimally"
                )
                try:
                    tokens = clip.tokenize([text]).to(self.device)
                    text_features = self.clip_model.encode_text(tokens)
                    text_features /= text_features.norm(dim=-1, keepdim=True)
                    text_features = (
                        text_features.cpu().detach().numpy().astype(np.float32)
                    )
                    # Change model_type to clip for the search phase
                    model_type = "clip"
                    print(
                        f"Falling back to CLIP encoding, features shape: {text_features.shape}"
                    )
                except Exception as e:
                    print(f"CLIP fallback also failed: {e}")
                    # Try with even shorter text
                    text = text[:50] if len(text) > 50 else text
                    print(f"Retrying with shorter text: {text}")
                    tokens = clip.tokenize([text]).to(self.device)
                    text_features = self.clip_model.encode_text(tokens)
                    text_features /= text_features.norm(dim=-1, keepdim=True)
                    text_features = (
                        text_features.cpu().detach().numpy().astype(np.float32)
                    )
                    model_type = "clip"
                    print(
                        f"CLIP encoding successful after retry, features shape: {text_features.shape}"
                    )
        elif model_type == "beit3":
            # Check if BEIT3 model is available
            if self.beit3_model is not None:
                text_features = self.beit3_model.encode_text(text)
                print(
                    f"BEIT3 text encoding successful, features shape: {text_features.shape}"
                )
            else:
                raise RuntimeError("BEIT3 model not available")
        elif model_type == "clip2video":
            raise NotImplementedError("clip2video not supported yet in text_search()")

        ##### SEARCHING #####
        print(f"Searching with model_type: {model_type}")
        if model_type == "clip":
            index_chosen = self.index_clip
            print(f"Using CLIP index with {index_chosen.ntotal} vectors")
        elif model_type == "longclip":
            index_chosen = self.index_longclip
            print(f"Using LongCLIP index with {index_chosen.ntotal} vectors")
        elif model_type == "beit3":
            index_chosen = self.index_beit3
            print(f"Using BEIT3 index with {index_chosen.ntotal} vectors")
        elif model_type == "clip2video":
            raise NotImplementedError("clip2video not supported yet in text_search()")

        print(f"Searching with text_features shape: {text_features.shape}")
        search_result = index_chosen.search(text_features, k=k)
        print(
            f"Search result type: {type(search_result)}, length: {len(search_result) if hasattr(search_result, '__len__') else 'N/A'}"
        )

        # Handle different return formats from FAISS search
        if isinstance(search_result, tuple) and len(search_result) == 2:
            scores, idxs = search_result
            print(
                f"Search returned tuple: scores shape {scores.shape}, idxs shape {idxs.shape}"
            )
        elif isinstance(search_result, np.ndarray):
            # Single array returned - this shouldn't happen with standard FAISS
            print(f"Warning: FAISS returned single array instead of tuple")
            scores = search_result
            idxs = np.arange(k)  # Create dummy indices
        else:
            print(f"Warning: Unexpected search result format: {type(search_result)}")
            # Try to handle it gracefully
            if hasattr(search_result, "flatten"):
                scores = search_result.flatten()
                idxs = np.arange(k)
            else:
                raise ValueError(
                    f"Unsupported search result format: {type(search_result)}"
                )

        # Ensure we get the expected format
        if isinstance(scores, tuple):
            # If search returns a tuple, unpack it properly
            scores, idxs = scores
        elif not isinstance(scores, np.ndarray):
            # If search returns something unexpected, handle it
            print(f"Warning: Unexpected search result format: {type(scores)}")
            if hasattr(scores, "flatten"):
                scores = scores.flatten()
            else:
                scores = np.array(scores).flatten()
            if hasattr(idxs, "flatten"):
                idxs = idxs.flatten()
            else:
                idxs = np.array(idxs).flatten()
        else:
            # Normal case: ensure arrays are flattened
            scores = scores.flatten()
            idxs = idxs.flatten()

        #### GET INFOS KEYFRAMES_ID #####
        # infos_query = list(map(self.id2img.get, list(idx_image)))
        image_paths = [self.id2img.get(int(i)) for i in idxs if int(i) in self.id2img]
        return scores, idxs, image_paths

    def temporal_search(
        self,
        text,
        k,
        model_type,
        topk_per_sentence=200,
        max_candidate_videos=30,
        w_min=1,
        w_max=None,
    ):
        """
        Temporal search (frame/shot sequence)
        Query segment -> search TopK using FAISS Indexing Search -> get video/ shot candidates
        For each candidate: load features, create a similarity matrix (M x N), using DP to find path
        Return TopK

        Args:
            text: input query
            k: final number of outputs
            model_type: 'clip' | 'longclip' | 'clip2video' | ...
            topk_per_sentence: number of results we get at FAISS Indexing Search phase
            max_candidate_videos: the maximum video candidates
            w_min: the minimum number of frame/ shot between 2 consecutive sentences
            w_max: the maximum number of frame/ shot between 2 consecutive sentences

        Returns:
            dict {
                "sentences": [...],
                "per_sentence": [
                    {"sentence": s_i, "shortlist": [{"video_id", "image_path", "faiss_index", "score"}, ...]}
                ],
                "candidate_videos": [...],
                "results": [
                    {"video_id": str, "frames": [f1, f2, ..., fM], "score": float}, ...
                ]
            }
        """

        temp = 20  # number of units to return per sentence (change later)
        # ================================================================================
        # 0. TEXT SEGMENTATION
        # ================================================================================
        text = self.translator(text)
        sentences = [s.strip() for s in text.split(".") if s.strip()]
        assert len(sentences) >= 1 and sentences[0].strip() != ""
        M = len(sentences)

        # IF QUERY HAS 1 SENTENCE, USE NORMAL TEXT_SEARCH FUNCTION
        if M == 1:
            scores, idxs, paths = self.text_search(sentences[0], k, model_type)
            out = []
            seen = set()
            for score, path in zip(scores, paths):
                unit_id = os.path.basename(os.path.dirname(path))  # E.g. L21_V001
                if unit_id not in seen:
                    out.append(
                        {"unit_id": unit_id, "frames": [None], "score": float(score)}
                    )
                    seen.add(unit_id)
                    if len(out) >= k:
                        break
            return {"sentences": sentences, "candidates": list(seen), "results": out}

        # ========================================
        # PHASE 1: SEARCHING FOR EACH SENTENCE
        # ========================================
        # 1.1 Encode queries
        text_feats_torch = []
        text_feats_numpy = []
        for s in sentences:
            if model_type == "clip":
                tokens = clip.tokenize([s]).to(self.device)
                feat = self.clip_model.encode_text(tokens)
                feat /= feat.norm(dim=-1, keepdim=True)
                feat = feat.squeeze(0)
                text_feats_torch.append(feat)
                text_feats_numpy.append(feat.cpu().numpy().astype(np.float32))
            elif model_type == "longclip":
                feat_np = self.longclip_model.encode_text(s)  # Already numpy [D]
                feat_torch = (
                    torch.from_numpy(feat_np).to(self.device).squeeze(0)
                )  # Convert to tensor
                feat_torch /= feat_torch.norm(dim=-1, keepdim=True)
                text_feats_torch.append(feat_torch)
                text_feats_numpy.append(feat_np.astype(np.float32))
            elif model_type == "clip2video":
                pass
            else:
                raise NotImplementedError(
                    "clip2video not supported yet in temporal_search()"
                )

        # 1.2 Choose Faiss Index
        if model_type == "clip":
            index_chosen = self.index_clip
        elif model_type == "longclip":
            index_chosen = self.index_longclip
            print(index_chosen.ntotal)
        elif model_type == "clip2video":
            raise NotImplementedError("clip2video not supported yet in text_search()")

        # 1.3 Per-sentence search & collect candidate videos
        per_sentence = []
        candidate_videos = []
        seen = set()

        for sentence, text_feat_numpy in zip(sentences, text_feats_numpy):
            scores, idxs = index_chosen.search(text_feat_numpy, k=topk_per_sentence)
            scores = scores.flatten()
            idxs = idxs.flatten()

            ranked_units = []
            for score, idx in zip(scores, idxs):
                img_path = self.id2img.get(int(idx))
                video_id = (
                    os.path.basename(os.path.dirname(img_path)) if img_path else None
                )
                ranked_units.append(
                    {
                        "video_id": video_id,
                        "image_path": img_path,
                        "faiss_id": int(idx),
                        "score": float(score),
                    }
                )
                if (
                    video_id
                    and video_id not in seen
                    and len(candidate_videos) < max_candidate_videos
                ):
                    candidate_videos.append(video_id)
                    seen.add(video_id)

            per_sentence.append(
                {"sentence": sentence, "ranked_units": ranked_units[:temp]}
            )

        if not candidate_videos:
            return {
                "sentences": sentences,
                "per_sentence": per_sentence,
                "candidate_videos": [],
                "results": [],
            }

        print(f"🎯 Found {len(candidate_videos)} candidate videos: {candidate_videos}")

        # 1.4 Temporal DP per video
        results = []

        for video_id in candidate_videos:
            try:
                video_features = self.load_video_features(model_type, video_id)
            except Exception:
                continue
            if video_features.numel() == 0:
                continue

            N = video_features.shape[0]
            if N < M:
                continue

            # Compute similarity matrix
            sim_list = []
            for text_feat_torch in text_feats_torch:
                sims = (text_feat_torch @ video_features.T) * 0.5 + 0.5
                sim_list.append(sims)

            # Normalize per-sentence results to [0, 1]
            norm_sim_list = []
            for sims in sim_list:
                smin = sims.min()
                smax = sims.max()
                if (smax - smin) < 1e-6:
                    norm = torch.zeros_like(sims)
                else:
                    norm = (sims - smin) / (smax - smin)
                norm_sim_list.append(norm)

            # Build anchor bonus from per-sentence hits for THIS video
            anchor_top = 5
            anchor_boost = 0.10
            anchor_window = 2
            bonus_list = [torch.zeros(N, device=self.device) for _ in range(M)]

            for i in range(M):
                hits = [
                    u
                    for u in per_sentence[i]["ranked_units"]
                    if u["video_id"] == video_id
                ]
                for h in hits[:anchor_top]:
                    img_path = h["image_path"]
                    if not img_path:
                        continue
                    try:
                        fname = os.path.basename(img_path)  # "222.jpg"
                        j = int(os.path.splitext(fname)[0]) - 1
                        if 0 <= j < N:
                            L = max(0, j - anchor_window)
                            R = min(N, j + anchor_window + 1)
                            for t in range(L, R):
                                decay = 1.0 - (abs(t - j) / (anchor_window + 1.0))
                                bonus_list[i][t] = torch.maximum(
                                    bonus_list[i][t],
                                    torch.tensor(
                                        anchor_boost * decay, device=self.device
                                    ),
                                )
                    except Exception:
                        continue
            work_sim_list = [norm_sim_list[i] + bonus_list[i] for i in range(M)]

            score_next = work_sim_list[M - 1].clone()
            backptr_tables = []

            for i in range(M - 1, 0, -1):
                prev_idx = torch.arange(0, N, device=self.device)
                next_idx = torch.arange(0, N, device=self.device)

                # Calculate gap between consecutive frames
                gap = next_idx.view(1, -1) - prev_idx.view(-1, 1)  # (N, N)

                valid = gap >= w_min
                if w_max is not None:
                    valid = valid & (gap <= w_max)

                next_scores = score_next
                score_mat = next_scores.view(1, -1).expand(N, -1)

                neg_inf = torch.tensor(-1e9, device=self.device)
                masked = torch.where(valid, score_mat, neg_inf)

                best_vals, best_cols = masked.max(dim=1)

                score_prev = best_vals + work_sim_list[i - 1]

                pointer = torch.full((N,), -1, dtype=torch.long, device=self.device)
                valid_rows = best_vals > -1e8
                pointer[valid_rows] = best_cols[valid_rows]
                backptr_tables.append(pointer)

                score_next = score_prev

            # Backtracking
            f0 = torch.argmax(score_next).item()
            total_score = score_next[f0].item()
            frames = [f0]

            ptrs_forward = backptr_tables[::-1]
            cur = f0
            feasible = True
            for t in range(M - 1):
                nxt = ptrs_forward[t][cur].item()
                if nxt < 0:
                    feasible = False
                    break
                frames.append(nxt)
                cur = nxt

            if feasible and len(frames) == M:
                frame_indices = [int(x) for x in frames]  # 0-based indices
                frame_files = [f"{idx+1:03d}.jpg" for idx in frame_indices]
                frame_paths = [
                    os.path.join(
                        "keyframe_btc",
                        f"Keyframes_{video_id.split('_')[0]}",
                        "keyframes",
                        video_id,
                        fname,
                    )
                    for fname in frame_files
                ]
                results.append(
                    {
                        "video_id": video_id,
                        "frames": [int(x) for x in frames],
                        "images": frame_files,
                        "paths": frame_paths,
                        "score": float(total_score * (100.0 / M)),
                    }
                )
            else:
                print(
                    f"❌ No valid path found for {video_id}. Feasible: {feasible}, Frames: {frames}"
                )

        # 1.5 Return top-k results
        results.sort(key=lambda r: r["score"], reverse=True)
        if k and k > 0:
            results = results[:k]

        return {
            "sentences": sentences,
            "per_sentence": per_sentence,
            "candidate_videos": candidate_videos,
            "results": results,
        }

    def context_search():
        # Search by object, ocr, asr
        pass

    def reranking():
        pass


##### TESTING #####
def main():
    bin_clip_file = os.path.join(
        DATA_ROOT, "features/features-clip/faiss_clip_vitb32.bin"
    )
    bin_longclip_file = os.path.join(
        DATA_ROOT, "features/features-longclip/faiss_longclip.bin"
    )
    id2img_json = os.path.join(DATA_ROOT, "dict/id2img.json")

    print("Initializing MyFaiss...")
    faiss_engine = MyFaiss(
        longclip_ckpt_path=os.path.join(DATA_ROOT, "checkpoints/longclip-B.pt"),
        bin_clip_file=bin_clip_file,
        bin_longclip_file=bin_longclip_file,
        id2img_json=id2img_json,
    )
    print("MyFaiss initialized!")

    # FOR TESTING IMAGE SEARCH
    # scores, ids, paths = faiss_engine.image_search(
    #     k=20,
    #     model_type="longclip",
    #     image_id=None,
    #     image_source=r"F:\Shared drives\keyframe_btc\Keyframes_L21\keyframes\L21_V019\252.jpg",
    # )
    # print(paths)

    # FOR TESTING TEXT SEARCH
    # query = "A close-up of a stylized bust sculpture of a woman with flowing hair, made of smooth green material with a futuristic metallic chrome-like garment. The sculpture is placed outdoors among trees, giving a natural backdrop that contrasts with the surreal, modern design of the artwork. The expression on the woman's face is calm and serene."

    # scores, ids, paths = faiss_engine.text_search(
    #     text=query,
    #     k=20,
    #     model_type='longclip'
    # )

    # print(f"Top {topk} results for query: {query}")
    # for i, (score, path) in enumerate(zip(scores, paths)):
    #     print(f"[{i}] Score: {score:.2f} | Path: {path}")

    # ====== for temporal search ====== #
    query = "A young couple is interviewed at a lively public event, standing close together among a crowd near a modern stadium. \
        The scene transitions to a colorful parade where a performer in an extravagant purple costume and white mask dances energetically. \
        Another performer wearing a blue-striped outfit and decorated cap smiles and salutes under a partly cloudy sky. \
        The sequence ends with a flower-covered float carrying a woman dressed in an ornate pink gown and headpiece, surrounded by bright blossoms and mannequins, celebrating in a festive atmosphere."

    # query = "A man and a woman are inside a modern boat's cabin, navigating and monitoring the sea using a digital nautical chart. \
    #     The next scene transitions to a scuba diver underwater, inspecting coral or marine rocks with a flashlight and camera, conducting marine research or exploration."

    result_dict = faiss_engine.temporal_search(
        text=query,
        k=100,
        model_type="longclip",
        topk_per_sentence=20,
        max_candidate_videos=20,
        w_min=1,
        w_max=2,
    )

    # ====================
    # PRINT RESULT
    # ====================
    sentences = result_dict["sentences"]
    per_sentence_results = result_dict["per_sentence"]
    candidate_videos = result_dict["candidate_videos"]
    results = result_dict["results"]

    print("\n🔍 Query Sentences:")
    for i, s in enumerate(sentences):
        print(f"  {i+1}. {s}")

    print("\n📊 Top Results per Sentence:")
    for i, sentence_result in enumerate(per_sentence_results):
        print(f"\nSentence {i+1}: {sentences[i]}")
        for hit in sentence_result["ranked_units"]:
            print(
                f"  - video_id: {hit['video_id']} | frame (img): {hit['image_path']} | score: {hit['score']:.4f}"
            )

    print("\n🎯 Candidate Videos for Temporal Matching:")
    for vid in candidate_videos:
        print(f"  - {vid}")

    print("\n🏁 Final Temporal Matching Results:")
    for r in results:
        print(f"  ✅ video_id: {r['video_id']}")
        # gộp thông tin index -> file -> path
        frame_infos = []
        for idx0, fname, path in zip(
            r["frames"], r.get("images", []), r.get("paths", [])
        ):
            frame_infos.append(f"{idx0}: {fname} -> {path}")
        print("     " + "\n     ".join(frame_infos))
        print(f"     score: {r['score']:.4f}")


if __name__ == "__main__":
    main()