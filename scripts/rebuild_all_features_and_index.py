#!/usr/bin/env python3
"""
Comprehensive script to rebuild all features and FAISS indexes for both K and L batches
"""

import argparse
import json
import os
import sys
import glob
from pathlib import Path
from typing import List, Dict, Tuple
import numpy as np
import faiss
import structlog

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

class ComprehensiveFeatureRebuilder:
    """Rebuild all features and indexes for both K and L batches"""
    
    def __init__(self, data_root: str, output_dir: str, checkpoint_dir: str):
        self.data_root = data_root
        self.output_dir = output_dir
        self.checkpoint_dir = checkpoint_dir
        self.dict_dir = os.path.join(ROOT_DIR, "dict")
        
        # Create output directories
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(self.dict_dir, exist_ok=True)
        
    def find_all_keyframe_batches(self) -> List[str]:
        """Find all keyframe batch directories (both K and L)"""
        keyframe_base = os.path.join(self.data_root, "keyframe_btc")
        if not os.path.exists(keyframe_base):
            logger.error(f"Keyframe base directory not found: {keyframe_base}")
            return []
            
        # Find all Keyframes_* directories
        batch_pattern = os.path.join(keyframe_base, "Keyframes_*")
        batch_dirs = glob.glob(batch_pattern)
        
        # Extract batch names and sort them
        batch_names = []
        for batch_dir in batch_dirs:
            batch_name = os.path.basename(batch_dir)
            if batch_name.startswith("Keyframes_"):
                batch_names.append(batch_name)
        
        batch_names.sort()
        logger.info(f"Found {len(batch_names)} keyframe batches: {batch_names}")
        return batch_names
    
    def find_all_video_dirs(self, batch_name: str) -> List[str]:
        """Find all video directories within a batch"""
        batch_path = os.path.join(self.data_root, "keyframe_btc", batch_name, "keyframes")
        if not os.path.exists(batch_path):
            logger.warning(f"Batch path not found: {batch_path}")
            return []
            
        video_dirs = glob.glob(os.path.join(batch_path, "*"))
        video_dirs = [d for d in video_dirs if os.path.isdir(d)]
        video_dirs.sort()
        
        logger.info(f"Found {len(video_dirs)} video directories in {batch_name}")
        return video_dirs
    
    def create_comprehensive_id2img_mapping(self) -> Dict[int, str]:
        """Create comprehensive ID to image mapping for all batches"""
        logger.info("Creating comprehensive ID to image mapping...")
        
        id2img_mapping = {}
        global_idx = 0
        
        # Process all batches
        batch_names = self.find_all_keyframe_batches()
        
        for batch_name in batch_names:
            logger.info(f"Processing batch: {batch_name}")
            video_dirs = self.find_all_video_dirs(batch_name)
            
            for video_dir in video_dirs:
                video_id = os.path.basename(video_dir)
                logger.info(f"  Processing video: {video_id}")
                
                # Find all images in this video directory
                image_pattern = os.path.join(video_dir, "*.jpg")
                image_files = sorted(glob.glob(image_pattern))
                
                if not image_files:
                    logger.warning(f"No images found in {video_dir}")
                    continue
                
                # Create mapping for each image
                for image_file in image_files:
                    # Create relative path from data root
                    relative_path = os.path.relpath(image_file, self.data_root)
                    id2img_mapping[global_idx] = relative_path
                    global_idx += 1
                
                logger.info(f"    Mapped {len(image_files)} images for {video_id}")
        
        logger.info(f"Created mapping for {len(id2img_mapping)} total images")
        return id2img_mapping
    
    def extract_features_for_all_batches(self, model_type: str = "longclip") -> Tuple[List[np.ndarray], Dict[int, str]]:
        """Extract features for all batches using the specified model"""
        logger.info(f"Extracting features using {model_type} model...")
        
        # Create ID mapping first
        id2img_mapping = self.create_comprehensive_id2img_mapping()
        
        # Initialize feature extractor based on model type
        if model_type == "longclip":
            from backend.features.features_longclip.longclip_wrapper import LongCLIPModel
            checkpoint_path = os.path.join(self.checkpoint_dir, "longclip-B.pt")
            extractor = LongCLIPModel(checkpoint_path, device="cuda" if os.system("nvidia-smi") == 0 else "cpu")
        elif model_type == "clip":
            import clip
            checkpoint_path = os.path.join(self.checkpoint_dir, "ViT-B-32.pt")
            model, preprocess = clip.load(checkpoint_path, device="cuda" if os.system("nvidia-smi") == 0 else "cpu")
            extractor = (model, preprocess)
        elif model_type == "beit3":
            from backend.features.features_beit3.beit3_wrapper import BEiT3Wrapper
            checkpoint_path = os.path.join(self.checkpoint_dir, "beit3_large_patch16_384_coco_retrieval.pth")
            spm_path = os.path.join(self.checkpoint_dir, "beit3.spm")
            extractor = BEiT3Wrapper(checkpoint_path, spm_path, device="cuda" if os.system("nvidia-smi") == 0 else "cpu")
        else:
            raise ValueError(f"Unsupported model type: {model_type}")
        
        # Extract features for all images
        all_features = []
        processed_count = 0
        
        for global_idx, image_path in id2img_mapping.items():
            full_image_path = os.path.join(self.data_root, image_path)
            
            if not os.path.exists(full_image_path):
                logger.warning(f"Image not found: {full_image_path}")
                continue
            
            try:
                if model_type == "longclip":
                    features = extractor.encode_image(full_image_path)
                elif model_type == "clip":
                    from PIL import Image
                    image = Image.open(full_image_path).convert("RGB")
                    image_tensor = preprocess(image).unsqueeze(0).to(extractor[0].device)
                    with torch.no_grad():
                        features = extractor[0].encode_image(image_tensor).cpu().numpy()
                elif model_type == "beit3":
                    features = extractor.encode_image(full_image_path)
                
                all_features.append(features.astype(np.float32))
                processed_count += 1
                
                if processed_count % 1000 == 0:
                    logger.info(f"Processed {processed_count} images...")
                    
            except Exception as e:
                logger.error(f"Failed to extract features from {full_image_path}: {e}")
                continue
        
        logger.info(f"Extracted features for {len(all_features)} images")
        return all_features, id2img_mapping
    
    def build_faiss_index(self, features: List[np.ndarray], model_type: str) -> faiss.Index:
        """Build FAISS index from features"""
        logger.info(f"Building FAISS index for {model_type}...")
        
        if not features:
            raise ValueError("No features to index")
        
        # Convert to numpy array
        features_array = np.array(features, dtype=np.float32)
        logger.info(f"Feature array shape: {features_array.shape}")
        
        # Normalize features
        faiss.normalize_L2(features_array)
        
        # Create index
        index = faiss.IndexFlatIP(features_array.shape[1])
        index.add(features_array)
        
        logger.info(f"FAISS index built with {index.ntotal} vectors")
        return index
    
    def rebuild_all(self, model_types: List[str] = None):
        """Rebuild all features and indexes"""
        if model_types is None:
            model_types = ["longclip", "clip", "beit3"]
        
        logger.info("Starting comprehensive rebuild...")
        
        for model_type in model_types:
            logger.info(f"Processing model: {model_type}")
            
            try:
                # Extract features
                features, id2img_mapping = self.extract_features_for_all_batches(model_type)
                
                if not features:
                    logger.error(f"No features extracted for {model_type}")
                    continue
                
                # Build FAISS index
                index = self.build_faiss_index(features, model_type)
                
                # Save index
                index_path = os.path.join(self.dict_dir, f"faiss_{model_type}.bin")
                faiss.write_index(index, index_path)
                logger.info(f"Saved {model_type} index to {index_path}")
                
                # Save features
                features_path = os.path.join(self.output_dir, f"features_{model_type}.npy")
                np.save(features_path, np.array(features))
                logger.info(f"Saved {model_type} features to {features_path}")
                
            except Exception as e:
                logger.error(f"Failed to process {model_type}: {e}")
                continue
        
        # Save comprehensive ID mapping
        id2img_path = os.path.join(self.dict_dir, "id2img.json")
        with open(id2img_path, "w") as f:
            json.dump(id2img_mapping, f, indent=2)
        logger.info(f"Saved comprehensive ID mapping to {id2img_path}")
        
        logger.info("Comprehensive rebuild completed!")

def main():
    parser = argparse.ArgumentParser(description="Rebuild all features and indexes")
    parser.add_argument("--data-root", default="data", help="Root directory containing data")
    parser.add_argument("--output-dir", default="data/features", help="Output directory for features")
    parser.add_argument("--checkpoint-dir", default="checkpoints", help="Checkpoint directory")
    parser.add_argument("--models", nargs="*", default=["longclip"], help="Models to process")
    
    args = parser.parse_args()
    
    rebuilder = ComprehensiveFeatureRebuilder(
        data_root=args.data_root,
        output_dir=args.output_dir,
        checkpoint_dir=args.checkpoint_dir
    )
    
    rebuilder.rebuild_all(model_types=args.models)

if __name__ == "__main__":
    main()
