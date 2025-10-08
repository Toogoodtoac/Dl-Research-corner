"use client";

import type React from "react";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import {
  List,
  ArrowRight,
  ExternalLink,
  Copy,
  AlertCircle,
} from "lucide-react";
import Link from "next/link";
import Image from "next/image";

interface ImageResult {
  id: string;
  url: string;
  videoId: string;
  videoUrl: string;
  found: boolean;
}

export default function FindImagePage() {
  const [imageIds, setImageIds] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSearching, setIsSearching] = useState(false);
  const [results, setResults] = useState<ImageResult[]>([]);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const router = useRouter();

  // Clear results when input changes
  useEffect(() => {
    if (results.length > 0) {
      setResults([]);
    }
  }, [imageIds]);

  const parseImageIds = (input: string): string[] => {
    // Split by commas, spaces, newlines, or semicolons and filter out empty strings
    return input
      .split(/[\s,;\n]+/)
      .map((id) => id.trim())
      .filter((id) => id.length > 0);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    // Parse the input to get an array of image IDs
    const parsedIds = parseImageIds(imageIds);

    // Basic validation
    if (parsedIds.length === 0) {
      setError("Please enter at least one image ID");
      return;
    }

    // Clear any previous errors
    setError(null);
    setIsSearching(true);

    // If only one ID is provided, navigate directly to that image
    if (parsedIds.length === 1) {
      router.push(`/image/${parsedIds[0]}`);
      return;
    }

    // Mock API call to fetch multiple images
    setTimeout(() => {
      // Create results array with mock data
      const mockResults = parsedIds.map((id) => {
        // Check if ID exists in our mock database
        const exists = ["img1", "img2", "img3", "img4", "img5"].includes(id);

        return {
          id,
          url: exists ? "/placeholder.svg?height=200&width=300" : "",
          videoId: exists
            ? id.includes("1") || id.includes("2")
              ? "video1"
              : "video2"
            : "",
          videoUrl: exists
            ? id.includes("1") || id.includes("2")
              ? "https://example.com/video1"
              : "https://example.com/video2"
            : "",
          found: exists,
        };
      });

      setResults(mockResults);
      setIsSearching(false);
    }, 800);
  };

  const handleCopyId = (id: string) => {
    navigator.clipboard.writeText(id);
    setCopiedId(id);

    // Reset copied status after 2 seconds
    setTimeout(() => {
      setCopiedId(null);
    }, 2000);
  };

  return (
    <div className="container mx-auto px-4 py-12 max-w-4xl">
      <div className="mb-8">
        <Link
          href="/"
          className="text-gray-600 hover:text-gray-900 flex items-center"
        >
          ← Back to search
        </Link>
      </div>

      <div className="bg-white rounded-lg shadow-lg p-8">
        <h1 className="text-2xl font-bold mb-6 text-center">
          Find Images by ID
        </h1>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label
              htmlFor="imageIds"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              Enter Image IDs
            </label>
            <div className="relative">
              <textarea
                id="imageIds"
                value={imageIds}
                onChange={(e) => setImageIds(e.target.value)}
                placeholder="Enter multiple IDs separated by commas, spaces, or new lines (e.g., img1, img2, img3)"
                className={`w-full px-4 py-3 pr-12 border rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-500 focus:border-transparent min-h-[100px] ${
                  error ? "border-red-500" : "border-gray-300"
                }`}
              />
              <List className="absolute right-3 top-3 h-5 w-5 text-gray-400" />
            </div>
            {error && <p className="mt-1 text-sm text-red-600">{error}</p>}
            <p className="mt-1 text-xs text-gray-500">
              Enter one or more image IDs. If you enter a single ID, you&apos;ll be
              redirected to that image&apos;s detail page.
            </p>
          </div>

          <button
            type="submit"
            disabled={isSearching}
            className={`w-full bg-gray-800 text-white py-3 rounded-lg font-medium hover:bg-gray-700 transition-colors ${
              isSearching ? "opacity-70 cursor-not-allowed" : ""
            }`}
          >
            {isSearching ? "Searching..." : "Find Images"}
          </button>
        </form>

        <div className="mt-8 pt-6 border-t border-gray-200">
          <h2 className="text-lg font-medium mb-3">Sample Image IDs</h2>
          <p className="text-gray-600 mb-4">
            Try these sample IDs from our demo database:
          </p>
          <div className="flex flex-wrap gap-2">
            {["img1", "img2", "img3", "img4", "img5"].map((id) => (
              <button
                key={id}
                onClick={() => {
                  setImageIds((prev) => (prev ? `${prev}, ${id}` : id));
                  setError(null);
                }}
                className="px-3 py-1 bg-gray-100 rounded-md text-gray-700 hover:bg-gray-200"
              >
                {id}
              </button>
            ))}
            <button
              onClick={() => {
                setImageIds("img1, img2, img3");
                setError(null);
              }}
              className="px-3 py-1 bg-gray-200 rounded-md text-gray-700 hover:bg-gray-300"
            >
              Multiple (img1, img2, img3)
            </button>
          </div>
        </div>
      </div>

      {/* Results Section */}
      {results.length > 0 && (
        <div className="mt-8 bg-white rounded-lg shadow-lg p-8">
          <h2 className="text-xl font-bold mb-6">
            Search Results{" "}
            <span className="text-gray-500 font-normal">
              ({results.length} images)
            </span>
          </h2>

          <div className="space-y-6">
            {results.map((result) => (
              <div
                key={result.id}
                className={`border rounded-lg overflow-hidden ${result.found ? "border-gray-200" : "border-red-200"}`}
              >
                <div className="bg-gray-50 px-4 py-3 border-b flex justify-between items-center">
                  <div className="flex items-center">
                    <span className="font-medium">ID: {result.id}</span>
                    {!result.found && (
                      <div className="ml-3 flex items-center text-red-500 text-sm">
                        <AlertCircle className="h-4 w-4 mr-1" />
                        Not found
                      </div>
                    )}
                  </div>
                  <div className="flex space-x-2">
                    <button
                      onClick={() => handleCopyId(result.id)}
                      className="p-1 text-gray-500 hover:text-gray-700 rounded-md flex items-center text-sm"
                      title="Copy ID"
                    >
                      {copiedId === result.id ? (
                        <span className="text-green-500">Copied!</span>
                      ) : (
                        <>
                          <Copy className="h-4 w-4 mr-1" /> Copy ID
                        </>
                      )}
                    </button>
                    {result.found && (
                      <Link
                        href={`/image/${result.id}`}
                        className="p-1 text-gray-500 hover:text-gray-700 rounded-md flex items-center text-sm"
                      >
                        <ArrowRight className="h-4 w-4 mr-1" /> View Details
                      </Link>
                    )}
                  </div>
                </div>

                {result.found && (
                  <div className="p-4">
                    <div className="flex flex-col sm:flex-row gap-6">
                      <div className="w-full sm:w-1/3 lg:w-1/4">
                        <div className="aspect-video relative rounded-md overflow-hidden">
                          <Image
                            src={result.url || "/placeholder.svg"}
                            alt={`Image ${result.id}`}
                            fill
                            className="object-cover"
                          />
                        </div>
                      </div>
                      <div className="flex-1">
                        <div className="space-y-2">
                          <div>
                            <span className="text-sm text-gray-500">
                              Video ID:
                            </span>
                            <span className="ml-2">{result.videoId}</span>
                          </div>
                          <div>
                            <a
                              href={result.videoUrl}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-gray-600 hover:text-gray-900 flex items-center text-sm"
                            >
                              Open Video{" "}
                              <ExternalLink className="ml-1 h-4 w-4" />
                            </a>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="mt-8 text-center text-gray-500 text-sm">
        <p>
          You can also access images directly by navigating to{" "}
          <code className="bg-gray-100 px-2 py-1 rounded text-gray-700">
            /image/[image-id]
          </code>
        </p>
      </div>
    </div>
  );
}
