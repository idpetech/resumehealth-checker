#!/bin/bash

# Start the v4-clean server locally with proper environment variables

echo "🚀 Starting Resume Health Checker v4.0 locally..."

# Set environment variables
export ENVIRONMENT="local"
export OPENAI_API_KEY="sk-test-placeholder-key-for-local-testing"
export STRIPE_SECRET_TEST_KEY="sk_test_PLACEHOLDER_REPLACE_WITH_REAL_KEY"
export STRIPE_PUBLISHABLE_TEST_KEY="pk_test_PLACEHOLDER_REPLACE_WITH_REAL_KEY"
export STRIPE_WEBHOOK_TEST_SECRET="whsec_1234567890abcdef_TEMP_FOR_STAGING"

echo "✅ Environment variables set"
echo "   ENVIRONMENT: $ENVIRONMENT"
echo "   STRIPE_SECRET_TEST_KEY: ${STRIPE_SECRET_TEST_KEY:0:20}..."
echo "   STRIPE_PUBLISHABLE_TEST_KEY: ${STRIPE_PUBLISHABLE_TEST_KEY:0:20}..."

# Start the server
cd v4-clean
echo "🌐 Starting server on http://localhost:8000"
python main.py

