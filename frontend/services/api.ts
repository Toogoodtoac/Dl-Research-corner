// API service functions for image search

/**
 * Interface for search parameters
 */
interface SearchParams {
  query: string;
  model?: string;
  limit?: number;
}

/**
 * Interface for OCR search parameters
 */
interface OCRSearchParams {
  query: string;
  limit?: number;
}

/**
 * Interface for visual search parameters
 */
interface VisualSearchParams {
  objectList: {
    class_name: string;
    bbox: number[];
  }[];
  limit?: number;
  logic?: "AND" | "OR";
}

/**
 * Interface for search results
 * Updated to match backend schema
 */
export interface SearchResult {
  frame_stamp?: number | null;
  image_id: string;
  link?: string | null;
  image_url?: string | null; // URL for displaying the image
  score: number;
  watch_url?: string | null;
  ocr_text?: string | null; // Optional OCR text field
  bbox?: number[] | null;
  video_id?: string | null;
  shot_index?: number | null;
  file_path?: string | null; // Folder and filename (e.g., "L21_V001/001.jpg")
  metadata?: any; // Additional metadata from backend
}

/**
 * Interface for video metadata
 */
export interface VideoMetadata {
  video_id: string;
  filename: string;
  total_frames: number;
  frame_timestamps: number[];
  duration_estimate: number;
  keyframe_count: number;
}

/**
 * Interface for frame metadata
 */
export interface FrameMetadata {
  frame_id: string;
  image_info: any;
  keyframe_info: any;
  video_info: any;
}

// Updated to use FastAPI backend
const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/**
 * Perform a text-based search
 */
export async function searchImages({
  query,
  limit = 20,
  model = "longclip",
}: SearchParams): Promise<SearchResult[]> {
  console.log("🔍 searchImages called with model:", model);
  try {
    const requestBody = {
      query,
      limit,
      model_type: model,
    };
    console.log("📤 Sending request body:", requestBody);
    
    const response = await fetch(`${BASE_URL}/api/search/text`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(requestBody),
    });

    if (!response.ok) {
      throw new Error(`Search failed with status: ${response.status}`);
    }

    const data = await response.json();
    console.log("Search response:", data);

    // Extract results from the new API response format
    return data.data?.results || [];
  } catch (error) {
    console.error("Error searching images:", error);
    throw error;
  }
}

export async function searchNeighbor({
  id,
  limit = 20,
  model = "clip",
}: {
  id: string;
  limit?: number;
  model?: string;
}): Promise<SearchResult[]> {
  const response = await fetch(`${BASE_URL}/api/search/neighbor`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      image_id: id,
      limit,
      model_type: model,
    }),
  });

  if (!response.ok) {
    throw new Error(`Neighbor search failed with status: ${response.status}`);
  }

  const data = await response.json();
  return data.data?.results || [];
}

/**
 * Perform OCR search to find images containing specific text
 */
export async function searchOCR({
  query,
  limit = 20,
}: OCRSearchParams): Promise<SearchResult[]> {
  try {
    const response = await fetch(`${BASE_URL}/api/ocr/extract`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        query,
        limit,
      }),
    });

    if (!response.ok) {
      throw new Error(`OCR search failed with status: ${response.status}`);
    }

    const data = await response.json();
    // OCR returns extracted text, not search results
    // This would need to be implemented differently
    return [];
  } catch (error) {
    console.error("Error performing OCR search:", error);
    throw error;
  }
}

/**
 * Perform a visual search based on symbols and their positions
 */
export async function visualSearch({
  objectList,
  limit = 20,
  logic = "AND",
  model = "clip",
}: VisualSearchParams & { model?: string }): Promise<SearchResult[]> {
  try {
    const response = await fetch(`${BASE_URL}/api/search/visual`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        object_list: objectList,
        limit,
        logic,
        model_type: model,
      }),
    });

    if (!response.ok) {
      throw new Error(`Visual search failed with status: ${response.status}`);
    }

    const data = await response.json();
    return data.data?.results || [];
  } catch (error) {
    console.error("Error performing visual search:", error);
    throw error;
  }
}

