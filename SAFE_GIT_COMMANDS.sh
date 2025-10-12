#!/bin/bash
# Safe Git Commands to Push to a New Branch
# This will NOT affect the main branch

cd "/Users/liyiwen/Desktop/215 agent"

echo "Step 1: Initialize git repository..."
git init

echo "Step 2: Add remote repository..."
git remote add origin https://github.com/joannawqy/the-daily-drip.git

echo "Step 3: Fetch existing branches (doesn't change anything locally)..."
git fetch origin

echo "Step 4: Create and switch to a NEW branch..."
git checkout -b feature/visualization-agent

echo "Step 5: Add your new files..."
git add integrated_agent.py
git add visualization_agent_v2.py
git add ANSWERS_TO_YOUR_QUESTIONS.md
git add INTEGRATION_USAGE.md
git add QUICK_START.md
git add GIT_PUSH_GUIDE.md
git add demo_bean.json
git add .gitignore

echo "Step 6: Commit with message..."
git commit -m "Add visualization agent with timeline integration

- Created integrated_agent.py to connect core agent with visualization agent
- Added visualization_agent_v2.py with new single-line timeline chart
- Improved HTML layout: parameters → timeline chart → brewing steps → flavor notes
- Added comprehensive documentation (ANSWERS, INTEGRATION_USAGE, QUICK_START)
- Included demo_bean.json for testing
- Added .gitignore for project

This closes the visualization component of the DailyDrip project."

echo "Step 7: Push to NEW branch (not main!)..."
git push -u origin feature/visualization-agent

echo ""
echo "✓ Done! Your work is now on the 'feature/visualization-agent' branch."
echo "✓ Main branch is untouched."
echo "✓ Go to GitHub to create a Pull Request!"
echo "✓ URL: https://github.com/joannawqy/the-daily-drip/compare/feature/visualization-agent"
