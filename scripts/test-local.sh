#!/bin/bash

# Local test runner using venv-test (Python 3.10) to match CI environment
# Usage: ./scripts/test-local.sh [component]
#   component: 'rag', 'agent', 'frontend', or omit for all

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

# Activate venv-test
if [ ! -d "venv-test" ]; then
    echo -e "${RED}Error: venv-test directory not found${NC}"
    echo "Please create it with: python3.10 -m venv venv-test"
    exit 1
fi

echo -e "${BLUE}🔧 Activating venv-test (Python 3.10.7)...${NC}"
source venv-test/bin/activate

# Verify Python version
PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
echo -e "${GREEN}✓ Using Python $PYTHON_VERSION${NC}"
echo ""

COMPONENT=${1:-all}

# Track failures
FAILED=0

# Test DailyDrip RAG
if [ "$COMPONENT" = "all" ] || [ "$COMPONENT" = "rag" ]; then
    echo -e "${BLUE}Testing DailyDrip RAG...${NC}"
    cd "$PROJECT_ROOT/dailydrip_rag"
    
    # Install dependencies if needed
    if ! python -c "import pytest" 2>/dev/null; then
        echo "Installing dependencies..."
        pip install -e ".[dev]" > /dev/null 2>&1
    fi
    
    if pytest tests/ -v --cov=src --cov-report=term --cov-report=html; then
        echo -e "${GREEN}✓ DailyDrip RAG tests passed${NC}"
    else
        echo -e "${RED}✗ DailyDrip RAG tests failed${NC}"
        FAILED=1
    fi
    echo ""
fi

# Test Agent Core
if [ "$COMPONENT" = "all" ] || [ "$COMPONENT" = "agent" ]; then
    echo -e "${BLUE}Testing Agent Core...${NC}"
    cd "$PROJECT_ROOT/agent_core"
    
    # Install dependencies if needed
    if ! python -c "import pytest" 2>/dev/null; then
        echo "Installing dependencies..."
        pip install -r agent_requirements.txt > /dev/null 2>&1
        pip install -r requirements-dev.txt > /dev/null 2>&1
    fi
    
    if pytest tests/ -v --cov=. --cov-report=term --cov-report=html; then
        echo -e "${GREEN}✓ Agent Core tests passed${NC}"
    else
        echo -e "${RED}✗ Agent Core tests failed${NC}"
        FAILED=1
    fi
    echo ""
fi

# Test Frontend (doesn't need Python, but included for completeness)
if [ "$COMPONENT" = "all" ] || [ "$COMPONENT" = "frontend" ]; then
    echo -e "${BLUE}Testing Frontend...${NC}"
    cd "$PROJECT_ROOT/frontend"
    
    if npm test -- --coverage --watchAll=false; then
        echo -e "${GREEN}✓ Frontend tests passed${NC}"
    else
        echo -e "${RED}✗ Frontend tests failed${NC}"
        FAILED=1
    fi
    echo ""
fi

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
    echo ""
    echo "Coverage reports available at:"
    [ "$COMPONENT" = "all" ] || [ "$COMPONENT" = "rag" ] && echo "  - dailydrip_rag/htmlcov/index.html"
    [ "$COMPONENT" = "all" ] || [ "$COMPONENT" = "agent" ] && echo "  - agent_core/htmlcov/index.html"
    [ "$COMPONENT" = "all" ] || [ "$COMPONENT" = "frontend" ] && echo "  - frontend/coverage/lcov-report/index.html"
    exit 0
else
    echo -e "${RED}❌ Some tests failed${NC}"
    echo ""
    echo "Please review the test output above and fix failing tests."
    exit 1
fi

