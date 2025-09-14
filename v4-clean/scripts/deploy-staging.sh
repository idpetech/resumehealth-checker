#!/bin/bash
# Staging Deployment Script
# Usage: ./scripts/deploy-staging.sh

set -e  # Exit on any error

echo "🚀 Starting Staging Deployment Pipeline..."

# Check if local tests passed
echo "🔍 Checking if local tests were run..."
if [ ! -f ".local-tests-passed" ]; then
    echo "❌ Please run local tests first: ./scripts/test-local.sh"
    exit 1
fi

# Commit current changes
echo "📝 Committing changes..."
git add .
if git diff --staged --quiet; then
    echo "ℹ️  No changes to commit"
else
    read -p "📝 Enter commit message: " commit_message
    git commit -m "$(cat <<EOF
$commit_message

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
fi

# Push to branch (both environments will deploy - but test staging first)
echo "🚀 Pushing to v4.0-deployment branch..."
echo "⚠️  WARNING: This will deploy to BOTH staging and production!"
echo "💡 Solution: Configure Railway with manual deploys instead of auto-deploy"
git push origin v4.0-deployment

# Wait for Railway deployment
echo "⏳ Waiting for Railway staging deployment (30 seconds)..."
sleep 30

# Test staging environment
echo "🔍 Testing staging environment..."
STAGING_URL="https://web-staging-f53d.up.railway.app"

# Health check
if curl -f -s $STAGING_URL/api/v1/health > /dev/null; then
    echo "✅ Staging health check passed"
else
    echo "❌ Staging health check failed"
    exit 1
fi

# Test pricing
if curl -f -s $STAGING_URL/api/v1/pricing > /dev/null; then
    echo "✅ Staging pricing test passed"
else
    echo "❌ Staging pricing test failed"
    exit 1
fi

# Mark staging tests as passed
touch .staging-tests-passed

echo ""
echo "✅ Staging deployment and tests passed!"
echo "🌐 Staging URL: $STAGING_URL"
echo "🚀 Next step: ./scripts/deploy-production.sh"