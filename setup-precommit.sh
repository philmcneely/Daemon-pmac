#!/bin/bash
# Setup script for pre-commit hooks

echo "🔧 Setting up pre-commit hooks for Daemon-pmac..."

# Check if pre-commit is installed
if ! command -v pre-commit &> /dev/null; then
    echo "📦 Installing pre-commit..."
    pip install pre-commit
else
    echo "✅ pre-commit is already installed"
fi

# Install the pre-commit hooks
echo "🪝 Installing pre-commit hooks..."
pre-commit install

# Run hooks on all files to ensure everything is working
echo "🧪 Testing pre-commit hooks on all files..."
pre-commit run --all-files

if [ $? -eq 0 ]; then
    echo "✅ Pre-commit hooks setup successfully!"
    echo ""
    echo "📋 What happens next:"
    echo "  • Black and isort will run automatically before each commit"
    echo "  • Code formatting issues will be caught before pushing to GitHub"
    echo "  • This prevents CI/CD pipeline failures due to formatting"
    echo ""
    echo "💡 Tips:"
    echo "  • Run 'pre-commit run --all-files' to check all files manually"
    echo "  • Run 'black .' to format all Python files"
    echo "  • Run 'isort .' to sort all imports"
    echo "  • Use 'git commit --no-verify' to skip hooks (not recommended)"
else
    echo "❌ Pre-commit hooks setup failed. Please check the errors above."
    exit 1
fi
