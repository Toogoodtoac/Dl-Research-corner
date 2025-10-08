"use client";

import React, { useState, useRef, useEffect, useCallback } from "react";
import DraggableSymbol from "./draggable-symbol";
import {
  Stage,
  Layer,
  Image as KonvaImage,
  Line,
  Transformer,
} from "react-konva";
import Konva from "konva";
import { ObjectList as availableSymbols } from "../constants/objects";
import { Search, Trash, Undo } from "lucide-react";
import useImage from "use-image";

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

interface KonvaSymbolGridProps {
  onSearch: ({
    objectList,
    logic,
  }: {
    objectList: { class_name: string; bbox: number[] }[];
    logic?: "AND" | "OR";
  }) => Promise<void>;
}

// URLImage component for Konva
const URLImage = ({
  image,
  isSelected,
  onSelect,
  onChange,
}: {
  image: PositionedSymbol;
  isSelected: boolean;
  onSelect: () => void;
  onChange: (newAttrs: Partial<PositionedSymbol>) => void;
}) => {
  const [img] = useImage(image.src || "");
  const shapeRef = useRef<Konva.Image | null>(null);
  const trRef = useRef<Konva.Transformer | null>(null);

  useEffect(() => {
    if (isSelected && trRef.current && shapeRef.current) {
      trRef.current.nodes([shapeRef.current]);
      trRef.current.getLayer()?.batchDraw();
    }
  }, [isSelected]);

  const handleDragStart = () => {
    if (shapeRef.current) {
      shapeRef.current.moveToTop();
      if (trRef.current) {
        trRef.current.moveToTop();
      }
    }
  };

  return (
    <>
      <KonvaImage
        image={img}
        x={image.x}
        y={image.y}
        width={image.width || 50}
        height={image.height || 50}
        rotation={image.rotation || 0}
        offsetX={(image.width || 50) / 2}
        offsetY={(image.height || 50) / 2}
        draggable
        onClick={onSelect}
        onTap={onSelect}
        ref={shapeRef}
        onDragStart={handleDragStart}
        onDragEnd={(e: Konva.KonvaEventObject<DragEvent>) => {
          onChange({
            x: e.target.x(),
            y: e.target.y(),
          });
        }}
        onTransformEnd={() => {
          const node = shapeRef.current;
          if (node) {
            const scaleX = node.scaleX();
            const scaleY = node.scaleY();
            node.scaleX(1);
            node.scaleY(1);
            onChange({
              x: node.x(),
              y: node.y(),
              width: Math.max(5, node.width() * scaleX),
              height: Math.max(5, node.height() * scaleY),
              rotation: node.rotation(),
            });
          }
        }}
      />
      {isSelected && (
        <Transformer
          ref={trRef}
          boundBoxFunc={(oldBox: Konva.Box, newBox: Konva.Box) => {
            if (newBox.width < 5 || newBox.height < 5) {
              return oldBox;
            }
            return newBox;
          }}
          rotateEnabled={true}
          enabledAnchors={[
            "top-left",
            "top-right",
            "bottom-left",
            "bottom-right",
          ]}
        />
      )}
    </>
  );
};

// Grid Layer component
const GridLayer = ({
  cellWidth,
  cellHeight,
  gridSize,
}: {
  cellWidth: number;
  cellHeight: number;
  gridSize: number;
}) => {
  return (
    <Layer>
      {Array.from({ length: gridSize - 1 }, (_, i) => (
        <React.Fragment key={i}>
          <Line
            points={[
              (i + 1) * cellWidth,
              0,
              (i + 1) * cellWidth,
              cellHeight * gridSize,
            ]}
            stroke="gray"
            strokeWidth={0.5}
            dash={[5, 5]}
          />
          <Line
            points={[
              0,
              (i + 1) * cellHeight,
              cellWidth * gridSize,
              (i + 1) * cellHeight,
            ]}
            stroke="gray"
            strokeWidth={0.5}
            dash={[5, 5]}
          />
        </React.Fragment>
      ))}
    </Layer>
  );
};

