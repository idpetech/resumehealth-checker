# Resume Health Checker - Development Commands

.PHONY: install test lint format clean dev deploy-staging deploy-prod setup-python

# Python executable detection
PYTHON := $(shell command -v python3 2> /dev/null || command -v python 2> /dev/null)
PIP := $(shell command -v pip3 2> /dev/null || command -v pip 2> /dev/null)

# Development setup
setup-python:
	@echo "Checking Python installation..."
	@if [ -z "$(PYTHON)" ]; then \
		echo "❌ Python not found! Please install Python 3.9+ first."; \
		echo "Visit: https://python.org/downloads/"; \
		exit 1; \
	fi
	@echo "✅ Found Python: $(PYTHON)"
	@$(PYTHON) --version
	@if [ -z "$(PIP)" ]; then \
		echo "❌ pip not found! Installing pip..."; \
		$(PYTHON) -m ensurepip --upgrade; \
	fi
	@echo "✅ Found pip: $(PIP)"

install: setup-python
	@echo "🐍 Creating virtual environment..."
	@if [ ! -d ".venv" ]; then \
		$(PYTHON) -m venv .venv; \
		echo "✅ Virtual environment created"; \
	else \
		echo "✅ Virtual environment already exists"; \
	fi
	@echo "📦 Installing dependencies in virtual environment..."
	@if [ -f ".venv/bin/activate" ]; then \
		. .venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt; \
	elif [ -f ".venv/Scripts/activate" ]; then \
		. .venv/Scripts/activate && pip install --upgrade pip && pip install -r requirements.txt; \
	else \
		echo "❌ Could not find virtual environment activation script"; \
		exit 1; \
	fi
	@echo "🎣 Installing pre-commit hooks..."
	@if [ -f ".venv/bin/activate" ]; then \
		. .venv/bin/activate && pre-commit install || echo "⚠️  Pre-commit install failed"; \
	elif [ -f ".venv/Scripts/activate" ]; then \
		. .venv/Scripts/activate && pre-commit install || echo "⚠️  Pre-commit install failed"; \
	fi
	@echo "✅ Setup complete!"
	@echo "Next steps:"
	@echo "1. Edit .env file with your API keys"
	@echo "2. Activate virtual environment: source .venv/bin/activate"
	@echo "3. Run tests: make test"
	@echo "4. Start dev server: make dev"

# Code quality
lint:
	$(PYTHON) -m flake8 main.py tests/ || echo "⚠️  Flake8 issues found"
	$(PYTHON) -m black --check main.py tests/ || echo "⚠️  Black formatting issues found"
	$(PYTHON) -m isort --check-only main.py tests/ || echo "⚠️  Import sorting issues found"
	$(PYTHON) -m bandit -r main.py || echo "⚠️  Security issues found"

format:
	@echo "🎨 Formatting code..."
	$(PYTHON) -m black main.py tests/
	$(PYTHON) -m isort main.py tests/
	@echo "✅ Code formatted!"

# Testing
test:
	@echo "🧪 Running tests..."
	$(PYTHON) -m pytest tests/ -v

test-cov:
	@echo "🧪 Running tests with coverage..."
	$(PYTHON) -m pytest tests/ -v --cov=main --cov-report=html --cov-report=term-missing

test-watch:
	@echo "👀 Running tests in watch mode..."
	$(PYTHON) -m pytest_watch tests/ -- -v

# Security
security:
	@echo "🔒 Running security checks..."
	$(PYTHON) -m safety check || echo "⚠️  Security vulnerabilities found in dependencies"
	$(PYTHON) -m bandit -r main.py || echo "⚠️  Security issues found in code"

# Development server
dev:
	@echo "🚀 Starting development server..."
	@echo "📝 Server will be available at http://localhost:8000"
	$(PYTHON) -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Production server (for local testing)
prod:
	@echo "🚀 Starting production server..."
	@echo "📝 Server will be available at http://localhost:8000"
	$(PYTHON) -m uvicorn main:app --host 0.0.0.0 --port 8000

# Deployment
deploy-staging:
	vercel --env OPENAI_API_KEY=$$OPENAI_API_KEY_STAGING --env STRIPE_PAYMENT_SUCCESS_TOKEN=$$STRIPE_TOKEN_STAGING

deploy-prod:
	vercel --prod --env OPENAI_API_KEY=$$OPENAI_API_KEY_PROD --env STRIPE_PAYMENT_SUCCESS_TOKEN=$$STRIPE_TOKEN_PROD

# Clean up
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -f .coverage
	rm -rf dist
	rm -rf build

# Full quality check (run before commit)
check: lint test security
	@echo "✅ All quality checks passed!"

# Help
help:
	@echo "Resume Health Checker - Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  install      Install dependencies and pre-commit hooks"
	@echo ""
	@echo "Development:"
	@echo "  dev          Start development server with hot reload"
	@echo "  prod         Start production server locally"
	@echo ""
	@echo "Code Quality:"
	@echo "  lint         Run all linters"
	@echo "  format       Format code with black and isort"
	@echo "  check        Run all quality checks (lint + test + security)"
	@echo ""
	@echo "Testing:"
	@echo "  test         Run all tests"
	@echo "  test-cov     Run tests with coverage report"
	@echo "  test-watch   Run tests in watch mode"
	@echo ""
	@echo "Security:"
	@echo "  security     Run security scans"
	@echo ""
	@echo "Deployment:"
	@echo "  deploy-staging  Deploy to staging environment"
	@echo "  deploy-prod     Deploy to production environment"
	@echo ""
	@echo "Utilities:"
	@echo "  clean        Clean up generated files"
	@echo "  help         Show this help message"