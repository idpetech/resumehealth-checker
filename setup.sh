#!/bin/bash

# Resume Health Checker - Setup Script
# Cross-platform setup for macOS/Linux

set -e  # Exit on any error

echo "🚀 Resume Health Checker - Setup"
echo "================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Find Python executable
if command -v python3 &> /dev/null; then
    PYTHON=python3
elif command -v python &> /dev/null; then
    PYTHON=python
else
    print_error "Python not found! Please install Python 3.9+ first."
    echo "Visit: https://python.org/downloads/"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$($PYTHON -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
print_status "Found Python $PYTHON_VERSION"

# Check if Python version is 3.9+
if ! $PYTHON -c "import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)" 2>/dev/null; then
    print_error "Python 3.9+ required, found $PYTHON_VERSION"
    echo "Visit: https://python.org/downloads/"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "🐍 Creating virtual environment..."
    $PYTHON -m venv .venv
    print_status "Virtual environment created"
else
    print_status "Virtual environment already exists"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
    print_status "Virtual environment activated"
elif [ -f ".venv/Scripts/activate" ]; then
    source .venv/Scripts/activate  # Windows Git Bash
    print_status "Virtual environment activated"
else
    print_error "Could not find virtual environment activation script"
    exit 1
fi

# Upgrade pip in virtual environment
echo "📦 Upgrading pip in virtual environment..."
pip install --upgrade pip

# Install requirements
echo "📦 Installing dependencies in virtual environment..."
pip install -r requirements.txt

# Install pre-commit hooks (optional)
echo "🎣 Installing pre-commit hooks..."
if pre-commit install; then
    print_status "Pre-commit hooks installed"
else
    print_warning "Pre-commit hooks installation failed (optional)"
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        cp .env.example .env
        print_status "Created .env file from template"
        echo "📝 Please edit .env file with your API keys"
    else
        print_warning "No .env.example found, you'll need to create .env manually"
    fi
else
    print_status ".env file already exists"
fi

print_status "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your API keys:"
echo "   OPENAI_API_KEY=your_openai_api_key_here"
echo "   STRIPE_PAYMENT_SUCCESS_TOKEN=your_stripe_token_here"
echo ""
echo "2. Activate virtual environment (each time you work on the project):"
echo "   source .venv/bin/activate  # On macOS/Linux"
echo "   # OR on Windows: .venv\\Scripts\\activate"
echo ""
echo "3. Test the setup:"
echo "   python -m pytest tests/ -v"
echo ""
echo "4. Start development server:"
echo "   python -m uvicorn main:app --reload"
echo "   Then visit: http://localhost:8000"
echo ""
echo "4. Run using setup commands:"
echo "   ./setup.sh test     # Run tests"
echo "   ./setup.sh dev      # Start dev server"
echo "   ./setup.sh lint     # Check code quality"
echo "   ./setup.sh format   # Format code"

# Handle command line arguments
if [ $# -gt 0 ]; then
    case $1 in
        "test")
            echo ""
            echo "🧪 Running tests..."
            # Activate venv and run tests
            if [ -f ".venv/bin/activate" ]; then
                source .venv/bin/activate && python -m pytest tests/ -v
            elif [ -f ".venv/Scripts/activate" ]; then
                source .venv/Scripts/activate && python -m pytest tests/ -v
            else
                print_warning "Virtual environment not found, using system Python"
                $PYTHON -m pytest tests/ -v
            fi
            ;;
        "dev")
            echo ""
            echo "🚀 Starting development server..."
            echo "📝 Server will be available at http://localhost:8000"
            # Activate venv and run dev server
            if [ -f ".venv/bin/activate" ]; then
                source .venv/bin/activate && python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
            elif [ -f ".venv/Scripts/activate" ]; then
                source .venv/Scripts/activate && python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
            else
                print_warning "Virtual environment not found, using system Python"
                $PYTHON -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
            fi
            ;;
        "lint")
            echo ""
            echo "🔍 Running code quality checks..."
            # Activate venv and run linting
            if [ -f ".venv/bin/activate" ]; then
                source .venv/bin/activate
                python -m flake8 main.py tests/ || print_warning "Flake8 issues found"
                python -m black --check main.py tests/ || print_warning "Black formatting issues found"  
                python -m isort --check-only main.py tests/ || print_warning "Import sorting issues found"
                python -m bandit -r main.py || print_warning "Security issues found"
            elif [ -f ".venv/Scripts/activate" ]; then
                source .venv/Scripts/activate
                python -m flake8 main.py tests/ || print_warning "Flake8 issues found"
                python -m black --check main.py tests/ || print_warning "Black formatting issues found"  
                python -m isort --check-only main.py tests/ || print_warning "Import sorting issues found"
                python -m bandit -r main.py || print_warning "Security issues found"
            else
                print_warning "Virtual environment not found, using system Python"
                $PYTHON -m flake8 main.py tests/ || print_warning "Flake8 issues found"
                $PYTHON -m black --check main.py tests/ || print_warning "Black formatting issues found"  
                $PYTHON -m isort --check-only main.py tests/ || print_warning "Import sorting issues found"
                $PYTHON -m bandit -r main.py || print_warning "Security issues found"
            fi
            ;;
        "format")
            echo ""
            echo "🎨 Formatting code..."
            # Activate venv and format code
            if [ -f ".venv/bin/activate" ]; then
                source .venv/bin/activate
                python -m black main.py tests/
                python -m isort main.py tests/
            elif [ -f ".venv/Scripts/activate" ]; then
                source .venv/Scripts/activate
                python -m black main.py tests/
                python -m isort main.py tests/
            else
                print_warning "Virtual environment not found, using system Python"
                $PYTHON -m black main.py tests/
                $PYTHON -m isort main.py tests/
            fi
            print_status "Code formatted!"
            ;;
        "help")
            echo ""
            echo "Available commands:"
            echo "  ./setup.sh         - Install dependencies and setup project"
            echo "  ./setup.sh test    - Run tests"
            echo "  ./setup.sh dev     - Start development server"
            echo "  ./setup.sh lint    - Run code quality checks"
            echo "  ./setup.sh format  - Format code"
            echo "  ./setup.sh help    - Show this help"
            ;;
        *)
            print_error "Unknown command: $1"
            echo "Run './setup.sh help' for available commands"
            exit 1
            ;;
    esac
fi