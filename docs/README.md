# MM-Data Intelligent Agent - Documentation Index

## Welcome to the Documentation

This documentation provides comprehensive coverage of the MM-Data Intelligent Agent system, designed to help team members understand everything from backend architecture to frontend development and data processing workflows.

## Documentation Structure

### Getting Started

- **[Consolidated System Overview](00-consolidated-overview.md)** - Complete system understanding
- **[Data Connection Guide](01-data-connection-guide.md)** - How to make search work successfully
- **[Development Workflow](02-development-workflow.md)** - Daily development practices

### Technical Documentation

- **[Backend Architecture](backend-architecture.md)** - FastAPI backend design and structure
- **[Run Guide](run-guide.md)** - Complete setup and running instructions
- **[Indexing Pipeline](indexing-pipeline.md)** - Data processing and feature extraction

### Support & Troubleshooting

- **[Troubleshooting Guide](03-troubleshooting-guide.md)** - Common issues and solutions

## Quick Start for New Team Members

### 1. Read the Consolidated Overview

Start with **[00-consolidated-overview.md](00-consolidated-overview.md)** to understand:

- What the system does
- How the components work together
- The complete data flow
- Architecture overview

### 2. Set Up Your Development Environment

Follow **[01-data-connection-guide.md](01-data-connection-guide.md)** to:

- Set up the backend environment
- Generate sample data
- Build search indexes
- Verify search functionality works

### 3. Learn the Development Workflow

Review **[02-development-workflow.md](02-development-workflow.md)** to understand:

- Daily development practices
- How to add new features
- Testing and debugging workflows
- Deployment processes

## What Each Document Covers

### Consolidated System Overview

**Purpose**: Complete system understanding for all team members

**Covers**:

- System purpose and capabilities
- High-level architecture
- Complete data flow explanation
- Frontend and backend overview
- Data layer structure
- Getting started checklist

**Best for**: New team members, system architects, product managers

---

### Data Connection Guide

**Purpose**: Make search functionality work successfully

**Covers**:

- Critical data requirements
- Step-by-step data setup
- Understanding the data pipeline
- Troubleshooting data issues
- Data validation checklist
- Emergency data recovery

**Best for**: Developers setting up the system, data engineers, ML engineers

---

### Development Workflow

**Purpose**: Daily development practices and workflows

**Covers**:

- Daily development routine
- Development commands reference
- Project structure understanding
- Adding new features
- Testing and debugging
- Performance optimization
- Deployment workflows

**Best for**: Active developers, team leads, DevOps engineers

---

### Backend Architecture

**Purpose**: Deep technical understanding of the backend

**Covers**:

- FastAPI application structure
- Service layer architecture
- API endpoint design
- Performance features
- Development features
- Integration points

**Best for**: Backend developers, system architects, API designers

---

### Run Guide

**Purpose**: Complete setup and running instructions

**Covers**:

- Prerequisites and installation
- Local development setup
- Docker Compose deployment
- Testing ML models
- Troubleshooting common issues
- Performance monitoring

**Best for**: DevOps engineers, system administrators, developers setting up environments

---

### Indexing Pipeline

**Purpose**: Data processing and feature extraction

**Covers**:

- Video indexing pipeline
- Feature extraction components
- FAISS index building
- Data structure and formats
- Performance considerations
- Integration with backend

**Best for**: Data engineers, ML engineers, researchers

---

### Troubleshooting Guide

**Purpose**: Solve common issues quickly

**Covers**:

- Critical issues (search not working)
- Development environment issues
- Docker problems
- Performance issues
- Frontend-specific problems
- Emergency recovery procedures

**Best for**: All team members when encountering issues

## How to Use This Documentation

### For New Team Members

1. **Start with** [Consolidated System Overview](00-consolidated-overview.md)
2. **Set up your environment** using [Data Connection Guide](01-data-connection-guide.md)
3. **Learn development practices** from [Development Workflow](02-development-workflow.md)
4. **Reference** [Troubleshooting Guide](03-troubleshooting-guide.md) when you encounter issues

### For Developers

1. **Daily reference**: [Development Workflow](02-development-workflow.md)
2. **Architecture understanding**: [Backend Architecture](backend-architecture.md)
3. **Setup and deployment**: [Run Guide](run-guide.md)
4. **Problem solving**: [Troubleshooting Guide](03-troubleshooting-guide.md)

### For Data Engineers/ML Engineers

1. **Data processing**: [Indexing Pipeline](indexing-pipeline.md)
2. **System integration**: [Backend Architecture](backend-architecture.md)
3. **Data setup**: [Data Connection Guide](01-data-connection-guide.md)
4. **Performance optimization**: [Development Workflow](02-development-workflow.md)

### For DevOps/System Administrators

1. **Deployment**: [Run Guide](run-guide.md)
2. **System architecture**: [Consolidated System Overview](00-consolidated-overview.md)
3. **Troubleshooting**: [Troubleshooting Guide](03-troubleshooting-guide.md)
4. **Performance**: [Development Workflow](02-development-workflow.md)

## Common Documentation Tasks

### Adding New Features

1. **Backend**: Follow patterns in [Development Workflow](02-development-workflow.md)
2. **Frontend**: Use component patterns from [Development Workflow](02-development-workflow.md)
3. **Documentation**: Update relevant sections in these guides

### Troubleshooting Issues

1. **Check** [Troubleshooting Guide](03-troubleshooting-guide.md) first
2. **Use diagnostic commands** from the troubleshooting guide
3. **Check logs** and system status
4. **Update documentation** if you find new solutions

### Setting Up New Environments

1. **Follow** [Data Connection Guide](01-data-connection-guide.md) step-by-step
2. **Use** [Run Guide](run-guide.md) for deployment options
3. **Verify** with health checks and test searches
4. **Document** any environment-specific configurations

## Documentation Maintenance

### Keeping Documentation Updated

- **Update guides** when adding new features
- **Add troubleshooting steps** for new issues encountered
- **Review and update** setup instructions regularly
- **Maintain consistency** across all documents

### Documentation Standards

- **Use clear headings** and consistent formatting
- **Include code examples** for all technical procedures
- **Provide diagnostic commands** for troubleshooting
- **Keep information current** with system changes

## Getting Help

### When Documentation Doesn't Help

1. **Check the troubleshooting guide** for similar issues
2. **Review system logs** for error details
3. **Test with sample data** to isolate problems
4. **Ask the team** for specific guidance

### Contributing to Documentation

1. **Document solutions** to new problems you encounter
2. **Update procedures** when you find better approaches
3. **Add examples** for common use cases
4. **Review and improve** existing documentation

---

## Quick Reference

### Essential Commands

```bash
# Development
make dev              # Start development environment
make index            # Generate sample data and build indexes
make test             # Run all tests

# Data Pipeline
make sample-data      # Generate test data
make ingest           # Extract features
make build-faiss      # Build search indexes

# Docker
make docker-up        # Start with Docker Compose
make docker-down      # Stop Docker services
```

### Critical Files

```
backend/.env          # Backend configuration
frontend/.env.local   # Frontend configuration
dict/faiss_*.bin      # Search indexes (CRITICAL)
support_models/       # ML model weights (CRITICAL)
```

### Health Checks

```bash
# Backend health
curl http://localhost:8000/health/

# Search test
curl -X POST http://localhost:8000/api/search/text \
  -H "Content-Type: application/json" \
  -d '{"query":"test","model_type":"longclip","limit":5}'
```

---

**Remember**: This documentation is a living resource. Keep it updated as you learn new things about the system, and use it to help other team members get up to speed quickly.

**Happy coding! 🚀**
