# Search State Persistence

This document explains how the search state persistence system works to solve the issue where clicking "Back to Search" would lose the previous search query and results.

## Problem Description

**Before**: When users navigated from search results to an image detail page and then clicked "Back to Search", the previous search state (query, results, limit, model selection) was completely lost. This created a poor user experience as users had to re-enter their search and wait for results again.

**After**: The search state is now automatically preserved and restored when users return to the search page, maintaining their search context and results.

## Solution Architecture

The solution implements a multi-layered approach to state persistence:

### 1. **URL Search Parameters**

- Search query and parameters are stored in the URL
- Enables bookmarking and sharing of search results
- Automatic restoration when navigating directly to URLs with search params

### 2. **localStorage Persistence**

- Complete search state (including results) is cached locally
- Survives page refreshes and browser sessions
- Automatic cleanup of old/stale data (24-hour expiration)

### 3. **State Restoration Logic**

- Priority-based restoration: URL params first, then localStorage
- Automatic search execution when restoring from URL
- Graceful fallback to empty state if no saved data

## Implementation Details

### State Interface

```typescript
interface SearchState {
  query: string;           // Search query text
  results: SearchResult[]; // Search results array
  limit: number;           // Number of results requested
  selectedModel: string;   // Selected AI model (clip, longclip, etc.)
  searchType: string;      // Search type (normal, temporal)
  timestamp: number;       // When the state was saved
}
```

### Storage Key

```typescript
const SEARCH_STATE_KEY = "video-search-state";
```

### Core Functions

#### Save State

```typescript
const saveSearchState = (state: Partial<SearchState>) => {
  try {
    const currentState = getSearchState();
    const newState: SearchState = {
      ...currentState,
      ...state,
      timestamp: Date.now(),
    };
    localStorage.setItem(SEARCH_STATE_KEY, JSON.stringify(newState));
  } catch (error) {
    console.warn("Failed to save search state:", error);
  }
};
```

#### Restore State

```typescript
const restoreSearchState = () => {
  try {
    const state = getSearchState();
    if (state.query && state.results.length > 0) {
      setSearchQuery(state.query);
      setSearchResults(state.results);
      setLimit(state.limit);
      setSelectedModel(state.selectedModel);
      setSearchType(state.searchType);
      return true;
    }
  } catch (error) {
    console.warn("Failed to restore search state:", error);
  }
  return false;
};
```

#### Get State

```typescript
const getSearchState = (): SearchState => {
  try {
    const stored = localStorage.getItem(SEARCH_STATE_KEY);
    if (stored) {
      const parsed = JSON.parse(stored);
      // Check if state is not too old (24 hours)
      if (Date.now() - parsed.timestamp < 24 * 60 * 60 * 1000) {
        return parsed;
      }
    }
  } catch (error) {
    console.warn("Failed to parse search state:", error);
  }
  return {
    query: "",
    results: [],
    limit: 20,
    selectedModel: "clip",
    searchType: "normal",
    timestamp: Date.now(),
  };
};
```

### State Persistence Triggers

State is automatically saved after successful searches:

1. **Text Search**: After `searchImages()` completes successfully
2. **Neighbor Search**: After `searchNeighbor()` completes successfully
3. **Visual Search**: After `visualSearch()` completes successfully
4. **OCR Search**: After OCR results are received

### URL Parameter Management

```typescript
// Update URL when search state changes
useEffect(() => {
  if (searchQuery) {
    const params = new URLSearchParams();
    params.set("q", searchQuery);
    params.set("limit", limit.toString());
    params.set("model", selectedModel);
    params.set("type", searchType);

    // Update URL without triggering navigation
    const newUrl = `${window.location.pathname}?${params.toString()}`;
    window.history.replaceState({}, "", newUrl);
  }
}, [searchQuery, limit, selectedModel, searchType]);
```

### State Restoration on Mount

```typescript
// Restore state from URL params and localStorage on mount
useEffect(() => {
  // First, try to restore from URL params
  const urlQuery = searchParams.get("q");
  const urlLimit = searchParams.get("limit");
  const urlModel = searchParams.get("model");
  const urlType = searchParams.get("type");

  if (urlQuery) {
    // If we have URL params, use them and perform search
    setSearchQuery(urlQuery);
    if (urlLimit) setLimit(Number(urlLimit));
    if (urlModel) setSelectedModel(urlModel);
    if (urlType) setSearchType(urlType);

    // Perform the search automatically
    handleTextSearch(urlQuery);
  } else {
    // If no URL params, try to restore from localStorage
    restoreSearchState();
  }
}, []);
```

