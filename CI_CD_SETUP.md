# CI/CD Setup Guide for n of 1 Platform

## 🚀 Overview

This document explains the automated CI/CD infrastructure for the n of 1 platform.

## 📁 What's Been Added

### Testing Infrastructure
- ✅ `tests/` - Comprehensive test suite
  - `unit/` - Unit tests for individual modules
  - `integration/` - End-to-end workflow tests
  - `conftest.py` - Shared test fixtures
- ✅ `pytest.ini` - Pytest configuration with 80% coverage gate
- ✅ `.coveragerc` - Coverage reporting configuration
- ✅ Updated `requirements.txt` with testing dependencies

### CI/CD Pipelines (`github/workflows/`)
- ✅ `backend-ci.yml` - Automated testing for backend (Python)
  - Runs tests on Python 3.11 & 3.12
  - Code linting with flake8
  - Type checking with mypy
  - Security scanning with Bandit
  - 80% coverage requirement
- ✅ `frontend-ci.yml` - Automated testing for frontend (React/TypeScript)
  - Tests on Node 18.x & 20.x
  - TypeScript type checking
  - ESLint linting
  - Lighthouse performance audits
- ✅ `deploy-staging.yml` - Auto-deploy to staging on push to `n-of-1-production`
- ✅ `deploy-production.yml` - Manual production deployment with confirmation
- ✅ `dependency-update.yml` - Weekly automated dependency updates

### Scripts (`scripts/`)
- ✅ `run_tests.sh` - Run all tests locally with coverage
- ✅ `check_coverage.sh` - Verify 80% coverage threshold
- ✅ `rollback.sh` - Rollback to previous version

## 🔧 Setup Required (One-Time)

### 1. GitHub Secrets

Add these secrets in GitHub (Settings → Secrets and variables → Actions):

**Backend (Railway):**
- `RAILWAY_TOKEN` - Railway API token
- `RAILWAY_PROJECT_ID` - Your Railway project ID
- `STAGING_BACKEND_URL` - Staging backend URL
- `PRODUCTION_BACKEND_URL` - Production backend URL

**Frontend (Vercel):**
- `VERCEL_TOKEN` - Vercel API token
- `VERCEL_ORG_ID` - Vercel organization ID
- `VERCEL_PROJECT_ID` - Vercel project ID
- `STAGING_FRONTEND_URL` - Staging frontend URL
- `PRODUCTION_FRONTEND_URL` - Production frontend URL

**API Keys:**
- `OPENAI_API_KEY` - Your OpenAI API key (for tests)

### 2. Install Test Dependencies

```bash
pip install -r requirements.txt
```

### 3. Make Scripts Executable

```bash
chmod +x scripts/*.sh
```

## 🎯 How It Works

### Automatic Workflows

**On Every Push to `main` or `n-of-1-production`:**
1. ✅ Backend CI runs (tests, linting, security scan)
2. ✅ Frontend CI runs (tests, build, type check)
3. ✅ Coverage must be ≥80% or build fails
4. ❌ If tests fail, PR is blocked

**On Push to `n-of-1-production`:**
1. ✅ All CI checks pass
2. ✅ Auto-deploy to staging environment
3. ✅ Health checks run
4. ✅ Smoke tests verify deployment

**Every Monday at 9 AM:**
1. ✅ Check for dependency updates
2. ✅ Create PR with updates
3. 👤 You review and merge

### Manual Workflows

**Production Deployment:**
1. Go to GitHub Actions
2. Select "Deploy to Production"
3. Click "Run workflow"
4. Enter version (e.g., `v1.2.3`)
5. Type "deploy" to confirm
6. ✅ Automatic deployment with health checks

**Rollback:**
```bash
./scripts/rollback.sh v1.2.2
```

## 📊 Running Tests Locally

### Run All Tests
```bash
./scripts/run_tests.sh
```

### Run Unit Tests Only
```bash
pytest tests/unit/ -v
```

### Run Integration Tests Only
```bash
pytest tests/integration/ -v
```

### Check Coverage
```bash
./scripts/check_coverage.sh
```

### View Coverage Report
```bash
pytest --cov --cov-report=html
open htmlcov/index.html
```

## 🔍 CI/CD Status

View status of all workflows:
- GitHub → Actions tab
- See green ✅ or red ❌ for each workflow

### Pipeline Stages

**Backend CI:**
```
Checkout → Setup Python → Install → Lint → Type Check → Test → Coverage → Security Scan
```

**Frontend CI:**
```
Checkout → Setup Node → Install → Lint → Type Check → Test → Build → Lighthouse
```

**Deploy Staging:**
```
Deploy Backend → Health Check → Deploy Frontend → Smoke Tests
```

**Deploy Production:**
```
Validate → Deploy Backend → Health Check → Deploy Frontend → Post-Deploy Tests → Notify
```

## 🎛️ Configuration

### Coverage Threshold
To change from 80%:
- Edit `pytest.ini` → `--cov-fail-under=XX`
- Edit `.github/workflows/backend-ci.yml` → `coverage report --fail-under=XX`

### Python Versions
Edit `.github/workflows/backend-ci.yml`:
```yaml
strategy:
  matrix:
    python-version: ['3.11', '3.12']
```

### Node Versions
Edit `.github/workflows/frontend-ci.yml`:
```yaml
strategy:
  matrix:
    node-version: ['18.x', '20.x']
```

## 📈 What You Need to Do

### Regular (Automated - Just Review):
- ✅ Merge dependency update PRs (~2 min/week)
- ✅ Review CI failures if tests break (~5 min/occurrence)

### Production Deployments (~2 min):
1. Go to GitHub Actions
2. Click "Deploy to Production"
3. Enter version and confirm
4. Monitor completion

### If Issues Occur (~10 min):
1. Check GitHub Actions logs
2. Fix failing tests or code
3. Push fix
4. Or run rollback: `./scripts/rollback.sh v1.2.2`

## 🚨 Rollback Procedure

If production deployment fails or has issues:

```bash
# Quick rollback to last known good version
./scripts/rollback.sh v1.2.2

# Or manually in Railway/Vercel dashboards
```

## 📚 Next Steps

After this Phase 1 setup:
- **Phase 2**: Infrastructure as Code (IaC) with Pulumi/Terraform
- **Phase 3**: Monitoring, alerting, and advanced deployment strategies (canary/blue-green)

## 🆘 Support

If anything fails:
1. Check GitHub Actions logs
2. Review error messages
3. Check Railway/Vercel deployment logs
4. Run tests locally to reproduce

---

**All automated! Your involvement: ~10 minutes/week** ✨




