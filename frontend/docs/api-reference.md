# API Reference Documentation

## Overview

VBS-Web 2.0 provides a RESTful API for image search operations. All endpoints support JSON request/response format with proper error handling and validation.

**Base URL**: `http://localhost:8080/api`

## Authentication

Currently, no authentication is required for API endpoints. All endpoints are publicly accessible.

## Common Response Format

### Success Response

```json
{
  "results": [...],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 150
  }
}
```

### Error Response

```json
{
  "error": "Error description",
  "code": "ERROR_CODE",
  "details": {}
}
```

## Endpoints

### 1. Text-Based Search

Search for images using natural language queries.

**Endpoint**: `POST /api/search`

#### Request Body

```json
{
  "query": "mountain landscape with lake",
  "limit": 20,
  "model": "blip2_feature_extractor"
}
```

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | string | Yes | - | Search query in natural language |
| `limit` | number | No | 20 | Maximum number of results (1-100) |
| `model` | string | No | "blip2_feature_extractor" | ML model for search |

#### Response

```json
{
  "results": [
    {
      "videoId": "video1",
      "videoUrl": "https://youtube.com/watch?v=...",
      "keywords": ["nature", "mountain", "water"],
      "images": [
        {
          "id": "img1",
          "url": "/placeholder.svg?height=200&width=300",
          "timestamp": "00:01:23",
          "description": "Mountain landscape with lake"
        }
      ]
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 45
  }
}
```

#### Example Usage

```typescript
const searchImages = async (query: string) => {
  const response = await fetch('/api/search', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      query,
      limit: 10
    })
  });

  if (!response.ok) {
    throw new Error(`Search failed: ${response.status}`);
  }

  return await response.json();
};
```

### 2. Visual Object Detection Search

Search for images containing specific objects with spatial relationships.

**Endpoint**: `POST /api/search-detections`

#### Request Body

```json
{
  "object_list": [
    {
      "class_name": "car",
      "bbox": [100, 100, 200, 200]
    },
    {
      "class_name": "person",
      "bbox": [150, 50, 250, 180]
    }
  ],
  "logic": "AND",
  "limit": 10
}
```

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `object_list` | array | Yes | - | List of objects with bounding boxes |
| `object_list[].class_name` | string | Yes | - | Object class name |
| `object_list[].bbox` | number[] | Yes | - | Bounding box [x, y, width, height] |
| `logic` | string | No | "AND" | Search logic: "AND" or "OR" |
| `limit` | number | No | 10 | Maximum results (1-100) |

#### Supported Object Classes

```typescript
const SUPPORTED_CLASSES = [
  'person', 'car', 'truck', 'bus', 'motorcycle', 'bicycle',
  'airplane', 'boat', 'bird', 'cat', 'dog', 'horse',
  'building', 'tree', 'flower', 'book', 'chair', 'sofa',
  'cup', 'laptop', 'cellphone', 'television'
  // ... and more
];
```

#### Response

```json
{
  "results": [
    {
      "videoId": "video2",
      "videoUrl": "https://youtube.com/watch?v=...",
      "keywords": ["urban", "traffic", "street"],
      "images": [
        {
          "id": "img5",
          "url": "/placeholder.svg?height=200&width=300",
          "timestamp": "00:02:15",
          "description": "Street scene with cars and pedestrians"
        }
      ]
    }
  ]
}
```

### 3. Neighbor Search (Similar Images)

Find images similar to a given image using ML embeddings.

**Endpoint**: `POST /api/neighbor`

#### Request Body

```json
{
  "id": "img123",
  "limit": 20
}
```

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `id` | string | Yes | - | Source image ID for similarity search |
| `limit` | number | No | 20 | Maximum similar images to return |

#### Response

```json
{
  "results": [
    {
      "videoId": "video1",
      "videoUrl": "https://youtube.com/watch?v=...",
      "keywords": ["nature", "landscape"],
      "images": [
        {
          "id": "img124",
          "url": "/placeholder.svg?height=200&width=300",
          "timestamp": "00:03:45",
          "description": "Similar mountain scene",
          "similarity_score": 0.89
        }
      ]
    }
  ]
}
```

### 4. Visual Search

Complex visual search combining multiple objects and spatial relationships.

**Endpoint**: `POST /api/visual_search`

#### Request Body

