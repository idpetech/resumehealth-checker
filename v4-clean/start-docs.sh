#!/bin/bash

# Resume Health Checker v4.0 - Documentation Server
# This script starts the MkDocs development server with live reload

echo "🚀 Starting Resume Health Checker v4.0 Documentation Server..."
echo "📚 Documentation will be available at: http://localhost:9000"
echo "🔄 Live reload enabled - changes will be reflected automatically"
echo "⏹️  Press Ctrl+C to stop the server"
echo ""

# Check if MkDocs is installed
if ! command -v mkdocs &> /dev/null; then
    echo "❌ MkDocs not found. Installing..."
    python3 -m pip install mkdocs mkdocs-material mkdocs-mermaid2-plugin
fi

# Start the development server on port 9000 (avoiding conflict with app on 8000)
mkdocs serve --dev-addr=0.0.0.0:9000
