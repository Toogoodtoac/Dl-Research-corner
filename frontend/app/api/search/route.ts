import { type NextRequest, NextResponse } from "next/server";

// Mock database of images - exported for use in other route files
export const mockDatabase = [
  {
    videoId: "video1",
    videoUrl: "https://example.com/video1",
    keywords: ["nature", "mountain", "water", "landscape", "outdoor"],
    images: [
      {
        id: "img1",
        url: "/placeholder.svg?height=200&width=300",
        timestamp: "00:01:23",
        description: "Mountain landscape with lake",
      },
      {
        id: "img2",
        url: "/placeholder.svg?height=200&width=300",
        timestamp: "00:02:45",
        description: "Forest trail with sunlight",
      },
    ],
  },
  {
    videoId: "video2",
    videoUrl: "https://example.com/video2",
    keywords: ["city", "urban", "building", "architecture", "street"],
    images: [
      {
        id: "img3",
        url: "/placeholder.svg?height=200&width=300",
        timestamp: "00:00:58",
        description: "City skyline at sunset",
      },
      {
        id: "img4",
        url: "/placeholder.svg?height=200&width=300",
        timestamp: "00:03:12",
        description: "Busy street with pedestrians",
      },
      {
        id: "img5",
        url: "/placeholder.svg?height=200&width=300",
        timestamp: "00:05:34",
        description: "Modern architecture building",
      },
    ],
  },
  {
    videoId: "video3",
    videoUrl: "https://example.com/video3",
    keywords: ["people", "person", "portrait", "face", "group"],
    images: [
      {
        id: "img6",
        url: "/placeholder.svg?height=200&width=300",
        timestamp: "00:01:45",
        description: "Group of friends at a party",
      },
      {
        id: "img7",
        url: "/placeholder.svg?height=200&width=300",
        timestamp: "00:04:23",
        description: "Portrait of a woman smiling",
      },
    ],
  },
  {
    videoId: "video4",
    videoUrl: "https://example.com/video4",
    keywords: ["food", "meal", "restaurant", "cooking", "kitchen"],
    images: [
      {
        id: "img8",
        url: "/placeholder.svg?height=200&width=300",
        timestamp: "00:02:10",
        description: "Gourmet meal on a plate",
      },
      {
        id: "img9",
        url: "/placeholder.svg?height=200&width=300",
        timestamp: "00:03:45",
        description: "Chef cooking in restaurant kitchen",
      },
    ],
  },
  {
    videoId: "video5",
    videoUrl: "https://example.com/video5",
    keywords: ["technology", "computer", "tech", "digital", "electronic"],
    images: [
      {
        id: "img10",
        url: "/placeholder.svg?height=200&width=300",
        timestamp: "00:00:30",
        description: "Person working on laptop",
      },
      {
        id: "img11",
        url: "/placeholder.svg?height=200&width=300",
        timestamp: "00:02:15",
        description: "Modern smartphone on desk",
      },
    ],
  },
];

export async function GET(request: NextRequest) {
  // Get search parameters
  const searchParams = request.nextUrl.searchParams;
  const query = searchParams.get("q") || "";
  const page = Number.parseInt(searchParams.get("page") || "1");
  const limit = Number.parseInt(searchParams.get("limit") || "20");

  // Simulate server processing time
  await new Promise((resolve) => setTimeout(resolve, 800));

  try {
    // Search logic - filter videos that have keywords matching the query
    const searchTerms = query.toLowerCase().split(/\s+/);

    const results = mockDatabase
      .filter((video) => {
        // Check if any keyword matches any search term
        return searchTerms.some(
          (term: string) =>
            video.keywords.some((keyword) =>
              keyword.toLowerCase().includes(term),
            ) ||
            // Also search in image descriptions
            video.images.some((image) =>
              image.description?.toLowerCase().includes(term),
            ),
        );
      })
      // Limit results based on pagination
      .slice(0, limit);

    return NextResponse.json({
      results,
      pagination: {
        page,
        limit,
        total: results.length,
      },
    });
  } catch (error) {
    console.error("Search error:", error);
    return NextResponse.json(
      { error: "Failed to perform search" },
      { status: 500 },
    );
  }
}

/**
 * POST handler for text-based search
 * Replaces the search function from services/api/search.ts
 */
export async function POST(request: NextRequest) {
  try {
    // Parse the request body
    const body = await request.json();
    const { query, model = "blip2_feature_extractor", limit = 100 } = body;

    // Simulate server processing time
    await new Promise((resolve) => setTimeout(resolve, 800));

    // Search logic - filter videos that have keywords matching the query
    const searchTerms = query.toLowerCase().split(/\s+/);

    const results = mockDatabase
      .filter((video) => {
        // Check if any keyword matches any search term
        return searchTerms.some(
          (term: string) =>
            video.keywords.some((keyword) =>
              keyword.toLowerCase().includes(term),
            ) ||
            // Also search in image descriptions
            video.images.some((image) =>
              image.description?.toLowerCase().includes(term),
            ),
        );
      })
      // Limit results based on limit parameter
      .slice(0, limit);

    return NextResponse.json(results);
  } catch (error) {
    console.error("Search error:", error);
    return NextResponse.json(
      { error: "Failed to perform search" },
      { status: 500 },
    );
  }
}

// Create separate routes for the other search endpoints
export const neighbor = {
  /**
   * POST handler for neighbor search
   * Replaces the neighborSearch function from services/api/search.ts
   */
  async POST(request: NextRequest) {
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
  },
};

export const searchDetections = {
  /**
   * POST handler for detection-based search
   * Replaces the detectionSearch function from services/api/search.ts
   */
  async POST(request: NextRequest) {
    try {
      // Parse the request body
      const body = await request.json();
      const { object_list, limit = 10, logic = "AND" } = body;

      // Simulate server processing time
      await new Promise((resolve) => setTimeout(resolve, 800));

      // Extract class names for searching
      const classNames = object_list.map(
        (obj: { class_name: string; bbox: number[] }) =>
          obj.class_name.toLowerCase(),
      );

      // Search logic based on class names
      const results = mockDatabase
        .filter((video) => {
          const matchingKeywords = video.keywords.filter((keyword) =>
            classNames.includes(keyword.toLowerCase()),
          );

          if (logic === "AND") {
            // All class names must match keywords
            return matchingKeywords.length === classNames.length;
          } else {
            // At least one class name must match keywords
            return matchingKeywords.length > 0;
          }
        })
        .slice(0, limit);

      return NextResponse.json(results);
    } catch (error) {
      console.error("Detection search error:", error);
      return NextResponse.json(
        { error: "Failed to perform detection search" },
        { status: 500 },
      );
    }
  },
};
