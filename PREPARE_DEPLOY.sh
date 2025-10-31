#!/bin/bash
# Deployment Preparation Script
# This script prepares the n-of-1 app for deployment to Railway and Vercel
# DO NOT ACTUALLY DEPLOY - just prepare and show what needs to be done

set -e  # Exit on error

echo "🚀 N of 1 - Deployment Preparation Script"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check we're in the right directory
if [ ! -f "app.py" ]; then
    echo -e "${RED}❌ Error: Must run from project root directory${NC}"
    exit 1
fi

echo -e "${BLUE}📋 Step 1: Checking Repository Status${NC}"
echo "----------------------------------------"
git status --short
echo ""

echo -e "${BLUE}🔍 Step 2: Checking Configuration Files${NC}"
echo "----------------------------------------"

# Check required files
REQUIRED_FILES=(
    "Procfile"
    "requirements.txt"
    "runtime.txt"
    "railway.json"
    "frontend/vercel.json"
    "frontend/package.json"
    ".gitignore"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓${NC} $file exists"
    else
        echo -e "${RED}✗${NC} $file missing"
    fi
done
echo ""

echo -e "${BLUE}🔐 Step 3: Checking for Sensitive Files${NC}"
echo "----------------------------------------"

# Check that sensitive files are NOT tracked
SENSITIVE_FILES=(
    "config.json"
    ".env"
    "nof1.db"
    "backend.log"
    "backend.pid"
)

for file in "${SENSITIVE_FILES[@]}"; do
    if git ls-files --error-unmatch "$file" 2>/dev/null; then
        echo -e "${RED}⚠️  WARNING: $file is tracked by git (should be in .gitignore)${NC}"
    else
        echo -e "${GREEN}✓${NC} $file not tracked"
    fi
done
echo ""

echo -e "${BLUE}🧪 Step 4: Testing Backend${NC}"
echo "----------------------------------------"

# Check if venv exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}⚠️  Warning: Virtual environment not found${NC}"
    echo "   Create with: python3 -m venv venv"
else
    echo -e "${GREEN}✓${NC} Virtual environment exists"
fi

# Check if dependencies are installed
if [ -d "venv" ]; then
    source venv/bin/activate
    
    # Check key packages
    echo "Checking Python packages..."
    python -c "import fastapi" 2>/dev/null && echo -e "${GREEN}✓${NC} fastapi installed" || echo -e "${RED}✗${NC} fastapi missing"
    python -c "import uvicorn" 2>/dev/null && echo -e "${GREEN}✓${NC} uvicorn installed" || echo -e "${RED}✗${NC} uvicorn missing"
    python -c "import openai" 2>/dev/null && echo -e "${GREEN}✓${NC} openai installed" || echo -e "${RED}✗${NC} openai missing"
    python -c "import anthropic" 2>/dev/null && echo -e "${GREEN}✓${NC} anthropic installed" || echo -e "${RED}✗${NC} anthropic missing"
    
    deactivate
fi
echo ""

echo -e "${BLUE}🎨 Step 5: Testing Frontend${NC}"
echo "----------------------------------------"

if [ -d "frontend/node_modules" ]; then
    echo -e "${GREEN}✓${NC} node_modules exists"
else
    echo -e "${YELLOW}⚠️  Warning: node_modules not found${NC}"
    echo "   Install with: cd frontend && npm install"
fi

# Check if frontend builds
echo "Checking if frontend can build..."
if [ -d "frontend/node_modules" ]; then
    cd frontend
    echo "Running: npm run build (this may take a minute)..."
    if npm run build > /tmp/frontend-build.log 2>&1; then
        echo -e "${GREEN}✓${NC} Frontend builds successfully"
    else
        echo -e "${RED}✗${NC} Frontend build failed"
        echo "See /tmp/frontend-build.log for details"
    fi
    cd ..
fi
echo ""

echo -e "${BLUE}🔗 Step 6: Environment Variables Needed${NC}"
echo "----------------------------------------"
echo ""
echo "Railway Backend needs:"
echo -e "${YELLOW}  OPENAI_API_KEY${NC}=your_openai_key"
echo -e "${YELLOW}  PORT${NC}=8000"
echo -e "${YELLOW}  PYTHON_VERSION${NC}=3.11.9"
echo ""
echo "Vercel Frontend needs:"
echo -e "${YELLOW}  REACT_APP_API_URL${NC}=https://your-railway-backend.up.railway.app"
echo ""

echo -e "${BLUE}📦 Step 7: Files to Commit${NC}"
echo "----------------------------------------"
echo ""
echo "Modified files:"
git diff --name-only
echo ""
echo "Untracked files:"
git ls-files --others --exclude-standard | grep -v "venv/" | grep -v "node_modules/" | grep -v "frontend/build/" | grep -v "__pycache__/" | grep -v "*.db" | grep -v "*.log" | grep -v "*.pid"
echo ""

echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}✅ Preparation Check Complete!${NC}"
echo -e "${GREEN}=========================================${NC}"
echo ""
echo -e "${YELLOW}Next Steps (DO NOT RUN AUTOMATICALLY):${NC}"
echo ""
echo "1. Review DEPLOYMENT_CHECKLIST.md for full details"
echo "2. Commit your changes:"
echo "   git add <files>"
echo '   git commit -m "Prepare for production deployment"'
echo "   git push origin n-of-1-production"
echo ""
echo "3. Deploy Backend to Railway:"
echo "   - Visit https://railway.app"
echo "   - Create new project from GitHub"
echo "   - Set environment variables"
echo "   - Generate domain"
echo ""
echo "4. Deploy Frontend to Vercel:"
echo "   - Visit https://vercel.com"
echo "   - Import project from GitHub"
echo "   - Set REACT_APP_API_URL to Railway backend URL"
echo "   - Deploy"
echo ""
echo -e "${BLUE}📖 Full instructions in: DEPLOYMENT_CHECKLIST.md${NC}"
echo ""

