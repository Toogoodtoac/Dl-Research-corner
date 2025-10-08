"use client";

import { useState, FormEvent } from "react";
import { Search, Loader2, FileText } from "lucide-react";
import { searchOCR } from "@/services/api";
import type { SearchResult } from "@/services/api";

interface OCRSearchProps {
  onResultsFound: (results: SearchResult[]) => void;
  onError: (message: string) => void;
  onLoading: (isLoading: boolean) => void;
  limit: number;
}

export default function OCRSearch({
  onResultsFound,
  onError,
  onLoading,
  limit = 20,
}: OCRSearchProps) {
  const [query, setQuery] = useState("");
  const [isSearching, setIsSearching] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();

    if (!query.trim()) {
      return;
    }

    try {
      setIsSearching(true);
      onLoading(true);

      const results = await searchOCR({ query, limit });

      onResultsFound(results);

      if (results.length === 0) {
        onError(`No images found containing text "${query}"`);
      }
    } catch (error) {
      console.error("OCR search error:", error);
      onError("Failed to perform OCR search. Please try again.");
    } finally {
      setIsSearching(false);
      onLoading(false);
    }
  };

  return (
    <div className="bg-white shadow-md mt-6 p-4 border border-indigo-200 rounded-lg">
      <div className="flex items-center mb-3">
        <FileText className="mr-2 w-5 h-5 text-indigo-600" />
        <h2 className="font-medium text-lg">Text in Image Search</h2>
      </div>

      <p className="mb-4 text-gray-600 text-sm">
        Find images containing specific text or words using OCR technology.
      </p>

      <form onSubmit={handleSubmit}>
        <div className="relative">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Enter text to find in images..."
            className="px-4 py-2 pr-4 pl-10 border border-gray-300 focus:border-transparent rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 w-full"
            disabled={isSearching}
          />
          <Search className="top-1/2 left-3 absolute w-4 h-4 text-gray-400 -translate-y-1/2 transform" />

          <div className="top-1/2 right-3 absolute -translate-y-1/2 transform">
            <span className="text-gray-500 text-xs">Max: {limit}</span>
          </div>
        </div>

        <div className="flex justify-end mt-3">
          <button
            type="submit"
            disabled={isSearching || !query.trim()}
            className="flex items-center bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 px-4 py-2 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 text-white transition-colors"
          >
            {isSearching ? (
              <>
                <Loader2 className="mr-2 w-4 h-4 animate-spin" />
                Searching...
              </>
            ) : (
              <>
                <Search className="mr-2 w-4 h-4" />
                Find Text
              </>
            )}
          </button>
        </div>
      </form>

      <div className="bg-gray-50 mt-3 p-2 border border-gray-100 rounded text-gray-500 text-xs">
        <p className="mb-1 font-medium">Example searches:</p>
        <p>• Words: &quot;exit&quot;, &quot;emergency&quot;, &quot;entrance&quot;</p>
        <p>• Numbers: &quot;2023&quot;, &quot;Room 101&quot;</p>
        <p>• Signs: &quot;stop&quot;, &quot;no parking&quot;, &quot;open&quot;</p>
      </div>
    </div>
  );
}
