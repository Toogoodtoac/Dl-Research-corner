#!/usr/bin/env python3
"""
Fix id2img mapping to match the current FAISS index size
"""

import json
import os
import sys
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

def fix_id2img_mapping(dict_dir: str, model_type: str = "longclip"):
    """Fix id2img mapping to match FAISS index size"""
    
    # Load current FAISS index
    index_path = os.path.join(dict_dir, f"faiss_{model_type}.bin")
    if not os.path.exists(index_path):
        logger.error(f"FAISS index not found: {index_path}")
        return
    
    index = faiss.read_index(index_path)
    logger.info(f"FAISS index has {index.ntotal} vectors")
    
    # Load current id2img mapping
    id2img_path = os.path.join(dict_dir, "id2img.json")
    if not os.path.exists(id2img_path):
        logger.error(f"id2img.json not found: {id2img_path}")
        return
    
    with open(id2img_path, "r") as f:
        id2img = json.load(f)
    
    logger.info(f"id2img mapping has {len(id2img)} entries")
    
    if index.ntotal == len(id2img):
        logger.info("Index and mapping sizes match, no fix needed")
        return
    
    # Create new mapping that only includes the first N entries
    new_id2img = {}
    for i in range(index.ntotal):
        if str(i) in id2img:
            new_id2img[str(i)] = id2img[str(i)]
        else:
            logger.warning(f"Missing mapping for index {i}")
    
    # Save new mapping
    new_id2img_path = os.path.join(dict_dir, "id2img_fixed.json")
    with open(new_id2img_path, "w") as f:
        json.dump(new_id2img, f, indent=2)
    
    logger.info(f"Created fixed mapping with {len(new_id2img)} entries")
    logger.info(f"Saved to {new_id2img_path}")
    
    # Backup original and replace
    backup_path = os.path.join(dict_dir, "id2img_backup.json")
    os.rename(id2img_path, backup_path)
    os.rename(new_id2img_path, id2img_path)
    
    logger.info(f"Backed up original to {backup_path}")
    logger.info(f"Replaced original with fixed mapping")
    
    # Verify the fix
    verify_index = faiss.read_index(index_path)
    with open(id2img_path, "r") as f:
        verify_id2img = json.load(f)
    
    logger.info(f"Verification: Index has {verify_index.ntotal} vectors, mapping has {len(verify_id2img)} entries")
    
    if verify_index.ntotal == len(verify_id2img):
        logger.info("✅ Fix successful!")
    else:
        logger.error("❌ Fix failed!")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Fix id2img mapping to match FAISS index")
    parser.add_argument("--dict-dir", default="dict", help="Directory containing dictionaries")
    parser.add_argument("--model", default="longclip", help="Model to fix")
    
    args = parser.parse_args()
    
    dict_dir = os.path.abspath(args.dict_dir)
    fix_id2img_mapping(dict_dir, args.model)

if __name__ == "__main__":
    main()
