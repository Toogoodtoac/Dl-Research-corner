import { type NextRequest, NextResponse } from "next/server";

// Mock database of images (same as in search route)
const mockDatabase = [
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

// Symbol to category mapping for visual search
const symbolCategories: Record<string, string[]> = {
  person: ["people", "person", "portrait", "face"],
  car: ["vehicle", "transportation", "automobile"],
  building: ["architecture", "city", "urban", "building"],
  tree: ["nature", "forest", "outdoor", "landscape"],
  animal: ["wildlife", "pet", "nature"],
  water: ["ocean", "lake", "river", "nature"],
  mountain: ["landscape", "nature", "outdoor"],
  sky: ["nature", "outdoor", "landscape"],
  food: ["meal", "restaurant", "cooking"],
  tech: ["technology", "computer", "digital", "electronic"],
  flower: ["nature", "plant", "garden"],
  book: ["reading", "education", "library"],
  phone: ["technology", "communication", "mobile"],
  chair: ["furniture", "interior", "home"],
  table: ["furniture", "interior", "home"],
  computer: ["technology", "digital", "electronic"],
};

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { symbols, positions, page = 1, limit = 20 } = body;

    // Simulate server processing time
    await new Promise((resolve) => setTimeout(resolve, 1000));

    // Visual search logic - use symbols to find matching videos
    // For this mock implementation, we'll just use the symbols as keywords
    const searchCategories: string[] = [];

    // Extract categories from symbols
    symbols.forEach((symbol) => {
      const categories = symbolCategories[symbol];
      if (categories) {
        searchCategories.push(...categories);
      }
    });

    // Filter videos that have keywords matching any of the search categories
    const results = mockDatabase
      .filter((video) => {
        return searchCategories.some((category) =>
          video.keywords.some((keyword) =>
            keyword.toLowerCase().includes(category.toLowerCase()),
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
    console.error("Visual search error:", error);
    return NextResponse.json(
      { error: "Failed to perform visual search" },
      { status: 500 },
    );
  }
}
