# VBS-Web Documentation

Welcome to the comprehensive documentation for VBS-Web, a sophisticated image search application built with Next.js that provides multiple search methods for finding and exploring images.

## Documentation Sections

This documentation is organized into the following detailed sections:

1. [Project Overview](./01-project-overview.md) - A comprehensive introduction to VBS-Web's purpose, functionality, and goals
2. [Tech Stack](./02-tech-stack.md) - Detailed explanation of the technologies used and how they're implemented
3. [Key Features](./03-key-features.md) - In-depth breakdown of the application's core features and their implementation
4. [Architecture](./04-architecture.md) - Technical details about the system architecture and technology integration
5. [Unique Aspects](./05-unique-aspects.md) - Deep dive into what makes VBS-Web unique, with technical implementation details

## Quick Start

To run the application locally:

```bash
# Install dependencies
pnpm install

# Start the development server
pnpm dev:web
```

The application will be available at <http://localhost:8080>.

## Main Documentation

For a high-level overview of the project, see the [README](./readme.md).

## Project Structure

The VBS-Web application follows a modern Next.js project structure:

```
/frontend
├── app/                # Next.js App Router pages and API routes
│   ├── api/            # Backend API endpoints
│   ├── find-image/     # Image lookup by ID page
│   ├── image/          # Individual image view page
│   └── page.tsx        # Main homepage
├── components/         # Reusable React components
├── services/           # API service functions
├── hooks/              # Custom React hooks
├── lib/                # Utility functions and helpers
├── public/             # Static assets
├── styles/             # Global styles
├── types/              # TypeScript type definitions
```

## Contributing

To contribute to the project, please follow the standard Git workflow:

1. Create a feature branch from main
2. Implement your changes with appropriate tests
3. Submit a pull request for review

## Contact

For questions or support, please contact the project maintainers.
