# CI/CD Pipeline Documentation 🚀

## Overview

This document describes the comprehensive CI/CD pipeline for the MM-Data Intelligent Agent webapp, built with GitHub Actions and tailored to the actual repository structure.

## Repository Analysis

### **Frontend (Next.js 15 + React 19):**
- ✅ **Package Manager**: `pnpm` (confirmed by `pnpm-lock.yaml`)
- ✅ **Build Tool**: Next.js with Turbopack
- ✅ **Config Files**: `next.config.mjs`, `tailwind.config.ts`, `tsconfig.json`
- ❌ **No Test Files**: No Jest/Testing Library setup found
- ✅ **Scripts**: `dev`, `build`, `start`, `lint`

### **Backend (FastAPI + Python 3.11):**
- ✅ **Framework**: FastAPI 0.104.1
- ✅ **Server**: Uvicorn with standard extras
- ✅ **ML Dependencies**: PyTorch, CLIP, FAISS, OpenCV
- ✅ **Testing**: pytest with test files in `tests/backend/`
- ✅ **Linting**: Black, isort, flake8
- ✅ **Pre-commit**: Black + isort hooks

### **Infrastructure:**
- ✅ **Docker**: Multi-service with Redis, PostgreSQL
- ✅ **Makefile**: Comprehensive development commands
- ✅ **Scripts**: Data pipeline, indexing, testing utilities

## Workflow Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Code Push     │───▶│   Lint & Check  │───▶│   Unit Tests    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Integration   │◀───│   Build Docker  │◀───│   Security      │
│     Tests       │    │     Images      │    │     Scan        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┘
│   Deploy to     │◀───│   Deploy to     │◀───│   Notify Team   │
│  Production     │    │    Staging      │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Workflows

### 1. Main CI/CD Pipeline (`ci-cd.yml`)

**Triggers:**
- Push to `main`, `develop`, or `feature/*` branches
- Pull requests to `main` or `develop`
- Manual workflow dispatch

**Jobs:**
- **Lint**: Code quality and formatting checks
- **Test Backend**: Python backend testing with matrix strategy (Python 3.11, 3.12)
- **Test Frontend**: Next.js frontend building and verification (Node 18, 20)
- **Integration Test**: End-to-end testing with Redis service
- **Security**: Vulnerability scanning with Safety, Bandit, pnpm audit
- **Build Docker**: Container image building and pushing to GitHub Container Registry
- **Deploy**: Staging (develop) and production (main) environments
- **Notify**: Team notifications on success/failure

### 2. Security Audit (`security-audit.yml`)

**Triggers:**
- Weekly scheduled (Monday 9 AM UTC)
- Manual dispatch
- Dependency file changes

**Features:**
- Python dependency vulnerability scanning (Safety, pip-audit)
- Python code security analysis (Bandit)
- Frontend dependency audit (pnpm audit)
- Automated PR comments with security reports
- Artifact uploads for detailed analysis

### 3. Dependency Update (`dependency-update.yml`)

**Triggers:**
- Weekly scheduled (Sunday 2 AM UTC)
- Manual dispatch with update type selection

**Update Types:**
- **Security**: Only security patches
- **All**: Complete dependency updates
- **Python**: Backend dependencies only
- **Frontend**: Frontend dependencies only

**Features:**
- Automated dependency updates
- Pull request creation for review
- Smart update detection
- Configurable update strategies

### 4. ML Pipeline (`ml-pipeline.yml`) - **NEW!**

**Triggers:**
- Manual dispatch with pipeline type selection
- Changes to ML-related code

**Pipeline Types:**
- **Test**: Component testing and validation
- **Sample Data**: Generate test datasets
- **Ingest**: Video processing and feature extraction
- **Build Indexes**: FAISS and Lucene index construction
- **Full Pipeline**: Complete end-to-end processing

**Features:**
- ML model validation
- Data pipeline execution
- Index building automation
- Artifact management
- Pipeline verification

## Environment Variables

### Required Secrets

```bash
# GitHub Container Registry
GITHUB_TOKEN                    # Auto-provided by GitHub

# Deployment (Add as needed)
KUBECONFIG                      # Kubernetes configuration
DOCKER_REGISTRY_TOKEN          # Container registry access
AWS_ACCESS_KEY_ID              # AWS deployment credentials
AWS_SECRET_ACCESS_KEY          # AWS deployment credentials
```

