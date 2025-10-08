#!/usr/bin/env python3
"""
Rebuild FAISS index in batches to avoid memory issues
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

class BatchFAISSIndexRebuilder:
    """Rebuild FAISS index in batches to avoid memory issues"""
    
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
    
    def extract_longclip_features_batch(self, image_paths: list, model, batch_size: int = 100) -> np.ndarray:
        """Extract LongCLIP features for a batch of images"""
        features = []
        
        for i in range(0, len(image_paths), batch_size):
            batch_paths = image_paths[i:i + batch_size]
            batch_features = []
            
            for image_path in batch_paths:
                full_path = os.path.join(self.data_root, image_path)
                
                if not os.path.exists(full_path):
                    logger.warning(f"Image not found: {full_path}")
                    continue
                
                try:
                    feat = model.encode_image(full_path)
                    batch_features.append(feat.astype(np.float32))
                except Exception as e:
                    logger.error(f"Failed to extract features from {full_path}: {e}")
                    continue
            
            if batch_features:
                features.extend(batch_features)
            
            # Force garbage collection
            gc.collect()
        
        return np.array(features, dtype=np.float32) if features else np.array([])
    
    def rebuild_complete_index(self, model_type: str = "longclip", batch_size: int = 1000):
        """Rebuild complete FAISS index in batches"""
        logger.info(f"Rebuilding complete {model_type} FAISS index in batches of {batch_size}...")
        
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
        
        # Initialize model
        if model_type == "longclip":
            sys.path.append(os.path.join(ROOT_DIR, "backend", "features", "features-longclip"))
            from longclip_wrapper import LongCLIPModel
            
            checkpoint_path = os.path.join(self.checkpoint_dir, "longclip-B.pt")
            model = LongCLIPModel(checkpoint_path, device="cpu")  # Use CPU to avoid memory issues
        else:
            raise ValueError(f"Unsupported model type: {model_type}")
        
        # Process in batches
        all_features = []
        total_processed = 0
        total_failed = 0
        
        # Convert id2img to list of (index, path) tuples
        image_items = list(id2img.items())
        
        for i in range(0, len(image_items), batch_size):
            batch_items = image_items[i:i + batch_size]
            batch_paths = [item[1] for item in batch_items]
            
            logger.info(f"Processing batch {i//batch_size + 1}/{(len(image_items) + batch_size - 1)//batch_size}")
            
            # Extract features for this batch
            batch_features = self.extract_longclip_features_batch(batch_paths, model, 100)
            
            if len(batch_features) > 0:
                all_features.append(batch_features)
                total_processed += len(batch_features)
            else:
                total_failed += len(batch_paths)
            
            logger.info(f"Batch completed: {len(batch_features)} features extracted")
            
            # Force garbage collection
            gc.collect()
        
        if not all_features:
            raise ValueError("No features extracted")
        
        # Combine all features
        logger.info("Combining all features...")
        combined_features = np.vstack(all_features)
        logger.info(f"Combined features shape: {combined_features.shape}")
        
        # Build FAISS index
        logger.info("Building FAISS index...")
        faiss.normalize_L2(combined_features)
        
        index = faiss.IndexFlatIP(combined_features.shape[1])
        index.add(combined_features)
        
        # Save new index
        index_path = os.path.join(self.dict_dir, f"faiss_{model_type}.bin")
        faiss.write_index(index, index_path)
        logger.info(f"Saved complete {model_type} index to {index_path}")
        
        # Verify the fix
        verify_index = faiss.read_index(index_path)
        logger.info(f"Verification: New index has {verify_index.ntotal} vectors, id2img has {len(id2img)} entries")
        logger.info(f"Total processed: {total_processed}, Total failed: {total_failed}")
        
        if verify_index.ntotal == len(id2img):
            logger.info(f"✅ {model_type} index rebuilt successfully!")
        else:
            logger.error(f"❌ {model_type} index rebuild failed!")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Rebuild complete FAISS index in batches")
    parser.add_argument("--data-root", default="data", help="Root directory containing data")
    parser.add_argument("--dict-dir", default="dict", help="Directory containing dictionaries")
    parser.add_argument("--checkpoint-dir", default="checkpoints", help="Checkpoint directory")
    parser.add_argument("--model", default="longclip", help="Model to rebuild")
    parser.add_argument("--batch-size", type=int, default=1000, help="Batch size for processing")
    
    args = parser.parse_args()
    
    # Use absolute paths
    data_root = os.path.abspath(args.data_root)
    dict_dir = os.path.abspath(args.dict_dir)
    checkpoint_dir = os.path.abspath(args.checkpoint_dir)
    
    rebuilder = BatchFAISSIndexRebuilder(data_root, dict_dir, checkpoint_dir)
    rebuilder.rebuild_complete_index(args.model, args.batch_size)

if __name__ == "__main__":
    main()
