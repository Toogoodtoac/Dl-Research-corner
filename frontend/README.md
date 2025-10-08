# VBS-Web 2.0

**Modern Image Search Platform** - Next.js 15 application with multi-modal search capabilities

[![Next.js](https://img.shields.io/badge/Next.js-15.2.4-black)](https://nextjs.org/)
[![React](https://img.shields.io/badge/React-19-blue)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0-blue)](https://www.typescriptlang.org/)
[![Tailwind](https://img.shields.io/badge/Tailwind-3.4.17-38B2AC)](https://tailwindcss.com/)

## ✨ Key Features

- **Text Search** - Natural language image queries
- **Visual Search** - Drag-and-drop symbol positioning
- **OCR Search** - Find text within images
- **Neighbor Search** - Discover similar images
- **Responsive Design** - Mobile-first UI
- **Performance Optimized** - Image caching & lazy loading

## Quick Start

```bash
# Install dependencies
pnpm install

# Start development server
pnpm dev

# Build for production
pnpm build

# Start production server
pnpm start
```

Application runs on: `http://localhost:8080`

## Project Structure

```
frontend
├── app/                    # Next.js App Router
│   ├── page.tsx           # Main search interface
│   ├── find-image/        # ID-based search page
│   ├── image/[id]/        # Image detail view
│   └── api/               # Backend API routes
├── components/            # Reusable UI components
│   ├── search-bar.tsx     # Search input component
│   ├── search-results.tsx # Results display
│   ├── symbol-grid.tsx    # Visual search interface
│   └── ui/                # Shadcn/UI components
├── services/              # API service layer
├── hooks/                 # Custom React hooks
├── lib/                   # Utility functions
└── types/                 # TypeScript type definitions
```

## Core Features Documentation

### 1. Text-Based Search

```typescript
// Usage in components
import { searchImages } from '@/services/api';

const results = await searchImages({
  query: "mountain landscape",
  limit: 20
});
```

### 2. Visual Search Interface

Interactive symbol grid allowing users to position objects:

- Drag symbols from palette
- Position on canvas
- Configure search logic (AND/OR)
- Execute visual query

### 3. OCR Text Search

Search for text content within images:

- Real-time text detection
- Configurable search parameters
- Result highlighting

### 4. Similar Image Discovery

Find related images using ML embeddings:

- Neighbor search algorithm
- Similarity scoring
- Visual result grouping

## API Routes

### Search Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/search` | GET/POST | Text-based image search |
| `/api/search-detections` | POST | Visual object detection search |
| `/api/neighbor` | POST | Similar image discovery |
| `/api/visual_search` | POST | Symbol-based visual search |
| `/api/images/[...path]` | GET | Static image serving |

### Example API Usage

```typescript
// Text Search
const response = await fetch('/api/search', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    query: "sunset over mountains",
    limit: 10
  })
});

// Visual Search
const response = await fetch('/api/search-detections', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    object_list: [
      { class_name: "car", bbox: [100, 100, 200, 200] }
    ],
    logic: "AND",
    limit: 20
  })
});
```

## Component Architecture

### Core Components

#### SearchBar Component

```typescript
interface SearchBarProps {
  onSearch: (query: string) => void;
  size?: 'default' | 'large';
}
```

#### SearchResults Component

```typescript
interface SearchResultsProps {
  results: SearchResult[];
  onMoreResults: (id: string) => void;
  focusId: string | null;
}
```

#### SymbolGrid Component

```typescript
interface SymbolGridProps {
  onSearch: (params: VisualSearchParams) => void;
}
```

### Design System

- **UI Library**: Radix UI primitives with Tailwind styling
- **Icons**: Lucide React icon set
- **Typography**: System font stack
- **Color Palette**: Blue-based theme with dark mode support
- **Spacing**: Tailwind spacing scale (4px increments)

## Development Guide

### Tech Stack

- **Framework**: Next.js 15 with App Router
- **Language**: TypeScript 5.0
- **Styling**: Tailwind CSS + Radix UI
- **State**: React hooks + Context API
- **Forms**: React Hook Form + Zod validation
- **Canvas**: Konva.js for interactive graphics
- **Storage**: LocalForage for client-side caching

### Code Patterns

#### Component Structure

```typescript
'use client';

import { useState, useEffect } from 'react';
import type { ComponentProps } from './types';

export default function Component({ prop1, prop2 }: ComponentProps) {
  // State management
  const [state, setState] = useState();

  // Effects
  useEffect(() => {
    // Effect logic
  }, [dependencies]);

  // Event handlers
  const handleEvent = () => {
    // Handler logic
  };

  return (
    <div>
      {/* Component JSX */}
    </div>
  );
}
```

#### API Route Pattern

```typescript
import { type NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    // Process request
    return NextResponse.json(result);
  } catch (error) {
    return NextResponse.json(
      { error: 'Error message' },
      { status: 500 }
    );
  }
}
```

### Performance Optimizations

- **Image Optimization**: Next.js Image component with lazy loading
- **Code Splitting**: Automatic with Next.js App Router
- **Caching**: LocalForage for search results and images
- **Bundle Analysis**: Built-in Next.js analyzer
- **Memory Management**: Proper cleanup in useEffect hooks

## Testing & Quality

```bash
# Linting
pnpm lint

# Type checking
pnpm build

# Format code
npx prettier --write .
```

### Code Quality Tools

- **ESLint**: Code linting and style enforcement
- **TypeScript**: Static type checking
- **Prettier**: Code formatting (via editor integration)
- **Next.js**: Built-in performance monitoring

## Browser Support

- Chrome 100+
- Firefox 100+
- Safari 15+
- Edge 100+

## Related Documentation

- [Project Overview](./docs/01-project-overview.md)
- [Tech Stack Details](./docs/02-tech-stack.md)
- [Feature Documentation](./docs/03-key-features.md)
- [Architecture Guide](./docs/04-architecture.md)
- [Unique Aspects](./docs/05-unique-aspects.md)

## License

Private project - All rights reserved
