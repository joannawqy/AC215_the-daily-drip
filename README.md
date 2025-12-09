# AC215 – Milestone 4 – DailyDrip

[![codecov](https://codecov.io/gh/joannawqy/AC215_the-daily-drip/branch/milestone4/graph/badge.svg)](https://codecov.io/gh/joannawqy/AC215_the-daily-drip)

## Team
- **Team Name:** DailyDrip Collective
- **Members:** Even Li, Joanna Wang, Jessica Wang, Zicheng Ma

## Background & Motivation
Coffee brewing is both an art and a science. Enthusiasts often struggle to dial in grind size, water ratio, pour schedule, and temperature to match their taste preferences. Keeping track of experiments can be overwhelming, especially when juggling multiple beans and brewers.

DailyDrip combines consumer preference data, brewing logs, and generative AI to build a practical assistant that makes everyday coffee brewing easier, more personalized, and more enjoyable. The project targets three coordinated capabilities:
1. **Brewing recipe agent** – recommends brewing parameters tailored to taste goals.
2. **Visualization agent** – renders recipes as timelines that clarify pour cadence and amounts.
3. **RAG-style knowledge base** – stores beans and past brews to ground future recommendations.

## Project Scope
- Implement a FastAPI brewing agent that generates complete JSON recipes from bean metadata.
- Provide a visualization agent that converts recipes into HTML/Mermaid/ASCII timelines.
- Maintain a Retrieval-Augmented Generation (RAG) pipeline (ingest → chunk → index → serve) to surface reference brews during recipe generation.
- Build a React frontend with user authentication, bean library management, and interactive recipe generation.
- Package the system in Docker containers and deliver reproducible commands for local testing.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        DailyDrip System                          │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────┐
│   React Frontend │  ← User Interface
│   (Port 3000)    │     - Authentication & User Profile
│                  │     - Bean Library Management
│   Components:    │     - Recipe Generator
│   - AuthLanding  │     - Visualization Display
│   - Profile      │
│   - BeanCollection│
│   - RecipeGen    │
└────────┬─────────┘
         │ HTTPS/REST
         ↓
┌──────────────────┐     ┌─────────────────┐
│  Agent Core API  │────→│   OpenAI API    │
│  (Port 9000)     │     │                 │
│                  │     │  - gpt-4o-mini  │
│  FastAPI Endpoints:    │  - Recipe Gen   │
│  - /auth/*       │     └─────────────────┘
│  - /profile      │
│  - /beans/*      │     ┌─────────────────┐
│  - /brew         │────→│  RAG Service    │
│  - /visualize    │     │  (Port 8000)    │
└──────────────────┘     │                 │
                         │  - ChromaDB     │
         ↓               │  - Embeddings   │
┌──────────────────┐     │  - Similarity   │
│ Visualization    │     │    Search       │
│ Agent V2         │     └─────────────────┘
│                  │
│  - HTML Timeline │            ↑
│  - Mermaid Chart │            │
│  - ASCII Art     │     ┌──────┴──────────┐
└──────────────────┘     │  RAG Pipeline   │
                         │                 │
                         │  ingest → chunk │
                         │         → index │
                         └─────────────────┘
```

## Repository Organization

The repository is organized into three main modules with clear separation of concerns:

```
AC215_the-daily-drip/
├── README.md                           # This file - setup & usage guide
├── INTEGRATION_USAGE.md                # Detailed agent integration guide
├── LICENSE                             # MIT License
├── Makefile                            # Docker workflow commands
├── docker-compose.yml                  # Container orchestration
├── Dockerfile.agent                    # Agent API container image
├── .gitignore                          # Git ignore rules
│
├── CI-tests/                           # CI/CD Testing Configuration
│   ├── .flake8                         # Python linting configuration
│   ├── CI_SETUP_SUMMARY.md             # CI/CD pipeline documentation
│   ├── QUICK_START_CI.md               # Quick CI setup guide
│   ├── setup-tests.sh                  # Test environment setup script
│   └── run-all-tests.sh                # Script to run all tests
│
├── agent_core/                         # Backend API & Agent Logic
│   ├── __init__.py                     # Package initialization
│   ├── agent.py                        # FastAPI brewing agent (main API)
│   ├── integrated_agent.py             # End-to-end agent workflow
│   ├── visualization_agent_v2.py       # Recipe visualization generator
│   ├── agent_requirements.txt          # Python dependencies
│   ├── requirements-dev.txt            # Development dependencies
│   ├── pytest.ini                      # Test configuration
│   └── tests/                          # Agent test suite
│       ├── __init__.py
│       ├── test_agent.py               # Core agent tests
│       ├── test_agent_logic.py         # Helper function tests
│       └── test_integrated_agent.py    # Integration tests
│
├── dailydrip_rag/                      # RAG Data Pipeline
│   ├── README.md                       # RAG-specific documentation
│   ├── Dockerfile                      # RAG service container
│   ├── Makefile                        # RAG pipeline commands
│   ├── pyproject.toml                  # Python package configuration
│   ├── pytest.ini                      # Test configuration
│   ├── .coveragerc                     # Coverage configuration
│   ├── src/                            # RAG pipeline modules
│   │   ├── __init__.py
│   │   ├── ingest.py                   # Data ingestion from CSV/JSON
│   │   ├── chunk.py                    # Text chunking for embeddings
│   │   ├── index.py                    # ChromaDB vector indexing
│   │   ├── query.py                    # Query utilities
│   │   └── service.py                  # FastAPI RAG service
│   ├── data/                           # Data storage
│   │   ├── raw/                        # Raw input data (CSV/JSON)
│   │   └── processed/                  # Processed JSONL files
│   │       ├── records.jsonl           # Normalized records
│   │       └── chunks.jsonl            # Embedded chunks
│   ├── indexes/                        # Vector store
│   │   └── chroma/                     # ChromaDB persistent index
│   ├── scripts/                        # Utility scripts
│   └── tests/                          # RAG test suite
│       ├── conftest.py                 # Pytest fixtures
│       ├── test_ingest.py
│       ├── test_chunk.py
│       ├── test_index.py
│       ├── test_query.py
│       ├── test_service.py
│       ├── test_service_comprehensive.py
│       └── test_more_coverage.py
│
├── frontend/                           # React Frontend Application
│   ├── package.json                    # Node dependencies & scripts
│   ├── package-lock.json               # Locked dependency versions
│   ├── jest.config.js                  # Jest test configuration
│   ├── tailwind.config.js              # Tailwind CSS configuration
│   ├── postcss.config.js               # PostCSS configuration
│   ├── .gitignore                      # Frontend-specific ignores
│   ├── public/                         # Static assets
│   │   ├── index.html
│   │   ├── favicon.ico
│   │   └── manifest.json
│   └── src/                            # React source code
│       ├── index.js                    # Application entry point
│       ├── index.css                   # Global styles
│       ├── App.js                      # Main application component
│       ├── App.test.js                 # App component tests
│       ├── App.comprehensive.test.js   # Comprehensive app tests
│       ├── setupTests.js               # Test setup
│       ├── components/                 # React components
│       │   ├── AuthLanding.js          # Login/Register page
│       │   ├── AuthLanding.test.js
│       │   ├── Profile.js              # User profile & preferences
│       │   ├── Profile.test.js
│       │   ├── BeanCollection.js       # Bean library CRUD
│       │   ├── BeanCollection.test.js
│       │   ├── BeanCollection.comprehensive.test.js
│       │   ├── RecipeGenerator.js      # Recipe generation UI
│       │   ├── RecipeGenerator.test.js
│       │   ├── RecipeGenerator.helpers.test.js
│       │   └── RecipeGenerator.comprehensive.test.js
│       ├── context/                    # React Context providers
│       │   ├── AuthContext.js          # Authentication state management
│       │   └── AuthContext.test.js
│       └── services/                   # API client layer
│           ├── agentClient.js          # Agent API client
│           └── agentClient.test.js
│
├── .github/                            # GitHub configuration
│   └── workflows/                      # CI/CD workflows
│       ├── python-ci.yml               # Backend testing & coverage
│       ├── frontend-ci.yml             # Frontend testing
│       └── docker-ci.yml               # Docker build verification
│
├── data/                               # Application data (gitignored)
│   └── user_store.jsonl                # User accounts & beans (development)
│
├── reports/                            # Project documentation
│   └── MS2 Report.pdf                  # Milestone 2 report
│
├── scripts/                            # Utility scripts
│
└── tools/                              # Development tools
    ├── bean_request.json               # Sample brew API request
    ├── visualize_request.json          # Sample visualization request
    └── save_visualization.py           # Visualization fetcher script
```

> **Note:** `dailydrip_rag/data` and `dailydrip_rag/indexes` contain small illustrative artifacts only. Do **not** commit large datasets or full production indexes to version control.

## Technology Stack

### Backend
- **FastAPI** - Modern, high-performance Python web framework
- **OpenAI API** - GPT-4o-mini for recipe generation
- **ChromaDB** - Vector database for similarity search
- **Sentence-Transformers** - `all-MiniLM-L6-v2` for text embeddings
- **Pydantic** - Data validation and settings management
- **httpx** - Async HTTP client for API calls

### Frontend
- **React 18** - Component-based UI library
- **Tailwind CSS** - Utility-first CSS framework
- **Lucide React** - Beautiful icon library
- **Create React App** - Zero-configuration build setup

### Infrastructure & DevOps
- **Docker & Docker Compose** - Containerization and orchestration
- **GitHub Actions** - CI/CD pipeline
- **Codecov** - Test coverage reporting
- **pytest** - Python testing framework
- **Jest & React Testing Library** - JavaScript testing

### Code Quality
- **flake8** - Python linting
- **black** - Python code formatting
- **ESLint** - JavaScript linting
- **coverage.py** - Python code coverage

## Quick Start

### Prerequisites
- **Docker** & **Docker Compose** v2+
- **Node.js** 16+ and **npm** (for frontend development)
- **Python** 3.10+ (for local development)
- **OpenAI API Key** (required for recipe generation)

### 1. Clone the Repository

```bash
git clone https://github.com/joannawqy/AC215_the-daily-drip.git
cd AC215_the-daily-drip
git checkout milestone4
```

### 2. Set Environment Variables

```bash
# Required: OpenAI API key
export OPENAI_API_KEY="your-api-key-here"

# Optional: Custom configuration
export RAG_SERVICE_URL="http://localhost:8000"
export REACT_APP_AGENT_API_URL="http://localhost:9000"
export FRONTEND_ORIGINS="http://localhost:3000,http://localhost:3001"
```

### 3. Start the Full Stack (Docker)

```bash
# Build and start all services (RAG + Agent API)
make run
```

This command will:
1. Build Docker images for RAG and Agent services
2. Run the RAG pipeline (ingest → chunk → index)
3. Start the RAG service on port 8000
4. Start the Agent API on port 9000

### 4. Start the Frontend

```bash
# In a new terminal
cd frontend
npm install
npm start
```

The React app will open at [http://localhost:3000](http://localhost:3000)

### 5. Test the System

**Option A: Use the Frontend UI**
1. Navigate to [http://localhost:3000](http://localhost:3000)
2. Register a new account
3. Add a coffee bean to your library
4. Generate a recipe with visualization

**Option B: Use the API Directly**

```bash
# Register a user
curl -X POST http://localhost:9000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "coffee@example.com",
    "password": "secure123",
    "name": "Coffee Enthusiast"
  }'

# Save the token from the response
TOKEN="<your-token-here>"

# Create a bean
curl -X POST http://localhost:9000/beans \
  -H "Content-Type: application/json" \
  -H "X-Auth-Token: $TOKEN" \
  -d '{
    "bean": {
      "name": "Ethiopia Sidamo Natural",
      "process": "Natural",
      "variety": "Heirloom",
      "origin": "Ethiopia",
      "roast_level": "Light",
      "roasted_on": "2024-11-15",
      "altitude": "1800-2200m",
      "flavor_notes": ["blueberry", "floral", "tea-like"]
    }
  }'

# Generate a recipe
curl -X POST http://localhost:9000/brew \
  -H "Content-Type: application/json" \
  -H "X-Auth-Token: $TOKEN" \
  -d '{
    "bean": {
      "name": "Ethiopia Sidamo Natural",
      "process": "Natural",
      "variety": "Heirloom",
      "roast_level": "Light",
      "roasted_days": 8,
      "flavor_notes": ["blueberry", "floral"]
    },
    "brewer": "V60",
    "note": "I prefer bright acidity and light body"
  }'
```

## Detailed Usage Examples

### Example 1: Complete Workflow with Authentication

```bash
# Step 1: Register and login
TOKEN=$(curl -s -X POST http://localhost:9000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "barista@example.com",
    "password": "mypassword",
    "name": "Alex Barista"
  }' | jq -r '.token')

echo "Authenticated with token: $TOKEN"

# Step 2: Set your taste preferences
curl -X PUT http://localhost:9000/profile/preferences \
  -H "Content-Type: application/json" \
  -H "X-Auth-Token: $TOKEN" \
  -d '{
    "flavor_notes": ["chocolate", "caramel", "nutty"],
    "roast_level": "Medium"
  }'

# Step 3: Add beans to your library
BEAN_ID=$(curl -s -X POST http://localhost:9000/beans \
  -H "Content-Type: application/json" \
  -H "X-Auth-Token: $TOKEN" \
  -d '{
    "bean": {
      "name": "Colombia Huila",
      "origin": "Colombia",
      "process": "Washed",
      "variety": "Caturra",
      "roast_level": "Medium",
      "roasted_on": "2024-11-20",
      "altitude": "1600m",
      "flavor_notes": ["chocolate", "caramel", "orange"]
    }
  }' | jq -r '.bean_id')

echo "Bean saved with ID: $BEAN_ID"

# Step 4: List all your beans
curl -X GET http://localhost:9000/beans \
  -H "X-Auth-Token: $TOKEN" | jq '.'

# Step 5: Generate a recipe for your bean
curl -X POST http://localhost:9000/brew \
  -H "Content-Type: application/json" \
  -H "X-Auth-Token: $TOKEN" \
  -d '{
    "bean": {
      "name": "Colombia Huila",
      "process": "Washed",
      "variety": "Caturra",
      "roast_level": "Medium",
      "roasted_days": 3,
      "flavor_notes": ["chocolate", "caramel"]
    },
    "brewer": "V60",
    "note": "Looking for balanced sweetness"
  }' > recipe.json

# Step 6: Visualize the recipe
curl -X POST http://localhost:9000/visualize \
  -H "Content-Type: application/json" \
  -H "X-Auth-Token: $TOKEN" \
  -d "{
    \"recipe\": $(cat recipe.json),
    \"formats\": [\"html\", \"mermaid\", \"ascii\"]
  }" > visualization.html

echo "Recipe and visualization saved!"
```

### Example 2: Using Different Brewers

```bash
# V60 Recipe (larger dose, slower pour)
curl -X POST http://localhost:9000/brew \
  -H "Content-Type: application/json" \
  -d '{
    "bean": {
      "name": "Kenya AA",
      "process": "Washed",
      "roast_level": "Light-Medium",
      "flavor_notes": ["blackcurrant", "tomato", "winey"]
    },
    "brewer": "V60"
  }' | jq '.brewing'

# April Recipe (flatter bed, faster flow)
curl -X POST http://localhost:9000/brew \
  -H "Content-Type: application/json" \
  -d '{
    "bean": {
      "name": "Guatemala Antigua",
      "process": "Washed",
      "roast_level": "Medium",
      "flavor_notes": ["cocoa", "apple", "caramel"]
    },
    "brewer": "April"
  }' | jq '.brewing'

# Origami Recipe (versatile, hybrid)
curl -X POST http://localhost:9000/brew \
  -H "Content-Type: application/json" \
  -d '{
    "bean": {
      "name": "Costa Rica Tarrazu",
      "process": "Honey",
      "roast_level": "Medium-Light",
      "flavor_notes": ["honey", "citrus", "brown sugar"]
    },
    "brewer": "Origami"
  }' | jq '.brewing'
```

### Example 3: RAG-Enhanced Recipe Generation

The system automatically queries the RAG service for similar recipes when available:

```bash
# The agent will:
# 1. Query RAG for similar beans (same origin, process, roast level)
# 2. Use top 3 reference recipes to inform the new recipe
# 3. Generate a personalized recipe considering your preferences

curl -X POST http://localhost:9000/brew \
  -H "Content-Type: application/json" \
  -d '{
    "bean": {
      "name": "Ethiopia Yirgacheffe",
      "process": "Washed",
      "variety": "Heirloom",
      "roast_level": "Light",
      "roasted_days": 10,
      "flavor_notes": ["jasmine", "bergamot", "lemon"]
    },
    "brewer": "V60",
    "note": "I want to highlight the floral notes"
  }'

# The response includes metadata about RAG retrieval:
# {
#   "brewing": { ... },
#   "metadata": {
#     "rag_references_used": 3,
#     "model": "gpt-4o-mini"
#   }
# }
```

### Example 4: Using the Integrated Agent CLI

```bash
# Install dependencies (if not using Docker)
cd agent_core
pip install -r agent_requirements.txt

# Generate recipe + visualization in one command
python -m agent_core.integrated_agent \
  --bean '{
    "name": "Brazil Cerrado",
    "process": "Natural",
    "roast_level": "Medium-Dark",
    "flavor_notes": ["chocolate", "nut", "caramel"]
  }' \
  --brewer V60 \
  --note "Looking for a full-bodied cup" \
  --output-dir ./my_recipe \
  --formats html mermaid ascii \
  --show-ascii

# Output:
# ✓ Recipe generated
# ✓ HTML saved to: ./my_recipe/Brazil_Cerrado_recipe.html
# ✓ Mermaid saved to: ./my_recipe/Brazil_Cerrado_recipe.md
# ✓ ASCII saved to: ./my_recipe/Brazil_Cerrado_recipe.txt
#
# [ASCII visualization displayed in terminal]
```

## Environment Configuration

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key for recipe generation | `sk-proj-...` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `RAG_SERVICE_URL` | RAG service endpoint | `http://localhost:8000` |
| `REACT_APP_AGENT_API_URL` | Agent API URL (frontend) | `http://localhost:9000` |
| `FRONTEND_ORIGINS` | Allowed CORS origins (comma-separated) | `http://localhost:3000` |
| `RAG_PERSIST_DIR` | ChromaDB index directory | `./dailydrip_rag/indexes/chroma` |
| `RAG_COLLECTION` | ChromaDB collection name | `coffee_chunks` |

## Docker Commands Reference

### Basic Commands

```bash
# Start full stack (build + pipeline + services)
make run

# Start services without rebuilding
make start

# Run RAG pipeline only (ingest → chunk → index)
make pipeline

# Start RAG service only
make rag

# Stop all services
make down

# Clean processed data and indexes
make clean
```

### Advanced Docker Usage

```bash
# Build specific service
docker compose build agent
docker compose build rag

# View logs
docker compose logs -f agent
docker compose logs -f rag

# Run pipeline steps individually
docker compose up ingest
docker compose up chunk
docker compose up index

# Execute commands in running containers
docker compose exec agent bash
docker compose exec rag python -m src.service
```

## Frontend Companion App

The `frontend/` directory hosts a Create React App + Tailwind UI that connects directly to the FastAPI agent.

### Local Development

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm start

# Run tests
npm test

# Run tests with coverage
npm run test:coverage

# Build for production
npm build

# Lint code
npm run lint
```

### Frontend Features

- **Authentication**: Register, login, logout with token-based auth
- **User Profile**: Manage taste preferences (flavor notes, roast level)
- **Bean Library**: CRUD operations for your coffee bean collection
- **Recipe Generator**:
  - Generate recipes from saved beans or manual input
  - Select brewer (V60, April, Orea, Origami)
  - Add custom brewing notes
- **Visualization**: View recipe timelines in multiple formats

### Configuration

```bash
# Point to different backend
export REACT_APP_AGENT_API_URL="https://api.dailydrip.com"

# Disable ESLint plugin (for older Node versions)
export DISABLE_ESLINT_PLUGIN=true
```

## API Documentation

### Authentication Endpoints

#### Register User
```bash
POST /auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "secure_password",
  "name": "User Name"
}

Response: {
  "token": "auth_token_here",
  "user": {
    "user_id": "uuid",
    "email": "user@example.com",
    "name": "User Name",
    "preferences": {
      "flavor_notes": [],
      "roast_level": null
    }
  }
}
```

#### Login
```bash
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "secure_password"
}

Response: Same as register
```

### Profile Endpoints

#### Get Profile
```bash
GET /profile
X-Auth-Token: your_token_here

Response: {
  "user_id": "uuid",
  "email": "user@example.com",
  "name": "User Name",
  "preferences": {
    "flavor_notes": ["chocolate", "nutty"],
    "roast_level": "Medium"
  }
}
```

#### Update Preferences
```bash
PUT /profile/preferences
X-Auth-Token: your_token_here
Content-Type: application/json

{
  "flavor_notes": ["fruity", "floral"],
  "roast_level": "Light"
}
```

### Bean Library Endpoints

#### List Beans
```bash
GET /beans
X-Auth-Token: your_token_here

Response: {
  "beans": [
    {
      "bean_id": "uuid",
      "name": "Ethiopia Sidamo",
      "origin": "Ethiopia",
      "process": "Natural",
      "roasted_days": 8,
      ...
    }
  ]
}
```

#### Create Bean
```bash
POST /beans
X-Auth-Token: your_token_here
Content-Type: application/json

{
  "bean": {
    "name": "Colombia Huila",
    "origin": "Colombia",
    "process": "Washed",
    "variety": "Caturra",
    "roast_level": "Medium",
    "roasted_on": "2024-11-20",
    "altitude": "1600m",
    "flavor_notes": ["chocolate", "caramel"]
  }
}
```

#### Update Bean
```bash
PUT /beans/{bean_id}
X-Auth-Token: your_token_here
Content-Type: application/json

{
  "bean": {
    "name": "Updated Name",
    ...
  }
}
```

#### Delete Bean
```bash
DELETE /beans/{bean_id}
X-Auth-Token: your_token_here
```

### Recipe Endpoints

#### Generate Recipe
```bash
POST /brew
Content-Type: application/json

{
  "bean": {
    "name": "Ethiopia Yirgacheffe",
    "process": "Washed",
    "roast_level": "Light",
    "roasted_days": 10,
    "flavor_notes": ["floral", "citrus"]
  },
  "brewer": "V60",
  "note": "Highlight floral notes"
}

Response: {
  "brewing": {
    "brewer": "V60",
    "temperature": 93,
    "grinding_size": 20,
    "dose": 15,
    "target_water": 240,
    "pours": [
      {"start": 0, "end": 30, "water_added": 50},
      {"start": 30, "end": 80, "water_added": 95},
      {"start": 80, "end": 130, "water_added": 95}
    ]
  }
}
```

#### Visualize Recipe
```bash
POST /visualize
Content-Type: application/json

{
  "recipe": {
    "bean": { ... },
    "brewing": { ... }
  },
  "formats": ["html", "mermaid", "ascii"]
}

Response: {
  "html": "<html>...</html>",
  "mermaid": "gantt\n...",
  "ascii": "=== Recipe Timeline ===\n..."
}
```

### RAG Service Endpoints

#### Query Similar Recipes
```bash
POST http://localhost:8000/rag
Content-Type: application/json

{
  "bean": {
    "name": "Kenya AA",
    "process": "Washed",
    "roast_level": "Light-Medium"
  },
  "k": 3,
  "use_evaluation_reranking": true,
  "similarity_weight": 0.7
}

Response: {
  "query": "bean.name: Kenya AA | bean.process: Washed | ...",
  "results": [
    {
      "rank": 1,
      "id": "chunk_id",
      "distance": 0.234,
      "bean_text": "...",
      "brewing": { ... },
      "evaluation": { ... },
      "combined_score": 0.89
    }
  ]
}
```

#### Health Check
```bash
GET http://localhost:8000/health

Response: {
  "status": "healthy",
  "collection": "coffee_chunks",
  "count": 1234
}
```

## RAG Pipeline

The Retrieval-Augmented Generation pipeline processes coffee brewing data and enables similarity-based recipe recommendations.

### Pipeline Stages

1. **Ingest** (`dailydrip_rag/src/ingest.py`)
   - Reads raw CSV/JSON data
   - Normalizes to canonical JSONL format
   - Output: `data/processed/records.jsonl`

2. **Chunk** (`dailydrip_rag/src/chunk.py`)
   - Splits records into text chunks
   - Prepares data for embedding
   - Output: `data/processed/chunks.jsonl`

3. **Index** (`dailydrip_rag/src/index.py`)
   - Generates embeddings using `all-MiniLM-L6-v2`
   - Builds ChromaDB vector index
   - Output: `indexes/chroma/`

4. **Service** (`dailydrip_rag/src/service.py`)
   - FastAPI service for similarity search
   - Supports evaluation-based reranking
   - Endpoint: `POST /rag`

### Running the Pipeline

```bash
# Run complete pipeline
make pipeline

# Or run stages individually
docker compose up ingest
docker compose up chunk
docker compose up index

# Start RAG service
make rag
```

### RAG Query Options

The RAG service supports advanced reranking based on evaluation scores:

```python
{
  "bean": { ... },                    # Query bean
  "k": 3,                             # Number of results
  "use_evaluation_reranking": true,   # Enable score-based reranking
  "similarity_weight": 0.7,           # Weight for similarity (0-1)
  "retrieval_multiplier": 3           # Fetch k × multiplier before reranking
}
```

## Testing

### Backend Tests

```bash
# RAG pipeline tests
cd dailydrip_rag
pytest tests/ -v --cov=src --cov-report=term

# Agent core tests
cd agent_core
pytest tests/ -v --cov=. --cov-report=term

# Run specific test file
pytest tests/test_service.py -v

# Run with coverage report
pytest --cov=src --cov-report=html
```

### Frontend Tests

```bash
cd frontend

# Run all tests
npm test

# Run tests with coverage
npm run test:coverage

# Run tests in CI mode
npm run test:ci

# Run specific test file
npm test -- BeanCollection.test.js
```

### CI/CD Pipeline

The project uses GitHub Actions for continuous integration:

- **Python CI** ([.github/workflows/python-ci.yml](.github/workflows/python-ci.yml))
  - Linting with flake8
  - Format checking with black
  - Unit tests with pytest
  - Coverage reporting to Codecov

- **Frontend CI** ([.github/workflows/frontend-ci.yml](.github/workflows/frontend-ci.yml))
  - Linting with ESLint
  - Unit tests with Jest
  - Coverage reporting

- **Docker CI** ([.github/workflows/docker-ci.yml](.github/workflows/docker-ci.yml))
  - Build verification for all services
  - Multi-stage build testing

All workflows run on push to `main` and `milestone4` branches, and on pull requests.

## Troubleshooting

### Common Issues

**Issue: "Connection refused" when calling API**
```bash
# Check if services are running
docker compose ps

# Check logs
docker compose logs agent
docker compose logs rag

# Restart services
make down
make run
```

**Issue: "OpenAI API key not found"**
```bash
# Set the environment variable
export OPENAI_API_KEY="your-key-here"

# Verify it's set
echo $OPENAI_API_KEY

# Restart the agent service
docker compose restart agent
```

**Issue: "ChromaDB index not found"**
```bash
# Rebuild the RAG index
make pipeline

# Verify index exists
ls -la dailydrip_rag/indexes/chroma/

# Restart RAG service
make rag
```

**Issue: Frontend can't connect to backend**
```bash
# Check API URL configuration
echo $REACT_APP_AGENT_API_URL

# Update if needed
export REACT_APP_AGENT_API_URL="http://localhost:9000"

# Restart frontend
cd frontend
npm start
```

**Issue: "Module not found" errors in frontend**
```bash
# Clear node_modules and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install
```

## Development Workflow

### Adding New Features

1. **Create a feature branch**
   ```bash
   git checkout -b feature/my-new-feature
   ```

2. **Make changes and test locally**
   ```bash
   # Backend
   cd dailydrip_rag  # or agent_core
   pytest tests/ -v
   flake8 src/

   # Frontend
   cd frontend
   npm test
   npm run lint
   ```

3. **Commit with descriptive messages**
   ```bash
   git add .
   git commit -m "Add feature: description"
   ```

4. **Push and create PR**
   ```bash
   git push origin feature/my-new-feature
   # Create pull request on GitHub
   ```

### Code Style Guidelines

**Python (PEP 8)**
- Max line length: 127 characters
- Use snake_case for functions and variables
- Use PascalCase for classes
- Add docstrings to all functions and classes
- Type hints encouraged

**JavaScript (Airbnb Style)**
- Use camelCase for functions and variables
- Use PascalCase for components
- Prefer functional components with hooks
- Add JSDoc comments for complex functions

## Validation & Deliverables

- ✅ **Functional Demo**: `/brew` → recipe JSON, `/visualize` → HTML timeline
- ✅ **RAG Integration**: Agent gracefully falls back when RAG is offline
- ✅ **Frontend UI**: Complete React application with authentication
- ✅ **Documentation**: Comprehensive README, integration guide, and code comments
- ✅ **Testing**: 11 test files with CI/CD integration
- ✅ **Code Coverage**: Tracked via Codecov with badges

## Additional Resources

- **Application Design**: See [APPLICATION_DESIGN.md](APPLICATION_DESIGN.md) for comprehensive architecture documentation
- **Integration Guide**: See [INTEGRATION_USAGE.md](INTEGRATION_USAGE.md) for detailed agent usage
- **RAG Documentation**: See [dailydrip_rag/README.md](dailydrip_rag/README.md) for pipeline details
- **CI Setup**: See [CI-tests/CI_SETUP_SUMMARY.md](CI-tests/CI_SETUP_SUMMARY.md) for CI/CD configuration
- **Quick Start CI**: See [CI-tests/QUICK_START_CI.md](CI-tests/QUICK_START_CI.md) for CI quick start guide
- **Project Report**: See [reports/MS2 Report.pdf](reports/MS2%20Report.pdf) for milestone 2 deliverables

## Future Enhancements

1. **Expanded RAG Coverage**: Collect real user brewing logs and feedback
2. **Adaptive Learning**: Integrate feedback loop for recipe evaluation
3. **Mobile App**: Build native mobile interface for iOS/Android
4. **Advanced Visualizations**: Interactive charts with taste profiles
5. **Community Features**: Share recipes and brewing techniques
6. **Hardware Integration**: Connect to smart scales and temperature sensors

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- UC Davis Coffee Center for sample brewing data
- OpenAI for GPT-4o-mini API
- ChromaDB for vector database technology
- Harvard AC215 course staff and instructors

---

**Questions or Issues?** Please open an issue on GitHub or contact the development team.
