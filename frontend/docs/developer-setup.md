# Developer Setup Guide

## Prerequisites

### System Requirements

- **Node.js**: 18.16.1 or higher
- **pnpm**: 9.1.0 (recommended package manager)
- **Git**: Latest version
- **VS Code**: Recommended editor with extensions

### Hardware Recommendations

- **RAM**: 8GB minimum, 16GB recommended
- **Storage**: 2GB free space for dependencies
- **CPU**: Multi-core processor for optimal build performance

## Quick Setup

### 1. Repository Clone

```bash
# Clone the repository
git clone <repository-url>
cd vbs-web

# Navigate to frontend directory
cd frontend
```

### 2. Package Manager Setup

```bash
# Install pnpm globally (if not already installed)
npm install -g pnpm@9.1.0

# Verify installation
pnpm --version
```

### 3. Dependencies Installation

```bash
# Install all dependencies
pnpm install

# Verify installation
pnpm list --depth=0
```

### 4. Development Server

```bash
# Start development server
pnpm dev

# Alternative with turbopack (faster)
pnpm dev --turbo
```

**Application URL**: `http://localhost:8080`

## Project Structure Deep Dive

```
frontend/
├── 📁 app/                     # Next.js App Router
│   ├── 📄 layout.tsx          # Root layout with providers
│   ├── 📄 page.tsx            # Home page (main search interface)
│   ├── 📄 loading.tsx         # Global loading UI
│   ├── 📄 globals.css         # Global styles
│   │
│   ├── 📁 api/                # Backend API routes
│   │   ├── 📁 search/         # Text search endpoint
│   │   ├── 📁 search-detections/ # Visual object search
│   │   ├── 📁 neighbor/       # Similar image search
│   │   ├── 📁 visual_search/  # Symbol-based search
│   │   └── 📁 images/         # Static image serving
│   │
│   ├── 📁 find-image/         # ID-based search page
│   │   ├── 📄 page.tsx        # Find by ID interface
│   │   └── 📄 loading.tsx     # Page loading state
│   │
│   └── 📁 image/[id]/         # Dynamic image detail pages
│       └── 📄 page.tsx        # Individual image view
│
├── 📁 components/             # Reusable UI components
│   ├── 📄 search-bar.tsx     # Main search input
│   ├── 📄 search-results.tsx # Results display (361 lines)
│   ├── 📄 symbol-grid.tsx    # Visual search interface
│   ├── 📄 ocr-search.tsx     # OCR text search
│   ├── 📄 draggable-symbol.tsx # Drag-and-drop symbols
│   ├── 📄 theme-provider.tsx # Dark/light theme management
│   │
│   ├── 📁 ui/                # Shadcn/UI components (30+ components)
│   │   ├── 📄 button.tsx     # Button variants with CVA
│   │   ├── 📄 input.tsx      # Form input components
│   │   ├── 📄 card.tsx       # Content containers
│   │   ├── 📄 dialog.tsx     # Modal dialogs
│   │   ├── 📄 toast.tsx      # Notification system
│   │   └── ... (25+ more UI components)
│   │
│   └── 📁 empty-state/       # Empty state illustrations
│       └── 📄 icons.tsx      # Custom SVG icons
│
├── 📁 services/              # API service layer
│   └── 📄 api.ts            # HTTP client and API functions
│
├── 📁 hooks/                 # Custom React hooks
│   ├── 📄 use-toast.ts      # Toast notification hook
│   └── 📄 use-mobile.tsx    # Mobile detection hook
│
├── 📁 lib/                   # Utility functions
│   └── 📄 utils.ts          # Common utilities (cn, URL conversion)
│
├── 📁 types/                 # TypeScript type definitions
│   ├── 📄 frame.ts          # Image/frame interfaces
│   └── 📄 object.ts         # Object detection types
│
├── 📁 constants/             # Application constants
│   └── 📄 objects.ts        # Symbol definitions and metadata
│
├── 📁 public/               # Static assets
│   ├── 📁 palette/          # Symbol images (33 object types)
│   └── 📄 placeholder.svg   # Fallback images
│
├── 📁 styles/               # Additional stylesheets
│   └── 📄 globals.css       # Additional global styles
│
├── 📁 docs/                 # Documentation
│   ├── 📄 readme.md         # Project overview
│   ├── 📄 api-reference.md  # API documentation
│   ├── 📄 component-guide.md # Component architecture
│   ├── 📄 user-guide.md     # User documentation
│   └── 📄 developer-setup.md # This file
│
└── 📁 Configuration Files
    ├── 📄 next.config.mjs    # Next.js configuration
    ├── 📄 tailwind.config.ts # Tailwind CSS configuration
    ├── 📄 tsconfig.json      # TypeScript configuration
    ├── 📄 components.json    # Shadcn/UI configuration
    ├── 📄 package.json       # Dependencies and scripts
    └── 📄 postcss.config.mjs # PostCSS configuration
```

