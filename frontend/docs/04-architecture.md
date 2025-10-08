# Architecture and Technology Integration - Technical Details

This document provides an in-depth examination of VBS-Web's architecture and how different technologies are integrated to create a cohesive application.

## System Architecture Overview

VBS-Web follows a modern frontend architecture with Next.js providing both client and server capabilities. The system is structured in layers:

1. **Presentation Layer**: React components and UI elements
2. **Application Layer**: Hooks, context providers, and client-side logic
3. **Service Layer**: API communication and data transformation
4. **API Layer**: Next.js API routes functioning as a backend
5. **Data Layer**: External data sources and mock databases

## 1. Pages and Routing

### Next.js App Router Implementation

The application uses Next.js App Router for file-based routing:

```
/app/
  page.tsx             # Main homepage
  layout.tsx           # Root layout
  find-image/          # Find image by ID route
    page.tsx
  image/               # Individual image view
    [id]/              # Dynamic route for image ID
      page.tsx
  api/                 # API routes
    search/
      route.ts
    neighbor/
      route.ts
    visual_search/
      route.ts
```

**Technical Details:**

- **Root Layout**: Defined in `/app/layout.tsx`, includes global providers and UI shells
- **Route Parameters**: Dynamic segments in brackets (e.g., `[id]`) extract parameters from URLs
- **Loading States**: Dedicated loading.tsx files provide loading UI during route transitions
- **Error Boundaries**: Error handling via error.tsx files for graceful error states
- **Metadata**: Each page exports metadata objects for SEO optimization

## 2. API Integration

### Service Layer Pattern

The application implements a service layer pattern to abstract API communication:

```typescript
// From /services/api.ts
export async function searchImages({
  query,
  limit = 20,
  model = 'blip2_feature_extractor',
}: SearchParams): Promise<SearchResult[]> {
  try {
    const response = await fetch(`${BASE_URL}/search`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, limit, model }),
    });

    if (!response.ok) {
      throw new Error(`Search failed with status: ${response.status}`);
    }

    const data = await response.json();
    return data.frames;
  } catch (error) {
    console.error('Error searching images:', error);
    throw error;
  }
}
```

**Technical Details:**

- **API Interface**: Typed interfaces define request and response structures
- **Error Handling**: Standardized error handling with try/catch blocks
- **Parameter Normalization**: Default parameters and type coercion ensure consistent API calls
- **Response Transformation**: Raw API responses are transformed into application-friendly formats
- **Service Isolation**: Each service function is isolated and focused on a specific capability

## 3. UI Component Library

### Composition of UI Components

The UI component library combines Radix UI primitives with Tailwind styling:

```tsx
// Example of component composition (simplified)
export function SearchBar({ onSearch, size = 'medium' }) {
  const [query, setQuery] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSearch(query);
  };

  const sizeClasses = {
    small: 'h-8 text-sm',
    medium: 'h-10 text-base',
    large: 'h-12 text-lg',
  };

  return (
    <form onSubmit={handleSubmit} className="flex w-full">
      <div className="relative flex-grow">
        <Input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className={`w-full pl-10 ${sizeClasses[size]}`}
          placeholder="Search images..."
        />
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
      </div>
      <Button type="submit" className="ml-2">Search</Button>
    </form>
  );
}
```

**Technical Details:**

- **Component Hierarchy**: Base UI components from Radix UI are extended with project-specific styling
- **Composition Pattern**: Smaller components compose into feature-complete UI elements
- **Prop Drilling**: Props pass configuration options down the component tree
- **Styling Strategy**: Tailwind classes applied directly to components
- **Theme Integration**: Components react to theme context for dark/light mode

## 4. Interactive Features

### Canvas and Drag-and-Drop Implementation

The visual search feature combines React Konva for canvas operations with React DND for drag-and-drop:

```tsx
// Simplified example of canvas and drag-and-drop integration
const SymbolCanvas = () => {
  const [symbols, setSymbols] = useState<PositionedSymbol[]>([]);
  const stageRef = useRef<Konva.Stage>(null);

  const handleDrop = (item: DragItem, monitor: DropTargetMonitor) => {
    if (!stageRef.current) return;

    const clientOffset = monitor.getClientOffset();
    if (!clientOffset) return;

    // Convert screen coordinates to canvas coordinates
    const stageRect = stageRef.current.container().getBoundingClientRect();
    const x = clientOffset.x - stageRect.left;
    const y = clientOffset.y - stageRect.top;

    // Add new symbol
    const newSymbol: PositionedSymbol = {
      id: `symbol-${Date.now()}`,
      symbol: item.symbol,
      x,
      y,
      zIndex: symbols.length + 1,
    };

    setSymbols([...symbols, newSymbol]);
  };

  return (
    <div ref={drop} className="canvas-container">
      <Stage ref={stageRef} width={800} height={600}>
        <Layer>
          {symbols.map((symbol) => (
            <DraggableSymbol
              key={symbol.id}
              id={symbol.id}
              symbol={symbol.symbol}
              x={symbol.x}
              y={symbol.y}
              onDragEnd={handleDragEnd}
              onRemove={handleRemove}
            />
          ))}
        </Layer>
      </Stage>
    </div>
  );
};
```

**Technical Details:**

- **Canvas Setup**: React Konva provides Stage, Layer, and shape primitives
- **Drag Sources**: Symbol grid items act as drag sources
- **Drop Target**: Canvas acts as the drop target
- **Coordinate Translation**: Screen coordinates are converted to canvas coordinates
- **State Management**: Canvas state tracks all positioned symbols
- **Event Handling**: Complex interactions are handled via events (drag start, drag end, click)

## 5. Form Handling

### Integration of React Hook Form with Zod

The application combines React Hook Form with Zod for robust form handling:

```tsx
// Example of form handling with validation
const SearchForm = ({ onSubmit }) => {
  // Define validation schema
  const schema = z.object({
    query: z.string().min(2, "Search term must be at least 2 characters"),
    filters: z.object({
      category: z.string().optional(),
      dateRange: z.array(z.date().optional()).optional(),
    }).optional(),
  });

  // Initialize form
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    reset,
  } = useForm({
    resolver: zodResolver(schema),
    defaultValues: {
      query: "",
      filters: { category: "", dateRange: [] },
    },
  });

  // Form submission handler
  const onFormSubmit = async (data) => {
    try {
      await onSubmit(data);
      reset(); // Reset form after successful submission
    } catch (error) {
      console.error("Form submission error:", error);
    }
  };

  return (
    <form onSubmit={handleSubmit(onFormSubmit)}>
      <div className="mb-4">
        <Label htmlFor="query">Search Query</Label>
        <Input id="query" {...register("query")} />
        {errors.query && (
          <p className="text-red-500 text-sm mt-1">{errors.query.message}</p>
        )}
      </div>

      {/* Additional form fields */}

      <Button type="submit" disabled={isSubmitting}>
        {isSubmitting ? "Searching..." : "Search"}
      </Button>
    </form>
  );
};
```

**Technical Details:**

- **Schema Definition**: Zod schemas define validation rules and type information
- **Form Initialization**: React Hook Form registers fields and validation
- **Error Handling**: Validation errors mapped to corresponding form fields
- **Submission Logic**: Asynchronous submission with loading states
- **Form Reset**: Clean form state after successful submission
- **Typescript Integration**: Type inference from Zod schema to form values
