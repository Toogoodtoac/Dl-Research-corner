#!/bin/bash

# MM-Data Intelligent Agent - Installation Test Script
# This script tests if your installation is working correctly

set -e

echo "🔍 MM-Data Intelligent Agent - Installation Test"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
  local status=$1
  local message=$2
  if [ "$status" = "OK" ]; then
    echo -e "${GREEN}✅ $message${NC}"
  elif [ "$status" = "WARN" ]; then
    echo -e "${YELLOW}⚠️  $message${NC}"
  elif [ "$status" = "ERROR" ]; then
    echo -e "${RED}❌ $message${NC}"
  else
    echo -e "${BLUE}ℹ️  $message${NC}"
  fi
}

# Function to check if a command exists
command_exists() {
  command -v "$1" >/dev/null 2>&1
}

# Function to check if a port is open
check_port() {
  local port=$1
  local service=$2
  if lsof -i :$port >/dev/null 2>&1; then
    print_status "OK" "$service is running on port $port"
    return 0
  else
    print_status "ERROR" "$service is not running on port $port"
    return 1
  fi
}

# Function to test HTTP endpoint
test_http() {
  local url=$1
  local description=$2
  if curl -s "$url" >/dev/null 2>&1; then
    print_status "OK" "$description is accessible"
    return 0
  else
    print_status "ERROR" "$description is not accessible"
    return 1
  fi
}

echo ""
echo "📋 Checking Prerequisites..."
echo "---------------------------"

# Check Python
if command_exists python3; then
  PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
  print_status "OK" "Python $PYTHON_VERSION found"
else
  print_status "ERROR" "Python 3 not found"
  exit 1
fi

# Check Node.js
if command_exists node; then
  NODE_VERSION=$(node --version)
  print_status "OK" "Node.js $NODE_VERSION found"
else
  print_status "ERROR" "Node.js not found"
  exit 1
fi

# Check pnpm
if command_exists pnpm; then
  PNPM_VERSION=$(pnpm --version)
  print_status "OK" "pnpm $PNPM_VERSION found"
else
  print_status "WARN" "pnpm not found (install with: npm install -g pnpm)"
fi

# Check Docker
if command_exists docker; then
  DOCKER_VERSION=$(docker --version | awk '{print $3}' | sed 's/,//')
  print_status "OK" "Docker $DOCKER_VERSION found"
else
  print_status "WARN" "Docker not found (optional for local development)"
fi

# Check Docker Compose
if command_exists docker-compose; then
  print_status "OK" "Docker Compose found"
elif docker compose version >/dev/null 2>&1; then
  print_status "OK" "Docker Compose (v2) found"
else
  print_status "WARN" "Docker Compose not found (optional for local development)"
fi

echo ""
echo "🏗️  Checking Repository Structure..."
echo "-----------------------------------"

# Check if we're in the right directory
if [ -f "backend/main.py" ] && [ -f "frontend/package.json" ]; then
  print_status "OK" "Repository structure looks correct"
else
  print_status "ERROR" "Not in the correct directory or repository structure is wrong"
  exit 1
fi

# Check for environment files
if [ -f "backend/env.example" ]; then
  print_status "OK" "Backend environment template found"
else
  print_status "ERROR" "Backend environment template not found"
fi

# Check for requirements.txt
if [ -f "backend/requirements.txt" ]; then
  print_status "OK" "Backend requirements.txt found"
else
  print_status "ERROR" "Backend requirements.txt not found"
fi

# Check for package.json
if [ -f "frontend/package.json" ]; then
  print_status "OK" "Frontend package.json found"
else
  print_status "ERROR" "Frontend package.json not found"
fi

echo ""
echo "🔧 Checking Backend Setup..."
echo "----------------------------"

# Check if .env exists
if [ -f "backend/.env" ]; then
  print_status "OK" "Backend .env file exists"
else
  print_status "WARN" "Backend .env file not found (run: cp backend/env.example backend/.env)"
fi

# Check if virtual environment exists
if [ -d ".venv" ] || [ -d "backend/.venv" ]; then
  print_status "OK" "Python virtual environment found"
else
  print_status "WARN" "Python virtual environment not found (run: python -m venv .venv)"
fi

# Check if backend dependencies are installed
if [ -d "backend/__pycache__" ] || [ -d ".venv/lib/python" ]; then
  print_status "OK" "Backend dependencies appear to be installed"
else
  print_status "WARN" "Backend dependencies may not be installed (run: pip install -r backend/requirements.txt)"
fi

echo ""
echo "🎨 Checking Frontend Setup..."
echo "-----------------------------"

# Check if frontend dependencies are installed
if [ -d "frontend/node_modules" ]; then
  print_status "OK" "Frontend dependencies are installed"
else
  print_status "WARN" "Frontend dependencies not installed (run: pnpm install)"
fi

