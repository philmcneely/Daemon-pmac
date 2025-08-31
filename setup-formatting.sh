#!/bin/bash
# Development Environment Setup Script
# This script configures your development environment for consistent code formatting

set -e

echo "🔧 Setting up development environment..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Install dependencies if not already installed
if [ ! -f "venv/lib/python*/site-packages/pre-commit" ]; then
    echo "📥 Installing development dependencies..."
    pip install --upgrade pip
    pip install -r requirements-dev.txt
fi

# Install pre-commit hooks
echo "📦 Installing pre-commit hooks..."
pre-commit install

# Update pre-commit hooks to latest versions
echo "🔄 Updating pre-commit hooks..."
pre-commit autoupdate

# Run pre-commit on all files to ensure everything is formatted
echo "🎨 Formatting all files with pre-commit hooks..."
pre-commit run --all-files

echo "✅ Development environment setup complete!"
echo ""
echo "📝 What's configured:"
echo "   • Virtual environment at ./venv/"
echo "   • Pre-commit hooks will auto-format code on commit"
echo "   • Black formatting (line length: 88)"
echo "   • isort import organization"
echo "   • VS Code settings for format-on-save"
echo ""
echo "💡 VS Code Extensions to install:"
echo "   • Python (ms-python.python)"
echo "   • Pylance (ms-python.vscode-pylance)"
echo "   • Black Formatter (ms-python.black-formatter)"
echo "   • isort (ms-python.isort)"
echo ""
echo "🎯 Now when you:"
echo "   • Save a file in VS Code → Auto-formatted with Black"
echo "   • Commit changes → Pre-commit hooks auto-format"
echo "   • No more formatting conflicts!"
echo ""
echo "🚀 To activate environment: source venv/bin/activate"
echo "🚀 To open in VS Code: code daemon.code-workspace"
