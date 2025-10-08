# Video Indexing Pipeline Documentation

## Overview

The MM-Data Intelligent Agent includes a comprehensive video indexing pipeline that extracts features from videos, stores them in HDF5 format, and builds searchable indexes using FAISS (for similarity search) and Lucene/Whoosh (for text search).

## Architecture

```
Video Files → Feature Extraction → HDF5 Storage → Index Building → Search APIs
     ↓              ↓                ↓            ↓           ↓
  Shot Detection  CLIP2Video     HDF5 Files   FAISS Index  kNN Search
  Object Detection LongCLIP      Metadata     Lucene Index Text Search
  Color Analysis  Mock Features  BBox Data    Whoosh Index Hybrid Search
```

## Components

### 1. Feature Extractors (`backend/feature_extractors/`)

- **TemporalExtractor**: Shot detection and keyframe extraction
- **ObjectDetector**: Object detection using OpenCV DNN or mock detection
- **ColorDetector**: Color analysis for bounding boxes

### 2. Indexing Modules (`backend/indexer/`)

- **HDF5Storage**: Efficient storage of features and metadata
- **FAISSIndex**: Vector similarity search indexes
- **LuceneIndex**: Text search with Whoosh fallback

### 3. Pipeline Scripts (`scripts/`)

- **ingest.py**: Main video ingestion pipeline
- **build_faiss.py**: FAISS index building
- **build_lucene.py**: Text index building
- **sample_data_generator.py**: Generate test data

## Quick Start

### 1. Generate Sample Data

```bash
# Generate 5 sample videos with 20 frames each
make sample-data

# Or customize:
python scripts/sample_data_generator.py \
  --num-videos 10 \
  --frames-per-video 30 \
  --feature-dim 512 \
  --output examples/sample_data
```

### 2. Run Complete Pipeline

```bash
# Run the entire indexing pipeline
make index

# This runs:
# 1. make sample-data    - Generate sample videos
# 2. make ingest         - Extract features to HDF5
# 3. make build-faiss    - Build FAISS indexes
# 4. make build-lucene   - Build text indexes
```

### 3. Individual Steps

```bash
# Generate sample data only
make sample-data

# Run ingestion only
make ingest

# Build FAISS indexes only
make build-faiss

# Build Lucene indexes only
make build-lucene
```

## Detailed Usage

### Video Ingestion

```bash
# Process single video
python scripts/ingest.py \
  --input path/to/video.mp4 \
  --output data/hdf5_features \
  --video-only

# Process directory of videos
python scripts/ingest.py \
  --input path/to/videos/ \
  --output data/hdf5_features

# Custom configuration
python scripts/ingest.py \
  --input path/to/videos/ \
  --output data/hdf5_features \
  --config config/ingestion.yml
```

### FAISS Index Building

```bash
# Build individual indexes
python scripts/build_faiss.py \
  --input data/hdf5_features \
  --output data/indexes/faiss

# Build combined index
python scripts/build_faiss.py \
  --input data/hdf5_features \
  --output data/indexes/faiss \
  --combined \
  --index-type ivf \
  --validate

# GPU acceleration (if available)
python scripts/build_faiss.py \
  --input data/hdf5_features \
  --output data/indexes/faiss \
  --use-gpu
```

### Lucene/Whoosh Index Building

```bash
# Build with Lucene (default)
python scripts/build_lucene.py \
  --input data/hdf5_features \
  --output data/indexes/lucene \
  --combined \
  --validate

# Use Whoosh fallback
python scripts/build_lucene.py \
  --input data/hdf5_features \
  --output data/indexes/lucene \
  --use-whoosh \
  --combined \
  --validate
```

## Configuration

### Ingestion Configuration (`config/ingestion.yml`)

```yaml
# Temporal analysis
temporal_threshold: 0.3
min_shot_length: 1.0
shot_detection_method: "histogram"  # or "optical_flow"
frames_per_shot: 3

# Object detection
object_detection_model: "mock"  # or "opencv"
confidence_threshold: 0.5

# Feature extraction
device: "cpu"  # or "cuda"
clip2video_checkpoint: "path/to/checkpoint"
longclip_checkpoint: "path/to/checkpoint"
```

### Index Configuration (`config/indexing.yml`)

```yaml
# FAISS settings
index_type: "flat"  # or "ivf", "ivfpq"
use_gpu: false
index_params:
  nlist: 4096
  m: 8
  bits: 8

# Lucene/Whoosh settings
use_lucene: true
index_params: {}
```

## Data Structure

### HDF5 File Structure