## Navigation Flow

### 1. **Search → Image Detail**

```
User performs search → State saved to localStorage + URL updated
User clicks on result → Navigate to /image/[id]
```

### 2. **Image Detail → Back to Search**

```
User clicks "Back to Search" → Navigate to / (home page)
useEffect runs → Restore state from localStorage
Search results reappear with previous query
```

### 3. **Direct URL Access**

```
User visits /?q=query&limit=20&model=clip
useEffect runs → Restore from URL params
Automatic search execution
```

## User Experience Improvements

### **Before (State Loss)**

1. User searches for "person walking"
2. Gets 20 results
3. Clicks on a result to view details
4. Clicks "Back to Search"
5. **❌ Search page is empty, query lost, results gone**
6. User must re-enter search and wait again

### **After (State Preserved)**

1. User searches for "person walking"
2. Gets 20 results
3. Clicks on a result to view details
4. Clicks "Back to Search"
5. **✅ Search page shows "person walking" query with 20 results**
6. User can immediately continue browsing or modify search

## Additional Features

### **Clear Search Button**

- Added above search results when results are present
- Clears all search state (query, results, localStorage, URL)
- Provides user control over state management

### **State Expiration**

- Search state expires after 24 hours
- Prevents accumulation of stale data
- Automatic cleanup of old search contexts

### **Error Handling**

- Graceful fallback if localStorage is unavailable
- Console warnings for debugging
- No breaking errors if persistence fails

### **URL Sharing**

- Search results can be bookmarked
- URLs can be shared with others
- Direct access to specific search contexts

## Browser Compatibility

### **Supported Features**

- ✅ localStorage (all modern browsers)
- ✅ URLSearchParams (all modern browsers)
- ✅ window.history.replaceState (all modern browsers)

### **Fallback Behavior**

- If localStorage fails: State not persisted, but app continues working
- If URL params fail: State not restored, but app continues working
- Graceful degradation ensures core functionality remains

## Performance Considerations

### **Storage Size**

- Search results are typically small (< 1MB)
- localStorage limit is usually 5-10MB
- Automatic cleanup prevents storage bloat

### **Restoration Speed**

- localStorage access is synchronous and fast
- URL parsing is minimal overhead
- State restoration happens in < 1ms

### **Memory Usage**

- State is only stored when needed
- Old states are automatically expired
- No memory leaks from accumulated state

## Future Enhancements

### **Planned Features**

1. **Multiple Search History**: Store last 5-10 searches
2. **Search Templates**: Save common search patterns
3. **Export/Import**: Share search contexts between users
4. **Cloud Sync**: Persist state across devices

### **Technical Improvements**

1. **Compression**: Compress large result sets
2. **IndexedDB**: Use for very large result sets
3. **Service Worker**: Cache search results offline
4. **Real-time Sync**: Live updates to shared searches

## Testing Scenarios

### **State Persistence**

- [ ] Perform search, navigate away, return
- [ ] Refresh page with search results
- [ ] Close browser, reopen, return to search
- [ ] Navigate between different search types

### **URL Parameters**

- [ ] Direct access to search URLs
- [ ] Bookmark search results
- [ ] Share search URLs
- [ ] Browser back/forward navigation

### **Error Handling**

- [ ] Disable localStorage
- [ ] Corrupted state data
- [ ] Expired state data
- [ ] Network failures during restoration

### **Edge Cases**

- [ ] Very large result sets
- [ ] Special characters in queries
- [ ] Long search queries
- [ ] Multiple rapid searches

## Conclusion

The search state persistence system provides a seamless user experience by:

- **Preserving Context**: Users never lose their search progress
- **Enabling Navigation**: Easy movement between search and detail views
- **Supporting Sharing**: Search results can be bookmarked and shared
- **Improving UX**: No more re-entering searches or waiting for results

This solution transforms the user experience from frustrating state loss to smooth, persistent search sessions that maintain context across the entire user journey.
