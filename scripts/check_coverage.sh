#!/bin/bash
# Check test coverage and fail if below threshold

set -e

THRESHOLD=80

echo "📊 Checking test coverage..."

# Run tests with coverage
pytest tests/ --cov --cov-report=term-missing --cov-report=xml -q

# Get coverage percentage
COVERAGE=$(coverage report --format=total)

echo ""
echo "Current coverage: $COVERAGE%"
echo "Required threshold: $THRESHOLD%"

# Check if coverage meets threshold
if (( $(echo "$COVERAGE < $THRESHOLD" | bc -l) )); then
    echo "❌ Coverage $COVERAGE% is below threshold $THRESHOLD%"
    exit 1
else
    echo "✅ Coverage $COVERAGE% meets threshold $THRESHOLD%"
    exit 0
fi




