.PHONY: help dev build test clean docker-up docker-down docker-build index ingest

# Default target
help:
	@echo "MM-Data Intelligent Agent - Available Commands:"
	@echo ""
	@echo "Development:"
	@echo "  make dev          - Start both frontend and backend development servers"
	@echo "  make dev-frontend - Start only frontend development server"
	@echo "  make dev-backend  - Start only backend development server"
	@echo "  AIC_ENV=prod make dev - Start with Google Drive data source"
	@echo ""
	@echo "Building:"
	@echo "  make build        - Build both frontend and backend"
	@echo "  make build-frontend - Build frontend only"
	@echo "  make build-backend  - Build backend only"
	@echo ""
	@echo "Testing:"
	@echo "  make test         - Run all tests"
	@echo "  make test-frontend - Run frontend tests"
	@echo "  make test-backend  - Run backend tests"
	@echo "  make test-installation - Test complete installation"
	@echo ""
	@echo "Indexing Pipeline:"
	@echo "  make sample-data  - Generate sample data for testing"
	@echo "  make ingest       - Run video ingestion pipeline"
	@echo "  make build-faiss  - Build FAISS indexes from HDF5 files"
	@echo "  make build-lucene - Build Lucene/Whoosh indexes from HDF5 files"
	@echo "  make index        - Run complete indexing pipeline (ingest + build indexes)"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-up    - Start all services with Docker Compose"
	@echo "  make docker-down  - Stop all Docker services"
	@echo "  make docker-build - Build Docker images"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean        - Clean build artifacts"
	@echo "  make install      - Install all dependencies"
	@echo "  make lint         - Run linting and formatting"

# Development
dev:
	@echo "Starting both backend and frontend development servers..."
	@echo "Backend will run on http://localhost:8000"
	@echo "Frontend will run on http://localhost:3000"
	@echo "Environment: $${AIC_ENV:-dev}"
	@echo "Press Ctrl+C to stop both servers"
	@trap 'kill %1 %2 2>/dev/null || true' INT; \
	(cd backend && export KMP_DUPLICATE_LIB_OK=TRUE && export AIC_ENV=$${AIC_ENV:-dev} && python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000) & \
	(cd frontend && pnpm dev) & \
	wait

dev-frontend:
	@echo "Starting frontend development server..."
	cd frontend && pnpm dev

dev-backend:
	@echo "Starting backend development server..."
	cd backend && export KMP_DUPLICATE_LIB_OK=TRUE && python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Building
build: build-backend build-frontend

build-frontend:
	@echo "Building frontend..."
	cd frontend && pnpm build

build-backend:
	@echo "Building backend..."
	cd backend && python -m pip install -r requirements.txt

# Testing
test: test-backend test-frontend

test-frontend:
	@echo "Running frontend tests..."
	cd frontend && pnpm test

test-backend:
	@echo "Running backend tests..."
	cd backend && export KMP_DUPLICATE_LIB_OK=TRUE && python -m pytest tests/ -v

test-installation:
	@echo "Testing installation..."
	./scripts/test-installation.sh

# Indexing Pipeline
sample-data:
	@echo "Generating sample data..."
	python scripts/sample_data_generator.py --clean

ingest:
	@echo "Running video ingestion pipeline..."
	# python scripts/ingest.py --input data/raw/keyframes/Keyframes_L22 --output data/hdf5_features

build-faiss:
	@echo "Building FAISS indexes..."
	python scripts/build_faiss.py --input data/hdf5_features --output data/indexes/faiss --combined --validate

build-lucene:
	@echo "Building Lucene/Whoosh indexes..."
	python scripts/build_lucene.py --input data/hdf5_features --output data/indexes/lucene --combined --validate

index: sample-data ingest build-faiss build-lucene
	@echo "Complete indexing pipeline finished!"

# Docker
docker-up:
	@echo "Starting Docker services..."
	docker-compose -f infra/docker-compose.yml up -d

docker-down:
	@echo "Stopping Docker services..."
	docker-compose -f infra/docker-compose.yml down

docker-build:
	@echo "Building Docker images..."
	docker-compose -f infra/docker-compose.yml build

# Utilities
clean:
	@echo "Cleaning build artifacts..."
	rm -rf frontend/.next
	rm -rf frontend/node_modules
	rm -rf backend/__pycache__
	rm -rf backend/*/__pycache__
	rm -rf data/
	rm -rf examples/sample_data/
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -delete

install: install-frontend install-backend

install-frontend:
	@echo "Installing frontend dependencies..."
	cd frontend && pnpm install

install-backend:
	@echo "Installing backend dependencies..."
	cd backend && python -m pip install -r requirements.txt

lint:
	@echo "Running linting and formatting..."
	cd backend && black . && isort . && flake8 .
	cd frontend && pnpm lint

# Environment setup
setup:
	@echo "Setting up development environment..."
	@echo "1. Installing dependencies..."
	make install
	@echo "2. Setting up pre-commit hooks..."
	@echo "3. Environment ready!"
	@echo ""
	@echo "To start development:"
	@echo "  make dev          # Start both frontend and backend"
	@echo "  make index        # Run complete indexing pipeline"
	@echo "  make docker-up    # Start with Docker Compose"
