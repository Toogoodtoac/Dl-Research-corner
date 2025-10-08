"use client";

import type React from "react";

import { useState } from "react";
import { Search } from "lucide-react";

interface SearchBarProps {
  onSearch: (query: string) => void;
  size?: "default" | "large";
  value?: string;
  onChange?: (query: string) => void;
}

export default function SearchBar({
  onSearch,
  size = "default",
  value,
  onChange,
}: SearchBarProps) {
  const [internalQuery, setInternalQuery] = useState("");
  const query = value !== undefined ? value : internalQuery;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      onSearch(query.trim());
    }
  };

  const isLarge = size === "large";

  return (
    <div className="w-full">
      <form onSubmit={handleSubmit} className="relative">
        <input
          type="text"
          value={query}
          onChange={(e) => {
            const newValue = e.target.value;
            if (onChange) {
              onChange(newValue);
            } else {
              setInternalQuery(newValue);
            }
          }}
          placeholder="Search for videos..."
          className={`
            w-full border border-gray-300 rounded-2xl focus:outline-none focus:ring-2 focus:ring-gray-500 focus:border-transparent
            ${isLarge ? "px-6 py-2 pr-14 text-lg shadow-lg" : "px-4 py-1 pr-12 text-base"}
          `}
        />
        <button
          type="submit"
          aria-label="Search"
          className={`
            absolute right-2 top-1/2 transform -translate-y-1/2 text-gray-500 hover:text-gray-700
            ${isLarge ? "p-2" : "p-1.5"}
          `}
        >
          <Search className={isLarge ? "h-6 w-6" : "h-5 w-5"} />
        </button>
      </form>
    </div>
  );
}
