"""
Configuration settings for the backend
"""

import os

# Import the env path manager
import sys
from typing import List, Optional

from pydantic_settings import BaseSettings

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from env_path_manager import get_path_manager


class Settings(BaseSettings):
    """Application settings"""

    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False

    # CORS settings
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8080",
    ]

    # Model paths - using absolute paths
    SUPPORT_MODELS_DIR: str = ""
    CLIP_MODEL_NAME: str = "ViT-B/32"
    LONGCLIP_CHECKPOINT: str = ""
    CLIP_CHECKPOINT: str = ""
    CLIP2VIDEO_CHECKPOINT: str = ""
    BEIT3_CHECKPOINT: str = ""
    BEIT3_SPM_PATH: str = ""

    # FAISS index paths - using absolute paths
    FAISS_CLIP_PATH: str = ""
    FAISS_LONGCLIP_PATH: str = ""
    FAISS_CLIP2VIDEO_PATH: str = ""
    FAISS_BEIT3_PATH: str = ""
    ID2IMG_JSON_PATH: str = ""
    MAP_KEYFRAMES_PATH: str = ""

    # Data paths - using absolute paths
    DATA_ROOT: str = ""
    FEATURES_DIR: str = ""
    RAW_DATA_DIR: str = ""
    VIDEO_DATA_DIR: str = ""
    KEYFRAME_DATA_DIR: str = ""

    # Indexing paths
    INDEXES_DIR: str = ""
    HDF5_FEATURES_DIR: str = ""
    FAISS_INDEXES_DIR: str = ""
    LUCENE_INDEXES_DIR: str = ""
    SAMPLE_DATA_DIR: str = ""

    # Cache settings
    REDIS_URL: str = "redis://localhost:6379"
    CACHE_TTL: int = 3600  # 1 hour

    # Model loading
    LAZY_LOAD_MODELS: bool = True
    MODEL_DEVICE: str = "auto"  # auto, cpu, cuda

    # Search settings
    DEFAULT_SEARCH_LIMIT: int = 20
    MAX_SEARCH_LIMIT: int = 100

    # OCR settings
    OCR_MODEL_PATH: str = ""

    # ASR settings
    ASR_MODEL_PATH: str = ""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Get the path manager instance
        path_manager = get_path_manager()

        # Use the env path manager for data paths
        self.DATA_ROOT = path_manager.get_data_root()

        # This file is in backend/core/, so we need to go up 2 levels to get to project root
        project_root = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..")
        )

        # Updated paths for new repository structure
        self.SUPPORT_MODELS_DIR = os.path.join(project_root, "support_models")

        # Checkpoints are now in root checkpoints folder
        self.LONGCLIP_CHECKPOINT = path_manager.get_checkpoints_data_path(
            "longclip-B.pt"
        )
        self.CLIP_CHECKPOINT = path_manager.get_checkpoints_data_path("ViT-B-32.pt")
        self.CLIP2VIDEO_CHECKPOINT = path_manager.get_checkpoints_data_path("")
        self.BEIT3_CHECKPOINT = path_manager.get_checkpoints_data_path(
            "beit3_large_patch16_384_coco_retrieval.pth"
        )
        self.BEIT3_SPM_PATH = path_manager.get_checkpoints_data_path("beit3.spm")

        # FAISS indexes are now in dict folder
        self.FAISS_CLIP_PATH = path_manager.get_dict_data_path(
            "faiss_clip_vitb32.bin"
        )
        self.FAISS_LONGCLIP_PATH = path_manager.get_dict_data_path(
            "faiss_longclip.bin"
        )
        self.FAISS_CLIP2VIDEO_PATH = path_manager.get_dict_data_path(
            "faiss_clip2video.bin"
        )
        self.FAISS_BEIT3_PATH = path_manager.get_dict_data_path(
            "faiss_beit3.bin"
        )

        # Mapping files are now in root dict folder
        self.ID2IMG_JSON_PATH = path_manager.get_dict_data_path("id2img.json")
        self.MAP_KEYFRAMES_PATH = path_manager.get_dict_data_path("map_keyframes.json")

        # Data paths using env path manager for flexible data source
        self.VIDEO_DATA_DIR = path_manager.get_video_data_path("Videos_L21/video")
        self.KEYFRAME_DATA_DIR = path_manager.get_keyframe_data_path(
            "Keyframes_L21/keyframes"
        )

        # Use the resolved data root for other data paths
        self.FEATURES_DIR = os.path.join(project_root, "features")
        self.RAW_DATA_DIR = self.DATA_ROOT  # Use resolved path
        self.INDEXES_DIR = os.path.join(
            project_root, "features"
        )  # Features now contain indexes
        self.HDF5_FEATURES_DIR = os.path.join(project_root, "features")
        self.FAISS_INDEXES_DIR = os.path.join(project_root, "features")
        self.LUCENE_INDEXES_DIR = os.path.join(
            path_manager.get_data_root(), "lucene"
        )  # If needed
        self.SAMPLE_DATA_DIR = os.path.join(project_root, "examples/sample_data")
        self.OCR_MODEL_PATH = os.path.join(project_root, "support_models/OCR")
        self.ASR_MODEL_PATH = os.path.join(project_root, "support_models/ASR")

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()

# Set OpenMP environment variable to fix library conflicts on macOS
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

# Override with environment variables if present
if os.getenv("HOST"):
    settings.HOST = os.getenv("HOST")
if os.getenv("PORT"):
    settings.PORT = int(os.getenv("PORT"))
if os.getenv("DEBUG"):
    settings.DEBUG = os.getenv("DEBUG").lower() == "true"
