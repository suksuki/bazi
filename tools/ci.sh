#!/bin/bash
# CI Automation Script
# Runs all tests and quality checks.

set -e  # Exit on error

# Ensure we are in the project root
cd "$(dirname "$0")/.."

echo "🚀 Starting CI Verification..."

# Activate venv if exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# 1. Run Tests (Unit + Integration)
echo "🧪 Running Pytest..."
export PYTHONPATH=.
pytest tests/ -v

echo "✅ All Tests Passed!"
