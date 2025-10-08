# VBS-Web: Visual Image Search Web Application

## Project Overview

VBS-Web is a sophisticated image search application built with Next.js that provides multiple search methods for finding and exploring images. The application offers text-based, visual, and OCR-based search capabilities, allowing users to find images using different criteria and approaches.

## Tech Stack

### Frontend Technologies

- **Next.js 15**: React framework with server-side rendering and API routes
- **React 19**: UI library for component-based architecture
- **TypeScript**: Static typing for improved code quality and developer experience
- **Tailwind CSS**: Utility-first CSS framework for styling
- **Radix UI**: Unstyled, accessible component primitives
- **Lucide React**: Icon library with clean, consistent icons
- **React Hook Form**: Form state management and validation
- **Zod**: TypeScript-first schema validation library
- **Konva/React-Konva**: Canvas-based drawing and image manipulation library

### Development Tools

- **Turbo**: Monorepo management with optimized build system
- **pnpm**: Fast, disk space efficient package manager
- **ESLint/Prettier**: Code quality and formatting tools
- **next-themes**: Dark/light theme management for Next.js

## Key Features and Functionality

1. **Multiple Search Methods**:
   - Text-based search using keywords
   - Visual search using draggable symbols and object positions
   - OCR-based search for finding text within images

2. **Image Exploration**:
   - Similar image search (neighbor search)
   - Image metadata viewing
   - Video timestamp integration

3. **Interactive User Interface**:
   - Responsive design for all device sizes
   - Symbol grid for visual query construction
   - Dynamic search results with pagination
   - Search result previews and details

4. **Performance Optimizations**:
   - Server-side API routes for backend logic
   - Next.js image optimization
   - Lazy loading and pagination for search results

## Architecture and Technology Integration

The application uses a modern architecture that integrates frontend and backend capabilities:

1. **Pages and Routing**: Next.js App Router provides a file-based routing system with layout inheritance, making navigation and page structure intuitive.

2. **API Integration**: The frontend components interact with backend APIs through service modules that abstract the communication details, allowing for clean separation of concerns.

3. **UI Component Library**: A comprehensive set of UI components powered by Radix UI and styled with Tailwind CSS provides a consistent design language across the application.

4. **Interactive Features**: The combination of React Konva for canvas operations and React DND for drag-and-drop enables the visual search functionality, where users can position symbols to create visual queries.

5. **Form Handling**: React Hook Form combined with Zod validation ensures robust form handling and data validation throughout the application.

## Unique Aspects

The most distinctive feature of VBS-Web is its multi-modal search capability, allowing users to find images using text, visual arrangement of objects, or text contained within images (OCR). This flexibility makes the application suitable for various use cases, from content creators looking for specific visuals to researchers analyzing image databases.

The drag-and-drop visual search interface is particularly innovative, allowing users to arrange symbols on a canvas to indicate the desired composition or layout of objects within images they're searching for.

## Conclusion

VBS-Web demonstrates the power of combining modern web technologies to create a feature-rich application. The integration of Next.js, React, and various specialized libraries results in a performant, accessible, and user-friendly image search platform with capabilities that go beyond traditional text-based search approaches.
