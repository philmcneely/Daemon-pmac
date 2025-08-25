#!/bin/bash
# Pre-commit script for code quality

echo "Running code quality checks..."

# Format with black
echo "Formatting with black..."
./venv/bin/black app/ --line-length 88 --quiet

# Sort imports
echo "Sorting imports with isort..."
./venv/bin/isort app/ --profile black --line-length 88 --quiet

# Run flake8
echo "Checking with flake8..."
./venv/bin/flake8 app/ --count --statistics

if [ $? -ne 0 ]; then
    echo "❌ Flake8 checks failed!"
    exit 1
fi

# Run mypy with relaxed settings for CI/CD compatibility
echo "Type checking with mypy..."
./venv/bin/mypy app/ \
    --ignore-missing-imports \
    --show-error-codes \
    --no-strict-optional \
    --allow-untyped-calls \
    --allow-untyped-defs \
    --allow-incomplete-defs \
    --allow-untyped-decorators \
    --no-warn-return-any

if [ $? -ne 0 ]; then
    echo "❌ MyPy type checking failed!"
    exit 1
fi

echo "✅ All code quality checks passed!"
