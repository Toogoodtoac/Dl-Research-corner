import { type NextRequest, NextResponse } from "next/server";

// Import mockDatabase from the search route
import { mockDatabase } from "../search/route";

/**
 * POST handler for neighbor search
 * Replaces the neighborSearch function from services/api/search.ts
 */
export async function POST(request: NextRequest) {
  try {
    // Parse the request body
    const body = await request.json();
    const { id, limit = 100 } = body;

    // Simulate server processing time
    await new Promise((resolve) => setTimeout(resolve, 800));

    // Find the image with the given ID
    let sourceImage = null;
    let sourceVideo = null;

    for (const video of mockDatabase) {
      const image = video.images.find((img) => img.id === id);
      if (image) {
        sourceImage = image;
        sourceVideo = video;
        break;
      }
    }

    if (!sourceImage) {
      return NextResponse.json({ error: "Image not found" }, { status: 404 });
    }

    // Find similar images (mock implementation)
    // In a real implementation, this would use embeddings or other similarity metrics
    const results = mockDatabase
      .filter((video) => {
        // Simple implementation: same video or videos with overlapping keywords
        return (
          video.videoId === sourceVideo?.videoId ||
          video.keywords.some((k) => sourceVideo?.keywords.includes(k))
        );
      })
      .slice(0, limit);

    return NextResponse.json(results);
  } catch (error) {
    console.error("Neighbor search error:", error);
    return NextResponse.json(
      { error: "Failed to perform neighbor search" },
      { status: 500 },
    );
  }
}
