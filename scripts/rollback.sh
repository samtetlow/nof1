#!/bin/bash
# Rollback to previous deployment

set -e

VERSION=$1

if [ -z "$VERSION" ]; then
    echo "Usage: ./scripts/rollback.sh <version>"
    echo "Example: ./scripts/rollback.sh v1.2.3"
    exit 1
fi

echo "🔄 Rolling back to version $VERSION"
echo "===================================="

# Confirm rollback
read -p "Are you sure you want to rollback to $VERSION? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "Rollback cancelled"
    exit 0
fi

# Checkout the specified version
echo "📥 Checking out version $VERSION..."
git fetch --all
git checkout $VERSION

# Rollback backend (Railway)
echo ""
echo "🔙 Rolling back backend..."
if [ ! -z "$RAILWAY_TOKEN" ]; then
    railway rollback --service backend-production
else
    echo "⚠️  RAILWAY_TOKEN not set. Please rollback manually in Railway dashboard."
fi

# Rollback frontend (Vercel)
echo ""
echo "🔙 Rolling back frontend..."
if [ ! -z "$VERCEL_TOKEN" ]; then
    cd frontend
    vercel rollback --token=$VERCEL_TOKEN --yes
else
    echo "⚠️  VERCEL_TOKEN not set. Please rollback manually in Vercel dashboard."
fi

echo ""
echo "=========================================="
echo "✅ Rollback to $VERSION initiated"
echo ""
echo "Next steps:"
echo "1. Verify health checks: curl https://your-backend-url/health"
echo "2. Test critical user flows"
echo "3. Monitor error rates and logs"




