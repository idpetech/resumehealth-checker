#!/bin/bash
# Full CI/CD Pipeline - Local → Staging → Production
# Usage: ./scripts/full-pipeline.sh

set -e  # Exit on any error

echo "🚀 Starting Full Deployment Pipeline..."
echo ""

# Step 1: Local Testing
echo "=========================================="
echo "STEP 1: LOCAL TESTING"
echo "=========================================="
./scripts/test-local.sh

# Mark local tests as passed
touch .local-tests-passed

echo ""
read -p "🤔 Local tests passed. Continue to staging? (yes/no): " continue_staging
if [ "$continue_staging" != "yes" ]; then
    echo "❌ Pipeline stopped at local testing"
    exit 1
fi

# Step 2: Staging Deployment
echo ""
echo "=========================================="
echo "STEP 2: STAGING DEPLOYMENT"
echo "=========================================="
./scripts/deploy-staging.sh

echo ""
read -p "🤔 Staging tests passed. Continue to production? (yes/no): " continue_production
if [ "$continue_production" != "yes" ]; then
    echo "❌ Pipeline stopped at staging"
    exit 1
fi

# Step 3: Production Deployment
echo ""
echo "=========================================="
echo "STEP 3: PRODUCTION DEPLOYMENT"
echo "=========================================="
./scripts/deploy-production.sh

echo ""
echo "🎉 FULL PIPELINE COMPLETE!"
echo "✅ Local → ✅ Staging → ✅ Production"