const MemoGridLayer = React.memo(GridLayer);

export default function KonvaSymbolGrid({ onSearch }: KonvaSymbolGridProps) {
  // State for positioned symbols in the grid
  const [positionedSymbols, setPositionedSymbols] = useState<
    PositionedSymbol[]
  >([]);
  // Reference to the grid container
  const gridRef = useRef<HTMLDivElement>(null);
  // State for the highest z-index used
  const [highestZIndex, setHighestZIndex] = useState(1);
  // State for grid cell highlighting
  const [highlightedCell, setHighlightedCell] = useState<{
    row: number;
    col: number;
  } | null>(null);
  // State for grid dimensions
  const [gridDimensions, setGridDimensions] = useState({
    width: 0,
    height: 0,
    cellSize: 0,
  });
  // State for showing grid lines
  const [showGridLines, setShowGridLines] = useState(true);
  // State for selected symbol
  const [selectedId, setSelectedId] = useState<string | null>(null);
  // State for search logic
  const [searchLogic, setSearchLogic] = useState<"AND" | "OR">("AND");
  // State for enabled/disabled
  const [isEnabled, setIsEnabled] = useState(true);
  // Reference to Konva stage
  const stageRef = useRef<Konva.Stage | null>(null);
  // State for hover state
  const [isOver, setIsOver] = useState(false);

  // Update grid dimensions on window resize
  useEffect(() => {
    const updateGridDimensions = () => {
      if (gridRef.current) {
        const width = gridRef.current.offsetWidth;
        const height = width; // Make it square
        const cellSize = width / 8; // 8x8 grid
        setGridDimensions({ width, height, cellSize });
      }
    };

    updateGridDimensions();
    window.addEventListener("resize", updateGridDimensions);

    return () => {
      window.removeEventListener("resize", updateGridDimensions);
    };
  }, []);

  // Handle drag over for highlighting
  const handleDragOver = useCallback(
    (e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      setIsOver(true);

      if (gridRef.current && showGridLines) {
        const gridRect = gridRef.current.getBoundingClientRect();

        // Calculate position relative to the grid
        const x = e.clientX - gridRect.left;
        const y = e.clientY - gridRect.top;

        // Calculate which cell we're hovering over
        const col = Math.floor(x / gridDimensions.cellSize);
        const row = Math.floor(y / gridDimensions.cellSize);

        // Only update if we're within bounds
        if (col >= 0 && col < 8 && row >= 0 && row < 8) {
          setHighlightedCell({ row, col });
        } else {
          setHighlightedCell(null);
        }
      }
    },
    [gridDimensions, showGridLines],
  );

  // Handle drop for adding symbols
  const handleDrop = useCallback(
    (e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      setIsOver(false);
      setHighlightedCell(null);

      if (!gridRef.current) return;

      const symbol = e.dataTransfer.getData("symbol");
      const src = e.dataTransfer.getData("src") || "";

      if (!symbol) return;

      const gridRect = gridRef.current.getBoundingClientRect();

      // Calculate position relative to the grid
      const x = e.clientX - gridRect.left;
      const y = e.clientY - gridRect.top;

      // Ensure the position is within grid bounds
      const boundedX = Math.max(0, Math.min(x, gridDimensions.width - 20));
      const boundedY = Math.max(0, Math.min(y, gridDimensions.height - 20));

      // Create a new positioned symbol
      const newSymbol: PositionedSymbol = {
        id: `${symbol}-${Date.now()}`,
        symbol,
        x: boundedX,
        y: boundedY,
        zIndex: highestZIndex + 1,
        width: gridDimensions.cellSize || 50,
        height: gridDimensions.cellSize || 50,
        rotation: 0,
        src,
      };

      setPositionedSymbols((prev) => [...prev, newSymbol]);
      setHighestZIndex((prev) => prev + 1);
    },
    [gridDimensions, highestZIndex],
  );

  // Handle removing a symbol (currently unused)
  // const handleRemoveSymbol = (id: string) => {
  //   const index = positionedSymbols.findIndex((s) => s.id === id);
  //   if (index !== -1) {
  //     setPositionedSymbols((prev) => prev.filter((s) => s.id !== id));
  //   }
  // };

  // Bring a symbol to the front when clicked
  const bringToFront = (id: string) => {
    setPositionedSymbols((prev) => {
      const newSymbols = [...prev];
      const index = newSymbols.findIndex((s) => s.id === id);

      if (index !== -1) {
        const symbol = newSymbols[index];
        const newZIndex = highestZIndex + 1;
        newSymbols[index] = { ...symbol, zIndex: newZIndex };
        setHighestZIndex(newZIndex);
      }

      return newSymbols;
    });
  };

  // Handle changes to symbol attributes (position, size, rotation)
  const handleSymbolChange = (
    id: string,
    newAttrs: Partial<PositionedSymbol>,
  ) => {
    setPositionedSymbols(
      positionedSymbols.map((symbol) =>
        symbol.id === id ? { ...symbol, ...newAttrs } : symbol,
      ),
    );
  };

  // Clear all symbols
  const handleClear = () => {
    setPositionedSymbols([]);
    setSelectedId(null);
  };

  // Reset to defaults
  const handleReset = () => {
    handleClear();
    setSearchLogic("AND");
    setIsEnabled(true);
  };

  // Handle search with formatted data for API
  const handleSearch = () => {
    if (!isEnabled || positionedSymbols.length === 0) return;

    // Format data for the detection search API
    const objectList = positionedSymbols.map((symbol) => {
      // Extract class name from symbol
      const class_name = symbol.symbol;

      // Calculate normalized coordinates
      const width = gridDimensions.width || 240;
      const height = gridDimensions.height || 240;
      const scaleX = 1280 / width;
      const scaleY = 720 / height;

      return {
        bbox: [
          (symbol.x - (symbol.width || 50) / 2) * scaleX,
          (symbol.y - (symbol.height || 50) / 2) * scaleY,
          (symbol.x + (symbol.width || 50) / 2) * scaleX,
          (symbol.y + (symbol.height || 50) / 2) * scaleY,
        ],
        class_name: class_name,
      };
    });

    console.log(objectList);
    // Call the parent's onSearch with the formatted data
    onSearch({ objectList, logic: searchLogic });
  };

  // Check for deselect when clicking outside of objects
  const checkDeselect = (
    e: Konva.KonvaEventObject<MouseEvent>,
  ) => {
    if (e.target === e.target.getStage()) {
      setSelectedId(null);
    }
  };

  // Generate grid cells for the 8x8 grid (for HTML5 drag and drop fallback)
  const renderGridCells = () => {
    if (!showGridLines) return null;

    const cells = [];
    for (let row = 0; row < 8; row++) {
      for (let col = 0; col < 8; col++) {
        const isHighlighted =
          highlightedCell?.row === row && highlightedCell?.col === col;
        cells.push(
          <div
            key={`cell-${row}-${col}`}
            className={`absolute border border-gray-200 ${isHighlighted ? "bg-gray-100" : ""}`}
            style={{
              left: col * gridDimensions.cellSize,
              top: row * gridDimensions.cellSize,
              width: gridDimensions.cellSize,
              height: gridDimensions.cellSize,
            }}
          />,
        );
      }
    }
    return cells;
  };

  return (
    <div className="bg-white shadow p-3 border border-red-200 rounded-lg">
      <h2 className="mb-3 font-semibold text-lg">Visual Search</h2>

      {/* Available symbols */}
      <div className="mb-3">
        <h3 className="mb-1 font-medium text-gray-500 text-sm">
          Available Symbols
        </h3>
        <div className="flex flex-wrap gap-1">
          {availableSymbols.map((symbol) => (
            <DraggableSymbol
              key={symbol.id}
              symbol={symbol.id}
              src={symbol.src}
              alt={symbol.alt}
            />
          ))}
        </div>
      </div>

      {/* Grid controls */}
      <div className="flex justify-between items-center mb-2">
        <div className="flex items-center">
          <div className="flex flex-row mr-2">
            <span className="mr-1 text-gray-500 text-xs">In</span>
            <div className="flex items-center gap-1 text-xs">
              <input
                type="radio"
                id="AND"
                name="ANDOR"
                value="AND"
                checked={searchLogic === "AND"}
                onChange={() => setSearchLogic("AND")}
                className="mr-1 w-3 h-3"
              />
              <label htmlFor="AND" className="mr-2 text-gray-500">
                AND
              </label>
              <input
                type="radio"
                id="OR"
                name="ANDOR"
                value="OR"
                checked={searchLogic === "OR"}
                onChange={() => setSearchLogic("OR")}
                className="mr-1 w-3 h-3"
              />
              <label htmlFor="OR" className="text-gray-500">
                OR
              </label>
            </div>
          </div>
          <label className="flex items-center mr-2 text-gray-500 text-xs">
            <input
              type="checkbox"
              checked={showGridLines}
              onChange={() => setShowGridLines(!showGridLines)}
              className="mr-1 w-3 h-3"
            />
            Grid
          </label>
          <label className="flex items-center mr-2 text-gray-500 text-xs">
            <input
              type="checkbox"
              checked={isEnabled}
              onChange={() => setIsEnabled(!isEnabled)}
              className="mr-1 w-3 h-3"
            />
            Enabled
          </label>
        </div>
      </div>

      {/* Drop area with Konva Stage */}
      <div
        ref={gridRef}
        className={`
          relative border-2 border-dashed rounded-lg mb-3
          ${isOver ? "border-gray-500 bg-gray-50" : "border-gray-300"}
        `}
        style={{
          height: gridDimensions.height || 240,
          width: "100%",
        }}
        onDragOver={handleDragOver}
        onDragLeave={() => {
          setIsOver(false);
          setHighlightedCell(null);
        }}
        onDrop={handleDrop}
      >
        {/* Render grid cells for HTML5 drag and drop preview */}
        {renderGridCells()}

        <Stage
          width={gridDimensions.width || 240}
          height={gridDimensions.height || 240}
          ref={stageRef}
          onMouseDown={checkDeselect}
          onTouchStart={checkDeselect}
        >
          {showGridLines && (
            <MemoGridLayer
              cellWidth={gridDimensions.cellSize || 30}
              cellHeight={gridDimensions.cellSize || 30}
              gridSize={8}
            />
          )}
          <Layer>
            {positionedSymbols.map((item) => (
              <URLImage
                key={item.id}
                image={item}
                isSelected={item.id === selectedId}
                onSelect={() => {
                  setSelectedId(item.id);
                  bringToFront(item.id);
                }}
                onChange={(newAttrs) => handleSymbolChange(item.id, newAttrs)}
              />
            ))}
          </Layer>
        </Stage>

        {/* Empty state message */}
        {positionedSymbols.length === 0 && (
          <div className="absolute inset-0 flex justify-center items-center text-gray-400 text-xs">
            Drag symbols here
          </div>
        )}
      </div>

      {/* Action buttons */}
      <div className="flex items-center mb-3">
        <button
          onClick={handleClear}
          className={`
            size-10 mr-2 px-3 border border-red-500 rounded-lg text-red-500
            flex items-center justify-center hover:bg-red-50
          `}
          title="Clear all symbols"
        >
          <Trash />
        </button>
        <button
          onClick={handleReset}
          className={`
            size-10 mr-2 px-3 border border-blue-500 rounded-lg text-blue-500
            flex items-center justify-center hover:bg-blue-50
          `}
          title="Reset all settings"
        >
          <Undo />
        </button>
        <button
          onClick={handleSearch}
          disabled={positionedSymbols.length === 0 || !isEnabled}
          className={`
            size-10 flex-grow px-4 rounded-lg font-medium text-sm flex items-center justify-center
            ${
              positionedSymbols.length > 0 && isEnabled
                ? "bg-gray-800 text-white hover:bg-gray-700"
                : "bg-gray-200 text-gray-500 cursor-not-allowed"
            }
          `}
        >
          <Search className="mr-2" />
          Search
        </button>
      </div>
    </div>
  );
}
