#!/usr/bin/env python3
"""
Resume Health Checker - Setup Script
Alternative to Makefile for systems without make
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description="", ignore_errors=False):
    """Run a command and handle errors"""
    print(f"🔧 {description}")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        if result.stdout.strip():
            print(f"✅ {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        if ignore_errors:
            print(f"⚠️  {description} failed: {e.stderr.strip()}")
            return False
        else:
            print(f"❌ {description} failed: {e.stderr.strip()}")
            sys.exit(1)

def check_python():
    """Check Python version"""
    if sys.version_info < (3, 9):
        print(f"❌ Python 3.9+ required, found {sys.version}")
        print("Visit: https://python.org/downloads/")
        sys.exit(1)
    
    print(f"✅ Python {sys.version.split()[0]} found")

def setup():
    """Main setup function"""
    print("🚀 Resume Health Checker - Setup")
    print("=" * 50)
    
    # Check Python version
    check_python()
    
    # Create virtual environment if it doesn't exist
    if not Path(".venv").exists():
        print("🐍 Creating virtual environment...")
        run_command(f"{sys.executable} -m venv .venv", "Creating virtual environment")
    else:
        print("✅ Virtual environment already exists")
    
    # Determine the activation script path
    if os.name == 'nt':  # Windows
        venv_python = Path(".venv/Scripts/python.exe")
        pip_cmd = str(Path(".venv/Scripts/pip.exe"))
    else:  # macOS/Linux
        venv_python = Path(".venv/bin/python")
        pip_cmd = str(Path(".venv/bin/pip"))
    
    if not venv_python.exists():
        print("❌ Virtual environment creation failed")
        sys.exit(1)
    
    # Use virtual environment Python and pip
    venv_python_str = str(venv_python)
    
    # Upgrade pip in virtual environment
    run_command(f"{venv_python_str} -m pip install --upgrade pip", "Upgrading pip in virtual environment")
    
    # Install requirements in virtual environment
    run_command(f"{venv_python_str} -m pip install -r requirements.txt", "Installing dependencies in virtual environment")
    
    # Install pre-commit hooks using virtual environment
    run_command(f"{venv_python_str} -m pre_commit install", "Installing pre-commit hooks", ignore_errors=True)
    
    # Create .env file if it doesn't exist
    if not Path(".env").exists():
        if Path(".env.example").exists():
            run_command("cp .env.example .env", "Creating .env file")
            print("📝 Please edit .env file with your API keys")
        else:
            print("⚠️  No .env.example found, you'll need to create .env manually")
    
    print("\n✅ Setup complete!")
    print("\nNext steps:")
    print("1. Edit .env file with your API keys")
    print("2. Activate virtual environment:")
    if os.name == 'nt':  # Windows
        print("   .venv\\Scripts\\activate")
    else:  # macOS/Linux
        print("   source .venv/bin/activate")
    print("3. Run tests: python -m pytest tests/ -v")
    print("4. Start dev server: python -m uvicorn main:app --reload")
    print("\nOr use the setup script commands:")
    print("   python setup.py test     # Run tests")
    print("   python setup.py dev      # Start dev server")

def get_venv_python():
    """Get virtual environment Python executable"""
    if os.name == 'nt':  # Windows
        venv_python = Path(".venv/Scripts/python.exe")
    else:  # macOS/Linux
        venv_python = Path(".venv/bin/python")
    
    if venv_python.exists():
        return str(venv_python)
    else:
        print("⚠️  Virtual environment not found, using system Python")
        return sys.executable

def test():
    """Run tests"""
    print("🧪 Running tests...")
    python_exe = get_venv_python()
    run_command(f"{python_exe} -m pytest tests/ -v", "Running tests")

def dev():
    """Start development server"""
    print("🚀 Starting development server...")
    print("📝 Server will be available at http://localhost:8000")
    python_exe = get_venv_python()
    run_command(f"{python_exe} -m uvicorn main:app --reload --host 0.0.0.0 --port 8000", "Starting server")

def lint():
    """Run linting"""
    print("🔍 Running code quality checks...")
    python_exe = get_venv_python()
    run_command(f"{python_exe} -m flake8 main.py tests/", "Running flake8", ignore_errors=True)
    run_command(f"{python_exe} -m black --check main.py tests/", "Checking black formatting", ignore_errors=True)
    run_command(f"{python_exe} -m isort --check-only main.py tests/", "Checking import sorting", ignore_errors=True)

def format_code():
    """Format code"""
    print("🎨 Formatting code...")
    python_exe = get_venv_python()
    run_command(f"{python_exe} -m black main.py tests/", "Running black formatter")
    run_command(f"{python_exe} -m isort main.py tests/", "Sorting imports")

def help_menu():
    """Show help menu"""
    print("Resume Health Checker - Setup Script")
    print("=" * 50)
    print("Available commands:")
    print("  python setup.py setup    - Install dependencies and setup project")
    print("  python setup.py test     - Run tests")
    print("  python setup.py dev      - Start development server")
    print("  python setup.py lint     - Run code quality checks")
    print("  python setup.py format   - Format code")
    print("  python setup.py help     - Show this help")
    print()
    print("Alternative using python -m commands:")
    print("  python -m pip install -r requirements.txt")
    print("  python -m pytest tests/ -v")
    print("  python -m uvicorn main:app --reload")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        help_menu()
        sys.exit(0)
    
    command = sys.argv[1].lower()
    
    if command == "setup":
        setup()
    elif command == "test":
        test()
    elif command == "dev":
        dev()
    elif command == "lint":
        lint()
    elif command == "format":
        format_code()
    elif command == "help":
        help_menu()
    else:
        print(f"❌ Unknown command: {command}")
        help_menu()
        sys.exit(1)