```json
{
  "objectList": [
    {
      "class_name": "car",
      "bbox": [50, 100, 150, 200]
    },
    {
      "class_name": "building",
      "bbox": [200, 50, 400, 300]
    }
  ],
  "logic": "AND",
  "limit": 15
}
```

#### Parameters

Same as `/api/search-detections` but with `objectList` parameter name.

### 5. Image Serving

Serve static images with optimization and caching.

**Endpoint**: `GET /api/images/[...path]`

#### URL Structure

```
GET /api/images/video1/frame_001.jpg
GET /api/images/thumbnails/thumb_123.jpg
```

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `path` | string[] | Dynamic path segments for image location |

#### Response Headers

```
Content-Type: image/jpeg
Cache-Control: public, max-age=31536000
ETag: "unique-hash"
```

## Error Handling

### Common Error Codes

| Status | Code | Description |
|--------|------|-------------|
| 400 | `INVALID_REQUEST` | Malformed request body or parameters |
| 404 | `NOT_FOUND` | Resource not found |
| 422 | `VALIDATION_ERROR` | Request validation failed |
| 500 | `INTERNAL_ERROR` | Server processing error |
| 503 | `SERVICE_UNAVAILABLE` | Backend service temporarily unavailable |

### Error Response Examples

#### Validation Error

```json
{
  "error": "Validation failed",
  "code": "VALIDATION_ERROR",
  "details": {
    "field": "query",
    "message": "Query parameter is required"
  }
}
```

#### Not Found Error

```json
{
  "error": "Image not found",
  "code": "NOT_FOUND",
  "details": {
    "id": "img999",
    "resource": "image"
  }
}
```

## Rate Limiting

Currently no rate limiting is implemented. For production deployment, consider:

- Rate limiting per IP: 100 requests/minute
- Burst allowance: 20 requests/10 seconds
- Rate limit headers in responses

## Request/Response Examples

### Complete Search Workflow

```typescript
// 1. Text search
const textResults = await fetch('/api/search', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    query: "sunset over ocean",
    limit: 5
  })
});

// 2. Get first image ID
const data = await textResults.json();
const firstImageId = data.results[0].images[0].id;

// 3. Find similar images
const similarResults = await fetch('/api/neighbor', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    id: firstImageId,
    limit: 10
  })
});

// 4. Visual search for specific objects
const visualResults = await fetch('/api/search-detections', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    object_list: [
      { class_name: "boat", bbox: [100, 150, 200, 250] }
    ],
    logic: "AND",
    limit: 8
  })
});
```

## SDK Usage

### TypeScript Interfaces

```typescript
interface SearchResult {
  frame_stamp: number;
  image_id: string;
  link: string;
  score: number;
  watch_url: string;
  ocr_text?: string;
}

interface VisualSearchParams {
  objectList: {
    class_name: string;
    bbox: number[];
  }[];
  limit?: number;
  logic?: 'AND' | 'OR';
}

interface SearchParams {
  query: string;
  model?: string;
  limit?: number;
}
```

### Service Functions

```typescript
import { searchImages, visualSearch, searchNeighbor } from '@/services/api';

// Text search
const results = await searchImages({
  query: "mountain landscape",
  limit: 20
});

// Visual search
const visualResults = await visualSearch({
  objectList: [
    { class_name: "car", bbox: [50, 50, 150, 150] }
  ],
  logic: "AND"
});

// Neighbor search
const similarImages = await searchNeighbor({
  id: "img123",
  limit: 10
});
```

## Testing

### Test Endpoints

```bash
# Text search test
curl -X POST http://localhost:8080/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "mountain", "limit": 5}'

# Visual search test
curl -X POST http://localhost:8080/api/search-detections \
  -H "Content-Type: application/json" \
  -d '{"object_list": [{"class_name": "car", "bbox": [0,0,100,100]}], "logic": "AND"}'

# Neighbor search test
curl -X POST http://localhost:8080/api/neighbor \
  -H "Content-Type: application/json" \
  -d '{"id": "img1", "limit": 3}'
```

## Performance Considerations

- **Response Times**: Target <800ms for search operations
- **Caching**: Results cached for 5 minutes on client-side
- **Pagination**: Use limit parameter to control response size
- **Image Optimization**: Images served through Next.js optimization
- **Concurrent Requests**: Server handles up to 50 concurrent requests

## Future API Enhancements

- Authentication and user sessions
- Saved searches and favorites
- Advanced filtering options
- Batch operations
- WebSocket real-time updates
- Analytics and usage metrics