## Development Scripts

### Available Commands

```bash
# Development
pnpm dev              # Start development server (port 8080)
pnpm dev --turbo      # Start with Turbopack (faster builds)

# Production
pnpm build            # Build for production
pnpm start            # Start production server
pnpm start --port=3000 # Start on custom port

# Code Quality
pnpm lint             # Run ESLint checks
pnpm lint --fix       # Fix auto-fixable lint issues
pnpm type-check       # Run TypeScript compiler

# Package Management
pnpm install          # Install dependencies
pnpm update           # Update dependencies
pnpm audit            # Security audit
```

### Monorepo Integration

```bash
# From project root (vbs-web/)
pnpm dev:web          # Start frontend development
turbo run dev         # Run all dev servers
turbo run build       # Build all packages
turbo run lint        # Lint all packages
```

## Technology Stack Configuration

### Next.js Configuration (`next.config.mjs`)

```javascript
const nextConfig = {
  // Performance optimizations
  experimental: {
    webpackBuildWorker: true,
    parallelServerBuildTraces: true,
    parallelServerCompiles: true,
  },

  // Image handling
  images: {
    unoptimized: true, // For development
  },

  // API routing
  async rewrites() {
    return [
      {
        source: '/images/:path*',
        destination: '/api/images/:path*',
      },
    ];
  },
};
```

### TypeScript Configuration (`tsconfig.json`)

```json
{
  "compilerOptions": {
    "target": "ES2017",
    "lib": ["dom", "dom.iterable", "ES6"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [
      {
        "name": "next"
      }
    ],
    "baseUrl": ".",
    "paths": {
      "@/*": ["./*"]
    }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
```

### Tailwind Configuration (`tailwind.config.ts`)

```typescript
import type { Config } from "tailwindcss"

const config: Config = {
  darkMode: ["class"],
  content: [
    './pages/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './app/**/*.{ts,tsx}',
    './src/**/*.{ts,tsx}',
  ],
  prefix: "",
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: {
        "2xl": "1400px",
      },
    },
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        // ... additional color variables
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      keyframes: {
        "accordion-down": {
          from: { height: "0" },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: "0" },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
}

export default config
```

## Development Environment

### VS Code Setup

#### Recommended Extensions

```json
{
  "recommendations": [
    "bradlc.vscode-tailwindcss",
    "esbenp.prettier-vscode",
    "ms-vscode.vscode-typescript-next",
    "ms-vscode.vscode-eslint",
    "unifiedjs.vscode-mdx",
    "ms-vscode.vscode-json"
  ]
}
```

#### VS Code Settings (`.vscode/settings.json`)

