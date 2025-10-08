"use client";

import { useState, useEffect, useRef } from "react";
import { useSearchParams } from "next/navigation";
import SearchBar from "@/components/search-bar";
import SymbolGrid from "@/components/symbol-grid";
import SearchResults from "@/components/search-results";
import Link from "next/link";
import { Search, AlertTriangle } from "lucide-react";
import {
  searchImages,
  searchNeighbor,
  visualSearch,
  type SearchResult,
} from "@/services/api";
import { InitialSearchIcon } from "@/components/empty-state/icons";
import OCRSearch from "@/components/ocr-search";
import TemporalSearch from "@/components/temporal-search";

// Interface for positioned symbols (currently unused)
// interface PositionedSymbol {
//   id: string;
//   symbol: string;
//   x: number;
//   y: number;
//   zIndex: number;
// }

// Search state interface for persistence
interface SearchState {
  query: string;
  results: SearchResult[];
  limit: number;
  selectedModel: string;
  searchType: string;
  timestamp: number;
}

// Storage key for search state
const SEARCH_STATE_KEY = "video-search-state";

function EmptyState({ isSearchQuery }: { isSearchQuery: boolean }) {
  return (
    <div className="flex flex-col justify-center items-center bg-white shadow-lg p-8 md:p-12 border border-blue-200 rounded-lg">
      {isSearchQuery ? (
        <>
          <div className="mb-6 w-32 h-32 text-gray-300">
            <InitialSearchIcon />
          </div>
          <h3 className="mb-2 font-semibold text-gray-700 text-lg">
            No matching results
          </h3>
          <p className="mb-6 max-w-md text-gray-500 text-center">
            We couldn&apos;t find any videos matching your search. Try using
            different keywords or criteria.
          </p>
        </>
      ) : (
        <>
          <div className="mb-6 w-32 h-32 text-blue-200">
            <InitialSearchIcon />
          </div>
          <h3 className="mb-2 font-semibold text-gray-700 text-lg">
            Start your image discovery
          </h3>
          <p className="mb-6 max-w-md text-gray-500 text-center">
            Search for videos using the search bar above or try the symbol grid
            for a more visual approach to finding what you need.
          </p>
        </>
      )}
    </div>
  );
}

