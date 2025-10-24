#!/bin/bash
# Startup script for N-of-1 React Frontend

echo "🚀 Starting N-of-1 Frontend..."
echo ""

cd "$(dirname "$0")/frontend"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

echo "✓ Starting React development server on port 3000..."
echo "✓ Make sure the backend API is running on port 8000"
echo ""
echo "Opening browser at http://localhost:3000"
echo ""

npm start


