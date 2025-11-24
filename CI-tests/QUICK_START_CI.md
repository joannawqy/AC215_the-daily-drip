# 🚀 Quick Start - CI/CD Pipeline

## One-Command Setup

```bash
# Install all testing dependencies
./scripts/setup-tests.sh
```

## One-Command Test Run

```bash
# Run all tests with coverage
./scripts/run-all-tests.sh
```

## Individual Commands

### Python Backend

```bash
# DailyDrip RAG
cd dailydrip_rag
pip install -e ".[dev]"
pytest tests/ -v --cov=src --cov-report=html

# Agent Core
cd agent_core
pip install -r agent_requirements.txt -r requirements-dev.txt
pytest tests/ -v --cov=. --cov-report=html
```

### Frontend

```bash
cd frontend
npm install
npm test -- --coverage --watchAll=false
```

### Linting

```bash
# Python
cd dailydrip_rag && flake8 src
cd agent_core && flake8 .

# Frontend
cd frontend && npm run lint
```

## View Coverage Reports

```bash
# Python
open dailydrip_rag/htmlcov/index.html
open agent_core/htmlcov/index.html

# Frontend
open frontend/coverage/lcov-report/index.html
```

## GitHub Actions

All tests run automatically on:
- Push to `main` or `milestone4`
- Pull requests to `main` or `milestone4`

View results: **GitHub → Actions tab**

## Coverage Requirements

✅ Minimum 50% coverage enforced for:
- Lines
- Functions
- Branches
- Statements

## Key Files

- **Tests:** `*/tests/test_*.py`, `*/src/**/*.test.js`
- **Config:** `pytest.ini`, `jest.config.js`, `.flake8`
- **Workflows:** `.github/workflows/*.yml`
- **Docs:** `CI_CD_DOCUMENTATION.md`, `TESTING_GUIDE.md`

## Need Help?

1. Check `TESTING_GUIDE.md` for detailed instructions
2. Review `CI_CD_DOCUMENTATION.md` for complete reference
3. See `CI_SETUP_SUMMARY.md` for what's implemented

## Status Badges

Add to README.md:

```markdown
![Python CI](https://github.com/joannawqy/AC215_the-daily-drip/workflows/Python%20Backend%20CI/badge.svg)
![Frontend CI](https://github.com/joannawqy/AC215_the-daily-drip/workflows/Frontend%20CI/badge.svg)
![Docker CI](https://github.com/joannawqy/AC215_the-daily-drip/workflows/Docker%20Build%20CI/badge.svg)
```

---

**Ready to go!** 🎉 Push your changes and watch the CI pipeline in action.
