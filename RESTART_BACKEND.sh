#!/bin/bash
# Restart Backend Script
# This ensures the latest code changes are loaded

echo "========================================"
echo "RESTARTING N OF 1 BACKEND"
echo "========================================"
echo ""

# Find and kill any running uvicorn/app.py processes
echo "Step 1: Stopping existing backend processes..."
pkill -f "uvicorn app:app" 2>/dev/null || true
pkill -f "python.*app.py" 2>/dev/null || true
sleep 2

# Check if anything is still running
RUNNING=$(ps aux | grep -E "uvicorn|python.*app.py" | grep -v grep | wc -l)
if [ $RUNNING -gt 0 ]; then
    echo "⚠️  Warning: Some processes still running. Force killing..."
    pkill -9 -f "uvicorn app:app" 2>/dev/null || true
    pkill -9 -f "python.*app.py" 2>/dev/null || true
    sleep 1
fi

echo "✅ Old processes stopped"
echo ""

# Activate virtual environment
echo "Step 2: Activating virtual environment..."
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✅ Virtual environment activated"
else
    echo "❌ No venv found. Please create one: python3 -m venv venv"
    exit 1
fi
echo ""

# Start backend
echo "Step 3: Starting backend with latest code..."
echo ""
echo "🚀 Starting: uvicorn app:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "========================================"
echo "BACKEND RUNNING"
echo "========================================"
echo ""
echo "Test the alignment fix:"
echo "  http://localhost:8000/api/test-alignment-fix"
echo ""
echo "Press Ctrl+C to stop"
echo ""

uvicorn app:app --reload --host 0.0.0.0 --port 8000

