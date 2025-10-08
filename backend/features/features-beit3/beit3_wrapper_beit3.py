"""
nhớ sửa trong beit3/utils
from torch._six import inf -> from math import inf
"""

import os, sys
from typing import Optional
import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image
from torchvision import transforms
from transformers import XLMRobertaTokenizer
from timm import create_model
from timm.data.constants import IMAGENET_INCEPTION_MEAN, IMAGENET_INCEPTION_STD
import sentencepiece as spm

BEIT3_MODEL_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "support_models/unilm/beit3"
)
if BEIT3_MODEL_PATH not in sys.path:
    sys.path.append(BEIT3_MODEL_PATH)

from modeling_finetune import BEiT3ForRetrieval

from config_beit3 import BEiT3Config


class BEiT3Wrapper:
    def __init__(self, checkpoint_path: str, spm_path: str, device: str = "cpu"):
        self.device = device

        # ===== LOAD MODEL =====
        # beit3_config = BEiT3Config()
        # self.beit3_model = BEiT3ForRetrieval(beit3_config)
        # checkpoint = torch.load(checkpoint_path, map_location="cpu")
        # self.beit3_model.load_state_dict(checkpoint["model"])
        # self.beit3_model = self.beit3_model.to(self.device).eval()

        checkpoint = torch.load(checkpoint_path, map_location="cpu")
        self.beit3_model = create_model("beit3_large_patch16_384_retrieval")
        self.beit3_model.load_state_dict(checkpoint["model"])
        self.beit3_model = self.beit3_model.to(self.device).eval()

        # ===== LOAD TOKENIZER =====

        # Load tokenizer using XLMRobertaTokenizer
        self.beit3_tokenizer = XLMRobertaTokenizer(spm_path)

        # Load tokenizer using SentencePiece
        # self.beit3_tokenizer = spm.SentencePieceProcessor()
        # self.beit3_tokenizer.load(spm_path)

        self.image_processor = transforms.Compose(
            [
                transforms.Resize((384, 384), interpolation=3),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=IMAGENET_INCEPTION_MEAN, std=IMAGENET_INCEPTION_STD
                ),
            ]
        )

        print("BEiT-3 model and tokenizer loaded successfully.")

    def encode_image(self, image_path: str) -> np.ndarray:
        try:
            raw_image = Image.open(image_path).convert("RGB")
        except:
            raw_image = raw_image
        inputs = self.process(image=raw_image, text=None)
        with torch.no_grad():
            image_feature, _ = self.beit3_model(
                image=inputs["image"].to(self.device), only_infer=True
            )
        image_feature /= image_feature.norm(dim=-1, keepdim=True)

        return image_feature[0].cpu().numpy().astype(np.float32)

    def encode_text(self, text: str) -> np.ndarray:
        inputs = self.process(image=None, text=text)
        with torch.no_grad():
            _, text_feature = self.beit3_model(
                text_description=inputs["text_description"].to(self.device),
                padding_mask=inputs["padding_mask"].to(self.device),
                only_infer=True,
            )
        text_feature /= text_feature.norm(dim=-1, keepdim=True)

        return text_feature.cpu().numpy().astype(np.float32)

    def process(self, image=None, text=None):
        assert (image is not None) or (text is not None)
        language_tokens = None
        padding_mask = None
        if image is not None:
            image = self.image_processor(image)
            image = image.unsqueeze(0)
        if text is not None:
            language_tokens, padding_mask, _ = self.get_text_segment(text)
        return {
            "image": image,
            "text_description": language_tokens,
            "padding_mask": padding_mask,
        }

    def get_text_segment(self, text, max_len=64):
        tokens = self.beit3_tokenizer.tokenize(text)
        tokens = self.beit3_tokenizer.convert_tokens_to_ids(tokens)

        if len(tokens) > max_len - 2:
            tokens = tokens[: max_len - 2]

        tokens = (
            [self.beit3_tokenizer.bos_token_id]
            + tokens[:]
            + [self.beit3_tokenizer.eos_token_id]
        )
        num_tokens = len(tokens)
        padding_mask = [0] * num_tokens + [1] * (max_len - num_tokens)
        language_tokens = tokens + [self.beit3_tokenizer.pad_token_id] * (
            max_len - num_tokens
        )
        return torch.tensor([language_tokens]), torch.tensor([padding_mask]), num_tokens
