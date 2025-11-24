# Application Design Document – DailyDrip

## 1. Solution Architecture

### Overview
DailyDrip is an AI-driven coffee brewing assistant that integrates a **frontend UI**, a **FastAPI backend**, and a **Retrieval-Augmented Generation (RAG)** data pipeline. Together, these components deliver personalized brewing recipes and visualizations based on user preferences, bean characteristics, and past brewing data.

The system is composed of four primary layers:

| Layer | Description | Technologies |
|-------|--------------|---------------|
| **User Interface (UI)** | React/Tailwind web application where users register, log in, manage beans, and request brew recipes. | React, Tailwind CSS, Axios |
| **API / Application Layer** | FastAPI backend that exposes `/brew`, `/visualize`, and `/auth` endpoints. It handles user authentication, connects to the RAG service, and communicates with the OpenAI API for recipe generation. | FastAPI, Pydantic, httpx |
| **RAG Pipeline (Data Layer)** | Responsible for ingesting, chunking, and indexing bean/brew data into a Chroma vector database. Serves similarity queries to ground recipe recommendations. | Python, ChromaDB, sentence-transformers |
| **Visualization Agent** | Converts recipe data into visual brewing timelines (HTML, Mermaid, ASCII). Reused both by the API and CLI. | Python (Matplotlib, Mermaid templates, Jinja2) |

### Data Flow
1. **User Interaction:** The user interacts with the frontend UI to log in, manage beans, and request brewing recommendations.  
2. **Request Handling:** The frontend sends REST API calls to the FastAPI backend (`/brew` or `/visualize`).  
3. **RAG Integration:** The backend queries the RAG service to retrieve similar brews and beans, providing contextual grounding for recipe generation.  
4. **LLM Generation:** The backend uses the retrieved data and bean metadata to prompt the OpenAI API (or a local model).  
5. **Response Assembly:** The system returns a structured JSON recipe and optionally a visualization.  
6. **Display:** The UI renders the recipe and visualization in an interactive, user-friendly format.

```
[Frontend UI] ⇄ [FastAPI Backend]
      │                 │
      │     RAG Query   ↓
      │           [RAG Service → ChromaDB]
      ↓
[LLM API] → Recipe JSON → Visualization → Frontend Display
```

## 2. Technical Architecture

### Technologies and Frameworks

| Component | Technology | Purpose |
|------------|-------------|----------|
| **Frontend** | React, Tailwind CSS | Build responsive and modular UI |
| **Backend (API)** | FastAPI, Pydantic, httpx | Expose REST endpoints, validate data, connect to RAG and LLMs |
| **RAG Pipeline** | Python, ChromaDB, sentence-transformers | Store and retrieve relevant brew data for grounding |
| **Visualization** | Mermaid.js, HTML templates | Render brewing timelines |
| **Data Storage** | JSONL files, Vector index | Store user profiles, beans, and embeddings |
| **Containerization** | Docker, Docker Compose | Ensure reproducible deployment |
| **Testing / Style** | Pytest, ESLint, Flake8 | Maintain code quality and linting consistency |

### Design Patterns Used

- **Service Layer Pattern:** Each domain (Agent, RAG, Visualization) exposes clean interfaces decoupled from API logic.  
- **Repository Pattern:** RAG service isolates database access and vector operations.  
- **Factory Pattern:** Used to initialize agents and models dynamically.  
- **API Gateway Pattern:** FastAPI backend acts as a single entry point for all client requests.  
- **MVC-inspired Separation:** UI (View) → FastAPI (Controller) → Agent/RAG (Model).

## 3. User Interface Design

### Structure
- **Login & Registration:** User authentication and token handling.  
- **Bean Library:** Add, view, and manage personal coffee beans.  
- **Brew Recommendation:** Input bean and preference data → view generated recipe.  
- **Visualization View:** Display brewing instructions as timelines.

### UI Behavior
- Implements **state management** using React Context and hooks.  
- Uses **Axios** for API calls and supports environment-based API URLs (`REACT_APP_AGENT_API_URL`).  
- Provides **responsive design** for desktop and mobile.  
- Includes clear error messages, loading indicators, and session persistence.

## 4. Code Organization

### Repository Layout
```
├── apps/
│   ├── api/                # FastAPI app (entrypoints, routes)
│   └── ui/                 # React + Tailwind frontend
│
├── packages/
│   ├── agent/              # Core brew and visualization logic
│   ├── rag/                # RAG ingestion, chunking, and index building
│   └── common/             # Shared utilities and configuration
│
├── data/                   # Development data (gitignored)
├── scripts/                # CLI scripts for training, ingesting, or testing
├── tools/                  # Helper utilities and sample payloads
├── tests/                  # Unit and integration tests
├── docker/                 # Dockerfiles for each service
├── docs/                   # Design docs and milestone reports
└── Makefile, docker-compose.yml, README.md
```

### Module Responsibilities
- **`apps/api`** – request routing, validation, and orchestration.  
- **`packages/agent`** – core brewing and visualization logic.  
- **`packages/rag`** – data preprocessing and vector indexing.  
- **`packages/common`** – shared logging, error handling, and config.  
- **`scripts`** – command-line entry points for batch or testing tasks.  
- **`frontend` (or `apps/ui`)** – all presentation and interaction logic.

## 5. Quality and Standards

- **Python:** follows PEP 8 with type hints and Google-style docstrings.  
- **JavaScript/React:** follows Airbnb JavaScript Style Guide with ESLint.  
- **Testing:** each service includes unit tests and API contract tests.  
- **Documentation:** every module has top-level docstrings explaining its purpose and inputs/outputs.  
- **Reproducibility:** all dependencies are pinned and containerized with Docker for consistent local and cloud environments.

## 6. Summary

DailyDrip’s design emphasizes **clear modular boundaries** and **scalable architecture**:
- The **UI** handles interaction and presentation.  
- The **FastAPI backend** coordinates logic and external services.  
- The **RAG pipeline** provides contextual knowledge for personalization.  
- The **Visualization Agent** converts recipes into intuitive visual guides.

This layered approach ensures maintainability, easy testing, and straightforward future extensions (e.g., feedback learning or cloud deployment).