# Check for frontend environment file
if [ -f "frontend/.env.local" ] || [ -f "frontend/.env" ]; then
  print_status "OK" "Frontend environment file found"
else
  print_status "WARN" "Frontend environment file not found (create frontend/.env.local)"
fi

echo ""
echo "🚀 Testing Services..."
echo "---------------------"

# Test backend if running
if check_port 8000 "Backend"; then
  if test_http "http://localhost:8000/health/" "Backend health endpoint"; then
    print_status "OK" "Backend is healthy and responding"
  fi
else
  print_status "WARN" "Backend is not running (start with: make dev-backend)"
fi

# Test frontend if running
if check_port 3000 "Frontend"; then
  if test_http "http://localhost:3000" "Frontend application"; then
    print_status "OK" "Frontend is accessible"
  fi
else
  print_status "WARN" "Frontend is not running (start with: make dev-frontend)"
fi

echo ""
echo "🧪 Testing ML Models..."
echo "----------------------"

# Check for model files
if [ -d "support_models" ]; then
  print_status "OK" "Support models directory exists"

  # Check for specific models
  if [ -d "support_models/Long-CLIP" ]; then
    print_status "OK" "Long-CLIP model directory found"
  else
    print_status "WARN" "Long-CLIP model directory not found"
  fi

  if [ -d "support_models/CLIP" ]; then
    print_status "OK" "CLIP model directory found"
  else
    print_status "WARN" "CLIP model directory not found"
  fi
else
  print_status "WARN" "Support models directory not found (run: git submodule update --init --recursive)"
fi

# Check for FAISS indices
if [ -d "dict" ]; then
  print_status "OK" "Dictionary directory exists"

  # Check for specific index files
  if [ -f "dict/faiss_longclip.bin" ]; then
    print_status "OK" "LongCLIP FAISS index found"
  else
    print_status "WARN" "LongCLIP FAISS index not found"
  fi

  if [ -f "dict/id2img.json" ]; then
    print_status "OK" "Image ID mapping found"
  else
    print_status "WARN" "Image ID mapping not found"
  fi
else
  print_status "WARN" "Dictionary directory not found"
fi

echo ""
echo "📊 Test Results Summary..."
echo "-------------------------"

# Count results
TOTAL_TESTS=$(grep -c "✅\|❌\|⚠️" <<<"$(grep -E "✅|❌|⚠️" <<<"$(grep -E "OK|ERROR|WARN" <<<"$(grep -E "print_status.*OK|print_status.*ERROR|print_status.*WARN" <<<"$(cat "$0")")")")" 2>/dev/null || echo "0")
PASSED_TESTS=$(grep -c "✅" <<<"$(grep -E "✅|❌|⚠️" <<<"$(grep -E "OK|ERROR|WARN" <<<"$(grep -E "print_status.*OK|print_status.*ERROR|print_status.*WARN" <<<"$(cat "$0")")")")" 2>/dev/null || echo "0")
FAILED_TESTS=$(grep -c "❌" <<<"$(grep -E "✅|❌|⚠️" <<<"$(grep -E "OK|ERROR|WARN" <<<"$(grep -E "print_status.*OK|print_status.*ERROR|print_status.*WARN" <<<"$(cat "$0")")")")" 2>/dev/null || echo "0")
WARNING_TESTS=$(grep -c "⚠️" <<<"$(grep -E "✅|❌|⚠️" <<<"$(grep -E "OK|ERROR|WARN" <<<"$(grep -E "print_status.*OK|print_status.*ERROR|print_status.*WARN" <<<"$(cat "$0")")")")" 2>/dev/null || echo "0")

echo "Total tests: $TOTAL_TESTS"
echo -e "${GREEN}Passed: $PASSED_TESTS${NC}"
echo -e "${RED}Failed: $FAILED_TESTS${NC}"
echo -e "${YELLOW}Warnings: $WARNING_TESTS${NC}"

echo ""
echo "🎯 Next Steps..."
echo "----------------"

if [ $FAILED_TESTS -eq 0 ]; then
  print_status "OK" "Installation looks good! You can now use the system."
  echo ""
  echo "To start development:"
  echo "  make dev-backend     # Start backend"
  echo "  make dev-frontend    # Start frontend"
  echo ""
  echo "To start with Docker:"
  echo "  make docker-up       # Start all services"
else
  print_status "ERROR" "Some tests failed. Please fix the issues above before proceeding."
  echo ""
  echo "Common fixes:"
  echo "  1. Run: cp backend/env.example backend/.env"
  echo "  2. Run: python -m venv .venv && source .venv/bin/activate"
  echo "  3. Run: pip install -r backend/requirements.txt"
  echo "  4. Run: pnpm install"
  echo "  5. Run: git submodule update --init --recursive"
fi

echo ""
echo "📖 For detailed setup instructions, see: docs/run-guide.md"
echo "🔧 For development commands, see: make help"
