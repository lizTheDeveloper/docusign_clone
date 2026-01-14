#!/bin/bash

# Test runner script with detailed output
# This script helps identify test issues

set -e

echo "🧪 Running Authentication Tests"
echo "================================"
echo ""

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Virtual environment not activated"
    echo "   Run: source venv/bin/activate"
    exit 1
fi

# Check if PostgreSQL is running
echo "1️⃣ Checking PostgreSQL connection..."
if ! pg_isready -h localhost -p 5432 > /dev/null 2>&1; then
    echo "❌ PostgreSQL is not running"
    echo "   Start it with: brew services start postgresql"
    echo "   Or: sudo systemctl start postgresql"
    exit 1
fi
echo "✅ PostgreSQL is running"
echo ""

# Check if test database exists
echo "2️⃣ Checking test database..."
if ! psql -U postgres -lqt | cut -d \| -f 1 | grep -qw docusign_clone_test; then
    echo "⚠️  Test database doesn't exist. Creating it..."
    createdb -U postgres docusign_clone_test || echo "   (Database may already exist)"
fi
echo "✅ Test database ready"
echo ""

# Run tests with different verbosity levels
echo "3️⃣ Running tests..."
echo ""

# Option 1: Run all tests with basic output
if [ "$1" == "simple" ]; then
    pytest tests/ -v
    exit 0
fi

# Option 2: Run with coverage (default)
if [ "$1" == "coverage" ]; then
    pytest tests/ --cov=app --cov-report=term-missing --cov-report=html
    echo ""
    echo "📊 Coverage report generated in htmlcov/index.html"
    exit 0
fi

# Option 3: Run specific test
if [ "$1" == "specific" ] && [ -n "$2" ]; then
    pytest tests/test_auth.py::$2 -v -s
    exit 0
fi

# Option 4: Run with detailed output (default)
echo "Running all tests with detailed output..."
pytest tests/ -v -s --tb=short

echo ""
echo "✅ Tests complete!"
echo ""
echo "💡 Other test options:"
echo "   ./run_tests.sh simple      # Basic output"
echo "   ./run_tests.sh coverage    # With coverage report"
echo "   ./run_tests.sh specific TestUserRegistration::test_register_user_success"
