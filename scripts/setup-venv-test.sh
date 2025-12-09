#!/bin/bash

# Setup script for venv-test to match CI environment (Python 3.10)
# This ensures all test dependencies are installed

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get the project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo -e "${BLUE}🔧 Setting up venv-test for local testing...${NC}"

# Check if venv-test exists
if [ ! -d "venv-test" ]; then
    echo -e "${YELLOW}Creating venv-test with Python 3.10...${NC}"
    python3.10 -m venv venv-test
fi

# Activate venv
source venv-test/bin/activate

# Verify Python version
PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
echo -e "${GREEN}✓ Using Python $PYTHON_VERSION${NC}"

# Upgrade pip
echo -e "${BLUE}📦 Upgrading pip...${NC}"
python -m pip install --upgrade pip > /dev/null 2>&1

# Setup DailyDrip RAG
echo -e "${BLUE}📦 Installing DailyDrip RAG dependencies...${NC}"
cd "$PROJECT_ROOT/dailydrip_rag"
pip install -e ".[dev]" > /dev/null 2>&1
echo -e "${GREEN}✓ DailyDrip RAG dependencies installed${NC}"

# Setup Agent Core
echo -e "${BLUE}📦 Installing Agent Core dependencies...${NC}"
cd "$PROJECT_ROOT/agent_core"
pip install -r agent_requirements.txt > /dev/null 2>&1
pip install -r requirements-dev.txt > /dev/null 2>&1
echo -e "${GREEN}✓ Agent Core dependencies installed${NC}"

echo ""
echo -e "${GREEN}✅ venv-test setup complete!${NC}"
echo ""
echo "To run tests locally, use:"
echo "  ./scripts/test-local.sh          # Run all tests"
echo "  ./scripts/test-local.sh rag      # Run only RAG tests"
echo "  ./scripts/test-local.sh agent    # Run only agent tests"
echo "  ./scripts/test-local.sh frontend # Run only frontend tests"
echo ""

