#!/usr/bin/env python3
"""
Rebuild incomplete FAISS indexes to match the complete id2img.json
"""

import json
import os
import sys
import numpy as np
import faiss
import structlog
from pathlib import Path
from tqdm import tqdm
import gc

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

class IncompleteIndexRebuilder:
    """Rebuild incomplete FAISS indexes to match complete id2img.json"""
    
    def __init__(self, data_root: str, dict_dir: str, checkpoint_dir: str):
        self.data_root = data_root
        self.dict_dir = dict_dir
        self.checkpoint_dir = checkpoint_dir
        
    def load_id2img_mapping(self) -> dict:
        """Load complete id2img mapping"""
        id2img_path = os.path.join(self.dict_dir, "id2img.json")
        if not os.path.exists(id2img_path):
            raise FileNotFoundError(f"id2img.json not found at {id2img_path}")
        
        with open(id2img_path, "r") as f:
            id2img = json.load(f)
        
        logger.info(f"Loaded id2img mapping with {len(id2img)} entries")
        return id2img
    
    def check_index_status(self) -> dict:
        """Check status of all FAISS indexes"""
        indexes = {
            'longclip': 'faiss_longclip.bin',
            'clip': 'faiss_clip_vitb32.bin', 
            'beit3': 'faiss_beit3.bin',
            'clip2video': 'faiss_clip2video.bin'
        }
        
        status = {}
        for model, filename in indexes.items():
            index_path = os.path.join(self.dict_dir, filename)
            if os.path.exists(index_path):
                try:
                    index = faiss.read_index(index_path)
                    status[model] = {
                        'path': index_path,
                        'vectors': index.ntotal,
                        'exists': True
                    }
                except Exception as e:
                    status[model] = {
                        'path': index_path,
                        'vectors': 0,
                        'exists': True,
                        'error': str(e)
                    }
            else:
                status[model] = {
                    'path': index_path,
                    'vectors': 0,
                    'exists': False
                }
        
        return status
    
    def extract_features_for_model(self, id2img: dict, model_type: str, batch_size: int = 1000) -> np.ndarray:
        """Extract features for a specific model"""
        logger.info(f"Extracting {model_type} features for {len(id2img)} images...")
        
        # Initialize model
        if model_type == "longclip":
            sys.path.append(os.path.join(ROOT_DIR, "backend", "features", "features-longclip"))
            from longclip_wrapper import LongCLIPModel
            
            checkpoint_path = os.path.join(self.checkpoint_dir, "longclip-B.pt")
            model = LongCLIPModel(checkpoint_path, device="cpu")
            feature_dim = 512
            
        elif model_type == "clip":
            import clip
            import torch
            
            checkpoint_path = os.path.join(self.checkpoint_dir, "ViT-B-32.pt")
            model, preprocess = clip.load(checkpoint_path, device="cpu")
            feature_dim = 512
            
        else:
            raise ValueError(f"Unsupported model type: {model_type}")
        
        # Extract features in batches
        all_features = []
        processed = 0
        failed = 0
        
        # Convert id2img to list of (index, path) tuples
        image_items = list(id2img.items())
        
        for i in range(0, len(image_items), batch_size):
            batch_items = image_items[i:i + batch_size]
            batch_paths = [item[1] for item in batch_items]
            
            logger.info(f"Processing batch {i//batch_size + 1}/{(len(image_items) + batch_size - 1)//batch_size}")
            
            batch_features = []
            for image_path in batch_paths:
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
                    
                    batch_features.append(feat.astype(np.float32))
                    processed += 1
                    
                except Exception as e:
                    logger.error(f"Failed to extract features from {full_path}: {e}")
                    failed += 1
                    continue
            
            if batch_features:
                all_features.append(np.array(batch_features))
            
            # Force garbage collection
            gc.collect()
        
        logger.info(f"Feature extraction completed: {processed} successful, {failed} failed")
        
        if not all_features:
            raise ValueError("No features extracted")
        
        # Combine all features
        combined_features = np.vstack(all_features)
        logger.info(f"Combined features shape: {combined_features.shape}")
        
        return combined_features
    
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
    
    def rebuild_incomplete_indexes(self, models: list = None, batch_size: int = 1000):
        """Rebuild incomplete FAISS indexes"""
        if models is None:
            models = ["longclip", "clip"]
        
        # Load complete id2img mapping
        id2img = self.load_id2img_mapping()
        
        # Check current status
        status = self.check_index_status()
        
        for model in models:
            if model not in status:
                logger.warning(f"Unknown model: {model}")
                continue
            
            model_status = status[model]
            expected_vectors = len(id2img)
            current_vectors = model_status['vectors']
            
            if current_vectors == expected_vectors:
                logger.info(f"{model} index is already complete ({current_vectors} vectors)")
                continue
            
            logger.info(f"Rebuilding {model} index: {current_vectors} -> {expected_vectors} vectors")
            
            try:
                # Extract features
                features = self.extract_features_for_model(id2img, model, batch_size)
                
                # Build index
                new_index = self.build_faiss_index(features, model)
                
                # Save index
                index_path = model_status['path']
                faiss.write_index(new_index, index_path)
                logger.info(f"Saved {model} index to {index_path}")
                
                # Verify
                verify_index = faiss.read_index(index_path)
                logger.info(f"Verification: {model} index has {verify_index.ntotal} vectors")
                
                if verify_index.ntotal == expected_vectors:
                    logger.info(f"✅ {model} index rebuilt successfully!")
                else:
                    logger.error(f"❌ {model} index rebuild failed!")
                    
            except Exception as e:
                logger.error(f"Failed to rebuild {model} index: {e}")
                continue

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Rebuild incomplete FAISS indexes")
    parser.add_argument("--data-root", default="data", help="Root directory containing data")
    parser.add_argument("--dict-dir", default="dict", help="Directory containing dictionaries")
    parser.add_argument("--checkpoint-dir", default="checkpoints", help="Checkpoint directory")
    parser.add_argument("--models", nargs="*", default=["longclip", "clip"], help="Models to rebuild")
    parser.add_argument("--batch-size", type=int, default=1000, help="Batch size for processing")
    
    args = parser.parse_args()
    
    # Use absolute paths
    data_root = os.path.abspath(args.data_root)
    dict_dir = os.path.abspath(args.dict_dir)
    checkpoint_dir = os.path.abspath(args.checkpoint_dir)
    
    rebuilder = IncompleteIndexRebuilder(data_root, dict_dir, checkpoint_dir)
    rebuilder.rebuild_incomplete_indexes(args.models, args.batch_size)

if __name__ == "__main__":
    main()
