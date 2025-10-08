# 🚀 Team Setup Guide

## Quick Start for New Team Members

This guide will help you get the MM-Data Intelligent Agent running locally in minutes.

## Prerequisites

### System Requirements
- **OS**: macOS 10.15+, Ubuntu 20.04+, or Windows 10+
- **Python**: 3.11 or 3.12
- **Node.js**: 18.x or 20.x
- **Git**: Latest version
- **Memory**: 8GB RAM minimum (16GB recommended)
- **Storage**: 10GB free space minimum

### Required Software
```bash
# Python
python --version  # Should be 3.11+
pip --version     # Should be latest

# Node.js
node --version    # Should be 18.x or 20.x
npm --version     # Should be latest

# Git
git --version     # Should be latest

# Package Managers
pnpm --version    # Should be 8.x+ (recommended)
# OR
npm --version     # Alternative to pnpm
```

## 🏗️ Installation Steps

### 1. Clone the Repository
```bash
# Clone with submodules (important!)
git clone --recursive <your-repo-url>
cd mm-data-intelligent-agent

# If you forgot --recursive, run:
git submodule update --init --recursive
```

### 2. Backend Setup
```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp env.example .env

# Edit .env with your settings
# (See Environment Configuration below)
```

### 3. Frontend Setup
```bash
# Navigate to frontend
cd ../frontend

# Install dependencies
pnpm install
# OR if you prefer npm:
npm install
```

### 4. Environment Configuration

#### Backend Environment (`.env`)
```bash
# Copy from template
cp backend/env.example backend/.env

# Edit backend/.env with your settings:
MODEL_DEVICE=cpu  # or 'cuda' if you have GPU
DATA_ROOT=../data
LOG_LEVEL=INFO
```

#### Frontend Environment
```bash
# Create .env.local in frontend directory
cd frontend
touch .env.local

# Add to .env.local:
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 🚀 Running the Application

### Option 1: Using Makefile (Recommended)
```bash
# Start both frontend and backend
make dev

# Or start individually:
make dev-backend    # Backend only
make dev-frontend   # Frontend only
```

### Option 2: Manual Start
```bash
# Terminal 1 - Backend
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
export KMP_DUPLICATE_LIB_OK=TRUE  # macOS fix
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 - Frontend
cd frontend
pnpm dev
# OR
npm run dev
```

### Option 3: Docker (Alternative)
```bash
# Start all services
make docker-up

# Stop services
make docker-down
```

## 🌐 Access Your Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## 🧪 Testing Your Setup

### Backend Tests
```bash
cd backend
source venv/bin/activate
make test-backend
# OR
python -m pytest tests/ -v
```

### Frontend Tests
```bash
cd frontend
pnpm test
# OR
npm test
```

### Full Test Suite
```bash
# From project root
make test
```

## 🔧 Troubleshooting

### Common Issues

#### Python/Backend Issues
```bash
# Virtual environment not activated
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Dependencies not installed
pip install -r requirements.txt

# Port already in use
lsof -ti:8000 | xargs kill -9  # macOS/Linux
netstat -ano | findstr :8000   # Windows
```

#### Node.js/Frontend Issues
```bash
# Clear cache
rm -rf frontend/.next
rm -rf frontend/node_modules
pnpm install

# Port already in use
lsof -ti:3000 | xargs kill -9  # macOS/Linux
netstat -ano | findstr :3000   # Windows
```

#### ML Model Issues
```bash
# Check if models are downloaded
ls support_models/

# Reinitialize submodules
git submodule update --init --recursive

# Check model paths in .env
cat backend/.env | grep MODEL
```

### Platform-Specific Issues

#### macOS
```bash
# OpenMP conflicts
export KMP_DUPLICATE_LIB_OK=TRUE

# Permission issues
sudo chown -R $(whoami) .
```

#### Windows
```bash
# Path issues
set PATH=%PATH%;C:\Python311\Scripts

# Virtual environment
venv\Scripts\activate
```

#### Linux
```bash
# System dependencies
sudo apt-get update
sudo apt-get install python3-dev python3-pip python3-venv

# Permission issues
sudo chown -R $USER:$USER .
```

## 📁 Project Structure

```
mm-data-intelligent-agent/
├── backend/                 # FastAPI backend
│   ├── api/                # API routes
│   ├── services/           # Business logic
│   ├── models/             # ML model wrappers
│   ├── schemas/            # Pydantic models
│   ├── core/               # Configuration
│   ├── utils/              # Utility functions
│   ├── tests/              # Backend tests
│   ├── requirements.txt    # Python dependencies
│   └── .env               # Backend environment
├── frontend/               # Next.js frontend
│   ├── app/                # App Router pages
│   ├── components/         # React components
│   ├── services/           # API service layer
│   ├── package.json        # Frontend dependencies
│   └── .env.local         # Frontend environment
├── support_models/          # ML model submodules
├── data/                   # Data directory (gitignored)
├── docs/                   # Documentation
├── tests/                  # Integration tests
├── Makefile                # Development commands
└── README.md               # Project overview
```

## 🔐 Security Notes

### What's Gitignored (Safe to Commit)
- Source code
- Configuration templates
- Documentation
- Test files
- Dependencies lists

### What's NOT Gitignored (Never Commit)
- `.env` files with secrets
- API keys and tokens
- Database credentials
- Personal configuration files
- Large data files
- ML model weights
- Virtual environments

## 🚀 Development Workflow

### 1. Daily Development
```bash
# Start development servers
make dev

# Make changes to code
# Save files (auto-reload enabled)

# Run tests
make test

# Check code quality
make lint
```

### 2. Before Committing
```bash
# Run full test suite
make test

# Check formatting
make lint

# Build to ensure no errors
make build
```

### 3. Pulling Updates
```bash
# Pull latest changes
git pull origin main

# Update submodules
git submodule update --init --recursive

# Reinstall dependencies if needed
cd backend && pip install -r requirements.txt
cd ../frontend && pnpm install
```

## 📚 Additional Resources

- **API Documentation**: http://localhost:8000/docs
- **Project README**: README.md
- **CI/CD Guide**: docs/CI-CD.md
- **Architecture**: docs/ARCHITECTURE.md
- **Contributing**: CONTRIBUTING.md

## 🆘 Getting Help

### Team Resources
- **GitHub Issues**: Create issue with appropriate labels
- **Discussions**: Use GitHub Discussions for questions
- **Wiki**: Check project wiki for FAQs
- **Slack/Discord**: Team communication channels

### Debugging Tips
1. Check the logs in your terminal
2. Verify environment variables
3. Ensure all dependencies are installed
4. Check if ports are available
5. Verify file permissions

---

**Happy Coding! 🎉**

*Last updated: $(date)*
*Maintained by: Development Team*
