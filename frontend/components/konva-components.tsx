"use client";

import React from "react";
import { Image as KonvaImage, Group, Text } from "react-konva";
import useImage from "use-image";

interface KonvaComponentsProps {
  symbol: string;
  index?: number;
  onRemove?: (index: number) => void;
  src?: string;
}

export default function KonvaComponents({
  symbol,
  index,
  onRemove,
  src = `/palette/${symbol}.png`,
}: KonvaComponentsProps) {
  const [image] = useImage(src);
  const [isDragging, setIsDragging] = React.useState(false);

  return (
    <Group
      draggable
      onDragStart={() => setIsDragging(true)}
      onDragEnd={() => setIsDragging(false)}
      opacity={isDragging ? 0.5 : 1}
    >
      {image && <KonvaImage image={image} width={30} height={30} />}
      <Text
        text={symbol}
        fontSize={12}
        padding={4}
        fill="#4a5568"
        align="center"
      />
      {onRemove && typeof index === "number" && (
        <Group
          onClick={() => onRemove(index)}
          x={35}
          y={0}
          width={15}
          height={15}
        >
          <Text text="×" fontSize={14} fill="#718096" align="center" />
        </Group>
      )}
    </Group>
  );
}
