#!/bin/bash

# Development Setup Script for Resume Health Checker

echo "🚀 Setting up development environment..."

# Set environment variables for development
export DISABLE_RATE_LIMITING=true
export RAILWAY_ENVIRONMENT=development

echo "✅ Environment variables set:"
echo "   - DISABLE_RATE_LIMITING=true"
echo "   - RAILWAY_ENVIRONMENT=development"

echo ""
echo "🔧 To start the development servers:"
echo "   1. Backend (Port 8000): python -m uvicorn main_modular:app --reload --host 0.0.0.0 --port 8000"
echo "   2. Legacy Frontend (Port 3000): cd frontend && python -m http.server 3000"
echo ""
echo "🌐 Access the application at:"
echo "   - New Backend: http://localhost:8000"
echo "   - Legacy Frontend: http://localhost:3000"
echo ""
echo "📝 Note: Rate limiting is disabled for development. Remember to enable it in production!"



