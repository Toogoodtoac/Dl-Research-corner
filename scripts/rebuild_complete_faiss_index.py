#!/usr/bin/env python3
"""
Rebuild complete FAISS index to match id2img.json mapping
"""

import json
import os
import sys
import numpy as np
import faiss
import structlog
from pathlib import Path
from tqdm import tqdm

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

class CompleteFAISSIndexRebuilder:
    """Rebuild complete FAISS index to match id2img.json"""
    
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
    
    def extract_longclip_features(self, id2img: dict) -> np.ndarray:
        """Extract LongCLIP features for all images in the mapping"""
        logger.info("Extracting LongCLIP features...")
        
        # Import LongCLIP
        sys.path.append(os.path.join(ROOT_DIR, "backend", "features", "features-longclip"))
        from longclip_wrapper import LongCLIPModel
        
        # Initialize model
        checkpoint_path = os.path.join(self.checkpoint_dir, "longclip-B.pt")
        model = LongCLIPModel(checkpoint_path, device="cuda" if os.system("nvidia-smi") == 0 else "cpu")
        
        # Extract features
        features = []
        processed = 0
        failed = 0
        
        for idx, image_path in tqdm(id2img.items(), desc="Extracting features"):
            full_path = os.path.join(self.data_root, image_path)
            
            if not os.path.exists(full_path):
                logger.warning(f"Image not found: {full_path}")
                failed += 1
                continue
            
            try:
                feat = model.encode_image(full_path)
                features.append(feat.astype(np.float32))
                processed += 1
                
            except Exception as e:
                logger.error(f"Failed to extract features from {full_path}: {e}")
                failed += 1
                continue
        
        logger.info(f"Feature extraction completed: {processed} successful, {failed} failed")
        
        if not features:
            raise ValueError("No features extracted")
        
        return np.array(features, dtype=np.float32)
    
    def build_faiss_index(self, features: np.ndarray) -> faiss.Index:
        """Build FAISS index from features"""
        logger.info(f"Building FAISS index for {features.shape[0]} features...")
        
        # Normalize features
        faiss.normalize_L2(features)
        
        # Create index
        index = faiss.IndexFlatIP(features.shape[1])
        index.add(features)
        
        logger.info(f"FAISS index built with {index.ntotal} vectors")
        return index
    
    def rebuild_complete_index(self, model_type: str = "longclip"):
        """Rebuild complete FAISS index"""
        logger.info(f"Rebuilding complete {model_type} FAISS index...")
        
        # Load id2img mapping
        id2img = self.load_id2img_mapping()
        
        # Check current index size
        current_index_path = os.path.join(self.dict_dir, f"faiss_{model_type}.bin")
        if os.path.exists(current_index_path):
            current_index = faiss.read_index(current_index_path)
            logger.info(f"Current index has {current_index.ntotal} vectors")
            
            if current_index.ntotal == len(id2img):
                logger.info("Index size already matches id2img mapping, no rebuild needed")
                return
        
        # Extract features for all images
        if model_type == "longclip":
            features = self.extract_longclip_features(id2img)
        else:
            raise ValueError(f"Unsupported model type: {model_type}")
        
        # Build new index
        new_index = self.build_faiss_index(features)
        
        # Save new index
        index_path = os.path.join(self.dict_dir, f"faiss_{model_type}.bin")
        faiss.write_index(new_index, index_path)
        logger.info(f"Saved complete {model_type} index to {index_path}")
        
        # Verify the fix
        verify_index = faiss.read_index(index_path)
        logger.info(f"Verification: New index has {verify_index.ntotal} vectors, id2img has {len(id2img)} entries")
        
        if verify_index.ntotal == len(id2img):
            logger.info(f"✅ {model_type} index rebuilt successfully!")
        else:
            logger.error(f"❌ {model_type} index rebuild failed!")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Rebuild complete FAISS index")
    parser.add_argument("--data-root", default="data", help="Root directory containing data")
    parser.add_argument("--dict-dir", default="dict", help="Directory containing dictionaries")
    parser.add_argument("--checkpoint-dir", default="checkpoints", help="Checkpoint directory")
    parser.add_argument("--model", default="longclip", help="Model to rebuild")
    
    args = parser.parse_args()
    
    # Use absolute paths
    data_root = os.path.abspath(args.data_root)
    dict_dir = os.path.abspath(args.dict_dir)
    checkpoint_dir = os.path.abspath(args.checkpoint_dir)
    
    rebuilder = CompleteFAISSIndexRebuilder(data_root, dict_dir, checkpoint_dir)
    rebuilder.rebuild_complete_index(args.model)

if __name__ == "__main__":
    main()
