"use client";

import React from "react";
import Image from "next/image";
import dynamic from "next/dynamic";

// Dynamically import konva components with no SSR
const KonvaComponents = dynamic(() => import("./konva-components"), { 
  ssr: false,
  loading: () => <div>Loading canvas...</div>
});

interface DraggableSymbolProps {
  symbol: string;
  index?: number;
  isInGrid?: boolean;
  onRemove?: (index: number) => void;
  src?: string;
  alt?: string;
}

export default function DraggableSymbol({
  symbol,
  index,
  isInGrid = false,
  onRemove,
  src = `/palette/${symbol}.png`,
  alt,
}: DraggableSymbolProps) {
  // If component is rendered as HTML (not in Konva canvas)
  if (!isInGrid) {
    const handleDragStart = (e: React.DragEvent<HTMLDivElement>) => {
      e.dataTransfer.setData("symbol", symbol);
      if (src) {
        e.dataTransfer.setData("src", src);
      }
    };

    return (
      <div
        draggable
        onDragStart={handleDragStart}
        className={`
          inline-flex items-center justify-center
          m-0.5 rounded-md text-xs font-medium
         text-gray-700 cursor-move hover:bg-gray-200
          relative
        `}
      >
        <Image src={src || ""} alt={alt || ""} width={20} height={20} />
      </div>
    );
  }

  // If rendered inside Konva canvas, use dynamic components
  return <KonvaComponents symbol={symbol} index={index} onRemove={onRemove} src={src} />;
}
