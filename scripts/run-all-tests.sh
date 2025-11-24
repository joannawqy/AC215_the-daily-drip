#!/bin/bash

# Run all tests across the project
# This script runs Python and Frontend tests with coverage

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get the project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo -e "${BLUE}🧪 Running all tests for The Daily Drip...${NC}"
echo ""

# Track failures
FAILED=0

# Test DailyDrip RAG
echo -e "${BLUE}Testing DailyDrip RAG...${NC}"
cd "$PROJECT_ROOT/dailydrip_rag"
if pytest tests/ -v --cov=src --cov-report=term --cov-report=html; then
    echo -e "${GREEN}✓ DailyDrip RAG tests passed${NC}"
else
    echo -e "${RED}✗ DailyDrip RAG tests failed${NC}"
    FAILED=1
fi
echo ""

# Test Agent Core
echo -e "${BLUE}Testing Agent Core...${NC}"
cd "$PROJECT_ROOT/agent_core"
if pytest tests/ -v --cov=. --cov-report=term --cov-report=html; then
    echo -e "${GREEN}✓ Agent Core tests passed${NC}"
else
    echo -e "${RED}✗ Agent Core tests failed${NC}"
    FAILED=1
fi
echo ""

# Test Frontend
echo -e "${BLUE}Testing Frontend...${NC}"
cd "$PROJECT_ROOT/frontend"
if npm test -- --coverage --watchAll=false; then
    echo -e "${GREEN}✓ Frontend tests passed${NC}"
else
    echo -e "${RED}✗ Frontend tests failed${NC}"
    FAILED=1
fi
echo ""

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
    echo ""
    echo "Coverage reports available at:"
    echo "  - dailydrip_rag/htmlcov/index.html"
    echo "  - agent_core/htmlcov/index.html"
    echo "  - frontend/coverage/lcov-report/index.html"
    exit 0
else
    echo -e "${RED}❌ Some tests failed${NC}"
    echo ""
    echo "Please review the test output above and fix failing tests."
    exit 1
fi