export async function getImageById(
  id: string,
  model: string = "clip",
): Promise<SearchResult> {
  const response = await fetch(`${BASE_URL}/api/search/neighbor`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      image_id: id,
      limit: 1,
      model_type: model,
    }),
  });

  const data = await response.json();
  const results = data.data?.results || [];
  return results[0] || null;
}

/**
 * New function to get available search models
 */
export async function getAvailableModels() {
  try {
    const response = await fetch(`${BASE_URL}/api/search/models`);
    if (!response.ok) {
      throw new Error(`Failed to fetch models: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error("Error fetching models:", error);
    return { models: [] };
  }
}

/**
 * Interface for temporal search parameters
 */
interface TemporalSearchParams {
  query: string;
  model?: string;
  limit?: number;
  topk_per_sentence?: number;
  max_candidate_videos?: number;
  w_min?: number;
  w_max?: number;
}

/**
 * Interface for temporal search results
 */
export interface TemporalResult {
  video_id: string;
  frames: number[];
  images: string[];
  paths: string[];
  score: number;
}

/**
 * Interface for temporal search data
 */
export interface TemporalData {
  sentences: string[];
  per_sentence: any[];
  candidate_videos: string[];
  results: TemporalResult[];
}

/**
 * Perform temporal search for video sequences
 */
export async function temporalSearch({
  query,
  model = "beit3",
  limit = 20,
  topk_per_sentence = 200,
  max_candidate_videos = 30,
  w_min = 1,
  w_max,
}: TemporalSearchParams): Promise<TemporalData> {
  try {
    const response = await fetch(`${BASE_URL}/api/temporal/search`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        query,
        model_type: model,
        limit,
        topk_per_sentence,
        max_candidate_videos,
        w_min,
        w_max,
      }),
    });

    if (!response.ok) {
      throw new Error(`Temporal search failed with status: ${response.status}`);
    }

    const data = await response.json();
    return data.data || {};
  } catch (error) {
    console.error("Error performing temporal search:", error);
    throw error;
  }
}

/**
 * Get detailed metadata for a specific video
 */
export async function getVideoMetadata(
  videoId: string,
): Promise<VideoMetadata> {
  try {
    const response = await fetch(
      `${BASE_URL}/api/search/metadata/video/${videoId}`,
    );

    if (!response.ok) {
      throw new Error(`Failed to get video metadata: ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error("Error getting video metadata:", error);
    throw error;
  }
}

/**
 * Get detailed metadata for a specific frame
 */
export async function getFrameMetadata(
  frameId: string,
): Promise<FrameMetadata> {
  try {
    const response = await fetch(
      `${BASE_URL}/api/search/metadata/frame/${frameId}`,
    );

    if (!response.ok) {
      throw new Error(`Failed to get frame metadata: ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error("Error getting frame metadata:", error);
    throw error;
  }
}

/**
 * Get list of all available videos
 */
export async function getAllVideos(): Promise<string[]> {
  try {
    const response = await fetch(`${BASE_URL}/api/search/metadata/videos`);

    if (!response.ok) {
      throw new Error(`Failed to get videos list: ${response.status}`);
    }

    const data = await response.json();
    return data.videos || [];
  } catch (error) {
    console.error("Error getting videos list:", error);
    throw error;
  }
}

/**
 * Get all frames for a specific video
 */
export async function getVideoFrames(
  videoId: string,
  limit: number = 100,
): Promise<FrameMetadata[]> {
  try {
    const response = await fetch(
      `${BASE_URL}/api/search/metadata/video/${videoId}/frames?limit=${limit}`,
    );

    if (!response.ok) {
      throw new Error(`Failed to get video frames: ${response.status}`);
    }

    const data = await response.json();
    return data.frames || [];
  } catch (error) {
    console.error("Error getting video frames:", error);
    throw error;
  }
}
