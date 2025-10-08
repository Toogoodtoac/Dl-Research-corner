# Component Architecture Guide

## Overview

VBS-Web 2.0 follows a modular component architecture built on React 19 and Next.js 15. This guide covers component patterns, design principles, and implementation details.

## Architecture Principles

### 1. Composition Over Inheritance

- Small, focused components with single responsibilities
- Compound components for complex functionality
- Reusable UI primitives from Radix UI

### 2. TypeScript-First Development

- Strict type definitions for all props and state
- Interface-driven component design
- Runtime type validation with Zod

### 3. Performance Optimization

- React.memo for expensive components
- useCallback for stable function references
- Lazy loading for heavy components

## Core Component Categories

### 1. Layout Components

#### Root Layout (`app/layout.tsx`)

```typescript
export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <Toaster />
        {children}
      </body>
    </html>
  );
}
```

**Purpose**: Root application wrapper with global providers

**Features**:

- Global toast notifications (Sonner)
- HTML document structure
- Global CSS imports

### 2. Search Components

#### SearchBar Component

**Location**: `components/search-bar.tsx`

```typescript
interface SearchBarProps {
  onSearch: (query: string) => void;
  size?: 'default' | 'large';
  placeholder?: string;
  disabled?: boolean;
}

export default function SearchBar({
  onSearch,
  size = 'default',
  placeholder = 'Search for images...',
  disabled = false
}: SearchBarProps)
```

**Key Features**:

- Responsive design with size variants
- Enter key submission
- Loading state management
- Debounced input for performance

**Implementation Details**:

```typescript
const [query, setQuery] = useState('');
const [isSearching, setIsSearching] = useState(false);

const handleSubmit = async (e: FormEvent) => {
  e.preventDefault();
  if (!query.trim() || isSearching) return;

  setIsSearching(true);
  try {
    await onSearch(query.trim());
  } finally {
    setIsSearching(false);
  }
};
```

#### SearchResults Component

**Location**: `components/search-results.tsx`

```typescript
interface SearchResultsProps {
  results: SearchResult[];
  onMoreResults: (id: string) => void;
  focusId: string | null;
}
```

**Architecture**: Compound component pattern

- `SearchResults` (Container)
- `VideoGroup` (Video grouping)
- `ImageResult` (Individual image)

**Key Features**:

- Video-based result grouping
- Image lazy loading with error handling
- Focus management and scrolling
- Copy-to-clipboard functionality
- Client-side image caching

**Performance Optimizations**:

```typescript
// Memoized ref registration
const registerFocusRef = useCallback(
  (id: string, ref: HTMLDivElement | null) => {
    if (ref) {
      setFocusRefs(prev => ({ ...prev, [id]: ref }));
    } else {
      setFocusRefs(prev => {
        const newRefs = { ...prev };
        delete newRefs[id];
        return newRefs;
      });
    }
  }, []
);

// Error handling with state cleanup
const handleImageError = useCallback((imageId: string) => {
  setFailedImageIds(prev => {
    const newSet = new Set(prev);
    newSet.add(imageId);
    return newSet;
  });
}, []);
```

### 3. Interactive Components

#### SymbolGrid Component

**Location**: `components/symbol-grid.tsx`

```typescript
interface SymbolGridProps {
  onSearch: (params: VisualSearchParams) => void;
}

interface PositionedSymbol {
  id: string;
  symbol: string;
  x: number;
  y: number;
  zIndex: number;
}
```

**Key Features**:

- Canvas-based drag-and-drop interface
- Symbol palette with 30+ object types
- Real-time position tracking
- Visual query construction
- AND/OR logic selection

**Implementation**: React-Konva integration

```typescript
// Stage configuration
const stage = useRef<Konva.Stage>(null);
const CANVAS_WIDTH = 400;
const CANVAS_HEIGHT = 300;

// Symbol positioning
const handleDragEnd = (e: KonvaEventObject<DragEvent>, symbolId: string) => {
  const node = e.target;
  const x = Math.max(0, Math.min(node.x(), CANVAS_WIDTH - 50));
  const y = Math.max(0, Math.min(node.y(), CANVAS_HEIGHT - 50));

  updateSymbolPosition(symbolId, x, y);
};
```

#### DraggableSymbol Component

**Location**: `components/draggable-symbol.tsx`

```typescript
interface DraggableSymbolProps {
  symbol: string;
  onDragStart: (symbol: string) => void;
  onDragEnd: () => void;
}
```

**Features**:

- HTML5 drag-and-drop API
- Visual feedback during drag
- Touch support for mobile
- Accessibility compliance

### 4. UI Components (Shadcn/UI)

#### Design System Structure

