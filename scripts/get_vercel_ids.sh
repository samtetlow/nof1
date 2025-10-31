#!/bin/bash
# Quick script to get Vercel IDs

echo "🔍 Finding Vercel IDs..."
echo "======================="

cd frontend

if [ -f ".vercel/project.json" ]; then
    echo ""
    echo "✅ Found Vercel project configuration:"
    echo ""
    cat .vercel/project.json | python3 -m json.tool
    echo ""
    echo "Copy these values:"
    echo "- orgId → VERCEL_ORG_ID"
    echo "- projectId → VERCEL_PROJECT_ID"
else
    echo ""
    echo "⚠️  No .vercel/project.json found"
    echo ""
    echo "Run this to link your project:"
    echo "  cd frontend && npx vercel link"
    echo ""
fi

cd ..




