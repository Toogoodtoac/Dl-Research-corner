"use client";

import React from "react";
import dynamic from "next/dynamic";

// Dynamically import the entire konva-based symbol grid to avoid SSR issues
const KonvaSymbolGrid = dynamic(() => import("./konva-symbol-grid"), { 
  ssr: false,
  loading: () => <div className="flex justify-center items-center p-8">Loading canvas grid...</div>
});

// Interface for positioned symbols
export interface PositionedSymbol {
  id: string;
  symbol: string;
  x: number;
  y: number;
  zIndex: number;
  width?: number;
  height?: number;
  rotation?: number;
  src?: string;
}

interface SymbolGridProps {
  onSearch: ({
    objectList,
    logic,
  }: {
    objectList: { class_name: string; bbox: number[] }[];
    logic?: "AND" | "OR";
  }) => Promise<void>;
}

export default function SymbolGrid({ onSearch }: SymbolGridProps) {
  // Render the konva-based grid only on the client side
  return <KonvaSymbolGrid onSearch={onSearch} />;
}