```
components/ui/
├── primitives/         # Basic building blocks
│   ├── button.tsx     # Button variants
│   ├── input.tsx      # Form inputs
│   ├── card.tsx       # Content containers
│   └── badge.tsx      # Status indicators
├── overlays/          # Modal components
│   ├── dialog.tsx     # Modal dialogs
│   ├── popover.tsx    # Contextual popups
│   └── tooltip.tsx    # Hover information
├── navigation/        # Navigation components
│   ├── tabs.tsx       # Tab interface
│   ├── pagination.tsx # Result pagination
│   └── breadcrumb.tsx # Navigation path
└── feedback/          # User feedback
    ├── toast.tsx      # Notifications
    ├── progress.tsx   # Loading indicators
    └── skeleton.tsx   # Loading placeholders
```

#### Button Component Pattern

```typescript
// Variant-based styling with CVA
const buttonVariants = cva(
  "inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground hover:bg-primary/90",
        destructive: "bg-destructive text-destructive-foreground hover:bg-destructive/90",
        outline: "border border-input bg-background hover:bg-accent hover:text-accent-foreground",
        secondary: "bg-secondary text-secondary-foreground hover:bg-secondary/80",
        ghost: "hover:bg-accent hover:text-accent-foreground",
        link: "text-primary underline-offset-4 hover:underline",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-9 rounded-md px-3",
        lg: "h-11 rounded-md px-8",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)
```

### 5. Page Components

#### Home Page (`app/page.tsx`)

**Architecture**: Complex stateful component (373 lines)

**Key Responsibilities**:

- Search state management
- Multiple search method coordination
- Responsive layout management
- Scroll-based header behavior
- Error handling and loading states

**State Structure**:

```typescript
// Search state
const [searchQuery, setSearchQuery] = useState('');
const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
const [isLoading, setIsLoading] = useState(false);
const [error, setError] = useState<string | null>(null);

// UI state
const [isHeaderFixed, setIsHeaderFixed] = useState(false);
const [limit, setLimit] = useState(20);
const [focusId, setFocusId] = useState<string | null>(null);

// Refs for scroll management
const heroSectionRef = useRef<HTMLDivElement>(null);
const headerRef = useRef<HTMLDivElement>(null);
const mainContentRef = useRef<HTMLDivElement>(null);
```

**Search Handlers**:

```typescript
// Text search with error handling
const handleTextSearch = async (query: string) => {
  setIsLoading(true);
  setSearchQuery(query);
  setError(null);
  setFocusId(null);

  try {
    const results = await searchImages({ query, limit });
    setSearchResults(results);

    // Mobile scroll optimization
    if (mainContentRef.current && window.innerWidth < 1024) {
      mainContentRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  } catch (err) {
    setError('Failed to perform search. Please try again.');
    console.error('Search error:', err);
  } finally {
    setIsLoading(false);
  }
};
```

## Component Patterns

### 1. Container/Presentational Pattern

#### Container Component

```typescript
// Logic and state management
function SearchContainer() {
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);

  const handleSearch = async (query: string) => {
    setLoading(true);
    try {
      const data = await searchAPI(query);
      setResults(data);
    } catch (error) {
      handleError(error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <SearchPresentation
      results={results}
      loading={loading}
      onSearch={handleSearch}
    />
  );
}
```

#### Presentational Component

```typescript
// Pure UI rendering
interface SearchPresentationProps {
  results: SearchResult[];
  loading: boolean;
  onSearch: (query: string) => void;
}

function SearchPresentation({ results, loading, onSearch }: SearchPresentationProps) {
  return (
    <div>
      <SearchBar onSearch={onSearch} disabled={loading} />
      {loading ? <LoadingSpinner /> : <SearchResults results={results} />}
    </div>
  );
}
```

### 2. Compound Component Pattern

#### Example: OCRSearch Component

```typescript
// Main component with subcomponents
function OCRSearch({ onResultsFound, onError, onLoading, limit }: OCRSearchProps) {
  return (
    <OCRSearchProvider>
      <OCRSearch.Input />
      <OCRSearch.Options />
      <OCRSearch.Results />
    </OCRSearchProvider>
  );
}

// Subcomponents
OCRSearch.Input = function OCRInput() {
  const { query, setQuery, handleSearch } = useOCRSearch();
  return <input value={query} onChange={setQuery} onSubmit={handleSearch} />;
};

OCRSearch.Options = function OCROptions() {
  const { options, setOptions } = useOCRSearch();
  return <OptionsPanel options={options} onChange={setOptions} />;
};
```

### 3. Custom Hooks Pattern

#### useImageCache Hook