```json
{
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "esbenp.prettier-vscode",
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": true
  },
  "typescript.preferences.importModuleSpecifier": "relative",
  "tailwindCSS.experimental.classRegex": [
    ["cva\\(([^)]*)\\)", "[\"'`]([^\"'`]*).*?[\"'`]"],
    ["cx\\(([^)]*)\\)", "(?:'|\"|`)([^']*)(?:'|\"|`)"]
  ]
}
```

#### Debugging Configuration (`.vscode/launch.json`)

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Next.js: debug server-side",
      "type": "node-terminal",
      "request": "launch",
      "command": "pnpm dev"
    },
    {
      "name": "Next.js: debug client-side",
      "type": "chrome",
      "request": "launch",
      "url": "http://localhost:8080"
    }
  ]
}
```

### Git Configuration

#### Pre-commit Hooks (`package.json`)

```json
{
  "husky": {
    "hooks": {
      "pre-commit": "lint-staged",
      "commit-msg": "commitlint -E HUSKY_GIT_PARAMS"
    }
  },
  "lint-staged": {
    "*.{js,jsx,ts,tsx}": [
      "eslint --fix",
      "prettier --write"
    ],
    "*.{json,md}": [
      "prettier --write"
    ]
  }
}
```

#### Commit Message Convention

```bash
# Format: type(scope): description

# Types:
feat: new feature
fix: bug fix
docs: documentation
style: formatting
refactor: code refactoring
test: adding tests
chore: maintenance

# Examples:
feat(search): add OCR text search functionality
fix(api): resolve image loading timeout issues
docs(readme): update setup instructions
style(components): format search-results component
refactor(hooks): extract image caching logic
```

## API Development

### Creating New API Routes

#### 1. Route Structure

```typescript
// app/api/new-endpoint/route.ts
import { type NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  try {
    // Handle GET requests
    const searchParams = request.nextUrl.searchParams;
    const query = searchParams.get('q');

    // Process request
    const result = await processRequest(query);

    return NextResponse.json(result);
  } catch (error) {
    console.error('API Error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

export async function POST(request: NextRequest) {
  try {
    // Handle POST requests
    const body = await request.json();

    // Validate input
    const validatedInput = validateInput(body);

    // Process request
    const result = await processRequest(validatedInput);

    return NextResponse.json(result);
  } catch (error) {
    if (error instanceof ValidationError) {
      return NextResponse.json(
        { error: error.message },
        { status: 400 }
      );
    }

    console.error('API Error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
```

#### 2. Input Validation with Zod

```typescript
import { z } from 'zod';

const SearchSchema = z.object({
  query: z.string().min(1, 'Query is required'),
  limit: z.number().min(1).max(100).default(20),
  filters: z.object({
    category: z.string().optional(),
    dateRange: z.object({
      start: z.string().datetime().optional(),
      end: z.string().datetime().optional(),
    }).optional(),
  }).optional(),
});

type SearchInput = z.infer<typeof SearchSchema>;

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const input = SearchSchema.parse(body);

    // Now input is fully typed and validated
    const results = await searchService(input);

    return NextResponse.json(results);
  } catch (error) {
    if (error instanceof z.ZodError) {
      return NextResponse.json(
        { error: 'Validation failed', details: error.errors },
        { status: 400 }
      );
    }
    // Handle other errors...
  }
}
```

### Service Layer Pattern

```typescript
// services/search.ts
export class SearchService {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  async textSearch(params: SearchParams): Promise<SearchResult[]> {
    const response = await fetch(`${this.baseUrl}/search`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    });

    if (!response.ok) {
      throw new APIError(`Search failed: ${response.status}`);
    }

    return response.json();
  }

  async visualSearch(params: VisualSearchParams): Promise<SearchResult[]> {
    // Implementation...
  }
}

// Usage in API route
const searchService = new SearchService(process.env.BACKEND_URL!);

export async function POST(request: NextRequest) {
  const body = await request.json();
  const results = await searchService.textSearch(body);
  return NextResponse.json(results);
}
```

## Component Development

### Component Creation Workflow

#### 1. Create Component File