export default function Home() {
  const searchParams = useSearchParams();

  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isHeaderFixed, setIsHeaderFixed] = useState(false);
  const [limit, setLimit] = useState(20); // This will be overridden by state restoration
  const [isLimitTooltipOpen, setIsLimitTooltipOpen] = useState(false);
  const [selectedModel, setSelectedModel] = useState("clip");
  const [searchType, setSearchType] = useState("normal");

  const heroSectionRef = useRef<HTMLDivElement>(null);
  const headerRef = useRef<HTMLDivElement>(null);
  const mainContentRef = useRef<HTMLDivElement>(null);
  const [focusId, setFocusId] = useState<string | null>(null);

  // State persistence functions
  const saveSearchState = (state: Partial<SearchState>) => {
    try {
      const currentState = getSearchState();
      const newState: SearchState = {
        ...currentState,
        ...state,
        timestamp: Date.now(),
      };
      localStorage.setItem(SEARCH_STATE_KEY, JSON.stringify(newState));
    } catch (error) {
      console.warn("Failed to save search state:", error);
    }
  };

  const getSearchState = (): SearchState => {
    try {
      const stored = localStorage.getItem(SEARCH_STATE_KEY);
      if (stored) {
        const parsed = JSON.parse(stored);
        // Check if state is not too old (24 hours)
        if (Date.now() - parsed.timestamp < 24 * 60 * 60 * 1000) {
          return parsed;
        }
      }
    } catch (error) {
      console.warn("Failed to parse search state:", error);
    }
    return {
      query: "",
      results: [],
      limit: 20, // Default limit - will be overridden by user selection
      selectedModel: "clip",
      searchType: "normal",
      timestamp: Date.now(),
    };
  };

  const restoreSearchState = async () => {
    try {
      const state = getSearchState();
      console.log("🔍 Restoring search state:", state);

      // Always restore settings if they exist in localStorage
      if (state.limit) {
        console.log("📊 Setting limit to:", state.limit);
        setLimit(state.limit);
      } else {
        console.log("⚠️ No limit found in saved state, using default 20");
      }
      if (state.selectedModel) {
        console.log("🤖 Setting model to:", state.selectedModel);
        setSelectedModel(state.selectedModel);
      }
      if (state.searchType) {
        console.log("🔍 Setting search type to:", state.searchType);
        setSearchType(state.searchType);
      }

      // Restore search query and results if they exist
      if (state.query) {
        console.log("🔍 Restoring query:", state.query);
        setSearchQuery(state.query);

        // Always re-fetch results to ensure consistency with the restored settings
        const currentLimit = state.limit || 20;
        const currentModel = state.selectedModel || "clip";
        const currentSearchType = state.searchType || "normal";
        
        console.log(
          `🔄 Re-fetching with restored settings: limit=${currentLimit}, model=${currentModel}, searchType=${currentSearchType}`,
        );
        
        // Use the restored model directly instead of relying on state
        await handleTextSearchWithLimitAndModel(state.query, currentLimit, currentModel);

        return true;
      }

      return true; // Always return true since we restored settings
    } catch (error) {
      console.warn("Failed to restore search state:", error);
      return false;
    }
  };

  // Restore state from URL params and localStorage on mount
  useEffect(() => {
    const initializeState = async () => {
      // First, try to restore from URL params
      const urlQuery = searchParams.get("q");
      const urlLimit = searchParams.get("limit");
      const urlModel = searchParams.get("model");
      const urlType = searchParams.get("type");

      if (urlQuery) {
        // If we have URL params, use them and perform search
        setSearchQuery(urlQuery);
        if (urlLimit) setLimit(Number(urlLimit));
        if (urlModel) setSelectedModel(urlModel);
        if (urlType) setSearchType(urlType);

        // Perform the search automatically
        handleTextSearch(urlQuery);
      } else {
        // If no URL params, try to restore from localStorage
        await restoreSearchState();
        // Don't override with defaults - let the restored state be the source of truth
      }
    };

    initializeState();
  }, []);

  // Update URL when search state changes
  useEffect(() => {
    if (searchQuery) {
      const params = new URLSearchParams();
      params.set("q", searchQuery);
      params.set("limit", limit.toString());
      params.set("model", selectedModel);
      params.set("type", searchType);

      // Update URL without triggering navigation
      const newUrl = `${window.location.pathname}?${params.toString()}`;
      window.history.replaceState({}, "", newUrl);
    }
  }, [searchQuery, limit, selectedModel, searchType]);

  // Save settings to localStorage whenever they change (even without search)
  useEffect(() => {
    // Always save the current state to preserve user preferences
    saveSearchState({
      limit,
      selectedModel,
      searchType,
    });
  }, [limit, selectedModel, searchType]);

  // Handle scroll events for header animation
  useEffect(() => {
    const handleScroll = () => {
      if (heroSectionRef.current) {
        const heroHeight = heroSectionRef.current.offsetHeight;
        const scrollPosition = window.scrollY;

        if (scrollPosition > heroHeight - 10) {
          setIsHeaderFixed(true);
        } else {
          setIsHeaderFixed(false);
        }
      }
    };

    window.addEventListener("scroll", handleScroll);
    return () => {
      window.removeEventListener("scroll", handleScroll);
    };
  }, []);

  // Handle text-based search
  const handleTextSearch = async (query: string) => {
    return handleTextSearchWithLimit(query, limit);
  };

  // Handle text-based search with specific limit and model
  const handleTextSearchWithLimitAndModel = async (
    query: string,
    searchLimit: number,
    model: string,
  ) => {
    console.log("🚀 handleTextSearchWithLimitAndModel called with:", {
      query,
      searchLimit,
      model,
    });
    setIsLoading(true);
    setSearchQuery(query);
    setError(null);
    setFocusId(null);
    try {
      console.log("🔍 Starting search for:", query, "with limit:", searchLimit, "and model:", model);
      const searchParams = {
        query,
        limit: searchLimit,
        model: model,
      };
      console.log("📤 Calling searchImages with params:", searchParams);
      const results = await searchImages(searchParams);
      console.log("📊 Search results received:", results);
      console.log("📊 Results length:", results.length);
      console.log("📊 Expected length:", searchLimit);
      console.log("📊 First result:", results[0]);
      setSearchResults(results);

      // Save search state after successful search
      console.log(
        `💾 Saving search state: query="${query}", results=${results.length}, limit=${searchLimit}, model=${model}`,
      );
      saveSearchState({
        query,
        results,
        limit: searchLimit,
        selectedModel: model,
        searchType,
      });

      // Scroll to results if on mobile
      if (mainContentRef.current && window.innerWidth < 1024) {
        mainContentRef.current.scrollIntoView({ behavior: "smooth" });
      }
    } catch (err) {
      setError("Failed to perform search. Please try again.");
      console.error("Search error:", err);
    } finally {
      setIsLoading(false);
    }
  };

  // Handle text-based search with specific limit (uses current state)
  const handleTextSearchWithLimit = async (
    query: string,
    searchLimit: number,
  ) => {
    return handleTextSearchWithLimitAndModel(query, searchLimit, selectedModel);
  };

  const handleNeighborSearch = async (id: string) => {
    setIsLoading(true);
    setError(null);

    try {
      const results = await searchNeighbor({ id, limit, model: selectedModel });
      setSearchResults(results);
      setFocusId(id);

      // Save search state after successful neighbor search
      saveSearchState({
        query: searchQuery,
        results,
        limit,
        selectedModel,
        searchType,
      });
    } catch (err) {
      setError("Failed to perform neighbor search. Please try again.");
      console.error("Neighbor search error:", err);
    } finally {
      setIsLoading(false);
    }
  };

  // Handle visual search
  const handleVisualSearch = async ({
    objectList,
    logic = "AND",
  }: {
    objectList: { class_name: string; bbox: number[] }[];
    logic?: "AND" | "OR";
  }) => {
    setFocusId(null);

    setIsLoading(true);
    setError(null);

    try {
      const results = await visualSearch({
        objectList,
        logic,
        limit,
        model: selectedModel,
      });
      setSearchResults(results);

      // Save search state after successful visual search
      saveSearchState({
        query: `Visual search: ${objectList.map((obj) => obj.class_name).join(", ")}`,
        results,
        limit,
        selectedModel,
        searchType,
      });

      // Scroll to results if on mobile
      if (mainContentRef.current && window.innerWidth < 1024) {
        mainContentRef.current.scrollIntoView({ behavior: "smooth" });
      }
    } catch (err) {
      setError("Failed to perform visual search. Please try again.");
      console.error("Visual search error:", err);
    } finally {
      setIsLoading(false);
    }
  };

  // Handle OCR text search
  const handleOCRSearch = async (results: SearchResult[]) => {
    setSearchResults(results);
    setFocusId(null);

    // Save search state after successful OCR search
    saveSearchState({
      query: "OCR text search",
      results,
      limit,
      selectedModel,
      searchType,
    });

    // Scroll to results if on mobile
    if (mainContentRef.current && window.innerWidth < 1024) {
      mainContentRef.current.scrollIntoView({ behavior: "smooth" });
    }
  };

  // Handle temporal search results
  const handleTemporalSearch = async (temporalData: any) => {
    // Convert temporal results to search results format for display
    const convertedResults: SearchResult[] = [];
    
    temporalData.results.forEach((result: any) => {
      result.frames.forEach((frame: number, index: number) => {
        const imagePath = result.paths[index] || `${result.video_id}/${result.images[index]}`;
        const imageUrl = `http://localhost:8000/data/${imagePath}`;
        
        convertedResults.push({
          image_id: `${result.video_id}_${frame}`,
          score: result.score / 100, // Convert percentage to 0-1 range
          video_id: result.video_id,
          shot_index: frame,
          file_path: imagePath,
          image_url: imageUrl,
        });
      });
    });

    setSearchResults(convertedResults);
    setFocusId(null);

    // Save search state after successful temporal search
    saveSearchState({
      query: searchQuery,
      results: convertedResults,
      limit,
      selectedModel,
      searchType,
    });

    // Scroll to results if on mobile
    if (mainContentRef.current && window.innerWidth < 1024) {
      mainContentRef.current.scrollIntoView({ behavior: "smooth" });
    }
  };

  // Handle limit change
  const handleLimitChange = (newLimit: number) => {
    console.log(`🔄 Limit changed from ${limit} to ${newLimit}`);
    setLimit(newLimit);

    // Save the new limit immediately to localStorage
    saveSearchState({ limit: newLimit });

    // Perform a new search with the updated limit if we have an active query
    if (searchQuery) {
      console.log(
        `🔄 Re-searching with new limit ${newLimit} for query: ${searchQuery}`,
      );
      handleTextSearchWithLimit(searchQuery, newLimit);
    }
  };

  // Handle model change
  const handleModelChange = (newModel: string) => {
    console.log(`🔄 Model changed from ${selectedModel} to ${newModel}`);
    setSelectedModel(newModel);
    saveSearchState({ selectedModel: newModel });

    // Perform a new search with the updated model if we have an active query
    if (searchQuery) {
      console.log(
        `🔄 Re-searching with new model ${newModel} for query: ${searchQuery}`,
      );
      handleTextSearchWithLimitAndModel(searchQuery, limit, newModel);
    }
  };

  // Handle search type change
  const handleSearchTypeChange = (newSearchType: string) => {
    console.log(`🔄 Search type changed from ${searchType} to ${newSearchType}`);
    setSearchType(newSearchType);
    saveSearchState({ searchType: newSearchType });

    // Perform a new search with the updated search type if we have an active query
    if (searchQuery) {
      console.log(
        `🔄 Re-searching with new search type ${newSearchType} for query: ${searchQuery}`,
      );
      handleTextSearchWithLimitAndModel(searchQuery, limit, selectedModel);
    }
  };

  // Toggle limit tooltip
  const toggleLimitTooltip = () => {
    setIsLimitTooltipOpen(!isLimitTooltipOpen);
  };

  const clearSearch = () => {
    setSearchQuery("");
    setSearchResults([]);
    setFocusId(null);
    saveSearchState({ query: "", results: [], limit: 20 });
    setError(null);
  };

  return (
    <>
      {/* Hero Section with Search */}
      <div ref={heroSectionRef} className="pt-16 pb-4">
        <div className="mx-auto container-md">
          <div className="mx-auto max-w-3xl text-center">
            <h1 className="mb-4 font-bold text-gray-900 text-4xl">
              Video Search
            </h1>
            <div className="mb-2">
              <SearchBar 
                onSearch={handleTextSearch} 
                size="large"
                value={searchQuery}
                onChange={setSearchQuery}
              />
            </div>

            {/* Model and Search Type Selection */}
            <div className="flex flex-col sm:flex-row justify-center items-center space-y-3 sm:space-y-0 sm:space-x-8 mb-6">
              <div className="flex items-center form-control-group">
                <label
                  htmlFor="model-select"
                  className="form-label text-sm font-medium"
                >
                  Model:
                </label>
                <select
                  id="model-select"
                  value={selectedModel}
                  onChange={(e) => handleModelChange(e.target.value)}
                  className="form-select bg-white text-sm"
                  disabled={isLoading}
                >
                  <option value="clip">clip</option>
                  <option value="longclip">longclip</option>
                  <option value="clip2video">clip2video</option>
                  <option value="beit3">beit3</option>
                  <option value="all">all</option>
                </select>
              </div>

              <div className="flex items-center form-control-group">
                <label
                  htmlFor="search-type-select"
                  className="form-label text-sm font-medium"
                >
                  Search Type:
                </label>
                <select
                  id="search-type-select"
                  value={searchType}
                  onChange={(e) => handleSearchTypeChange(e.target.value)}
                  className="form-select bg-white text-sm"
                  disabled={isLoading}
                >
                  <option value="normal">Normal Search</option>
                  <option value="temporal">Temporal Search</option>
                </select>
              </div>
            </div>

            <div className="flex justify-center items-center space-x-8">
              <Link
                href="/find-image"
                className="flex items-center text-gray-600 hover:text-gray-900"
              >
                <Search className="mr-2 w-4 h-4" />
                Find image by ID
              </Link>

              {/* Limit selector in hero section */}
              <div className="relative flex items-center">
                <label htmlFor="hero-limit" className="form-label text-sm">
                  Results:
                </label>
                <select
                  id="hero-limit"
                  value={limit}
                  onChange={(e) => handleLimitChange(Number(e.target.value))}
                  className="form-select bg-white text-sm"
                  disabled={isLoading}
                >
                  <option value={10}>10</option>
                  <option value={20}>20</option>
                  <option value={50}>50</option>
                  <option value={100}>100</option>
                </select>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Fixed Header (appears on scroll) */}
      <header
        ref={headerRef}
        className={`w-full bg-white z-50 transition-all duration-300 ease-in-out ${
          isHeaderFixed ? "fixed top-0 shadow-md" : "absolute -top-20 opacity-0"
        }`}
      >
        <div className="flex lg:flex-row flex-col items-center mx-auto px-4 py-3 container">
          <h1
            className={`text-2xl font-bold transition-all duration-300 ease-in-out ${
              isHeaderFixed ? "lg:mr-6 text-xl" : "mb-4 lg:mb-0 text-3xl"
            }`}
          >
            Video Search
          </h1>

          <div
            className={`w-full transition-all duration-300 ${isHeaderFixed ? "max-w-xl lg:mr-8" : ""}`}
          >
            <SearchBar 
              onSearch={handleTextSearch} 
              value={searchQuery}
              onChange={setSearchQuery}
            />
          </div>

          {/* Model and Search Type Selection in Fixed Header */}
          <div className="flex flex-col sm:flex-row items-center space-y-2 sm:space-y-0 sm:space-x-6 mt-4 lg:mt-0">
            <div className="flex items-center">
              <label
                htmlFor="header-model-select"
                className="mr-3 text-gray-600 text-xs font-medium"
              >
                Model:
              </label>
              <select
                id="header-model-select"
                value={selectedModel}
                onChange={(e) => handleModelChange(e.target.value)}
                className="bg-white px-3 py-1.5 border border-gray-300 focus:border-transparent rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-xs"
                disabled={isLoading}
              >
                <option value="clip">clip</option>
                <option value="longclip">longclip</option>
                <option value="clip2video">clip2video</option>
                <option value="beit3">beit3</option>
                <option value="all">all</option>
              </select>
            </div>

            <div className="flex items-center">
              <label
                htmlFor="header-search-type-select"
                className="mr-3 text-gray-600 text-xs font-medium"
              >
                Type:
              </label>
              <select
                id="header-search-type-select"
                value={searchType}
                onChange={(e) => setSearchType(e.target.value)}
                className="bg-white px-3 py-1.5 border border-gray-300 focus:border-transparent rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-xs"
                disabled={isLoading}
              >
                <option value="normal">Normal</option>
                <option value="temporal">Temporal</option>
              </select>
            </div>
          </div>

          <div className="flex items-center space-x-4 mt-4 lg:mt-0 ml-auto">
            <Link
              href="/find-image"
              className="flex items-center text-gray-600 hover:text-gray-900"
            >
              <Search className="mr-1 w-4 h-4" />
              Find by ID
            </Link>

            {/* Limit selector in fixed header */}
            <div className="relative">
              <div className="flex items-center">
                <button
                  type="button"
                  onClick={toggleLimitTooltip}
                  className="flex items-center space-x-1 bg-gray-50 px-2 py-1 border border-gray-200 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-600 hover:text-gray-900 text-sm"
                  disabled={isLoading}
                >
                  <span>{limit} Results</span>
                  <svg
                    className="w-4 h-4"
                    viewBox="0 0 20 20"
                    fill="currentColor"
                  >
                    <path
                      fillRule="evenodd"
                      d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z"
                      clipRule="evenodd"
                    />
                  </svg>
                </button>
              </div>

              {isLimitTooltipOpen && (
                <div className="right-0 z-50 absolute bg-white shadow-lg mt-1 py-1 border border-gray-200 rounded-md w-48">
                  <div className="px-3 py-2 border-gray-100 border-b">
                    <p className="font-medium text-gray-500 text-xs">
                      Maximum number of results
                    </p>
                  </div>
                  {[10, 20, 50, 100].map((value) => (
                    <button
                      key={value}
                      onClick={() => {
                        handleLimitChange(value);
                        setIsLimitTooltipOpen(false);
                      }}
                      className={`w-full text-left px-4 py-2 text-sm hover:bg-gray-50 ${
                        limit === value
                          ? "bg-blue-50 text-blue-600"
                          : "text-gray-700"
                      }`}
                    >
                      {value} results
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Spacer for fixed header */}
      {isHeaderFixed && <div className="h-[72px] lg:h-[60px]"></div>}

      {/* Main Content Area */}
      <div
        ref={mainContentRef}
        className="flex lg:flex-row flex-col lg:space-x-6 mx-auto px-4 py-4"
      >
        {/* Left Section - Visual Search and OCR Search (1/5 width) */}
        <aside className="mb-6 lg:mb-0 lg:w-1/5">
          <SymbolGrid onSearch={handleVisualSearch} />

          {/* OCR Search Component */}
          <OCRSearch
            onResultsFound={handleOCRSearch}
            onError={setError}
            onLoading={setIsLoading}
            limit={limit}
          />
        </aside>

        {/* Right Section - Search Results (4/5 width) */}
        <main className="lg:w-4/5">
          {error && (
            <div className="flex items-start bg-red-50 mb-6 px-4 py-3 border border-red-200 rounded-lg text-red-700">
              <AlertTriangle className="flex-shrink-0 mt-0.5 mr-2 w-5 h-5" />
              <p>{error}</p>
            </div>
          )}

          {searchType === "temporal" ? (
            <TemporalSearch
              onResultsFound={handleTemporalSearch}
              onError={setError}
              onLoading={setIsLoading}
              limit={limit}
            />
          ) : isLoading ? (
            <div className="flex flex-col justify-center items-center bg-white shadow-lg py-12 rounded-lg">
              <div className="mb-4 border-gray-900 border-t-2 border-b-2 rounded-full w-12 h-12 animate-spin"></div>
              <p className="text-gray-500">Searching for videos...</p>
            </div>
          ) : searchResults.length > 0 ? (
            <SearchResults
              results={searchResults}
              onMoreResults={handleNeighborSearch}
              focusId={focusId}
              limit={limit}
              onClearSearch={clearSearch}
            />
          ) : (
            <EmptyState isSearchQuery={!!searchQuery} />
          )}
        </main>
      </div>
    </>
  );
}