```typescript
function useImageCache() {
  const [cache, setCache] = useState<Map<string, string>>(new Map());

  const getCachedImage = useCallback(async (imageId: string) => {
    if (cache.has(imageId)) {
      return cache.get(imageId);
    }

    try {
      const cached = await imageCache.getItem(imageId);
      if (cached) {
        setCache(prev => new Map(prev).set(imageId, cached));
        return cached;
      }
    } catch (error) {
      console.warn('Cache read failed:', error);
    }

    return null;
  }, [cache]);

  const setCachedImage = useCallback(async (imageId: string, url: string) => {
    try {
      await imageCache.setItem(imageId, url);
      setCache(prev => new Map(prev).set(imageId, url));
    } catch (error) {
      console.warn('Cache write failed:', error);
    }
  }, []);

  return { getCachedImage, setCachedImage };
}
```

### 4. Error Boundary Pattern

#### Component Error Boundary

```typescript
interface ErrorBoundaryState {
  hasError: boolean;
  error?: Error;
}

class ComponentErrorBoundary extends Component<
  PropsWithChildren<{}>,
  ErrorBoundaryState
> {
  constructor(props: PropsWithChildren<{}>) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Component error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return <ErrorFallback error={this.state.error} />;
    }

    return this.props.children;
  }
}
```

## Performance Optimization Patterns

### 1. Memoization

```typescript
// Component memoization
const ImageResult = React.memo(({ image, onMoreResults, focusId }: ImageResultProps) => {
  // Component implementation
}, (prevProps, nextProps) => {
  // Custom comparison for optimization
  return (
    prevProps.image.image_id === nextProps.image.image_id &&
    prevProps.focusId === nextProps.focusId
  );
});

// Hook memoization
const memoizedSearchFunction = useCallback(
  async (query: string) => {
    return await searchImages({ query, limit });
  },
  [limit]
);
```

### 2. Lazy Loading

```typescript
// Component lazy loading
const LazySymbolGrid = lazy(() => import('@/components/symbol-grid'));

// Usage with Suspense
<Suspense fallback={<SymbolGridSkeleton />}>
  <LazySymbolGrid onSearch={handleVisualSearch} />
</Suspense>
```

### 3. Virtual Scrolling (Future Enhancement)

```typescript
// For large result sets
import { FixedSizeList as List } from 'react-window';

function VirtualizedResults({ results }: { results: SearchResult[] }) {
  const Row = ({ index, style }: { index: number; style: CSSProperties }) => (
    <div style={style}>
      <ImageResult image={results[index]} />
    </div>
  );

  return (
    <List
      height={600}
      itemCount={results.length}
      itemSize={200}
      width="100%"
    >
      {Row}
    </List>
  );
}
```

## Testing Patterns

### 1. Component Testing

```typescript
// Jest + React Testing Library
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import SearchBar from '@/components/search-bar';

describe('SearchBar', () => {
  it('calls onSearch when form is submitted', async () => {
    const onSearch = jest.fn();
    render(<SearchBar onSearch={onSearch} />);

    const input = screen.getByPlaceholderText('Search for images...');
    const form = screen.getByRole('form');

    fireEvent.change(input, { target: { value: 'mountain' } });
    fireEvent.submit(form);

    await waitFor(() => {
      expect(onSearch).toHaveBeenCalledWith('mountain');
    });
  });
});
```

### 2. Hook Testing

```typescript
import { renderHook, act } from '@testing-library/react';
import { useImageCache } from '@/hooks/use-image-cache';

describe('useImageCache', () => {
  it('caches and retrieves images', async () => {
    const { result } = renderHook(() => useImageCache());

    await act(async () => {
      await result.current.setCachedImage('img1', 'url1');
    });

    await act(async () => {
      const cachedUrl = await result.current.getCachedImage('img1');
      expect(cachedUrl).toBe('url1');
    });
  });
});
```

## Best Practices

### 1. Component Design

- Keep components under 200 lines when possible
- Use TypeScript interfaces for all props
- Implement proper error boundaries
- Follow single responsibility principle
- Use descriptive component and prop names

### 2. State Management

- Use local state for component-specific data
- Consider React Context for app-wide state
- Implement proper cleanup in useEffect
- Use reducers for complex state logic

### 3. Performance

- Memoize expensive computations
- Use React.memo for pure components
- Implement proper dependency arrays
- Avoid creating objects in render
- Use appropriate loading strategies

### 4. Accessibility

- Include proper ARIA labels
- Ensure keyboard navigation
- Maintain focus management
- Use semantic HTML elements
- Test with screen readers

### 5. Error Handling

- Implement error boundaries
- Provide user-friendly error messages
- Log errors for debugging
- Graceful degradation for failures
- Retry mechanisms for network errors

## Future Enhancements

### 1. Component Library

- Extract reusable components
- Create component documentation
- Implement visual regression testing
- Build component playground

### 2. Performance Monitoring

- Add React DevTools Profiler
- Implement performance metrics
- Monitor bundle size
- Track component render times

### 3. Advanced Patterns

- Implement micro-frontends
- Add state machines (XState)
- Consider server components
- Add streaming capabilities
