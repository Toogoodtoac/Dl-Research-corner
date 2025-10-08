"use client";

import { useState } from "react";
import { temporalSearch, TemporalData, TemporalResult } from "@/services/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Loader2, Search, Video, Clock, Star } from "lucide-react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

interface TemporalSearchProps {
  onResultsFound?: (results: TemporalData) => void;
  onError?: (error: string) => void;
  onLoading?: (loading: boolean) => void;
  limit?: number;
}

export default function TemporalSearch({
  onResultsFound,
  onError,
  onLoading,
  limit = 20,
}: TemporalSearchProps) {
  const [query, setQuery] = useState("");
  const [model, setModel] = useState("beit3");
  const [isLoading, setIsLoading] = useState(false);
  const [results, setResults] = useState<TemporalData | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = async () => {
    if (!query.trim()) return;

    setIsLoading(true);
    setError(null);
    onLoading?.(true);

    try {
      const data = await temporalSearch({
        query: query.trim(),
        model,
        limit,
      });

      setResults(data);
      onResultsFound?.(data);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Search failed";
      setError(errorMessage);
      onError?.(errorMessage);
    } finally {
      setIsLoading(false);
      onLoading?.(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !isLoading) {
      handleSearch();
    }
  };

  const formatScore = (score: number) => {
    return (score * 100).toFixed(1);
  };

  return (
    <div className="space-y-6">
      {/* Search Input */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Video className="h-5 w-5" />
            Temporal Video Search
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-2">
            <Input
              placeholder="Describe a video sequence (e.g., 'A person walks into a room. They sit down at a table. They open a book.')"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyPress={handleKeyPress}
              className="flex-1"
              disabled={isLoading}
            />
            <Button onClick={handleSearch} disabled={isLoading || !query.trim()}>
              {isLoading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Search className="h-4 w-4" />
              )}
            </Button>
          </div>

          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <label className="text-sm font-medium">Model:</label>
              <Select value={model} onValueChange={setModel}>
                <SelectTrigger className="w-32">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="beit3">BEiT-3</SelectItem>
                  <SelectItem value="clip">CLIP</SelectItem>
                  <SelectItem value="longclip">LongCLIP</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Error Display */}
      {error && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="pt-6">
            <p className="text-red-600">{error}</p>
          </CardContent>
        </Card>
      )}

      {/* Results */}
      {results && (
        <div className="space-y-6">
          {/* Query Analysis */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Query Analysis</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <p className="text-sm text-gray-600">
                  Found {results.sentences.length} sentence(s) in your query:
                </p>
                <div className="space-y-1">
                  {results.sentences.map((sentence, index) => (
                    <div key={index} className="flex items-start gap-2">
                      <Badge variant="outline" className="mt-0.5">
                        {index + 1}
                      </Badge>
                      <p className="text-sm">{sentence}</p>
                    </div>
                  ))}
                </div>
                <p className="text-sm text-gray-600">
                  Candidate videos: {results.candidate_videos.length}
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Search Results */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Star className="h-5 w-5" />
                Search Results ({results.results.length})
              </CardTitle>
            </CardHeader>
            <CardContent>
              {results.results.length === 0 ? (
                <p className="text-gray-500 text-center py-8">
                  No matching video sequences found.
                </p>
              ) : (
                <div className="space-y-4">
                  {results.results.map((result, index) => (
                    <Card key={index} className="border-l-4 border-l-blue-500">
                      <CardContent className="pt-4">
                        <div className="flex items-start justify-between mb-3">
                          <div>
                            <h3 className="font-semibold text-lg">
                              Video: {result.video_id}
                            </h3>
                            <p className="text-sm text-gray-600">
                              {result.frames.length} frames matched
                            </p>
                          </div>
                          <Badge variant="secondary" className="flex items-center gap-1">
                            <Star className="h-3 w-3" />
                            {formatScore(result.score)}%
                          </Badge>
                        </div>

                        <div className="space-y-2">
                          <div className="flex items-center gap-2 text-sm text-gray-600">
                            <Clock className="h-4 w-4" />
                            <span>Frame sequence: {result.frames.join(" → ")}</span>
                          </div>
                          
                          {result.images.length > 0 && (
                            <div className="space-y-2">
                              <p className="text-sm font-medium">Frame Sequence:</p>
                              <div className="flex gap-2 overflow-x-auto">
                                {result.images.map((image, imgIndex) => {
                                  const imagePath = result.paths[imgIndex] || `${result.video_id}/${image}`;
                                  const imageUrl = `http://localhost:8000/data/${imagePath}`;
                                  return (
                                    <div key={imgIndex} className="flex-shrink-0">
                                      <img
                                        src={imageUrl}
                                        alt={`Frame ${result.frames[imgIndex]}`}
                                        className="w-20 h-20 object-cover rounded border"
                                        onError={(e) => {
                                          e.currentTarget.style.display = 'none';
                                        }}
                                      />
                                      <p className="text-xs text-center mt-1">{image}</p>
                                    </div>
                                  );
                                })}
                              </div>
                            </div>
                          )}

                          {result.paths.length > 0 && (
                            <div className="space-y-1">
                              <p className="text-sm font-medium">Paths:</p>
                              <div className="space-y-1">
                                {result.paths.map((path, pathIndex) => (
                                  <p key={pathIndex} className="text-xs text-gray-500 font-mono">
                                    {path}
                                  </p>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
