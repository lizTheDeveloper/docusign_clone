#!/bin/bash
# Quick E2E Test Runner for Document Management

set -e

echo "🚀 Document Management E2E Test Suite"
echo "======================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if backend is running
echo "📡 Checking backend status..."
if curl -s http://localhost:8000/api/v1/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Backend is running${NC}"
else
    echo -e "${RED}✗ Backend is NOT running${NC}"
    echo "Please start the backend:"
    echo "  cd backend && uvicorn app.main:app --reload"
    exit 1
fi

# Navigate to frontend
cd "$(dirname "$0")/frontend"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

# Check if Playwright browsers are installed
if [ ! -d "node_modules/.playwright" ]; then
    echo "🎭 Installing Playwright browsers..."
    npx playwright install chromium
fi

echo ""
echo "🧪 Running E2E Tests..."
echo ""

# Parse arguments
if [ "$1" == "--ui" ]; then
    echo "Opening Playwright UI..."
    npm run test:e2e:ui
elif [ "$1" == "--headed" ]; then
    echo "Running tests in headed mode..."
    npm run test:e2e:headed
elif [ "$1" == "--debug" ]; then
    echo "Running tests in debug mode..."
    npm run test:e2e:debug
elif [ "$1" == "--documents" ]; then
    echo "Running document tests only..."
    npx playwright test documents.spec.ts
elif [ "$1" == "--report" ]; then
    echo "Opening test report..."
    npm run test:e2e:report
else
    echo "Running all tests..."
    npm run test:e2e
    
    echo ""
    echo "📊 Test Results"
    echo "==============="
    echo "To view detailed report:"
    echo "  npm run test:e2e:report"
    echo ""
    echo "Test options:"
    echo "  $0 --ui          # Interactive UI mode"
    echo "  $0 --headed      # See browser"
    echo "  $0 --debug       # Debug mode"
    echo "  $0 --documents   # Only document tests"
    echo "  $0 --report      # View last report"
fi

echo ""
echo -e "${GREEN}✓ Tests complete!${NC}"