```
/features/
  /clip2video/     # Shape: (N, 512) - CLIP2Video features
  /longclip/       # Shape: (N, 512) - LongCLIP features
  /mock/           # Shape: (N, 512) - Mock features

/meta/
  /video_ids/      # Shape: (N,) - Video identifiers
  /frame_ids/      # Shape: (N,) - Frame identifiers
  /shot_ids/       # Shape: (N,) - Shot identifiers

/bboxes/
  /indices/        # Shape: (M, 4) - [x1, y1, x2, y2]
  /frame_index/    # Shape: (M,) - Frame index for each bbox
  /class/          # Shape: (M,) - Class ID for each bbox
  /color_name/     # Shape: (M,) - Color name for each bbox
```

### FAISS Index Structure

- **Index file**: `faiss_{feature_type}.bin`
- **Metadata file**: `metadata_{feature_type}.json`
- **Supported types**: `flat`, `ivf`, `ivfpq`

### Lucene/Whoosh Index Structure

- **Index directory**: Contains searchable documents
- **Fields**: `id`, `video_id`, `frame_id`, `shot_id`, `aladin_text`, `gem_text`, `object_classes`, `bbox_text`, `metadata`

## Search APIs

### kNN Search (FAISS)

```python
from backend.indexer.faiss_index import FAISSIndex

# Load index
faiss_index = FAISSIndex()
faiss_index.load_index("path/to/index.bin", "path/to/metadata.json")

# Search
scores, indices, metadata = faiss_index.search(query_features, k=10)
```

### Text Search (Lucene/Whoosh)

```python
from backend.indexer.lucene_index import LuceneIndex

# Load index
lucene_index = LuceneIndex("path/to/index")

# Search
results = lucene_index.search("person", limit=20)
class_results = lucene_index.search_by_class("car", limit=10)
color_results = lucene_index.search_by_color("red", limit=10)
```

## Performance Considerations

### FAISS Index Types

- **Flat**: Fastest search, highest memory usage
- **IVF**: Balanced performance, moderate memory
- **IVFPQ**: Fastest search, lowest memory, quantization loss

### GPU Acceleration

```bash
# Install GPU version
pip install faiss-gpu

# Use GPU for building
python scripts/build_faiss.py --use-gpu
```

### Memory Management

- **Large datasets**: Use IVF or IVFPQ indexes
- **Batch processing**: Process videos in chunks
- **Index merging**: Build indexes incrementally

## Troubleshooting

### Common Issues

1. **OpenCV not found**: Install `opencv-python`
2. **FAISS import error**: Install `faiss-cpu` or `faiss-gpu`
3. **Lucene not available**: Falls back to Whoosh automatically
4. **Memory errors**: Reduce batch size or use smaller index types

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Run with verbose output
python scripts/ingest.py --input videos/ --output features/ -v
```

### Validation

```bash
# Validate FAISS index
python scripts/build_faiss.py --validate

# Test search functionality
python scripts/build_lucene.py --test-search
```

## Integration with Backend

### Loading Indexes

```python
# In backend startup
from backend.indexer.faiss_index import FAISSIndex
from backend.indexer.lucene_index import LuceneIndex

# Load indexes
faiss_index = FAISSIndex()
faiss_index.load_index(settings.FAISS_INDEX_PATH, settings.FAISS_METADATA_PATH)

lucene_index = LuceneIndex(settings.LUCENE_INDEX_PATH)
```

### Search Endpoints

```python
# kNN search
@router.post("/search/knn")
async def knn_search(request: KNNSearchRequest):
    scores, indices, metadata = faiss_index.search(request.query_features, k=request.limit)
    return {"results": metadata, "scores": scores.tolist()}

# Text search
@router.post("/search/text")
async def text_search(request: TextSearchRequest):
    results = lucene_index.search(request.query, limit=request.limit)
    return {"results": results}
```

## Examples

### Sample Dataset

The pipeline includes a sample dataset generator that creates:

- 5 sample videos (640x480, 10 fps, 20 frames each)
- Moving colored rectangles with object labels
- Mock features (512-dimensional vectors)
- Sample bounding boxes and metadata

### Test Queries

```bash
# Test kNN search
curl -X POST "http://localhost:8000/api/search/knn" \
  -H "Content-Type: application/json" \
  -d '{"query_features": [0.1, 0.2, ...], "limit": 10}'

# Test text search
curl -X POST "http://localhost:8000/api/search/text" \
  -H "Content-Type: application/json" \
  -d '{"query": "person", "limit": 20}'
```

## Future Enhancements

- **Real-time indexing**: Stream processing for live video
- **Distributed indexing**: Multi-node processing
- **Advanced features**: Audio features, motion vectors
- **Index optimization**: Automatic index type selection
- **Cloud integration**: S3/Google Cloud Storage support

## Support

For issues and questions:

1. Check the troubleshooting section
2. Review logs with `LOG_LEVEL=DEBUG`
3. Validate indexes with built-in validation tools
4. Check system requirements and dependencies
