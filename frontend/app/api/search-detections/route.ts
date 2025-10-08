import { type NextRequest, NextResponse } from "next/server";

// Import mockDatabase from the search route
import { mockDatabase } from "../search/route";

/**
 * POST handler for detection-based search
 * Replaces the detectionSearch function from services/api/search.ts
 */
export async function POST(request: NextRequest) {
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
}
