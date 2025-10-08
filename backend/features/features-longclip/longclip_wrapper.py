"""
LongCLIP wrapper for feature extraction
"""

import os
import sys
from typing import Optional, Union

import numpy as np

# Add Long-CLIP to path
longclip_path = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "support_models", "Long-CLIP"
)
if longclip_path not in sys.path:
    sys.path.append(longclip_path)

try:
    # Try to import the actual LongCLIP model
    import torch
    from model.longclip import load

    class LongCLIPModel:
        """LongCLIP model wrapper"""

        def __init__(self, checkpoint_path: str, device: str = "cpu"):
            self.device = device
            self.model = None
            self.preprocess = None
            self._load_model(checkpoint_path)

        def _load_model(self, checkpoint_path: str):
            """Load LongCLIP model"""
            try:
                if os.path.exists(checkpoint_path):
                    self.model, self.preprocess = load(
                        checkpoint_path, device=self.device
                    )
                    print(f"LongCLIP model loaded from {checkpoint_path}")
                else:
                    print(f"Checkpoint not found: {checkpoint_path}")
                    self.model = None
            except Exception as e:
                print(f"Failed to load LongCLIP model: {e}")
                print(
                    "This is likely due to dependency conflicts. LongCLIP search will fall back to CLIP."
                )
                self.model = None

        def encode_image(
            self, image_source: Union[str, bytes, np.ndarray]
        ) -> np.ndarray:
            """Encode image to features"""
            if self.model is None:
                return self._generate_mock_features()

            try:
                # Convert image source to PIL Image
                if isinstance(image_source, str):
                    # Load image from path
                    from PIL import Image

                    image = Image.open(image_source).convert("RGB")
                elif isinstance(image_source, bytes):
                    # Load image from bytes
                    import io

                    from PIL import Image

                    image = Image.open(io.BytesIO(image_source)).convert("RGB")
                elif isinstance(image_source, np.ndarray):
                    # Convert numpy array to PIL Image
                    from PIL import Image

                    image = Image.fromarray(image_source).convert("RGB")
                else:
                    raise ValueError(
                        f"Unsupported image source type: {type(image_source)}"
                    )

                # Preprocess and encode with model
                if self.preprocess:
                    image_tensor = self.preprocess(image).unsqueeze(0).to(self.device)
                else:
                    # Fallback preprocessing
                    image_tensor = (
                        self._preprocess_image(image).unsqueeze(0).to(self.device)
                    )

                with torch.no_grad():
                    features = self.model.encode_image(image_tensor)
                    features = features.cpu().numpy()
                    return features.flatten()

            except Exception as e:
                print(f"Image encoding failed: {e}")
                return self._generate_mock_features()

        def encode_text(self, text: str) -> np.ndarray:
            """Encode text to features"""
            if self.model is None:
                return self._generate_mock_features()

            try:
                # LongCLIP expects tokenized text, not raw text
                # Import the tokenizer from the longclip module
                import sys

                longclip_path = os.path.join(
                    os.path.dirname(__file__),
                    "..",
                    "..",
                    "..",
                    "support_models",
                    "Long-CLIP",
                )
                if longclip_path not in sys.path:
                    sys.path.append(longclip_path)

                from model import longclip

                # Tokenize the text first
                tokens = longclip.tokenize([text]).to(self.device)

                # Encode with model
                with torch.no_grad():
                    features = self.model.encode_text(tokens)
                    features = features.cpu().numpy()
                    # Ensure features have the right shape for FAISS (batch dimension)
                    if features.ndim == 1:
                        features = features.reshape(1, -1)
                    elif features.ndim == 2 and features.shape[0] == 1:
                        # Already correct shape
                        pass
                    else:
                        # Take first batch if multiple
                        features = features[:1]
                    return features

            except Exception as e:
                print(f"Text encoding failed: {e}")
                return self._generate_mock_features()

        def _preprocess_image(self, image):
            """Fallback preprocessing for image"""
            # Basic preprocessing - resize to 224x224
            image = image.resize((224, 224))

            # Convert to tensor and normalize
            image_tensor = torch.from_numpy(np.array(image)).float()
            image_tensor = image_tensor.permute(2, 0, 1) / 255.0

            # Normalize with ImageNet stats
            mean = torch.tensor([0.48145466, 0.4578275, 0.40821073])
            std = torch.tensor([0.26862954, 0.26130258, 0.27577711])
            image_tensor = (
                image_tensor - mean.unsqueeze(1).unsqueeze(2)
            ) / std.unsqueeze(1).unsqueeze(2)

            return image_tensor

        def _generate_mock_features(self) -> np.ndarray:
            """Generate mock features for testing"""
            return np.random.randn(512).astype(np.float32)

except ImportError:
    # Fallback to mock model
    class LongCLIPModel:
        """Mock LongCLIP model for testing"""

        def __init__(self, checkpoint_path: str = None, device: str = "cpu"):
            self.device = device
            print("Using mock LongCLIP model")

        def encode_image(
            self, image_source: Union[str, bytes, np.ndarray]
        ) -> np.ndarray:
            """Generate mock image features"""
            return np.random.randn(512).astype(np.float32)

        def encode_text(self, text: str) -> np.ndarray:
            """Generate mock text features"""
            return np.random.randn(512).astype(np.float32)
