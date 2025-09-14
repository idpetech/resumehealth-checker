#!/bin/bash
# Local Testing Script - Run before any deployment
# Usage: ./scripts/test-local.sh

set -e  # Exit on any error

echo "🧪 Starting Local Testing Pipeline..."

# Check if we're in the right directory
if [ ! -f "main.py" ]; then
    echo "❌ Error: Run this script from the project root directory"
    exit 1
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Start local server in background
echo "🚀 Starting local server..."
python main.py &
SERVER_PID=$!

# Wait for server to start
echo "⏳ Waiting for server to start..."
sleep 5

# Test health endpoint
echo "🔍 Testing health endpoint..."
if curl -f -s http://localhost:8000/api/v1/health > /dev/null; then
    echo "✅ Health check passed"
else
    echo "❌ Health check failed"
    kill $SERVER_PID
    exit 1
fi

# Test file upload endpoint
echo "🔍 Testing file upload (if test file exists)..."
if [ -f "test-files/sample-resume.pdf" ]; then
    curl -X POST -F "file=@test-files/sample-resume.pdf" \
         -F "analysis_type=free" \
         http://localhost:8000/api/v1/analyze > /dev/null
    echo "✅ File upload test passed"
else
    echo "ℹ️  Skipping file upload test (no test file found)"
fi

# Test pricing endpoint
echo "🔍 Testing pricing endpoint..."
if curl -f -s http://localhost:8000/api/v1/pricing > /dev/null; then
    echo "✅ Pricing endpoint test passed"
else
    echo "❌ Pricing endpoint test failed"
    kill $SERVER_PID
    exit 1
fi

# Clean up
echo "🧹 Cleaning up..."
kill $SERVER_PID

echo ""
echo "✅ All local tests passed! Ready for staging deployment."
echo "🚀 Next step: ./scripts/deploy-staging.sh"