import csv
import io
import json
import os
import subprocess
import sys
from typing import List, Optional, Tuple

import faiss
import numpy as np
import torch
from config_clip2video import CLIP2VideoConfig
from PIL import Image
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


class CLIP2VideoWrapper:
    def __init__(
        self, checkpoint_dir: str, clip_weights_path: str, device: str = "cuda"
    ):
        self.args = CLIP2VideoConfig(
            checkpoint=checkpoint_dir, clip_path=clip_weights_path
        )
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

        self.tokenizer = ClipTokenizer()

        # Image preprocessing
        self.image_processor = T.Compose([
            T.Resize((224, 224)),
            T.ToTensor(),
            T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])

        self.SPECIAL_TOKEN = {
            "CLS_TOKEN": "<|startoftext|>",
            "SEP_TOKEN": "<|endoftext|>",
            "MASK_TOKEN": "[MASK]",
            "UNK_TOKEN": "[UNK]",
            "PAD_TOKEN": "[PAD]",
        }

        self.max_words = 32

    def encode_text(self, text):
        words = self.tokenizer.tokenize(text)

        # add cls token
        words = [self.SPECIAL_TOKEN["CLS_TOKEN"]] + words
        total_length_with_CLS = self.max_words - 1
        if len(words) > total_length_with_CLS:
            words = words[:total_length_with_CLS]

        # add end token
        words = words + [self.SPECIAL_TOKEN["SEP_TOKEN"]]

        # convert token to id according to the vocab
        input_ids = self.tokenizer.convert_to_ids(words)

        # add zeros for feature of the same length
        input_mask = [1] * len(input_ids)
        segment_ids = [0] * len(input_ids)
        while len(input_ids) < self.max_words:
            input_ids.append(0)
            input_mask.append(0)
            segment_ids.append(0)

        # ensure the length of feature to be equal with max words
        assert len(input_ids) == self.max_words
        assert len(input_mask) == self.max_words
        assert len(segment_ids) == self.max_words
        pairs_text = torch.LongTensor(input_ids)
        pairs_mask = torch.LongTensor(input_mask)
        pairs_segment = torch.LongTensor(segment_ids)

        return pairs_text, pairs_mask, pairs_segment

    def get_text_features(self, sequence_output, attention_mask, shaped=False):
        """get the similarity for global and local representation during inference
        Args:
            sequence_output: embedding
            visual_output: embedding
            attention_mask: caption mask
            video_mask: video mask
            shaped: whether to shape the dimension
        Returns:
            text_out:output embedding [1,512]
            video_out: output embedding [1,512]
        """
        if shaped is False:
            attention_mask = attention_mask.view(-1, attention_mask.shape[-1])

        sequence_output = sequence_output.contiguous()

        # normalize sequence embedding
        sequence_output = sequence_output.squeeze(1)
        sequence_output = sequence_output / sequence_output.norm(dim=-1, keepdim=True)

        return sequence_output

    def get_text_embedding(self, text):
        input_ids, input_mask, segment_ids = self.encode_text(text)

        input_ids, segment_ids, input_mask = (
            input_ids.unsqueeze(0),
            segment_ids.unsqueeze(0),
            input_mask.unsqueeze(0),
        )
        input_ids, segment_ids, input_mask = (
            input_ids.to(self.device),
            segment_ids.to(self.device),
            input_mask.to(self.device),
        )

        with torch.no_grad():
            sequence_output = self.model.get_sequence_output(
                input_ids, segment_ids, input_mask
            )

            text_feature = self.get_text_features(sequence_output, input_mask)
            text_feature = text_feature.squeeze(0).cpu().numpy()

        return text_feature

    def encode_image(self, image_source):
        """Encode image using CLIP2Video model"""
        # Load and preprocess image
        if isinstance(image_source, str):
            image = Image.open(image_source).convert("RGB")
        elif hasattr(image_source, "read"):
            image = Image.open(image_source).convert("RGB")
        elif isinstance(image_source, (bytes, bytearray)):
            image = Image.open(io.BytesIO(image_source)).convert("RGB")
        else:
            image = image_source.convert("RGB")
        
        # Preprocess image
        image = self.image_processor(image).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            # Get visual features
            visual_output = self.model.get_visual_output(image)
            # Use the same processing as video features but for single image
            video_mask = torch.ones(1, 1, device=self.device)  # Single frame
            visual_feature = self.get_video_features(visual_output, video_mask)
            visual_feature = visual_feature.squeeze(0).cpu().numpy()
        
        return visual_feature

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