```typescript
// components/new-component.tsx
'use client';

import { useState, useEffect } from 'react';
import { cn } from '@/lib/utils';

interface NewComponentProps {
  required: string;
  optional?: boolean;
  children?: React.ReactNode;
  className?: string;
}

export default function NewComponent({
  required,
  optional = false,
  children,
  className,
}: NewComponentProps) {
  const [state, setState] = useState<boolean>(false);

  useEffect(() => {
    // Effect logic
  }, [required]);

  const handleClick = () => {
    setState(!state);
  };

  return (
    <div
      className={cn(
        "base-styles",
        optional && "optional-styles",
        className
      )}
      onClick={handleClick}
    >
      {children}
    </div>
  );
}
```

#### 2. Add to Component Index

```typescript
// components/index.ts
export { default as NewComponent } from './new-component';
export { default as SearchBar } from './search-bar';
export { default as SearchResults } from './search-results';
// ... other exports
```

#### 3. Create Tests

```typescript
// __tests__/new-component.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import NewComponent from '@/components/new-component';

describe('NewComponent', () => {
  it('renders with required props', () => {
    render(<NewComponent required="test" />);
    expect(screen.getByRole('button')).toBeInTheDocument();
  });

  it('handles click events', () => {
    const mockFn = jest.fn();
    render(<NewComponent required="test" onClick={mockFn} />);

    fireEvent.click(screen.getByRole('button'));
    expect(mockFn).toHaveBeenCalled();
  });
});
```

### UI Component Guidelines

#### Shadcn/UI Integration

```typescript
// Example: Creating a new UI component
import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const newComponentVariants = cva(
  "inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground hover:bg-primary/90",
        destructive: "bg-destructive text-destructive-foreground hover:bg-destructive/90",
        outline: "border border-input bg-background hover:bg-accent hover:text-accent-foreground",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-9 rounded-md px-3",
        lg: "h-11 rounded-md px-8",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

export interface NewComponentProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof newComponentVariants> {
  asChild?: boolean
}

const NewComponent = React.forwardRef<HTMLButtonElement, NewComponentProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button"
    return (
      <Comp
        className={cn(newComponentVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    )
  }
)
NewComponent.displayName = "NewComponent"

export { NewComponent, newComponentVariants }
```

## Testing Setup

### Test Configuration

#### Jest Configuration (`jest.config.js`)

```javascript
const nextJest = require('next/jest')

const createJestConfig = nextJest({
  dir: './',
})

const customJestConfig = {
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  testEnvironment: 'jest-environment-jsdom',
  moduleNameMapping: {
    '^@/(.*)$': '<rootDir>/$1',
  },
  collectCoverageFrom: [
    'components/**/*.{js,jsx,ts,tsx}',
    'app/**/*.{js,jsx,ts,tsx}',
    'services/**/*.{js,jsx,ts,tsx}',
    'hooks/**/*.{js,jsx,ts,tsx}',
    '!**/*.d.ts',
    '!**/node_modules/**',
  ],
}

module.exports = createJestConfig(customJestConfig)
```

#### Test Setup (`jest.setup.js`)

```javascript
import '@testing-library/jest-dom'

// Mock Next.js router
jest.mock('next/router', () => ({
  useRouter() {
    return {
      route: '/',
      pathname: '/',
      query: '',
      asPath: '',
      push: jest.fn(),
      pop: jest.fn(),
      reload: jest.fn(),
      back: jest.fn(),
      prefetch: jest.fn().mockResolvedValue(undefined),
      beforePopState: jest.fn(),
      events: {
        on: jest.fn(),
        off: jest.fn(),
        emit: jest.fn(),
      },
    }
  },
}))

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(),
    removeListener: jest.fn(),
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
})
```

### Running Tests

```bash
# Run all tests
pnpm test

# Run tests in watch mode
pnpm test --watch

# Run tests with coverage
pnpm test --coverage

# Run specific test file
pnpm test search-bar.test.tsx

# Run tests matching pattern
pnpm test --testNamePattern="should render"
```

