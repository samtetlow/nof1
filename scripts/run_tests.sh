#!/bin/bash
# Run all tests with coverage

set -e

echo "🧪 Running n of 1 Platform Tests..."
echo "=================================="

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Install test dependencies
echo "📦 Installing dependencies..."
pip install -q -r requirements.txt

# Run pytest with coverage
echo ""
echo "🔬 Running unit tests..."
pytest tests/unit/ -v --cov --cov-report=term-missing

echo ""
echo "🔗 Running integration tests..."
pytest tests/integration/ -v --cov --cov-append

# Generate HTML coverage report
echo ""
echo "📊 Generating coverage report..."
coverage html
echo "Coverage report generated in htmlcov/index.html"

# Check coverage threshold
echo ""
echo "✅ Checking coverage threshold (80%)..."
coverage report --fail-under=80

echo ""
echo "========================================="
echo "✅ All tests passed! Coverage: $(coverage report --format=total)%"




