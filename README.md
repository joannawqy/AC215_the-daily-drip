# DailyDrip - AI-Powered Coffee Brewing Assistant

[![codecov](https://codecov.io/gh/joannawqy/AC215_the-daily-drip/branch/milestone4/graph/badge.svg)](https://codecov.io/gh/joannawqy/AC215_the-daily-drip)

**Final Project - AC215 Fall 2024**

## Team
- **Team Name:** DailyDrip Collective
- **Members:** Even Li, Joanna Wang, Jessica Wang, Zicheng Ma

## Overview

DailyDrip is an intelligent coffee brewing assistant that combines AI-powered recipe generation, retrieval-augmented generation (RAG), and interactive visualizations to help coffee enthusiasts brew the perfect cup. The system learns from historical brewing data and user preferences to provide personalized brewing recommendations tailored to specific coffee beans and brewing equipment.

### Key Features
- 🤖 **AI Recipe Generation** - GPT-4o-mini generates personalized brewing parameters
- 🔍 **RAG-Enhanced Recommendations** - Retrieves similar recipes from ChromaDB vector database
- 📊 **Multi-Format Visualizations** - HTML timelines, Mermaid diagrams, and ASCII art
- 🌐 **Full-Stack Web Application** - React frontend with FastAPI backend
- 🔐 **User Authentication** - Secure token-based auth with personal bean libraries
- 🐳 **Containerized Architecture** - Docker monolith with nginx, RAG service, and API

---

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Setup Instructions](#setup-instructions)
3. [Deployment Instructions](#deployment-instructions)
4. [Usage Guide](#usage-guide)
5. [API Reference](#api-reference)
6. [Known Issues and Limitations](#known-issues-and-limitations)
7. [Project Architecture](#project-architecture)
8. [Testing](#testing)
9. [Additional Resources](#additional-resources)

---

## Prerequisites

### Required Software
- **Docker** 20.10+ and **Docker Compose** v2+
- **OpenAI API Key** (required for recipe generation)

### Optional (for local development)
- **Node.js** 16+ and **npm** 8+
- **Python** 3.11+
- **Git**

### System Requirements
- **RAM:** 8GB minimum (for ChromaDB and model embeddings)
- **Storage:** 2GB free space for Docker images and indexes
- **OS:** macOS, Linux, or Windows with WSL2

### API Keys and Credentials
You'll need to obtain an OpenAI API key:
1. Sign up at https://platform.openai.com/
2. Create an API key in your account settings
3. Set the environment variable: `export OPENAI_API_KEY="sk-..."`

---

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/joannawqy/AC215_the-daily-drip.git
cd AC215_the-daily-drip
```

### 2. Set Environment Variables

```bash
# Required: OpenAI API key for recipe generation
export OPENAI_API_KEY="your-api-key-here"

# Optional: Custom configuration
export RAG_SERVICE_URL="http://localhost:8000"
export REACT_APP_AGENT_API_URL="http://localhost:9000"
export FRONTEND_ORIGINS="http://localhost:3000"
```

### 3. Start the Application

The application runs as a monolithic Docker container with all services:

```bash
# Build and start the full application
make start
```

This single command will:
1. Build the Docker image (frontend + backend + RAG service)
2. Run the RAG pipeline (ingest → chunk → index)
3. Start nginx (port 80), RAG service (port 8000), and Agent API (port 9000)
4. All services managed by supervisord

### 4. Access the Application

Once the container is running:

- **Web Application:** http://localhost (port 80)
- **API Endpoints:** http://localhost/api (proxied through nginx)
- **RAG Service (Debug):** http://localhost:8000
- **Agent API (Debug):** http://localhost:9000

### 5. Verify Installation

```bash
# Check if all services are running
docker compose ps

# View logs
docker compose logs -f app

# Test API health
curl http://localhost:8000/health
```

---

## Deployment Instructions

### Local Development Deployment

The easiest way to run the application locally:

```bash
# Start everything in one container
make start

# Stop the application
make down

# Clean data and rebuild
make clean
make start
```

### Google Cloud Platform (GCP) / Kubernetes Deployment

#### Step 1: Build and Push Docker Image

```bash
# Build the monolithic image
docker build -f deployment/Dockerfile.monolith -t the-daily-drip-app:latest .

# Tag for Google Container Registry
docker tag the-daily-drip-app:latest gcr.io/ac215-480602/the-daily-drip-app:latest

# Push to GCR (requires gcloud authentication)
docker push gcr.io/ac215-480602/the-daily-drip-app:latest
```

#### Step 2: Create Kubernetes Secret

```bash
# Create secret for OpenAI API key
kubectl create secret generic openai-api-key \
  --from-literal=key="your-openai-api-key-here"
```

#### Step 3: Deploy to Kubernetes

```bash
# Apply deployment configuration
kubectl apply -f k8s/deployment.yaml

# Apply service configuration (LoadBalancer)
kubectl apply -f k8s/service.yaml

# Check deployment status
kubectl get pods
kubectl get services
```

#### Step 4: Access Deployed Application

```bash
# Get external IP address
kubectl get service daily-drip-service

# Wait for EXTERNAL-IP to be assigned (may take a few minutes)
# Access the application at: http://<EXTERNAL-IP>
```

### Infrastructure as Code (Pulumi)

For automated infrastructure provisioning:

```bash
cd k8s/pulumi

# Install dependencies
pip install -r requirements.txt

# Configure Pulumi
pulumi config set gcp:project ac215-480602
pulumi config set image_tag latest
pulumi config set-secret openai_key "your-key"

# Deploy infrastructure
pulumi up

# Get outputs
pulumi stack output service_ip
```

### Environment Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `OPENAI_API_KEY` | OpenAI API key | None | Yes |
| `RAG_SERVICE_URL` | RAG service endpoint | `http://localhost:8000` | No |
| `RAG_PERSIST_DIR` | ChromaDB storage path | `/app/indexes/chroma` | No |
| `RAG_COLLECTION` | ChromaDB collection name | `coffee_chunks` | No |
| `PORT` | Application port (K8s) | `8000` | No |

---

## Usage Guide

### Web Interface Usage

#### 1. Register and Login

1. Navigate to http://localhost
2. Click "Create Account"
3. Enter email, password, and name
4. Login with your credentials

#### 2. Set Taste Preferences

1. Go to your Profile page
2. Select preferred flavor notes (e.g., chocolate, fruity, floral)
3. Choose preferred roast level (Light, Medium, Dark)
4. Save preferences

#### 3. Manage Your Bean Library

1. Navigate to "My Beans"
2. Click "Add New Bean"
3. Fill in bean details:
   - Name (e.g., "Ethiopia Sidamo Natural")
   - Origin
   - Process method (Natural, Washed, Honey)
   - Roast level
   - Roast date
   - Flavor notes
4. Save the bean to your library

#### 4. Generate Brewing Recipes

1. Go to "Recipe Generator"
2. Select a bean from your library (or enter manually)
3. Choose your brewer (V60, April, Orea, Origami)
4. Add optional brewing notes
5. Click "Generate Recipe"
6. View the recipe with:
   - Temperature and grind size
   - Pour schedule with timing
   - Interactive visualization timeline

### API Usage Examples

#### Example 1: Complete User Workflow

```bash
# Step 1: Register a new user
TOKEN=$(curl -s -X POST http://localhost/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "coffee@example.com",
    "password": "secure123",
    "name": "Coffee Enthusiast"
  }' | jq -r '.token')

# Step 2: Update taste preferences
curl -X PUT http://localhost/api/profile/preferences \
  -H "Content-Type: application/json" \
  -H "X-Auth-Token: $TOKEN" \
  -d '{
    "flavor_notes": ["chocolate", "nutty", "caramel"],
    "roast_level": "Medium"
  }'

# Step 3: Add a coffee bean
BEAN_ID=$(curl -s -X POST http://localhost/api/beans \
  -H "Content-Type: application/json" \
  -H "X-Auth-Token: $TOKEN" \
  -d '{
    "bean": {
      "name": "Colombia Huila",
      "origin": "Colombia",
      "process": "Washed",
      "variety": "Caturra",
      "roast_level": "Medium",
      "roasted_on": "2024-12-01",
      "altitude": "1600m",
      "flavor_notes": ["chocolate", "caramel", "orange"]
    }
  }' | jq -r '.bean_id')

echo "Bean saved with ID: $BEAN_ID"

# Step 4: Generate a recipe
curl -X POST http://localhost/api/brew \
  -H "Content-Type: application/json" \
  -H "X-Auth-Token: $TOKEN" \
  -d '{
    "bean": {
      "name": "Colombia Huila",
      "process": "Washed",
      "roast_level": "Medium",
      "roasted_days": 11,
      "flavor_notes": ["chocolate", "caramel"]
    },
    "brewer": "V60",
    "note": "Looking for balanced sweetness"
  }' | jq '.'

# Step 5: Get visualization
curl -X POST http://localhost/api/visualize \
  -H "Content-Type: application/json" \
  -H "X-Auth-Token: $TOKEN" \
  -d '{
    "recipe": {...},
    "formats": ["html", "ascii"]
  }' > visualization.html
```

#### Example 2: Different Brewers

```bash
# V60 - Larger dose, multiple pours
curl -X POST http://localhost/api/brew \
  -H "Content-Type: application/json" \
  -d '{
    "bean": {
      "name": "Kenya AA",
      "process": "Washed",
      "roast_level": "Light-Medium",
      "flavor_notes": ["blackcurrant", "tomato"]
    },
    "brewer": "V60"
  }' | jq '.brewing'

# April - Flatter bed, faster flow
curl -X POST http://localhost/api/brew \
  -H "Content-Type: application/json" \
  -d '{
    "bean": {
      "name": "Guatemala Antigua",
      "process": "Washed",
      "roast_level": "Medium"
    },
    "brewer": "April"
  }' | jq '.brewing'
```

#### Example 3: RAG-Enhanced Generation

The system automatically queries similar recipes from the vector database:

```bash
curl -X POST http://localhost/api/brew \
  -H "Content-Type: application/json" \
  -d '{
    "bean": {
      "name": "Ethiopia Yirgacheffe",
      "process": "Washed",
      "roast_level": "Light",
      "roasted_days": 10,
      "flavor_notes": ["jasmine", "bergamot"]
    },
    "brewer": "V60",
    "note": "Highlight floral notes"
  }'

# Response includes RAG metadata:
# {
#   "brewing": {...},
#   "metadata": {
#     "rag_references_used": 3,
#     "model": "gpt-4o-mini"
#   }
# }
```

### Command-Line Usage (Advanced)

For developers and power users:

```bash
# Generate recipe + visualization using integrated agent
cd agent_core
python -m agent_core.integrated_agent \
  --bean '{
    "name": "Brazil Cerrado",
    "process": "Natural",
    "roast_level": "Medium-Dark",
    "flavor_notes": ["chocolate", "nut"]
  }' \
  --brewer V60 \
  --output-dir ./my_recipe \
  --formats html mermaid ascii \
  --show-ascii

# Query RAG service directly
curl -X POST http://localhost:8000/rag \
  -H "Content-Type: application/json" \
  -d '{
    "bean": {
      "name": "Ethiopia",
      "process": "Natural",
      "roast_level": "Light"
    },
    "k": 3
  }' | jq '.'
```

---

## API Reference

### Authentication Endpoints

#### POST /api/auth/register
Register a new user account.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "secure_password",
  "name": "User Name"
}
```

**Response:**
```json
{
  "token": "auth_token_string",
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

#### POST /api/auth/login
Login with existing credentials.

**Request:** Same as register (email + password only)

### Profile Endpoints

#### GET /api/profile
Get current user profile.

**Headers:** `X-Auth-Token: <token>`

**Response:**
```json
{
  "user_id": "uuid",
  "email": "user@example.com",
  "name": "User Name",
  "preferences": {
    "flavor_notes": ["chocolate", "nutty"],
    "roast_level": "Medium"
  }
}
```

#### PUT /api/profile/preferences
Update taste preferences.

**Headers:** `X-Auth-Token: <token>`

**Request:**
```json
{
  "flavor_notes": ["fruity", "floral"],
  "roast_level": "Light"
}
```

### Bean Library Endpoints

#### GET /api/beans
List all beans in user's library.

**Headers:** `X-Auth-Token: <token>`

#### POST /api/beans
Add a new bean to library.

**Headers:** `X-Auth-Token: <token>`

**Request:**
```json
{
  "bean": {
    "name": "Colombia Huila",
    "origin": "Colombia",
    "process": "Washed",
    "variety": "Caturra",
    "roast_level": "Medium",
    "roasted_on": "2024-12-01",
    "altitude": "1600m",
    "flavor_notes": ["chocolate", "caramel"]
  }
}
```

#### PUT /api/beans/{bean_id}
Update an existing bean.

#### DELETE /api/beans/{bean_id}
Delete a bean from library.

### Recipe Endpoints

#### POST /api/brew
Generate a brewing recipe.

**Request:**
```json
{
  "bean": {
    "name": "Ethiopia Yirgacheffe",
    "process": "Washed",
    "roast_level": "Light",
    "roasted_days": 10,
    "flavor_notes": ["floral", "citrus"]
  },
  "brewer": "V60",
  "note": "Optional brewing instruction"
}
```

**Response:**
```json
{
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
  },
  "metadata": {
    "rag_references_used": 3,
    "model": "gpt-4o-mini"
  }
}
```

#### POST /api/visualize
Generate recipe visualizations.

**Request:**
```json
{
  "recipe": {
    "bean": {...},
    "brewing": {...}
  },
  "formats": ["html", "mermaid", "ascii"]
}
```

**Response:**
```json
{
  "html": "<html>...</html>",
  "mermaid": "gantt\n...",
  "ascii": "=== Timeline ===\n..."
}
```

### RAG Service Endpoints

#### POST /rag (Port 8000)
Query similar brewing recipes from vector database.

**Request:**
```json
{
  "bean": {
    "name": "Kenya AA",
    "process": "Washed",
    "roast_level": "Light"
  },
  "k": 3,
  "use_evaluation_reranking": true,
  "similarity_weight": 0.7
}
```

#### GET /health
Check RAG service health.

---

## Known Issues and Limitations

### Current Limitations

#### 1. Data and Model Constraints
- **Limited Training Data:** RAG index contains sample data only (~100-200 records)
- **Model Scope:** GPT-4o-mini may occasionally generate inconsistent pour timings
- **Embedding Model:** Uses `all-MiniLM-L6-v2` which has ~384 dimensions (trade-off between speed and accuracy)
- **Brewer Support:** Currently supports V60, April, Orea, and Origami only

#### 2. System Performance
- **Cold Start:** First RAG query may take 5-10 seconds while loading embeddings
- **Memory Usage:** ChromaDB requires ~4-6GB RAM for full index
- **Concurrent Users:** Single-instance deployment may slow with >10 concurrent users
- **Token Limits:** Very long bean descriptions (>500 words) may be truncated

#### 3. Deployment and Infrastructure
- **State Management:** User data stored in JSONL files (not production-grade)
- **No Database:** User accounts and beans are file-based (no PostgreSQL/MongoDB)
- **Single Container:** Monolithic architecture limits horizontal scaling
- **No Load Balancing:** Kubernetes deployment runs single replica
- **Secret Management:** API keys via environment variables (consider HashiCorp Vault for production)

#### 4. Frontend Limitations
- **No Offline Mode:** Requires active internet connection
- **Mobile Experience:** Optimized for desktop, mobile UI could be improved
- **Browser Support:** Tested on Chrome/Firefox/Safari; may have issues with older browsers
- **No Real-Time Updates:** Requires manual refresh to see new data

#### 5. Authentication and Security
- **Simple Token Auth:** Uses basic token authentication (not OAuth2/JWT with refresh tokens)
- **No Password Reset:** Password recovery not implemented
- **No Rate Limiting:** API endpoints not rate-limited (vulnerable to abuse)
- **CORS Configuration:** Open CORS for development (should be restricted in production)

### Known Issues

#### Issue 1: RAG Service Connection Timeouts
**Problem:** Occasionally, the agent API cannot reach the RAG service on first startup.

**Workaround:**
```bash
# Restart the application
make down
make start

# Or restart just the RAG service
docker compose restart app
```

#### Issue 2: ChromaDB Lock Errors
**Problem:** If the container crashes, ChromaDB may leave lock files causing startup failures.

**Workaround:**
```bash
# Clean the index and restart
make clean
make start
```

#### Issue 3: Frontend Build Errors (Node Version)
**Problem:** `npm install` fails with older Node versions (<16).

**Workaround:**
```bash
# Use Node 18 (LTS)
nvm install 18
nvm use 18
cd frontend
npm install
```

#### Issue 4: OpenAI API Rate Limits
**Problem:** Free-tier OpenAI accounts may hit rate limits with frequent requests.

**Workaround:**
- Wait 60 seconds between requests
- Upgrade to paid OpenAI account
- Use `--no-rag` flag to reduce token usage

#### Issue 5: Large Bean Libraries (>100 beans)
**Problem:** Frontend may slow down when displaying >100 beans.

**Workaround:**
- Implement pagination (currently showing all beans)
- Use search/filter functionality

### Future Improvements

To address these limitations, future versions could include:

1. **Data Enhancements**
   - Collect real user brewing feedback
   - Expand training data to 1000+ recipes
   - Support more brewers (AeroPress, French Press, Chemex)

2. **Architecture Improvements**
   - Microservices architecture with separate containers
   - PostgreSQL for user data
   - Redis for session management and caching
   - Message queue (RabbitMQ/Kafka) for async processing

3. **Feature Additions**
   - Recipe versioning and history
   - Community sharing and ratings
   - Multi-language support
   - Hardware integration (smart scales, timers)
   - Brew log tracking and analytics

4. **Security Enhancements**
   - OAuth2 authentication
   - Role-based access control (RBAC)
   - API rate limiting and throttling
   - HTTPS/TLS encryption

5. **Performance Optimization**
   - Response caching
   - Horizontal pod autoscaling (HPA)
   - CDN for frontend assets
   - Database indexing and query optimization

---

## Project Architecture

### System Architecture

```
┌─────────────────────────────────────────────────────┐
│              DailyDrip System (Port 80)              │
│                   Nginx Reverse Proxy                │
└─────────────────┬───────────────────────────────────┘
                  │
    ┌─────────────┴─────────────┐
    │                           │
    ▼                           ▼
┌────────────┐            ┌─────────────┐
│  Frontend  │            │  API Proxy  │
│   (React)  │            │ /api/* → :9000│
│  Static    │            └──────┬───────┘
│  Files     │                   │
└────────────┘                   │
                                 ▼
                        ┌──────────────────┐
                        │   Agent API      │
                        │   (FastAPI)      │
                        │   Port 9000      │
                        └────────┬─────────┘
                                 │
                    ┌────────────┴────────────┐
                    │                         │
                    ▼                         ▼
           ┌─────────────────┐      ┌─────────────────┐
           │  OpenAI API     │      │  RAG Service    │
           │  (gpt-4o-mini)  │      │  Port 8000      │
           └─────────────────┘      └────────┬────────┘
                                              │
                                              ▼
                                     ┌─────────────────┐
                                     │   ChromaDB      │
                                     │ Vector Database │
                                     └─────────────────┘
```

### Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | React 18, Tailwind CSS | User interface and interactions |
| **Reverse Proxy** | Nginx | Serve static files, proxy API requests |
| **API** | FastAPI, Python 3.11 | REST API endpoints |
| **AI/ML** | OpenAI GPT-4o-mini | Recipe generation |
| **RAG** | ChromaDB, Sentence-Transformers | Similarity search and retrieval |
| **Process Manager** | Supervisord | Manage multiple services in one container |
| **Container** | Docker, Docker Compose | Containerization and orchestration |
| **Orchestration** | Kubernetes (GKE) | Production deployment |
| **IaC** | Pulumi (Python) | Infrastructure as Code |

### Repository Structure

```
AC215_the-daily-drip/
├── README.md                    # This file
├── LICENSE                      # MIT License
├── Makefile                     # Build and deployment commands
├── .gitignore                   # Git ignore rules
│
├── docs/                        # Documentation
│   ├── INTEGRATION_USAGE.md     # Agent integration guide
│   ├── application_design.md    # Architecture documentation
│   ├── COVERAGE_GAPS.md         # Test coverage analysis
│   ├── DATA_VERSIONING.md       # Data versioning docs
│   ├── RAG_EVALUATION(MODEL_FINETUNING).md
│   └── BLOG_POST.md             # Project blog post
│
├── deployment/                  # Deployment Configuration
│   ├── docker-compose.yml       # Container orchestration
│   ├── Dockerfile.monolith      # Multi-stage Docker build
│   ├── Dockerfile.agent         # Agent-only Dockerfile
│   ├── nginx.monolith.conf      # Nginx configuration
│   └── supervisord.conf         # Process manager config
│
├── agent_core/                  # Backend API & Agent Logic
│   ├── agent.py                 # FastAPI application
│   ├── integrated_agent.py      # CLI agent
│   ├── visualization_agent_v2.py
│   ├── agent_requirements.txt
│   └── tests/                   # Unit tests
│
├── dailydrip_rag/               # RAG Pipeline
│   ├── src/
│   │   ├── ingest.py            # Data ingestion
│   │   ├── chunk.py             # Text chunking
│   │   ├── index.py             # Vector indexing
│   │   ├── query.py             # Similarity search
│   │   └── service.py           # FastAPI RAG service
│   ├── data/                    # Raw and processed data
│   ├── indexes/                 # ChromaDB vector store
│   ├── tests/                   # RAG tests
│   └── Makefile                 # RAG-specific commands
│
├── frontend/                    # React Application
│   ├── src/
│   │   ├── components/          # React components
│   │   ├── context/             # Auth context
│   │   ├── services/            # API client
│   │   └── App.js
│   ├── public/
│   ├── package.json
│   └── Dockerfile
│
├── k8s/                         # Kubernetes Deployment
│   ├── deployment.yaml
│   ├── service.yaml
│   └── pulumi/                  # Infrastructure as Code
│
├── CI-tests/                    # CI/CD Configuration
│   ├── setup-tests.sh
│   └── run-all-tests.sh
│
├── scripts/                     # Utility scripts
├── tools/                       # Development tools
├── data/                        # Application data (gitignored)
└── reports/                     # Project reports
```

---

## Testing

### Running Tests

#### Backend Tests (Python)

```bash
# RAG pipeline tests
cd dailydrip_rag
pytest tests/ -v --cov=src --cov-report=term-missing

# Agent core tests
cd agent_core
pytest tests/ -v --cov=. --cov-report=term-missing

# Run specific test file
pytest tests/test_service.py -v

# Generate HTML coverage report
pytest --cov=src --cov-report=html
open htmlcov/index.html
```

#### Frontend Tests (JavaScript)

```bash
cd frontend

# Run all tests
npm test

# Run with coverage
npm run test:coverage

# Run in CI mode (non-interactive)
npm run test:ci
```

### Test Coverage

Current test coverage:
- **Agent Core:** 77% (see COVERAGE_GAPS.md)
- **RAG Service:** 67%
- **Frontend:** ~80%

Coverage reports are automatically uploaded to [Codecov](https://codecov.io/gh/joannawqy/AC215_the-daily-drip) on each commit.

### Continuous Integration

The project uses GitHub Actions for automated testing:

- **Python CI:** Linting (flake8), formatting (black), unit tests (pytest)
- **Frontend CI:** Linting (ESLint), unit tests (Jest)
- **Docker CI:** Build verification for all services

All workflows run on push and pull requests.

---

## Additional Resources

### Documentation

- **[docs/INTEGRATION_USAGE.md](docs/INTEGRATION_USAGE.md)** - Detailed agent integration guide and CLI usage
- **[docs/application_design.md](docs/application_design.md)** - Comprehensive architecture documentation
- **[dailydrip_rag/README.md](dailydrip_rag/README.md)** - RAG pipeline detailed documentation
- **[docs/COVERAGE_GAPS.md](docs/COVERAGE_GAPS.md)** - Test coverage analysis and improvement areas
- **[CI-tests/CI_SETUP_SUMMARY.md](CI-tests/CI_SETUP_SUMMARY.md)** - CI/CD pipeline configuration

### Sample Files

- **[tools/bean_request.json](tools/bean_request.json)** - Sample brew API request
- **[tools/visualize_request.json](tools/visualize_request.json)** - Sample visualization request

### External Links

- **GitHub Repository:** https://github.com/joannawqy/AC215_the-daily-drip
- **Codecov Dashboard:** https://codecov.io/gh/joannawqy/AC215_the-daily-drip
- **OpenAI API Docs:** https://platform.openai.com/docs
- **ChromaDB Docs:** https://docs.trychroma.com/

---

## Troubleshooting

### Common Issues and Solutions

**Problem: "Connection refused" when accessing http://localhost**

```bash
# Check if container is running
docker compose ps

# View logs
docker compose logs -f app

# Restart
make down && make start
```

**Problem: "OPENAI_API_KEY not set" error**

```bash
# Set the environment variable
export OPENAI_API_KEY="sk-your-key-here"

# Verify
echo $OPENAI_API_KEY

# Restart container to pick up new env var
make down && make start
```

**Problem: ChromaDB "Collection not found" error**

```bash
# Rebuild RAG index
make clean
make start

# Wait for initialization (check logs)
docker compose logs -f app | grep "RAG"
```

**Problem: Frontend shows "Network Error"**

This usually means nginx is not proxying correctly to the backend.

```bash
# Check nginx config
docker compose exec app cat /etc/nginx/conf.d/default.conf

# Check if agent API is running
docker compose exec app curl http://localhost:9000/health

# Restart nginx
docker compose exec app supervisorctl restart nginx
```

**Problem: High memory usage (>8GB)**

```bash
# Check container memory
docker stats

# Reduce ChromaDB cache (edit docker-compose.yml)
# Add: CHROMA_CACHE_SIZE=100

# Restart
make down && make start
```

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- **UC Davis Coffee Center** for sample brewing data and research
- **OpenAI** for GPT-4o-mini API access
- **ChromaDB** for open-source vector database
- **Harvard AC215 (Fall 2024)** course staff and instructors
- Coffee enthusiast community for inspiration and feedback

---

## Contact and Support

**Questions or Issues?**
- Open an issue on [GitHub Issues](https://github.com/joannawqy/AC215_the-daily-drip/issues)
- Contact the development team via course channels

**Contributing:**
While this is a course project, we welcome feedback and suggestions for future improvements.

---

**Happy Brewing! ☕**
