#!/bin/bash
# Start backend with visible logging
cd /Users/samtetlow/Cursor/nof1
source venv/bin/activate

echo "=========================================="
echo "STARTING BACKEND WITH VISIBLE LOGS"
echo "=========================================="
echo ""
echo "Backend running at: http://localhost:8000"
echo "Frontend should be at: http://localhost:3000"
echo ""
echo "Watch for 🔍 DEBUG messages when you upload a solicitation"
echo ""
echo "Press Ctrl+C to stop"
echo ""
echo "=========================================="
echo ""

uvicorn app:app --reload --host 0.0.0.0 --port 8000

