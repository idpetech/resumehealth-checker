# 🚀 Quick Start Guide

## Option 1: Shell Script (Recommended for macOS/Linux)

```bash
# Make executable and run setup
chmod +x setup.sh
./setup.sh
```

## Option 2: Python Script (Cross-platform)

```bash
python setup.py setup
```

## Option 3: Manual Setup

```bash
# 1. Create virtual environment
python3 -m venv .venv

# 2. Activate virtual environment
# On macOS/Linux:
source .venv/bin/activate
# On Windows:
# .venv\Scripts\activate

# 3. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 4. Install pre-commit hooks (optional)
pre-commit install

# 5. Create environment file
cp .env.example .env
# Edit .env with your API keys
```

## Next Steps

1. **Edit .env file** with your API keys:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   STRIPE_PAYMENT_SUCCESS_TOKEN=your_stripe_token_here
   ```

2. **Activate virtual environment** (do this each time you work on the project):
   ```bash
   source .venv/bin/activate  # macOS/Linux
   # OR
   .venv\Scripts\activate     # Windows
   ```

3. **Run tests** to verify setup:
   ```bash
   python -m pytest tests/ -v
   ```

4. **Start development server**:
   ```bash
   python -m uvicorn main:app --reload
   ```
   Visit: http://localhost:8000

## Development Commands

Once set up, you can use these commands:

### Using Shell Script:
```bash
./setup.sh test     # Run tests
./setup.sh dev      # Start dev server
./setup.sh lint     # Check code quality
./setup.sh format   # Format code
```

### Using Python Script:
```bash
python setup.py test     # Run tests
python setup.py dev      # Start dev server
python setup.py lint     # Check code quality
python setup.py format   # Format code
```

### Using Make (if available):
```bash
make install    # Setup project
make test       # Run tests
make dev        # Start dev server
make lint       # Check code quality
make format     # Format code
```

### Direct Python Commands:
```bash
# Always activate venv first: source .venv/bin/activate

python -m pytest tests/ -v                    # Run tests
python -m pytest tests/ -v --cov=main         # Run tests with coverage
python -m uvicorn main:app --reload            # Start dev server
python -m black main.py tests/                # Format code
python -m flake8 main.py tests/               # Lint code
```

## Troubleshooting

### Common Issues:

1. **"pip: No such file or directory"**
   - Use `python setup.py setup` instead of `make install`
   - Or install pip: `python -m ensurepip --upgrade`

2. **"Python not found"**
   - Install Python 3.9+: https://python.org/downloads/
   - Try `python3` instead of `python`

3. **"Virtual environment not activating"**
   - On macOS/Linux: `source .venv/bin/activate`
   - On Windows: `.venv\Scripts\activate`
   - Or use absolute path

4. **"Tests failing"**
   - Ensure virtual environment is activated
   - Check that all dependencies are installed
   - Verify .env file has placeholder values

5. **"Pre-commit hooks failing"**
   - Run `pre-commit install` manually
   - Format code first: `python -m black main.py tests/`

### System Requirements:

- **Python 3.9+** (required)
- **pip** (usually comes with Python)
- **git** (for pre-commit hooks)
- **make** (optional, for Makefile commands)

### Platform Notes:

- **macOS**: Use `./setup.sh` (recommended)
- **Linux**: Use `./setup.sh` (recommended)  
- **Windows**: Use `python setup.py setup` or Git Bash with `./setup.sh`

## Production Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for complete deployment instructions including:
- GitHub Actions CI/CD setup
- Vercel deployment
- Environment configuration
- Monitoring setup