# Key Features - Implementation Details

This document provides a comprehensive breakdown of VBS-Web's key features and their technical implementation details.

## 1. Multiple Search Methods

### Text-based Search

**Implementation:**

- **Component:** `SearchBar` component in `/components/search-bar.tsx` handles user input
- **API:** Text queries are processed by the `/api/search` endpoint
- **Search Logic:**
  - Queries are tokenized and normalized (lowercase, removal of stop words)
  - Search terms are matched against image metadata including descriptions and tags
  - Results are ranked by relevance score based on term frequency and match quality
- **State Management:** Search state is managed in the parent component using React's `useState`
- **Performance:** Debounced input prevents excessive API calls during typing

### Visual Search

**Implementation:**

- **Components:**
  - `SymbolGrid` component in `/components/symbol-grid.tsx` displays available symbols
  - `DraggableSymbol` in `/components/draggable-symbol.tsx` enables drag and drop functionality
- **Canvas:** React-Konva provides the canvas infrastructure in `app/page.tsx`
- **Search Parameters:**
  - Symbol positions are translated to normalized coordinates (0-1 range)
  - Each placed symbol generates an object with class name and bounding box
  - Position data is formatted as `{class_name: string, bbox: number[]}` objects
- **API:** Visual queries sent to `/api/search-detections` endpoint
- **Logic Options:** Users can select between "AND" and "OR" logic for multiple symbols

### OCR-based Search

**Implementation:**

- **Component:** `OCRSearch` component in `/components/ocr-search.tsx` handles text-in-image search
- **API:** OCR queries processed by `/api/search-ocr` endpoint
- **Results Processing:**
  - Images containing the queried text are highlighted with the matching text
  - Results include the OCR-extracted text from the image for context
- **UI:** Search results include snippet of the detected text with the query highlighted

## 2. Image Exploration

### Similar Image Search (Neighbor Search)

**Implementation:**

- **Function:** `searchNeighbor` in `/services/api.ts` handles the API calls
- **API:** Neighbor search requests go to `/api/neighbor` endpoint
- **Logic:**
  - Takes image ID as input
  - Returns images that share similar visual features or metadata
  - Implemented using vector similarity in the feature space
- **UI Integration:** Available from search results through a "Find similar" button

### Image Metadata Viewing

**Implementation:**

- **Components:** Image details modal displays metadata when a result is selected
- **Data Points:** Each image includes:
  - Unique ID
  - Source video information
  - Timestamp
  - Descriptive tags
  - Confidence scores for detected objects
- **UI:** Information is displayed in a structured panel with tabs for different metadata categories

### Video Timestamp Integration

**Implementation:**

- **Format:** Timestamps stored in standardized format (HH:MM:SS.ms)
- **Functionality:**
  - Links to source video with timestamp parameter
  - Preview shows frame at timestamp
  - Navigation allows jumping to previous/next frames
- **UI:** Timeline component provides visual representation of the image's position in video

## 3. Interactive User Interface

### Responsive Design

**Implementation:**

- **Tailwind:** Responsive classes (sm:, md:, lg:, xl:) adapt layouts to different screen sizes
- **Component Design:** Flexible components that reflow based on available space
- **Media Queries:** Custom breakpoints defined in `tailwind.config.ts`
- **Testing:** Validated across various devices and viewport sizes

### Symbol Grid for Visual Query Construction

**Implementation:**

- **Grid Layout:** CSS Grid system organizes symbols in a responsive grid
- **Symbol Data:** Symbols defined in a configuration object with categories
- **Interaction:** Click to select, drag to position on canvas
- **Accessibility:** Keyboard navigation and screen reader support

### Dynamic Search Results with Pagination

**Implementation:**

- **Component:** `SearchResults` in `/components/search-results.tsx` handles result display
- **Pagination:**
  - Server-side pagination with limit and offset parameters
  - Client-side state tracks current page
  - Results fetched in batches to optimize performance
- **Loading States:** Skeleton loaders display during data fetching
- **Error Handling:** Graceful degradation when results can't be loaded

### Search Result Previews and Details

**Implementation:**

- **Preview:** Thumbnail images with hover effects for quick viewing
- **Details Modal:** Expandable modal with comprehensive image information
- **Video Integration:** Direct links to source videos at specific timestamps
- **Download Option:** Image download capability with proper attribution

## 4. Performance Optimizations

### Server-side API Routes

**Implementation:**

- **API Structure:** Routes defined in `/app/api/` directory
- **Handler Functions:** Each endpoint has GET/POST handlers for different operations
- **Error Handling:** Standardized error responses with appropriate HTTP status codes
- **Validation:** Request body validation using Zod schemas

### Next.js Image Optimization

**Implementation:**

- **Component:** Next.js `Image` component with automatic optimization
- **Configuration:** Image settings in `next.config.mjs` define quality and sizing behavior
- **Loading Strategy:** Images use lazy loading with blur placeholders
- **Formats:** Automatic serving of modern formats like WebP

### Lazy Loading and Pagination

**Implementation:**

- **Intersection Observer:** Used to detect when more results should load
- **Virtualization:** Large result sets use virtualized lists to minimize DOM elements
- **Load Thresholds:** Configurable thresholds determine when to fetch next batch
- **State Management:** Loading states prevent duplicate requests
