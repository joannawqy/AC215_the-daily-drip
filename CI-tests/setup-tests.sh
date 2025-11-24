#!/bin/bash

# Setup script for testing environment
# This script installs all dependencies needed for testing

set -e  # Exit on error

echo "🚀 Setting up testing environment for The Daily Drip..."

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo -e "${BLUE}📦 Installing Python dependencies...${NC}"

# Setup DailyDrip RAG
echo "Setting up DailyDrip RAG..."
cd "$PROJECT_ROOT/dailydrip_rag"
pip install -e ".[dev]"
echo -e "${GREEN}✓ DailyDrip RAG dependencies installed${NC}"

# Setup Agent Core
echo "Setting up Agent Core..."
cd "$PROJECT_ROOT/agent_core"
pip install -r agent_requirements.txt
pip install -r requirements-dev.txt
echo -e "${GREEN}✓ Agent Core dependencies installed${NC}"

# Setup Frontend
echo -e "${BLUE}📦 Installing Frontend dependencies...${NC}"
cd "$PROJECT_ROOT/frontend"
npm install
echo -e "${GREEN}✓ Frontend dependencies installed${NC}"

echo ""
echo -e "${GREEN}✅ All dependencies installed successfully!${NC}"
echo ""
echo "Next steps:"
echo "  1. Run Python tests: cd dailydrip_rag && pytest tests/ -v"
echo "  2. Run Frontend tests: cd frontend && npm test"
echo "  3. Check coverage: pytest --cov=src --cov-report=html"
echo ""
echo "For more information, see TESTING_GUIDE.md"
