#!/bin/bash
# Production Deployment Script
# Usage: ./scripts/deploy-production.sh

set -e  # Exit on any error

echo "🚨 Starting Production Deployment Pipeline..."

# Check if staging tests passed
echo "🔍 Checking if staging tests passed..."
if [ ! -f ".staging-tests-passed" ]; then
    echo "❌ Please run staging deployment first: ./scripts/deploy-staging.sh"
    exit 1
fi

# Double confirmation for production
echo "⚠️  You are about to deploy to PRODUCTION!"
echo "📊 This will affect real users and payments."
read -p "🤔 Are you sure you want to continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "❌ Production deployment cancelled"
    exit 1
fi

# Production deployment (both staging and production use v4.0-deployment branch)
echo "⚠️  NOTE: Both staging and production currently deploy from v4.0-deployment"
echo "🚀 Pushing updated v4.0-deployment to trigger production deployment..."
git push origin v4.0-deployment

echo "📋 Production Railway service should be configured to deploy from v4.0-deployment branch"

# Wait for Railway production deployment
echo "⏳ Waiting for Railway production deployment (45 seconds)..."
sleep 45

# Test production environment
echo "🔍 Testing production environment..."
PRODUCTION_URL="https://web-production-f7f3.up.railway.app"

# Health check
echo "🔍 Testing production health..."
if curl -f -s $PRODUCTION_URL/api/v1/health > /dev/null; then
    echo "✅ Production health check passed"
else
    echo "❌ Production health check failed - INVESTIGATE IMMEDIATELY"
    exit 1
fi

# Test with small real payment (optional)
echo ""
echo "🧪 Manual testing required:"
echo "1. 🌐 Open: $PRODUCTION_URL"
echo "2. 📄 Upload a test resume"
echo "3. 💳 Test payment flow with small amount"
echo "4. ✅ Verify premium analysis generation"

# Clean up test flags
rm -f .local-tests-passed .staging-tests-passed

echo ""
echo "🎉 Production deployment complete!"
echo "🌐 Production URL: $PRODUCTION_URL"
echo "📊 Monitor for the next 15 minutes for any issues"