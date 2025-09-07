#!/bin/bash
# Railway Staging Environment Variables
# Run this script to set up environment variables for Railway staging deployment

echo "🚀 Setting up Railway Staging Environment Variables..."

# Core environment settings
export ENVIRONMENT=staging
export PUBLIC_BASE_URL=https://web-production-f7f3.up.railway.app

# OpenAI API Key (required)
export OPENAI_API_KEY=${OPENAI_API_KEY:-"your-openai-api-key-here"}

# Stripe Test Keys (for staging)
export STRIPE_SECRET_TEST_KEY=${STRIPE_SECRET_TEST_KEY:-"sk_test_your-stripe-test-key-here"}
export STRIPE_PUBLISHABLE_TEST_KEY=${STRIPE_PUBLISHABLE_TEST_KEY:-"pk_test_your-stripe-publishable-key-here"}
export STRIPE_WEBHOOK_TEST_SECRET=${STRIPE_WEBHOOK_TEST_SECRET:-"whsec_your-webhook-secret-here"}

# Database settings
export DATABASE_PATH=database.db

# Application settings
export PORT=8000
export MAX_FILE_SIZE=10485760  # 10MB

echo "✅ Environment variables set for staging:"
echo "   ENVIRONMENT: $ENVIRONMENT"
echo "   PUBLIC_BASE_URL: $PUBLIC_BASE_URL"
echo "   OPENAI_API_KEY: ${OPENAI_API_KEY:0:20}..."
echo "   STRIPE_SECRET_TEST_KEY: ${STRIPE_SECRET_TEST_KEY:0:20}..."
echo ""
echo "🔧 To deploy to Railway staging:"
echo "   1. Set these environment variables in Railway dashboard"
echo "   2. Deploy your code"
echo "   3. Test payment flow at: $PUBLIC_BASE_URL"
echo ""
echo "📋 Copy these environment variables to Railway:"
echo "ENVIRONMENT=$ENVIRONMENT"
echo "PUBLIC_BASE_URL=$PUBLIC_BASE_URL"
echo "OPENAI_API_KEY=$OPENAI_API_KEY"
echo "STRIPE_SECRET_TEST_KEY=$STRIPE_SECRET_TEST_KEY"
echo "STRIPE_PUBLISHABLE_TEST_KEY=$STRIPE_PUBLISHABLE_TEST_KEY"
echo "STRIPE_WEBHOOK_TEST_SECRET=$STRIPE_WEBHOOK_TEST_SECRET"
echo "DATABASE_PATH=$DATABASE_PATH"
echo "PORT=$PORT"
echo "MAX_FILE_SIZE=$MAX_FILE_SIZE"


