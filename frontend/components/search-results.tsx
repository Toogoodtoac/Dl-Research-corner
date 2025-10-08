"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import Image from "next/image";
import Link from "next/link";
import { ChevronRight, Copy, ExternalLink, Grid, List } from "lucide-react";
import type { SearchResult } from "@/services/api";
import {
  cn,
  convertDriveLinkToImageUrl,
  getLocalImageUrl,
  getMeaningfulId,
} from "@/lib/utils";
import { toast } from "sonner";

// Image cache for future use
// const imageCache = localforage.createInstance({
//   name: "imageCache",
// });

interface SearchResultsProps {
  results: SearchResult[];
  onMoreResults: (id: string) => void;
  focusId: string | null;
  limit?: number;
  onClearSearch?: () => void;
}

interface VideoGroup {
  videoId: string;
  images: SearchResult[];
  videoUrl: string;
}

// Single image result component - optimized for grid layout
const ImageResult = ({
  image,
  videoUrl,
  copiedId,
  onCopyId,
  onMoreResults,
  focusId,
  setFocusRef,
  onImageError,
  layoutMode = "grid",
  keyframesMap,
}: {
  image: SearchResult;
  videoUrl: string;
  copiedId: string | null;
  onCopyId: (image: SearchResult) => void;
  onMoreResults: (id: string) => void;
  focusId: string | null;
  setFocusRef: (id: string, ref: HTMLDivElement | null) => void;
  onImageError: (imageId: string) => void;
  layoutMode?: "grid" | "list";
  keyframesMap: Record<string, unknown> | null;
}) => {
  const [googleDriveImageUrl, setGoogleDriveImageUrl] = useState<string | null>(
    null,
  );
  const [imageError, setImageError] = useState(false);
  const imageRef = useRef<HTMLDivElement>(null);

  // Use the backend's image_url field if available, otherwise fallback to local URL
  const backendUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  let imageUrl: string | null = null;

  if (image.image_url) {
    if (image.image_url.startsWith("/data/")) {
      imageUrl = `${backendUrl}${image.image_url}`;
    } else if (image.image_url.startsWith("raw/")) {
      imageUrl = `${backendUrl}/data/${image.image_url}`;
    } else {
      imageUrl = `${backendUrl}/data/${image.image_url}`;
    }
  } else {
    imageUrl = getLocalImageUrl();
  }

  // Register ref with parent if this is the focused image
  useEffect(() => {
    if (focusId === image.image_id && imageRef.current) {
      setFocusRef(image.image_id, imageRef.current);
    }
  }, [focusId, image.image_id, setFocusRef]);

  useEffect(() => {
    const ref = imageRef.current;
    if (ref) {
      setFocusRef(image.image_id, ref);
    }
    return () => {
      setFocusRef(image.image_id, null);
    };
  }, []);

  useEffect(() => {
    if (image.link) {
      convertDriveLinkToImageUrl(image.link).then((url) =>
        setGoogleDriveImageUrl(url),
      );
    }
  }, [image.link]);

  const handleImageError = () => {
    setImageError(true);
    onImageError(image.image_id);
  };

  if (imageError) {
    return null;
  }

  if (layoutMode === "list") {
    // List layout - more compact, shows more info
    return (
      <div
        ref={imageRef}
        className={cn([
          focusId === image.image_id &&
            "border-2 border-blue-500 p-2 rounded-lg",
          "group relative bg-white border border-gray-200 rounded-lg p-3 hover:shadow-md transition-shadow",
        ])}
      >
        <div className="flex items-start space-x-3">
          {/* Image */}
          <div
            className="relative rounded-md overflow-hidden flex-shrink-0"
            style={{ width: "120px", height: "90px" }}
          >
            <Link href={`/image/${image.image_id}`}>
              <Image
                src={imageUrl || googleDriveImageUrl || "/placeholder.svg"}
                sizes="120px"
                placeholder="blur"
                blurDataURL="data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZjFmMWYxIi8+PC9zdmc+"
                alt={`Image ${image.image_id}`}
                fill
                className="object-cover group-hover:scale-105 transition-transform"
                onError={handleImageError}
                loading="lazy"
              />
            </Link>
          </div>

          {/* Content */}
          <div className="flex-1 min-w-0">
            <div className="flex justify-between items-start mb-2">
              <div className="min-w-0 flex-1">
                <h4 className="font-medium text-sm text-gray-900 truncate">
                  {getMeaningfulId(
                    image.file_path || "",
                    keyframesMap,
                    image.image_id,
                  )}
                </h4>
                {/* File path information */}
                {image.file_path && (
                  <p className="text-xs text-blue-600 mt-1 font-medium">
                    📁 {image.file_path}
                  </p>
                )}
                <p className="text-xs text-gray-500 mt-1">
                  {image.frame_stamp
                    ? `Frame at ${Math.floor(image.frame_stamp)}s`
                    : "Frame timestamp not available"}
                </p>
                {image.score !== undefined && (
                  <p className="text-xs text-blue-600 mt-1">
                    Score: {image.score.toFixed(4)}
                  </p>
                )}
              </div>

              {/* Action buttons */}
              <div className="flex space-x-1 ml-2">
                <button
                  onClick={() => onCopyId(image)}
                  className="p-1 rounded-md text-gray-500 hover:text-gray-700 hover:bg-gray-100"
                  title="Copy ID"
                >
                  {copiedId === image.image_id ? (
                    <span className="text-green-500 text-xs">Copied!</span>
                  ) : (
                    <Copy className="w-4 h-4" />
                  )}
                </button>

                <a
                  href={videoUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="p-1 rounded-md text-gray-500 hover:text-gray-700 hover:bg-gray-100"
                  title="Open video"
                >
                  <ExternalLink className="w-4 h-4" />
                </a>

                <button
                  onClick={() => onMoreResults(image.image_id)}
                  className="p-1 rounded-md text-gray-500 hover:text-gray-700 hover:bg-gray-100"
                  title="More similar images"
                >
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Grid layout - compact, shows images prominently
  return (
    <div
      ref={imageRef}
      className={cn([
        focusId === image.image_id &&
          "border-2 border-blue-500 p-2 rounded-lg focus-animation",
        "group relative bg-white border border-gray-200 rounded-lg p-3 hover:shadow-md transition-shadow image-result-card",
      ])}
    >
      {/* Image */}
      <div className="relative rounded-md aspect-video overflow-hidden mb-3">
        <Link href={`/image/${image.image_id}`}>
          <Image
            src={imageUrl || googleDriveImageUrl || "/placeholder.svg"}
            sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
            placeholder="blur"
            blurDataURL="data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZjFmMWYxIi8+PC9zdmc+"
            alt={`Image ${image.image_id}`}
            fill
            className="object-cover group-hover:scale-105 transition-transform"
            onError={handleImageError}
            loading="lazy"
          />
        </Link>
      </div>

      {/* Content */}
      <div className="space-y-3">
        <div className="flex items-start justify-between">
          <div className="flex-1 min-w-0">
            <h3 className="text-sm font-medium text-gray-900 truncate mb-1">
              {getMeaningfulId(
                image.file_path || "",
                keyframesMap,
                image.image_id,
              )}
            </h3>

            {/* Enhanced metadata display for detailed mode */}
            {layoutMode === "grid" && (
              <div className="metadata-section">
                {/* File path information */}
                {image.file_path && (
                  <div className="file-path-info text-blue-600 font-medium">
                    📁 {image.file_path}
                  </div>
                )}

                {/* Video information */}
                {image.watch_url && (
                  <div className="video-info">
                    📹 Video:{" "}
                    {image.watch_url.split("/").pop()?.split("query")[0] ||
                      "Unknown"}
                  </div>
                )}

                {/* Timestamp information */}
                {image.frame_stamp !== undefined &&
                image.frame_stamp !== null ? (
                  <div className="timestamp-info">
                    ⏰ Frame: {Math.floor(image.frame_stamp)}s
                    {image.frame_stamp > 0 && (
                      <span className="ml-2 text-gray-600">
                        ({Math.floor(image.frame_stamp / 60)}m{" "}
                        {Math.floor(image.frame_stamp % 60)}s)
                      </span>
                    )}
                  </div>
                ) : (
                  <div className="timestamp-info text-gray-500">
                    ⏰ No timestamp available
                  </div>
                )}

                {/* Score information */}
                {image.score !== undefined && (
                  <div className="score-info">
                    🎯 Score: {image.score.toFixed(3)}
                  </div>
                )}
              </div>
            )}
          </div>

          <div className="flex items-center space-x-1 ml-2">
            <button
              onClick={() => onCopyId(image)}
              className="p-1 text-gray-400 hover:text-gray-600 transition-colors"
              title="Copy image ID"
            >
              <Copy className="w-4 h-4" />
            </button>
            <Link
              href={videoUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="p-1 text-gray-400 hover:text-gray-600 transition-colors"
              title="Open video in new tab"
            >
              <ExternalLink className="w-4 h-4" />
            </Link>
            <button
              onClick={() => onMoreResults(image.image_id)}
              className="p-1 text-gray-400 hover:text-gray-600 transition-colors"
              title="Find similar images"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

// Optimized search results component
export default function SearchResults({
  results,
  onMoreResults,
  focusId,
  limit,
  onClearSearch,
}: SearchResultsProps) {
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [focusRefs, setFocusRefs] = useState<Record<string, HTMLDivElement>>(
    {},
  );
  const [failedImageIds, setFailedImageIds] = useState<Set<string>>(new Set());
  const [layoutMode, setLayoutMode] = useState<"grid" | "list">("grid");
  const [showVideoGroups, setShowVideoGroups] = useState(false);
  const [keyframesMap, setKeyframesMap] = useState<Record<string, unknown> | null>(null);
  // Always use comfortable density mode (currently unused)
  // const densityMode = "comfortable";

  // Debug logging
  console.log("🔍 SearchResults props:", {
    resultsLength: results.length,
    limit,
    validResultsLength: results.filter((r) => !failedImageIds.has(r.image_id))
      .length,
  });

  // Filter out failed images
  const validResults = results.filter(
    (result) => !failedImageIds.has(result.image_id),
  );

  // Group videos if requested
  const videoGroups = showVideoGroups ? groupingVideos(validResults) : [];

  // Always use comfortable grid layout
  const getGridClass = () => "responsive-image-grid";

  // Register refs for focused images
  const registerFocusRef = useCallback(
    (id: string, ref: HTMLDivElement | null) => {
      if (ref) {
        setFocusRefs((prev) => ({ ...prev, [id]: ref }));
      } else {
        setFocusRefs((prev) => {
          const newRefs = { ...prev };
          delete newRefs[id];
          return newRefs;
        });
      }
    },
    [],
  );

  // Handle image errors
  const handleImageError = useCallback((imageId: string) => {
    setFailedImageIds((prev) => {
      const newSet = new Set(prev);
      newSet.add(imageId);
      return newSet;
    });
  }, []);

  // Scroll to focused image when focusId changes
  useEffect(() => {
    if (focusId && focusRefs[focusId]) {
      const timeoutId = setTimeout(() => {
        focusRefs[focusId].scrollIntoView({
          behavior: "smooth",
          block: "center",
        });
        focusRefs[focusId].classList.add("animate-pulse");
        setTimeout(() => {
          if (focusRefs[focusId]) {
            focusRefs[focusId].classList.remove("animate-pulse");
          }
        }, 1500);
      }, 100);

      return () => clearTimeout(timeoutId);
    }
  }, [focusId, focusRefs]);

  // Load keyframes mapping data
  useEffect(() => {
    const loadKeyframesMap = async () => {
      try {
        const response = await fetch("/map_keyframes.json");
        if (response.ok) {
          const data = await response.json();
          setKeyframesMap(data);
        } else {
          console.warn(
            "Failed to load keyframes mapping:",
            response.statusText,
          );
        }
      } catch (error) {
        console.warn("Error loading keyframes mapping:", error);
      }
    };

    loadKeyframesMap();
  }, []);

  // Function to get the correct ID for copying
  const getCopyId = (image: SearchResult): string => {
    // First, get the meaningful ID using the existing function
    const meaningfulId = getMeaningfulId(
      image.file_path || "",
      keyframesMap,
      image.image_id,
    );
    
    // If the meaningful ID is different from the original (meaning we found a mapping)
    if (meaningfulId !== image.image_id) {
      // Extract the last part after the last underscore
      // Example: "L21_V001_272_33861" -> "33861"
      const parts = meaningfulId.split('_');
      if (parts.length >= 4) {
        return parts[parts.length - 1]; // Return the last part (timestamp ID)
      }
    }
    
    // If no mapping found or meaningful ID format is unexpected, return the original
    return image.image_id;
  };

  const handleCopyId = (image: SearchResult) => {
    const copyId = getCopyId(image);
    navigator.clipboard.writeText(copyId);
    setCopiedId(image.image_id); // Use original image_id for UI state
    toast.success(`Image ID ${copyId} copied to clipboard`);
    setTimeout(() => {
      setCopiedId(null);
    }, 2000);
  };

  // If all images failed to load
  if (validResults.length === 0 && failedImageIds.size > 0) {
    return (
      <div className="bg-gray-50 p-8 border border-gray-200 rounded-xl text-center">
        <p className="mb-2 text-gray-600">No images could be displayed</p>
        <p className="text-gray-500 text-sm">
          {failedImageIds.size} {failedImageIds.size === 1 ? "image" : "images"}{" "}
          failed to load
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Layout Controls */}
      <div className="flex justify-between items-center bg-white p-4 rounded-lg border border-gray-200">
        <div className="flex items-center space-x-4">
          <h3 className="text-lg font-semibold text-gray-900">
            Search Results ({validResults.length})
          </h3>

          {/* Layout Toggle */}
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setLayoutMode("grid")}
              className={cn(
                "p-2 rounded-md transition-colors",
                layoutMode === "grid"
                  ? "bg-blue-100 text-blue-600"
                  : "text-gray-500 hover:text-gray-700 hover:bg-gray-100",
              )}
              title="Grid layout"
            >
              <Grid className="w-4 h-4" />
            </button>
            <button
              onClick={() => setLayoutMode("list")}
              className={cn(
                "p-2 rounded-md transition-colors",
                layoutMode === "list"
                  ? "bg-blue-100 text-blue-600"
                  : "text-gray-500 hover:text-gray-700 hover:bg-gray-100",
              )}
              title="List layout"
            >
              <List className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* View Options */}
        <div className="flex items-center space-x-4">
          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={showVideoGroups}
              onChange={(e) => setShowVideoGroups(e.target.checked)}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <span className="text-sm text-gray-700">Group by video</span>
          </label>

          {/* Clear Search Button */}
          {onClearSearch && (
            <button
              onClick={onClearSearch}
              className="px-3 py-1.5 text-sm text-red-600 hover:text-red-900 hover:bg-red-50 rounded-md transition-colors"
              title="Clear search and results"
            >
              Clear Search
            </button>
          )}
        </div>
      </div>

      {/* Results Display */}
      {showVideoGroups ? (
        // Video Group Layout (original functionality)
        <div className="space-y-6">
          {videoGroups.map((videoGroup) => (
            <VideoGroup
              key={videoGroup.videoId}
              videoGroup={videoGroup}
              onCopyId={handleCopyId}
              onMoreResults={onMoreResults}
              onImageError={handleImageError}
            />
          ))}
        </div>
      ) : (
        // Optimized Grid/List Layout
        <div
          className={cn(layoutMode === "grid" ? getGridClass() : "space-y-3")}
        >
          {validResults.map((image) => (
            <ImageResult
              key={image.image_id}
              image={image}
              videoUrl={
                image.watch_url
                  ? `${image.watch_url}&t=${image.frame_stamp ? Math.floor(image.frame_stamp) : 0}`
                  : "#"
              }
              copiedId={copiedId}
              onCopyId={handleCopyId}
              onMoreResults={onMoreResults}
              focusId={focusId}
              setFocusRef={registerFocusRef}
              onImageError={handleImageError}
              layoutMode={layoutMode}
              keyframesMap={keyframesMap}
            />
          ))}
        </div>
      )}
    </div>
  );
}

// Video group component (kept for backward compatibility)
const VideoGroup = ({
  videoGroup,
  onCopyId,
  onMoreResults,
  onImageError,
}: {
  videoGroup: VideoGroup;
  onCopyId: (image: SearchResult) => void;
  onMoreResults: (id: string) => void;
  onImageError: (imageId: string) => void;
}) => {
  const [filteredImages, setFilteredImages] = useState(videoGroup.images);

  // Handle image error by filtering out failed images
  const handleImageError = useCallback((imageId: string) => {
    setFilteredImages((prev) => prev.filter((img) => img.image_id !== imageId));
    onImageError(imageId);
  }, [onImageError]);

  if (filteredImages.length === 0) {
    return null;
  }

  // Sort images by frame_stamp if available for better chronological order
  const sortedImages = [...filteredImages].sort((a, b) => {
    if (
      a.frame_stamp !== undefined &&
      a.frame_stamp !== null &&
      b.frame_stamp !== undefined &&
      b.frame_stamp !== null
    ) {
      return a.frame_stamp - b.frame_stamp;
    }
    return 0;
  });

  return (
    <div className="bg-white shadow-lg rounded-xl overflow-hidden border border-gray-200">
      {/* Video Header */}
      <div className="bg-gradient-to-r from-blue-50 via-indigo-50 to-purple-50 px-8 py-6 border-b border-gray-200">
        <div className="flex justify-between items-center">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-3">
              <div className="w-4 h-4 bg-gradient-to-r from-blue-500 to-indigo-500 rounded-full shadow-sm"></div>
              <h3 className="text-xl font-bold text-gray-800">
                Video: {videoGroup.videoId}
              </h3>
            </div>
            <div className="flex items-center space-x-3">
              <span className="px-3 py-1.5 bg-blue-100 text-blue-800 text-sm font-semibold rounded-full shadow-sm">
                {filteredImages.length} frame
                {filteredImages.length !== 1 ? "s" : ""}
              </span>
              {filteredImages.some(
                (img) =>
                  img.frame_stamp !== undefined && img.frame_stamp !== null,
              ) && (
                <span className="px-3 py-1.5 bg-green-100 text-green-800 text-sm font-medium rounded-full">
                  <svg
                    className="w-3 h-3 inline mr-1"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                    />
                  </svg>
                  Timestamped
                </span>
              )}
            </div>
          </div>
          <a
            href={videoGroup.videoUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center px-4 py-2.5 bg-gradient-to-r from-blue-600 to-indigo-600 text-white text-sm font-semibold rounded-lg hover:from-blue-700 hover:to-indigo-700 transition-all duration-200 shadow-md hover:shadow-lg"
          >
            <ExternalLink className="mr-2 w-4 h-4" />
            Open Video
          </a>
        </div>
      </div>

      {/* Frames Grid */}
      <div className="p-6">
        <div className="gap-6 grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
          {sortedImages.map((image, index) => {
            // Use the same image URL logic as ImageResult component
            const backendUrl =
              process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
            let imageUrl: string | null = null;

            if (image.image_url) {
              if (image.image_url.startsWith("/data/")) {
                imageUrl = `${backendUrl}${image.image_url}`;
              } else if (image.image_url.startsWith("raw/")) {
                imageUrl = `${backendUrl}/data/${image.image_url}`;
              } else {
                imageUrl = `${backendUrl}/data/${image.image_url}`;
              }
            } else {
              imageUrl = getLocalImageUrl();
            }

            return (
              <div key={image.image_id} className="relative group">
                <div className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow duration-200">
                  {/* Frame number indicator */}
                  <div className="absolute top-3 left-3 z-10 bg-blue-600 text-white text-sm font-semibold px-3 py-1 rounded-full shadow-lg">
                    #{index + 1}
                  </div>

                  {/* Image container with better aspect ratio */}
                  <div className="relative aspect-video overflow-hidden">
                    <Image
                      src={imageUrl || "/placeholder.svg"}
                      alt={`Frame ${index + 1} of ${videoGroup.videoId}`}
                      fill
                      className="object-cover group-hover:scale-105 transition-transform duration-300"
                      sizes="(max-width: 640px) 100vw, (max-width: 768px) 50vw, (max-width: 1024px) 33vw, (max-width: 1280px) 25vw, 20vw"
                      loading="lazy"
                      onError={() => handleImageError(image.image_id)}
                    />
                  </div>

                  {/* Frame info */}
                  <div className="p-4 space-y-2">
                    <div className="text-sm font-medium text-gray-900 truncate">
                      {image.file_path?.split("/").pop() || image.image_id}
                    </div>

                    <div className="flex items-center justify-between text-xs text-gray-500">
                      <span className="flex items-center">
                        <svg
                          className="w-3 h-3 mr-1"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                          />
                        </svg>
                        {image.frame_stamp !== undefined &&
                        image.frame_stamp !== null
                          ? `${Math.floor(image.frame_stamp)}s`
                          : "No timestamp"}
                      </span>
                      <span className="flex items-center font-semibold text-blue-600">
                        <svg
                          className="w-3 h-3 mr-1"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                          />
                        </svg>
                        {image.score.toFixed(3)}
                      </span>
                    </div>

                    {/* Action buttons */}
                    <div className="flex items-center justify-between pt-2">
                      <div className="flex space-x-1">
                        <button
                          onClick={() => onCopyId(image)}
                          className="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded transition-colors"
                          title="Copy ID"
                        >
                          <Copy className="w-4 h-4" />
                        </button>
                        <a
                          href={
                            image.watch_url
                              ? `${image.watch_url}&t=${image.frame_stamp ? Math.floor(image.frame_stamp) : 0}`
                              : "#"
                          }
                          target="_blank"
                          rel="noopener noreferrer"
                          className="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded transition-colors"
                          title="Open video"
                        >
                          <ExternalLink className="w-4 h-4" />
                        </a>
                        <button
                          onClick={() => onMoreResults(image.image_id)}
                          className="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded transition-colors"
                          title="Find similar"
                        >
                          <ChevronRight className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Video Summary */}
        {filteredImages.length > 0 && (
          <div className="mt-8 pt-6 border-t border-gray-200">
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex flex-wrap gap-6 text-sm">
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                  <span className="font-semibold text-gray-700">
                    Total frames:
                  </span>
                  <span className="text-blue-600 font-bold">
                    {filteredImages.length}
                  </span>
                </div>
                {filteredImages.some(
                  (img) =>
                    img.frame_stamp !== undefined && img.frame_stamp !== null,
                ) && (
                  <div className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                    <span className="font-semibold text-gray-700">
                      Duration:
                    </span>
                    <span className="text-green-600 font-bold">
                      {(() => {
                        const timestamps = filteredImages
                          .map((img) => img.frame_stamp)
                          .filter(
                            (ts) => ts !== undefined && ts !== null,
                          ) as number[];
                        if (timestamps.length > 0) {
                          const min = Math.min(...timestamps);
                          const max = Math.max(...timestamps);
                          return `${Math.floor(min)}s - ${Math.floor(max)}s`;
                        }
                        return "N/A";
                      })()}
                    </span>
                  </div>
                )}
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
                  <span className="font-semibold text-gray-700">Video ID:</span>
                  <span className="text-purple-600 font-mono text-xs bg-purple-100 px-2 py-1 rounded">
                    {videoGroup.videoId}
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

function groupingVideos(videos: SearchResult[]): VideoGroup[] {
  console.log("🎬 Grouping videos:", videos.length, "videos");

  return videos.reduce((acc, video) => {
    // Extract video ID from file_path (primary strategy)
    let videoId: string;

    // Strategy 1: Extract video ID from file_path (e.g., L22_V014 from L22_V014/094.jpg)
    if (video.file_path) {
      const pathParts = video.file_path.split("/");
      if (pathParts.length >= 2) {
        videoId = pathParts[0]; // Get the folder name (e.g., L22_V014)
        console.log(
          `📹 Extracted video ID from file_path: ${video.file_path} -> ${videoId}`,
        );
      } else {
        videoId = video.file_path;
        console.log(`📹 Using full file_path as video ID: ${videoId}`);
      }
    } else {
      // Strategy 2: Fallback to image_id extraction
      const parts = video.image_id.split("_");
      if (parts.length >= 2) {
        videoId = parts.slice(0, 2).join("_");
        console.log(
          `📹 Extracted video ID from image_id: ${video.image_id} -> ${videoId}`,
        );
      } else {
        videoId = video.image_id;
        console.log(`📹 Using full image_id as video ID: ${videoId}`);
      }
    }

    // Strategy 3: Only use URL-based ID as last resort
    if (!video.file_path && video.watch_url) {
      const urlParts = video.watch_url.split("/");
      const lastPart = urlParts[urlParts.length - 1];
      if (lastPart) {
        videoId = lastPart.split("?")[0]; // Remove query parameters
        console.log(`📹 Using URL-based video ID: ${videoId}`);
      }
    }

    const existingGroup = acc.find((group) => group.videoId === videoId);
    if (existingGroup) {
      console.log(`📹 Adding to existing group: ${videoId}`);
      existingGroup.images.push(video);
      return acc;
    }
    console.log(`📹 Creating new group: ${videoId}`);
    acc.push({
      videoId,
      images: [video],
      videoUrl: video.watch_url || "#",
    });
    return acc;
  }, [] as VideoGroup[]);
}
