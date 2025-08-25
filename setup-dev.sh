#!/bin/bash

# Development environment setup script for Daemon

echo "🚀 Setting up Daemon development environment..."

# Check if Python 3.9+ is available
python_version=$(python3 --version 2>&1 | sed 's/.* \([0-9]\+\.[0-9]\+\).*/\1/')
required_version="3.9"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python 3.9+ is required. Found: $python_version"
    exit 1
fi

echo "✅ Python version: $python_version"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install production dependencies
echo "📥 Installing production dependencies..."
pip install -r requirements.txt

# Install development dependencies
echo "🛠️ Installing development dependencies..."
pip install -r requirements-dev.txt

# Setup pre-commit hooks
echo "🪝 Setting up pre-commit hooks..."
pre-commit install

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p data
mkdir -p logs
mkdir -p backups

# Initialize database (if needed)
if [ ! -f "daemon.db" ]; then
    echo "🗃️ Initializing database..."
    touch daemon.db
fi

echo ""
echo "✅ Development environment setup complete!"
echo ""
echo "To activate the environment in the future, run:"
echo "  source venv/bin/activate"
echo ""
echo "To start the development server:"
echo "  python dev.py"
echo ""
echo "To run tests:"
echo "  pytest tests/"
echo ""
echo "To run linting:"
echo "  black app/ tests/"
echo "  isort app/ tests/"
echo "  flake8 app/ tests/"
echo ""
echo "Happy coding! 🎉"
