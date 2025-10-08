# Tech Stack - Detailed Implementation

This document provides an in-depth look at how each technology in VBS-Web's tech stack is specifically implemented and utilized within the project.

## Frontend Technologies

### Next.js 15

Next.js serves as the foundation of VBS-Web, providing both the frontend framework and API routing capabilities. Implementation details include:

- **App Router**: The project uses Next.js 15's App Router for file-based routing, with page components located in the `/app` directory
- **API Routes**: Backend-like functionality is implemented through API routes in the `/app/api` directory, handling search requests and data fetching
- **SSR (Server-Side Rendering)**: Critical pages utilize SSR for improved initial load performance and SEO
- **Middleware**: Custom middleware handles authentication and request processing
- **Image Optimization**: Next.js Image component optimizes image loading for search results
- **Turbopack**: Enabled for faster development experience with hot module replacement

### React 19

As the UI library, React 19 powers all interactive components:

- **Server Components**: The project leverages React 19's server components for improved performance
- **Hooks**: Extensive use of hooks like `useState`, `useEffect`, `useRef`, and custom hooks in `/hooks` directory
- **Client Components**: Marked with `'use client'` directive for interactive features
- **Context API**: Used for state management, particularly for search state and theme

### TypeScript

TypeScript provides static typing throughout the codebase:

- **Type Definitions**: Custom types in `/types` directory define interfaces for search parameters, results, and API responses
- **Type Safety**: All components and functions have explicit typing for arguments and return values
- **Type Guards**: Used to handle conditional logic based on data types
- **Generics**: Employed for reusable components and functions that work with different data types

### Tailwind CSS

Tailwind CSS handles styling with a utility-first approach:

- **Custom Configuration**: Tailored configuration in `tailwind.config.ts` includes extended color schemes and custom components
- **Responsive Design**: Breakpoint utilities ensure proper rendering across device sizes
- **Dark Mode Support**: Theme-based dark mode implementation using CSS variables
- **Component Classes**: Composite utility classes defined for consistent UI elements

### Radix UI

Radix UI provides accessible, unstyled component primitives:

- **Dialog Components**: Used for modals, alerts, and confirmation dialogs
- **Navigation Components**: Menu bars and dropdown navigations
- **Form Components**: Form controls like checkbox, radio, select, and input components
- **Feedback Components**: Toast notifications and progress indicators
- **Layout Components**: Accordion, tabs, and collapsible sections

### React Hook Form with Zod

Form handling uses React Hook Form with Zod validation:

- **Form State Management**: Implemented in search forms for maintaining input state
- **Schema Validation**: Zod schemas define validation rules for search parameters
- **Error Handling**: Validation errors displayed inline with form fields
- **Form Submission**: Controlled submission process with loading states

### Konva/React-Konva

Canvas manipulation is handled by React-Konva:

- **Symbol Canvas**: The interactive drawing surface for visual queries
- **Drag-and-Drop Elements**: Draggable symbols that users can position
- **Coordinate System**: Translate pixel positions to search parameters
- **Layer Management**: Multiple canvas layers for different interaction modes

## Development Tools

### Turbo

Monorepo management with Turbo:

- **Workspace Configuration**: Defined in `turbo.json` with optimized build pipelines
- **Task Running**: Standardized scripts for development, building, and testing
- **Caching**: Build artifacts caching for faster rebuilds
- **Dependencies**: Manages internal package dependencies

### pnpm

Package management using pnpm:

- **Workspace Support**: Configured in `pnpm-workspace.yaml` for monorepo package management
- **Dependency Hoisting**: Efficient node_modules structure
- **Lockfile**: Deterministic builds via `pnpm-lock.yaml`

### ESLint/Prettier

Code quality tools:

- **Custom ESLint Config**: Project-specific rules defined in ESLint configuration
- **Prettier Integration**: Code formatting synchronized with ESLint
- **Husky Hooks**: Pre-commit hooks enforce code quality standards
- **Editor Integration**: VSCode setup for inline linting and formatting

### next-themes

Theme management:

- **Theme Provider**: Wraps the application for consistent theme context
- **Theme Switching**: UI controls for toggling between light and dark modes
- **System Preference Detection**: Automatically matches system color scheme
- **Persistent Preferences**: Saves user theme preference to local storage