### Environment Configuration

```yaml
env:
  PYTHON_VERSION: '3.11'
  NODE_VERSION: '18'
  PNPM_VERSION: '8'
  BACKEND_PORT: 8000
  FRONTEND_PORT: 3000
```

## Matrix Testing Strategy

### Backend Testing

- **Python Versions**: 3.11, 3.12
- **Operating Systems**: Ubuntu, macOS
- **Coverage**: pytest with Codecov integration

### Frontend Testing

- **Node.js Versions**: 18, 20
- **Build Verification**: Next.js build process
- **Linting**: ESLint with Next.js rules

## Caching Strategy

### Python Dependencies

```yaml
- uses: actions/cache@v3
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ matrix.python-version }}-${{ hashFiles('backend/requirements.txt') }}
```

### Frontend Dependencies

```yaml
- uses: actions/cache@v3
  with:
    path: |
      frontend/node_modules
      frontend/.next/cache
    key: ${{ runner.os }}-node-${{ matrix.node-version }}-${{ hashFiles('frontend/pnpm-lock.yaml') }}
```

### Docker Layer Caching

```yaml
- uses: docker/build-push-action@v5
  with:
    cache-from: type=gha
    cache-to: type=gha,mode=max
```

## Security Features

### Automated Scanning

- **Dependency Vulnerabilities**: Safety, pip-audit
- **Code Security**: Bandit static analysis
- **Frontend Security**: pnpm audit
- **Container Security**: Docker best practices

### Security Reports

- JSON format for integration
- GitHub artifacts for download
- Automated PR comments
- Weekly scheduled scans

## Deployment Strategy

### Branch Strategy

- **`develop`** → Staging environment
- **`main`** → Production environment
- **Feature branches** → CI only (no deployment)

### Environment Protection

```yaml
environment: production
# Requires approval for production deployments
```

### Rollback Strategy

- Docker image versioning
- Kubernetes deployment rollbacks
- Database migration safety

## Performance Optimizations

### Parallel Execution

- Independent job execution where possible
- Matrix strategies for testing
- Cached dependencies

### Resource Management

- Efficient Docker builds
- Layer caching
- Dependency caching
- Minimal runner usage

## Monitoring and Notifications

### Success Notifications

- ✅ Pipeline completion
- 📊 Test coverage reports
- 🔒 Security scan results
- 🚀 Deployment status

### Failure Notifications

- ❌ Pipeline failures
- 🔍 Detailed error logs
- 📋 Artifact downloads
- 👥 Team alerts

## Customization Guide

### Adding New Tests

1. Create test files in appropriate directories
2. Update Makefile targets
3. Add to CI workflow jobs
4. Configure test reporting

### Adding New Security Tools

1. Install tool in workflow
2. Configure scanning parameters
3. Add to artifact uploads
4. Update documentation

### Modifying Deployment

1. Update environment configurations
2. Modify deployment scripts
3. Configure environment protection
4. Test deployment process

## Troubleshooting

### Common Issues

#### Build Failures

- Check dependency versions
- Verify Python/Node.js compatibility
- Review error logs in Actions tab

#### Test Failures

- Run tests locally first
- Check test environment setup
- Verify test data availability

#### Deployment Issues

- Check environment secrets
- Verify deployment permissions
- Review deployment logs

### Debug Commands

```bash
# Local testing
make test-backend
make test-frontend
make build

# Docker testing
make docker-build
make docker-up

# Security scanning
safety check
bandit -r backend/
pnpm audit
```

## Best Practices

### Code Quality

- Run linting before commits
- Maintain test coverage >80%
- Use pre-commit hooks
- Regular dependency updates

### Security

- Weekly security audits
- Immediate security patches
- Regular dependency reviews
- Container security scanning

### Performance

- Optimize Docker builds
- Use efficient caching
- Parallel job execution
- Resource monitoring

## Support and Maintenance

### Regular Tasks

- Monitor workflow performance
- Update GitHub Actions versions
- Review security reports
- Optimize caching strategies

### Contact Information

- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions
- **Security**: Private security advisories

---

*Last updated: $(date)*
*Maintained by: Development Team*
