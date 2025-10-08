#!/usr/bin/env python3
"""
Fix FAISS index mismatch by rebuilding index to match existing id2img.json
"""

import json
import os
import sys
import glob
import numpy as np
import faiss
import structlog
from pathlib import Path

# Setup logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Add project root to path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

import env_path_manager as pm

class FAISSIndexFixer:
    """Fix FAISS index mismatch by rebuilding to match id2img.json"""
    
    def __init__(self, data_root: str, dict_dir: str, checkpoint_dir: str):
        self.data_root = data_root
        self.dict_dir = dict_dir
        self.checkpoint_dir = checkpoint_dir
        
    def load_id2img_mapping(self) -> dict:
        """Load existing id2img mapping"""
        id2img_path = os.path.join(self.dict_dir, "id2img.json")
        if not os.path.exists(id2img_path):
            raise FileNotFoundError(f"id2img.json not found at {id2img_path}")
        
        with open(id2img_path, "r") as f:
            id2img = json.load(f)
        
        logger.info(f"Loaded id2img mapping with {len(id2img)} entries")
        return id2img
    
    def check_current_faiss_index(self, model_type: str) -> tuple:
        """Check current FAISS index size"""
        index_path = os.path.join(self.dict_dir, f"faiss_{model_type}.bin")
        if not os.path.exists(index_path):
            logger.warning(f"FAISS index not found: {index_path}")
            return None, 0
        
        try:
            index = faiss.read_index(index_path)
            logger.info(f"Current {model_type} FAISS index has {index.ntotal} vectors")
            return index, index.ntotal
        except Exception as e:
            logger.error(f"Failed to read FAISS index: {e}")
            return None, 0
    
    def extract_features_for_mapping(self, id2img: dict, model_type: str) -> np.ndarray:
        """Extract features for all images in the mapping"""
        logger.info(f"Extracting {model_type} features for {len(id2img)} images...")
        
        # Initialize model
        if model_type == "longclip":
            from backend.features.features_longclip.longclip_wrapper import LongCLIPModel
            checkpoint_path = os.path.join(self.checkpoint_dir, "longclip-B.pt")
            model = LongCLIPModel(checkpoint_path, device="cuda" if os.system("nvidia-smi") == 0 else "cpu")
        elif model_type == "clip":
            import clip
            import torch
            checkpoint_path = os.path.join(self.checkpoint_dir, "ViT-B-32.pt")
            model, preprocess = clip.load(checkpoint_path, device="cuda" if os.system("nvidia-smi") == 0 else "cpu")
        elif model_type == "beit3":
            from backend.features.features_beit3.beit3_wrapper import BEiT3Wrapper
            checkpoint_path = os.path.join(self.checkpoint_dir, "beit3_large_patch16_384_coco_retrieval.pth")
            spm_path = os.path.join(self.checkpoint_dir, "beit3.spm")
            model = BEiT3Wrapper(checkpoint_path, spm_path, device="cuda" if os.system("nvidia-smi") == 0 else "cpu")
        else:
            raise ValueError(f"Unsupported model type: {model_type}")
        
        # Extract features
        features = []
        processed = 0
        failed = 0
        
        for idx, image_path in id2img.items():
            full_path = os.path.join(self.data_root, image_path)
            
            if not os.path.exists(full_path):
                logger.warning(f"Image not found: {full_path}")
                failed += 1
                continue
            
            try:
                if model_type == "longclip":
                    feat = model.encode_image(full_path)
                elif model_type == "clip":
                    from PIL import Image
                    image = Image.open(full_path).convert("RGB")
                    image_tensor = preprocess(image).unsqueeze(0).to(model.device)
                    with torch.no_grad():
                        feat = model.encode_image(image_tensor).cpu().numpy()
                elif model_type == "beit3":
                    feat = model.encode_image(full_path)
                
                features.append(feat.astype(np.float32))
                processed += 1
                
                if processed % 1000 == 0:
                    logger.info(f"Processed {processed}/{len(id2img)} images...")
                    
            except Exception as e:
                logger.error(f"Failed to extract features from {full_path}: {e}")
                failed += 1
                continue
        
        logger.info(f"Feature extraction completed: {processed} successful, {failed} failed")
        
        if not features:
            raise ValueError("No features extracted")
        
        return np.array(features, dtype=np.float32)
    
    def build_faiss_index(self, features: np.ndarray, model_type: str) -> faiss.Index:
        """Build FAISS index from features"""
        logger.info(f"Building FAISS index for {model_type}...")
        
        # Normalize features
        faiss.normalize_L2(features)
        
        # Create index
        index = faiss.IndexFlatIP(features.shape[1])
        index.add(features)
        
        logger.info(f"FAISS index built with {index.ntotal} vectors")
        return index
    
    def fix_index(self, model_type: str):
        """Fix FAISS index for a specific model"""
        logger.info(f"Fixing {model_type} FAISS index...")
        
        # Load id2img mapping
        id2img = self.load_id2img_mapping()
        
        # Check current index
        current_index, current_size = self.check_current_faiss_index(model_type)
        
        if current_size == len(id2img):
            logger.info(f"{model_type} index size matches id2img mapping ({current_size}), no fix needed")
            return
        
        logger.info(f"Index mismatch detected: FAISS has {current_size}, id2img has {len(id2img)}")
        
        # Extract features for all images in mapping
        features = self.extract_features_for_mapping(id2img, model_type)
        
        # Build new index
        new_index = self.build_faiss_index(features, model_type)
        
        # Save new index
        index_path = os.path.join(self.dict_dir, f"faiss_{model_type}.bin")
        faiss.write_index(new_index, index_path)
        logger.info(f"Saved fixed {model_type} index to {index_path}")
        
        # Verify the fix
        verify_index = faiss.read_index(index_path)
        logger.info(f"Verification: New index has {verify_index.ntotal} vectors, id2img has {len(id2img)} entries")
        
        if verify_index.ntotal == len(id2img):
            logger.info(f"✅ {model_type} index fixed successfully!")
        else:
            logger.error(f"❌ {model_type} index fix failed!")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Fix FAISS index mismatch")
    parser.add_argument("--data-root", default="data", help="Root directory containing data")
    parser.add_argument("--dict-dir", default="dict", help="Directory containing dictionaries")
    parser.add_argument("--checkpoint-dir", default="checkpoints", help="Checkpoint directory")
    parser.add_argument("--models", nargs="*", default=["longclip", "clip", "beit3"], help="Models to fix")
    
    args = parser.parse_args()
    
    # Use absolute paths
    data_root = os.path.abspath(args.data_root)
    dict_dir = os.path.abspath(args.dict_dir)
    checkpoint_dir = os.path.abspath(args.checkpoint_dir)
    
    fixer = FAISSIndexFixer(data_root, dict_dir, checkpoint_dir)
    
    for model_type in args.models:
        try:
            fixer.fix_index(model_type)
        except Exception as e:
            logger.error(f"Failed to fix {model_type}: {e}")
            continue
    
    logger.info("FAISS index fixing completed!")

if __name__ == "__main__":
    main()