## Performance Optimization

### Bundle Analysis

```bash
# Analyze bundle size
ANALYZE=true pnpm build

# View bundle analyzer report
# Opens in browser at http://localhost:8888
```

### Performance Monitoring

```typescript
// Add to pages for performance tracking
import { getCLS, getFID, getFCP, getLCP, getTTFB } from 'web-vitals';

function sendToAnalytics(metric) {
  // Send to your analytics service
  console.log(metric);
}

// Measure all Web Vitals
getCLS(sendToAnalytics);
getFID(sendToAnalytics);
getFCP(sendToAnalytics);
getLCP(sendToAnalytics);
getTTFB(sendToAnalytics);
```

### Image Optimization

```typescript
// Optimize images in components
import Image from 'next/image';

<Image
  src="/image.jpg"
  alt="Description"
  width={500}
  height={300}
  priority={isAboveTheFold}
  loading={isAboveTheFold ? "eager" : "lazy"}
  placeholder="blur"
  blurDataURL="data:image/svg+xml;base64,..."
/>
```

## Deployment

### Build Process

```bash
# Create production build
pnpm build

# Test production build locally
pnpm start

# Check build output
ls -la .next/static/
```

### Environment Variables

```bash
# .env.local (for development)
NEXT_PUBLIC_API_URL=http://localhost:3001
NEXT_PUBLIC_ENVIRONMENT=development

# .env.production (for production)
NEXT_PUBLIC_API_URL=https://api.production.com
NEXT_PUBLIC_ENVIRONMENT=production
```

### Docker Configuration (Optional)

```dockerfile
# Dockerfile
FROM node:18-alpine AS deps
WORKDIR /app
COPY package.json pnpm-lock.yaml ./
RUN npm install -g pnpm && pnpm install --frozen-lockfile

FROM node:18-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm install -g pnpm && pnpm build

FROM node:18-alpine AS runner
WORKDIR /app
ENV NODE_ENV production

COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

EXPOSE 8080
ENV PORT 8080

CMD ["node", "server.js"]
```

## Troubleshooting

### Common Issues

#### 1. Port Already in Use

```bash
# Kill process on port 8080
lsof -ti:8080 | xargs kill -9

# Or use different port
pnpm dev -- --port=3001
```

#### 2. Module Resolution Issues

```bash
# Clear Next.js cache
rm -rf .next

# Clear node_modules and reinstall
rm -rf node_modules pnpm-lock.yaml
pnpm install
```

#### 3. TypeScript Errors

```bash
# Run type checking
pnpm tsc --noEmit

# Generate types
pnpm build
```

#### 4. Build Failures

```bash
# Verbose build output
DEBUG=* pnpm build

# Check dependency issues
pnpm audit
pnpm update
```

### Performance Issues

#### 1. Slow Development Server

- Enable Turbopack: `pnpm dev --turbo`
- Increase Node.js memory: `NODE_OPTIONS="--max-old-space-size=4096" pnpm dev`
- Clear `.next` cache regularly

#### 2. Large Bundle Size

- Analyze bundle: `ANALYZE=true pnpm build`
- Use dynamic imports for large components
- Remove unused dependencies

#### 3. Slow Image Loading

- Optimize image sizes
- Use Next.js Image component
- Implement proper caching headers

### Debug Configuration

#### Chrome DevTools

1. **Enable source maps** in development
2. **Use React DevTools** extension
3. **Monitor Network tab** for API calls
4. **Check Console** for errors and warnings

#### VS Code Debugging

1. **Set breakpoints** in TypeScript files
2. **Use debug console** for variable inspection
3. **Step through code** execution
4. **Inspect component state** and props

This comprehensive setup guide covers everything needed to develop effectively with VBS-Web 2.0. Follow these configurations and best practices for optimal development experience.
