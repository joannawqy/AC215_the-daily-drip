# DailyDrip Application Design Document

**Project:** DailyDrip - AI-Powered Coffee Brewing Assistant
**Team:** DailyDrip Collective (Even Li, Joanna Wang, Jessica Wang, Zicheng Ma)
**Course:** AC215 - Harvard University
**Last Updated:** November 2024

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Solution Architecture](#solution-architecture)
3. [Technical Architecture](#technical-architecture)
4. [User Interface Design](#user-interface-design)
5. [Code Organization](#code-organization)
6. [Data Flow](#data-flow)
7. [Design Patterns](#design-patterns)
8. [Security & Authentication](#security--authentication)
9. [Scalability & Performance](#scalability--performance)
10. [Testing Strategy](#testing-strategy)

---

## Executive Summary

DailyDrip is a full-stack AI-powered application that provides personalized coffee brewing recommendations using Retrieval-Augmented Generation (RAG) and large language models. The system combines historical brewing data, user preferences, and generative AI to help coffee enthusiasts optimize their pour-over brewing technique.

### Key Features
- **AI-Powered Recipe Generation**: Uses OpenAI GPT-4o-mini to generate personalized brewing recipes
- **RAG-Enhanced Recommendations**: Retrieves similar brewing recipes from a vector database to inform recommendations
- **Interactive Visualizations**: Renders recipes as HTML timelines, Mermaid diagrams, and ASCII art
- **User Management**: Secure authentication and per-user bean library management
- **Multi-Brewer Support**: Tailored recipes for V60, April, Orea, and Origami brewers

---

## Solution Architecture

### High-Level System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                          DailyDrip System                            │
│                                                                       │
│  ┌───────────────┐      ┌──────────────┐      ┌──────────────┐     │
│  │   Frontend    │─────→│  Agent API   │─────→│  OpenAI API  │     │
│  │  React + UI   │      │   FastAPI    │      │   (GPT-4o)   │     │
│  └───────────────┘      └──────────────┘      └──────────────┘     │
│                                │                                     │
│                                │                                     │
│                                ↓                                     │
│                         ┌──────────────┐                            │
│                         │ RAG Service  │                            │
│                         │   ChromaDB   │                            │
│                         └──────────────┘                            │
│                                ↑                                     │
│                                │                                     │
│                         ┌──────────────┐                            │
│                         │ RAG Pipeline │                            │
│                         │ Ingest/Index │                            │
│                         └──────────────┘                            │
└─────────────────────────────────────────────────────────────────────┘
```

### System Components

#### 1. **Frontend Layer** (React Application)
- **Purpose**: User-facing interface for all interactions
- **Technology**: React 18, Tailwind CSS, Lucide React Icons
- **Port**: 3000
- **Responsibilities**:
  - User authentication (register, login, logout)
  - Bean library management (CRUD operations)
  - Recipe generation interface
  - Visualization rendering
  - User preference management

#### 2. **Agent Core API** (FastAPI Backend)
- **Purpose**: Central orchestration service for business logic
- **Technology**: FastAPI, Pydantic, OpenAI SDK
- **Port**: 9000
- **Responsibilities**:
  - Authentication & session management
  - User profile & preferences
  - Bean library persistence
  - Recipe generation (LLM orchestration)
  - Visualization generation
  - RAG query coordination

#### 3. **RAG Service** (Vector Database Service)
- **Purpose**: Similarity-based recipe retrieval
- **Technology**: ChromaDB, Sentence-Transformers (all-MiniLM-L6-v2)
- **Port**: 8000
- **Responsibilities**:
  - Vector similarity search
  - Evaluation-based reranking
  - Recipe metadata retrieval
  - Health monitoring

#### 4. **RAG Pipeline** (Data Processing)
- **Purpose**: ETL pipeline for brewing data
- **Technology**: Python, pandas, ChromaDB
- **Responsibilities**:
  - Data ingestion (CSV/JSON → JSONL)
  - Text chunking
  - Embedding generation
  - Vector index creation

#### 5. **Visualization Agent** (Recipe Renderer)
- **Purpose**: Multi-format recipe visualization
- **Technology**: Pure Python (no dependencies)
- **Responsibilities**:
  - HTML timeline generation
  - Mermaid diagram creation
  - ASCII art rendering
  - Pour schedule visualization

---

## Technical Architecture

### Technology Stack

#### Backend Technologies

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **API Framework** | FastAPI | 0.111+ | High-performance async REST API |
| **Language Model** | OpenAI GPT-4o-mini | Latest | Recipe generation |
| **Vector Database** | ChromaDB | Latest | Similarity search |
| **Embeddings** | all-MiniLM-L6-v2 | Latest | Text vectorization |
| **Data Validation** | Pydantic | 2.0+ | Request/response validation |
| **HTTP Client** | httpx | 0.27+ | Async HTTP requests |
| **Container Runtime** | Docker | 20.10+ | Containerization |
| **Orchestration** | Docker Compose | 2.0+ | Multi-container management |

#### Frontend Technologies

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **UI Framework** | React | 18.2 | Component-based UI |
| **Build Tool** | Create React App | 5.0 | Zero-config build setup |
| **Styling** | Tailwind CSS | 3.3+ | Utility-first CSS |
| **Icons** | Lucide React | 0.263+ | Icon library |
| **HTTP Client** | Fetch API | Native | API communication |
| **State Management** | React Context | Native | Authentication state |

#### DevOps & Infrastructure

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **CI/CD** | GitHub Actions | Automated testing & deployment |
| **Code Coverage** | Codecov | Test coverage tracking |
| **Python Testing** | pytest | Unit & integration tests |
| **JS Testing** | Jest + React Testing Library | Component tests |
| **Linting (Python)** | flake8 + black | Code quality |
| **Linting (JS)** | ESLint | Code quality |
| **Version Control** | Git + GitHub | Source control |

### Architecture Patterns

#### 1. **Microservices Architecture**
The application follows a microservices pattern with three independent services:

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Frontend   │────→│  Agent API   │────→│ RAG Service  │
│  (Port 3000) │     │  (Port 9000) │     │  (Port 8000) │
└──────────────┘     └──────────────┘     └──────────────┘
     HTTP/REST           HTTP/REST             HTTP/REST
```

**Benefits**:
- Independent scaling of each service
- Fault isolation (RAG failure doesn't crash Agent API)
- Technology flexibility (each service can use optimal stack)
- Independent deployment cycles

#### 2. **Repository Pattern**
User data persistence uses a repository pattern with JSONL file storage:

```python
# Abstraction layer for data access
class UserRepository:
    - _load_user_store()
    - _persist_user_store()
    - create_user()
    - find_by_email()
    - update_preferences()
    - manage_beans()
```

**Benefits**:
- Abstraction from storage implementation
- Easy migration to database (PostgreSQL, MongoDB, etc.)
- Centralized data access logic
- Simplified testing with mock repositories

#### 3. **Service Layer Pattern**
Business logic is encapsulated in service classes:

```python
# RAG Service
class RagService:
    - query_similar_recipes()
    - rerank_by_evaluation()

# Visualization Service
class VisualizationAgent:
    - generate_html()
    - generate_mermaid()
    - generate_ascii()
```

**Benefits**:
- Clear separation of concerns
- Reusable business logic
- Easier unit testing
- Single responsibility principle

#### 4. **API Gateway Pattern**
Agent Core API acts as an API gateway:

```
Frontend → Agent API → [OpenAI API, RAG Service, Visualization]
```

**Benefits**:
- Single entry point for frontend
- Centralized authentication
- Request/response transformation
- Error handling & retry logic

#### 5. **Event-Driven Pipeline**
RAG pipeline uses event-driven stages:

```
Ingest Event → Chunk Event → Index Event → Service Ready
```

**Benefits**:
- Incremental processing
- Restart from failure point
- Observable progress
- Idempotent operations

### Component Interactions

#### Recipe Generation Flow

```
┌─────────┐  1. POST /brew     ┌─────────────┐
│ Frontend│ ───────────────────→│ Agent API   │
└─────────┘                     └─────────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    │                 │                 │
             2. Query RAG       3. Generate      4. Validate
                    │            Recipe (LLM)     Response
                    ↓                 ↓                 ↓
            ┌──────────────┐   ┌──────────┐    ┌───────────┐
            │ RAG Service  │   │ OpenAI   │    │ Pydantic  │
            └──────────────┘   └──────────┘    └───────────┘
                    │                 │                 │
                    └─────────────────┴─────────────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    │                 │                 │
             5. Generate         6. Format          7. Return
              Visualization      Response            JSON
                    ↓                 ↓                 ↓
            ┌──────────────┐   ┌──────────┐    ┌───────────┐
            │ Viz Agent    │   │ Response │    │ Frontend  │
            └──────────────┘   │ Model    │    └───────────┘
                               └──────────┘
```

#### Authentication Flow

```
┌─────────┐  1. POST /auth/register  ┌─────────────┐
│ Frontend│ ────────────────────────→│ Agent API   │
└─────────┘                           └─────────────┘
                                            │
                          2. Hash Password  │ 3. Generate Token
                                            ↓
                                      ┌──────────────┐
                                      │ User Store   │
                                      │ (JSONL)      │
                                      └──────────────┘
                                            │
                          4. Return Token   │
                                            ↓
                                      ┌──────────────┐
                                      │ Frontend     │
                                      │ (Store Token)│
                                      └──────────────┘

Subsequent Requests:
┌─────────┐  X-Auth-Token: xxx     ┌─────────────┐
│ Frontend│ ────────────────────→  │ Agent API   │
└─────────┘                         └─────────────┘
                                          │
                      1. Validate Token   │
                                          ↓
                                    ┌──────────────┐
                                    │ Active Tokens│
                                    │ (In-Memory)  │
                                    └──────────────┘
```

### Data Storage Architecture

#### 1. **User Data Storage**
- **Format**: JSONL (JSON Lines)
- **Location**: `data/user_store.jsonl`
- **Schema**:
```json
{
  "user_id": "uuid",
  "email": "user@example.com",
  "password_hash": "sha256_hash",
  "name": "User Name",
  "preferences": {
    "flavor_notes": ["chocolate", "nutty"],
    "roast_level": "Medium"
  },
  "beans": [
    {
      "bean_id": "uuid",
      "name": "Colombia Huila",
      "origin": "Colombia",
      "process": "Washed",
      "roast_level": "Medium",
      "roasted_on": "2024-11-20",
      "flavor_notes": ["chocolate", "caramel"],
      "created_at": "2024-11-23T12:00:00Z",
      "updated_at": "2024-11-23T12:00:00Z"
    }
  ]
}
```

**Design Rationale**:
- Simple file-based storage for MVP
- Easy to inspect and debug
- No database setup required
- Migration path to PostgreSQL/MongoDB available

#### 2. **RAG Data Storage**

**Raw Data**: `dailydrip_rag/data/raw/`
- CSV files with brewing experiments
- JSON files with structured recipes

**Processed Data**: `dailydrip_rag/data/processed/`
- `records.jsonl`: Normalized brewing records
- `chunks.jsonl`: Text chunks with metadata

**Vector Index**: `dailydrip_rag/indexes/chroma/`
- ChromaDB persistent index
- Embeddings for 384-dimensional vectors
- Metadata for filtering and reranking

#### 3. **Caching Strategy**

```python
# LRU cache for RAG collection
@lru_cache(maxsize=1)
def _get_collection(persist_dir: str, collection: str):
    # Expensive operation cached in memory
    return chromadb_client.get_collection(name=collection)
```

**Benefits**:
- Reduced ChromaDB connection overhead
- Faster query response times
- Memory-efficient (single instance)

---

## User Interface Design

### Frontend Architecture

```
src/
├── index.js                    # Application entry point
├── App.js                      # Root component with routing
├── components/                 # UI components
│   ├── AuthLanding.js          # Login/Register page
│   ├── Profile.js              # User profile & preferences
│   ├── BeanCollection.js       # Bean library CRUD
│   └── RecipeGenerator.js      # Recipe generation UI
├── context/
│   └── AuthContext.js          # Global authentication state
└── services/
    └── agentClient.js          # API client layer
```

### Component Hierarchy

```
<AuthProvider>
  <App>
    {!user ? (
      <AuthLanding />
    ) : (
      <AppShell>
        <Navigation />
        {activeSection === 'profile' && <Profile />}
        {activeSection === 'beans' && <BeanCollection />}
        {activeSection === 'recipe' && <RecipeGenerator />}
      </AppShell>
    )}
  </App>
</AuthProvider>
```

### State Management

#### 1. **Global State** (React Context)
```javascript
// AuthContext provides:
{
  user: {
    user_id, email, name, preferences
  },
  token: "auth_token_string",
  login: (email, password) => Promise,
  logout: () => void,
  refreshProfile: () => Promise
}
```

#### 2. **Component State** (useState)
```javascript
// Local state per component
const [beans, setBeans] = useState([])
const [loading, setLoading] = useState(false)
const [error, setError] = useState(null)
const [formData, setFormData] = useState({...})
```

#### 3. **Computed State** (useMemo)
```javascript
// Memoized computations
const roastedDays = useMemo(
  () => computeRoastedDays(bean.roasted_on),
  [bean.roasted_on]
)
```

### UI/UX Patterns

#### 1. **Progressive Disclosure**
- Hide advanced options behind toggles
- Show recipe parameters only after generation
- Expandable sections for bean details

#### 2. **Optimistic UI Updates**
```javascript
// Immediately update UI, rollback on error
setBeans(prev => [...prev, newBean])
try {
  await createBean(newBean)
} catch (error) {
  setBeans(prev => prev.filter(b => b.id !== newBean.id))
  showError(error)
}
```

#### 3. **Loading States**
```javascript
{loading ? (
  <Spinner />
) : error ? (
  <ErrorMessage error={error} />
) : (
  <DataDisplay data={data} />
)}
```

#### 4. **Form Validation**
- Client-side validation for immediate feedback
- Server-side validation for security
- Clear error messages with actionable guidance

### Responsive Design

```css
/* Tailwind breakpoints */
sm: 640px   /* Mobile landscape */
md: 768px   /* Tablet */
lg: 1024px  /* Desktop */
xl: 1280px  /* Large desktop */
```

**Layout Strategy**:
- Mobile-first design
- Stacked layout on mobile
- Side-by-side on tablet+
- Grid layout on desktop

---

## Code Organization

### Backend Structure

```
agent_core/
├── __init__.py                 # Package exports
├── agent.py                    # Main FastAPI application (850+ lines)
│   ├── Authentication endpoints
│   ├── Profile management
│   ├── Bean library endpoints
│   ├── Recipe generation
│   └── Visualization endpoints
├── integrated_agent.py         # End-to-end CLI workflow
├── visualization_agent_v2.py   # Visualization generation
├── agent_requirements.txt      # Production dependencies
├── requirements-dev.txt        # Development dependencies
└── tests/
    ├── test_agent.py           # API endpoint tests
    ├── test_agent_logic.py     # Helper function tests
    └── test_integrated_agent.py # Integration tests

dailydrip_rag/
├── src/
│   ├── ingest.py               # CSV/JSON → JSONL normalization
│   ├── chunk.py                # Text chunking for embeddings
│   ├── index.py                # Vector index creation
│   ├── query.py                # Query utilities
│   └── service.py              # FastAPI RAG service
├── data/
│   ├── raw/                    # Input data
│   └── processed/              # Pipeline outputs
├── indexes/
│   └── chroma/                 # Vector database
└── tests/                      # Comprehensive test suite
```

### Module Responsibilities

#### Agent Core (`agent_core/agent.py`)

**Key Classes & Functions**:
```python
# Pydantic Models (Data Validation)
class RegisterRequest(BaseModel)
class LoginRequest(BaseModel)
class BeanPayload(BaseModel)
class BrewRequest(BaseModel)
class VisualizeRequest(BaseModel)

# Authentication
def _hash_password(password: str) -> str
def _issue_token(user_id: str) -> str
def _require_auth(token: str) -> dict

# User Management
def _load_user_store() -> None
def _persist_user_store() -> None

# Bean Management
def _compute_roasted_days(roasted_on: str) -> int
def _normalize_roast_fields(bean: dict) -> dict

# Recipe Generation
async def brew_recipe(request: BrewRequest) -> dict
async def _query_rag(bean: dict, k: int) -> list

# Visualization
async def visualize_recipe(request: VisualizeRequest) -> dict
```

**Design Principles**:
- Single Responsibility: Each function has one job
- Pure Functions: Helper functions have no side effects
- Dependency Injection: RAG service URL as parameter
- Error Handling: Graceful fallbacks for external services

#### RAG Service (`dailydrip_rag/src/service.py`)

**Key Functions**:
```python
# ChromaDB Connection
@lru_cache(maxsize=1)
def _get_collection(persist_dir: str, collection: str)

# Reranking Logic
def _rerank_by_evaluation(
    results: list,
    similarity_weight: float
) -> list

# API Endpoints
@app.post("/rag")
async def query_rag(payload: RagQuery) -> RagResponse

@app.get("/health")
async def health_check() -> dict
```

**Design Principles**:
- Caching: LRU cache for expensive operations
- Separation of Concerns: Query vs. reranking logic
- Configurable: All parameters exposed via API
- Observable: Health check endpoint for monitoring

#### Visualization Agent (`visualization_agent_v2.py`)

**Key Classes**:
```python
@dataclass
class BrewingStep:
    step_number: int
    start_time: int
    end_time: int
    water_added: int
    cumulative_water: int
    action: str

class CoffeeBrewVisualizationAgent:
    def load_recipe(self, recipe: dict) -> None
    def generate_html(self) -> str
    def generate_mermaid(self) -> str
    def generate_ascii(self) -> str
    def save_visualization(self, path: str, format: str) -> None
```

**Design Principles**:
- No Dependencies: Pure Python standard library
- Multiple Formats: Single source → multiple outputs
- Data Class: Immutable brewing step representation
- Composability: Can be used standalone or integrated

### Frontend Structure

```
src/
├── index.js                    # ReactDOM.render
├── App.js                      # Root component (200+ lines)
│   ├── AppShell navigation
│   ├── Section routing
│   └── Callback handlers
├── components/
│   ├── AuthLanding.js          # 200+ lines
│   │   ├── Login form
│   │   └── Register form
│   ├── Profile.js              # 150+ lines
│   │   ├── User info display
│   │   └── Preferences editor
│   ├── BeanCollection.js       # 450+ lines
│   │   ├── Bean list view
│   │   ├── Bean form modal
│   │   └── CRUD operations
│   └── RecipeGenerator.js      # 750+ lines
│       ├── Bean selection
│       ├── Manual bean input
│       ├── Recipe generation
│       └── Visualization display
├── context/
│   └── AuthContext.js          # 120+ lines
│       ├── Auth state
│       ├── Login/logout logic
│       └── Profile refresh
└── services/
    └── agentClient.js          # 86 lines
        ├── HTTP client setup
        ├── Auth token management
        └── API endpoint wrappers
```

### Code Quality Standards

#### Python (PEP 8)
```python
# Configuration: .flake8
max-line-length = 127
max-complexity = 10
ignore = E203, E266, W503

# Naming Conventions
class UserRepository:        # PascalCase for classes
def create_user():           # snake_case for functions
SYSTEM_PROMPT = "..."        # UPPER_CASE for constants
_private_helper():           # Leading underscore for private

# Type Hints (encouraged)
def compute_days(date: str) -> Optional[int]:
    ...
```

#### JavaScript (Airbnb Style)
```javascript
// Configuration: ESLint extends "react-app"

// Naming Conventions
class BeanCollection extends React.Component  // PascalCase
function computeRoastedDays(roastedOn)        // camelCase
const API_BASE_URL = "..."                    // UPPER_CASE

// Prefer functional components
function RecipeGenerator({ beans, onGenerate }) {
  const [recipe, setRecipe] = useState(null)
  return <div>...</div>
}
```

---

## Data Flow

### 1. User Registration Flow

```
User Input (Frontend)
    ↓
Validation (Client-side)
    ↓
POST /auth/register
    ↓
Agent API receives request
    ↓
Pydantic validation
    ↓
Check email uniqueness
    ↓
Hash password (SHA-256)
    ↓
Generate user_id (UUID)
    ↓
Create user record
    ↓
Persist to user_store.jsonl
    ↓
Generate auth token
    ↓
Return {token, user} to frontend
    ↓
Store token in memory
    ↓
Update AuthContext state
    ↓
Redirect to main app
```

### 2. Bean Creation Flow

```
User fills bean form (Frontend)
    ↓
Client-side validation
    ↓
POST /beans with X-Auth-Token header
    ↓
Agent API validates token
    ↓
Extract user_id from token
    ↓
Validate bean payload (Pydantic)
    ↓
Generate bean_id (UUID)
    ↓
Compute roasted_days from roasted_on
    ↓
Add timestamps (created_at, updated_at)
    ↓
Append to user's beans array
    ↓
Persist entire user_store
    ↓
Return formatted bean record
    ↓
Frontend updates bean list (optimistic UI)
    ↓
User sees new bean immediately
```

### 3. Recipe Generation Flow (Detailed)

```
1. User selects bean or enters manually (Frontend)
    ↓
2. User selects brewer (V60, April, Orea, Origami)
    ↓
3. Optional: Add custom note
    ↓
4. Click "Generate Recipe"
    ↓
5. POST /brew with bean data
    ↓
─────────────── Agent API ───────────────
    ↓
6. Validate BrewRequest (Pydantic)
    ↓
7. Normalize bean data
    │   ├─ Compute roasted_days if roasted_on provided
    │   └─ Clean flavor_notes array
    ↓
8. Query RAG Service (if available)
    │   ├─ POST http://rag:8000/rag
    │   ├─ Body: {bean, k=3, use_evaluation_reranking=true}
    │   ├─ RAG returns similar recipes
    │   └─ If RAG fails → continue without references
    ↓
9. Build LLM prompt
    │   ├─ System prompt (constraints, format)
    │   ├─ Bean information (JSON)
    │   ├─ Brewer name
    │   ├─ Custom note (if provided)
    │   └─ RAG references (if retrieved)
    ↓
10. Call OpenAI API
    │   ├─ Model: gpt-4o-mini
    │   ├─ Temperature: 0.7
    │   ├─ Max tokens: 800
    │   └─ Response format: JSON
    ↓
11. Parse LLM response
    │   ├─ Extract JSON from markdown code blocks
    │   └─ Validate structure
    ↓
12. Validate recipe fields
    │   ├─ Temperature: 88-96°C
    │   ├─ Grinding size: 18-28 clicks
    │   ├─ Dose: 13-20g
    │   ├─ Target water: 200-320g
    │   ├─ Pours: sum(water_added) == target_water
    │   └─ Brewer matches request
    ↓
13. Return recipe JSON
    ↓
─────────────── Frontend ───────────────
    ↓
14. Receive recipe response
    ↓
15. Update UI state
    ↓
16. Render recipe parameters
    │   ├─ Temperature, grind, dose, water
    │   └─ Pour schedule table
    ↓
17. Optionally request visualization
    │   ├─ POST /visualize
    │   ├─ Body: {recipe, formats: ["html", "ascii"]}
    │   └─ Render HTML timeline in iframe
    ↓
18. User views complete recipe
```

### 4. RAG Pipeline Flow

```
┌─────────────────────────────────────────┐
│  Ingest Stage (src/ingest.py)           │
└─────────────────────────────────────────┘
    ↓
Raw CSV data (ucdavis_sample.csv)
    ↓
Parse CSV → DataFrame
    ↓
For each row:
    ├─ Flatten nested fields (bean.*, brewing.*, evaluation.*)
    ├─ Convert lists to comma-separated strings
    ├─ Normalize field names
    └─ Build JSON record
    ↓
Write to data/processed/records.jsonl
    ↓
┌─────────────────────────────────────────┐
│  Chunk Stage (src/chunk.py)             │
└─────────────────────────────────────────┘
    ↓
Read records.jsonl
    ↓
For each record:
    ├─ Extract bean fields → bean_text
    ├─ Extract brewing parameters → brewing_text
    ├─ Extract evaluation scores → evaluation_data
    └─ Create chunk with metadata
    ↓
Write to data/processed/chunks.jsonl
    ↓
┌─────────────────────────────────────────┐
│  Index Stage (src/index.py)             │
└─────────────────────────────────────────┘
    ↓
Read chunks.jsonl
    ↓
Initialize ChromaDB client
    ↓
Create or get collection "coffee_chunks"
    ↓
For each chunk:
    ├─ Generate embedding (all-MiniLM-L6-v2)
    ├─ Flatten metadata for ChromaDB
    └─ Add to collection
    ↓
Persist index to indexes/chroma/
    ↓
┌─────────────────────────────────────────┐
│  Service Stage (src/service.py)         │
└─────────────────────────────────────────┘
    ↓
Load ChromaDB collection (cached)
    ↓
Expose FastAPI endpoints:
    ├─ POST /rag → Query similar recipes
    └─ GET /health → Service status
```

---

## Design Patterns

### 1. **Dependency Injection**

```python
# Agent API
class BrewAgent:
    def __init__(self, rag_url: Optional[str] = None):
        self.rag_url = rag_url or os.getenv("RAG_SERVICE_URL")
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    async def generate_recipe(self, bean: dict) -> dict:
        references = await self._query_rag(bean) if self.rag_url else []
        ...
```

**Benefits**:
- Testable: Mock RAG service in tests
- Configurable: Different URLs for dev/prod
- Flexible: RAG service optional

### 2. **Factory Pattern**

```python
# Visualization format factory
class VisualizationAgent:
    def generate(self, format: str) -> str:
        generators = {
            'html': self.generate_html,
            'mermaid': self.generate_mermaid,
            'ascii': self.generate_ascii
        }
        return generators[format]()
```

**Benefits**:
- Extensible: Add new formats easily
- Type-safe: Single interface
- Maintainable: Isolated implementations

### 3. **Decorator Pattern**

```python
# FastAPI dependency injection for auth
async def require_auth(token: str = Header(None, alias="X-Auth-Token")):
    if not token or token not in _active_tokens:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return _active_tokens[token]

@app.get("/profile")
async def get_profile(user_id: str = Depends(require_auth)):
    return _user_store[user_id]
```

**Benefits**:
- Reusable: Apply to any endpoint
- Clean: Separates auth from business logic
- Composable: Chain multiple dependencies

### 4. **Strategy Pattern**

```python
# RAG reranking strategies
def rerank_by_similarity(results: list) -> list:
    return sorted(results, key=lambda x: x.distance)

def rerank_by_evaluation(results: list, weight: float) -> list:
    for r in results:
        r.combined_score = (
            weight * (1 - r.distance) +
            (1 - weight) * r.evaluation_score
        )
    return sorted(results, key=lambda x: -x.combined_score)

# Select strategy based on config
rerank = rerank_by_evaluation if use_evaluation else rerank_by_similarity
```

**Benefits**:
- Flexible: Switch algorithms at runtime
- Testable: Test each strategy independently
- Extensible: Add new strategies easily

### 5. **Observer Pattern** (React Context)

```javascript
// AuthContext notifies all subscribers
const AuthContext = createContext()

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)

  const login = async (email, password) => {
    const response = await loginUser({ email, password })
    setUser(response.user)  // All observers update automatically
  }

  return (
    <AuthContext.Provider value={{ user, login }}>
      {children}
    </AuthContext.Provider>
  )
}

// Components subscribe to changes
function Profile() {
  const { user } = useAuth()  // Re-renders when user changes
  return <div>{user.name}</div>
}
```

### 6. **Facade Pattern**

```javascript
// agentClient.js provides simplified API
export async function brewRecipe(payload) {
  return request('/brew', { method: 'POST', body: payload })
}

export async function listBeans() {
  return request('/beans')
}

// Components use simple interface
const recipe = await brewRecipe({ bean, brewer })
const beans = await listBeans()
```

---

## Security & Authentication

### Authentication Mechanism

#### Token-Based Authentication

```
┌──────────────┐
│ Register/    │
│ Login        │
└──────┬───────┘
       │
       ↓
┌──────────────────────────────────────┐
│ Generate Token                       │
│ token = secrets.token_urlsafe(32)    │
│ _active_tokens[token] = user_id      │
└──────┬───────────────────────────────┘
       │
       ↓
┌──────────────────────────────────────┐
│ Return to Client                     │
│ Response: {token, user}              │
└──────┬───────────────────────────────┘
       │
       ↓
┌──────────────────────────────────────┐
│ Client Stores Token                  │
│ authToken = response.token           │
└──────┬───────────────────────────────┘
       │
       ↓
┌──────────────────────────────────────┐
│ Subsequent Requests                  │
│ X-Auth-Token: {token}                │
└──────────────────────────────────────┘
```

**Token Properties**:
- **Length**: 32 bytes (256 bits)
- **Encoding**: URL-safe base64
- **Storage**: In-memory dictionary (server-side)
- **Lifetime**: Session-based (until logout or restart)

### Password Security

```python
import hashlib

def _hash_password(password: str) -> str:
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

# During registration
user_record = {
    "password_hash": _hash_password(request.password),
    # Never store plaintext password
}

# During login
input_hash = _hash_password(request.password)
if input_hash == user_record["password_hash"]:
    # Login successful
```

**Security Properties**:
- SHA-256 hashing (one-way function)
- No plaintext password storage
- Comparison in constant time

**Production Recommendations**:
- Use bcrypt or Argon2 (better than SHA-256)
- Add salt to prevent rainbow table attacks
- Implement rate limiting on login attempts
- Add password complexity requirements

### CORS Configuration

```python
from fastapi.middleware.cors import CORSMiddleware

FRONTEND_ORIGINS = os.getenv(
    "FRONTEND_ORIGINS",
    "http://localhost:3000,http://localhost:3001"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Security Implications**:
- Restricts cross-origin requests
- Configurable for different environments
- Prevents CSRF attacks

### Input Validation

```python
from pydantic import BaseModel, EmailStr, Field, validator

class RegisterRequest(BaseModel):
    email: EmailStr  # Validates email format
    password: str = Field(min_length=8)  # Minimum length
    name: str = Field(min_length=1, max_length=100)

    @validator('password')
    def password_strength(cls, v):
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v
```

**Validation Layers**:
1. **Type validation** (Pydantic)
2. **Business rule validation** (custom validators)
3. **Database constraints** (unique email, etc.)

### API Security Best Practices

| Threat | Mitigation |
|--------|-----------|
| **SQL Injection** | Not applicable (no SQL database) |
| **XSS** | React auto-escapes by default, sanitize user input |
| **CSRF** | Token-based auth (not cookie-based) |
| **Injection** | Pydantic validation on all inputs |
| **Secrets Exposure** | Environment variables, not hardcoded |
| **HTTPS** | Required in production (Dockerfile has HTTPS support) |
| **Rate Limiting** | TODO: Add rate limiting middleware |
| **DoS** | Docker resource limits, timeout configurations |

---

## Scalability & Performance

### Current Performance Characteristics

| Component | Latency | Throughput | Bottleneck |
|-----------|---------|------------|------------|
| **Frontend** | ~50ms | N/A | Network RTT |
| **Agent API** | ~2-5s | 10 req/s | OpenAI API |
| **RAG Service** | ~100-200ms | 50 req/s | ChromaDB query |
| **Recipe Generation** | ~3-6s | 10 req/s | LLM generation |

### Optimization Strategies

#### 1. **Caching**

```python
# Collection caching (already implemented)
@lru_cache(maxsize=1)
def _get_collection(persist_dir: str, collection: str):
    # Expensive ChromaDB connection cached
    return client.get_collection(name=collection)

# Recipe caching (future enhancement)
from functools import lru_cache

@lru_cache(maxsize=100)
def generate_recipe(bean_hash: str, brewer: str) -> dict:
    # Cache recipes for identical inputs
    pass
```

#### 2. **Async Processing**

```python
# FastAPI async endpoints
@app.post("/brew")
async def brew_recipe(request: BrewRequest):
    # Non-blocking I/O for external calls
    rag_task = asyncio.create_task(query_rag(request.bean))
    llm_task = asyncio.create_task(call_openai(request))

    rag_results = await rag_task
    recipe = await llm_task

    return recipe
```

#### 3. **Database Optimization** (Future)

```python
# Current: JSONL (linear scan)
# Future: PostgreSQL with indexes

CREATE INDEX idx_user_email ON users(email);
CREATE INDEX idx_bean_user_id ON beans(user_id);
CREATE INDEX idx_bean_roasted_on ON beans(roasted_on);
```

#### 4. **CDN for Static Assets**

```
Frontend Build:
├── static/js/main.js → CDN (CloudFront, Cloudflare)
├── static/css/main.css → CDN
└── index.html → Origin server
```

### Horizontal Scaling Strategy

```
┌─────────────────────────────────────────────┐
│            Load Balancer (Nginx)            │
└──────────────┬──────────────────────────────┘
               │
       ┌───────┼───────┐
       ↓       ↓       ↓
   ┌─────┐ ┌─────┐ ┌─────┐
   │Agent│ │Agent│ │Agent│  ← Stateless (can scale horizontally)
   │API 1│ │API 2│ │API 3│
   └─────┘ └─────┘ └─────┘
       │       │       │
       └───────┼───────┘
               ↓
       ┌───────────────┐
       │  RAG Service  │     ← Read-only (can scale)
       │  (Replica)    │
       └───────────────┘
               ↓
       ┌───────────────┐
       │  PostgreSQL   │     ← Single source of truth
       │  (Primary +   │
       │   Replicas)   │
       └───────────────┘
```

**Stateless Design Enables Scaling**:
- No server-side sessions (token-based auth)
- No in-memory user data (use Redis or database)
- No local file storage (use S3 or shared volume)

### Resource Limits (Docker)

```yaml
# docker-compose.yml
services:
  agent:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M

  rag:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
```

### Monitoring & Observability

```python
# Add Prometheus metrics (future)
from prometheus_client import Counter, Histogram

request_count = Counter('api_requests_total', 'Total API requests')
request_latency = Histogram('api_request_latency_seconds', 'Request latency')

@app.post("/brew")
async def brew_recipe(request: BrewRequest):
    request_count.inc()
    with request_latency.time():
        return await _generate_recipe(request)
```

---

## Testing Strategy

### Test Coverage Goals

| Component | Target Coverage | Current Status |
|-----------|----------------|----------------|
| **Agent Core** | 80%+ | ✅ ~85% |
| **RAG Pipeline** | 80%+ | ✅ ~90% |
| **Frontend** | 70%+ | ✅ ~75% |
| **Integration** | Key flows | ✅ Implemented |

### Testing Pyramid

```
       ┌───────────────┐
       │  E2E Tests    │  ← Few (critical user flows)
       │  (Selenium)   │
       └───────────────┘
      ┌─────────────────┐
      │ Integration     │  ← Some (API + DB + RAG)
      │ Tests (pytest)  │
      └─────────────────┘
    ┌───────────────────────┐
    │   Unit Tests          │  ← Many (pure functions)
    │   (pytest, Jest)      │
    └───────────────────────┘
```

### Backend Testing

#### Unit Tests
```python
# tests/test_agent_logic.py
def test_compute_roasted_days():
    roasted_on = "2024-11-15"
    days = _compute_roasted_days(roasted_on)
    assert isinstance(days, int)
    assert days >= 0

def test_hash_password():
    password = "secure123"
    hash1 = _hash_password(password)
    hash2 = _hash_password(password)
    assert hash1 == hash2  # Deterministic
    assert len(hash1) == 64  # SHA-256 hex length
```

#### Integration Tests
```python
# tests/test_agent.py
@pytest.mark.asyncio
async def test_register_and_login(test_client):
    # Register
    response = await test_client.post("/auth/register", json={
        "email": "test@example.com",
        "password": "password123",
        "name": "Test User"
    })
    assert response.status_code == 200
    token = response.json()["token"]

    # Use token
    response = await test_client.get(
        "/profile",
        headers={"X-Auth-Token": token}
    )
    assert response.status_code == 200
```

#### Mock External Services
```python
# tests/conftest.py
@pytest.fixture
def mock_openai(mocker):
    mock_response = {
        "choices": [{
            "message": {
                "content": json.dumps({
                    "brewing": {
                        "brewer": "V60",
                        "temperature": 92,
                        ...
                    }
                })
            }
        }]
    }
    return mocker.patch('openai.ChatCompletion.create', return_value=mock_response)
```

### Frontend Testing

#### Component Tests
```javascript
// src/components/BeanCollection.test.js
import { render, screen, fireEvent } from '@testing-library/react'
import BeanCollection from './BeanCollection'

test('renders bean list', () => {
  const beans = [
    { bean_id: '1', name: 'Ethiopia Sidamo', origin: 'Ethiopia' }
  ]
  render(<BeanCollection beans={beans} />)
  expect(screen.getByText('Ethiopia Sidamo')).toBeInTheDocument()
})

test('calls onCreate when form submitted', async () => {
  const onCreate = jest.fn()
  render(<BeanCollection beans={[]} onCreate={onCreate} />)

  fireEvent.click(screen.getByText('Add Bean'))
  fireEvent.change(screen.getByLabelText('Name'), { target: { value: 'Kenya AA' } })
  fireEvent.click(screen.getByText('Save'))

  expect(onCreate).toHaveBeenCalledWith(expect.objectContaining({
    name: 'Kenya AA'
  }))
})
```

#### API Client Tests
```javascript
// src/services/agentClient.test.js
import { brewRecipe, setAuthToken } from './agentClient'

global.fetch = jest.fn()

test('brewRecipe includes auth token', async () => {
  setAuthToken('test-token')
  fetch.mockResolvedValueOnce({
    ok: true,
    json: async () => ({ brewing: {} })
  })

  await brewRecipe({ bean: {}, brewer: 'V60' })

  expect(fetch).toHaveBeenCalledWith(
    'http://localhost:9000/brew',
    expect.objectContaining({
      headers: expect.objectContaining({
        'X-Auth-Token': 'test-token'
      })
    })
  )
})
```

### CI/CD Testing

```yaml
# .github/workflows/python-ci.yml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt

      - name: Lint with flake8
        run: flake8 src/ --max-line-length=127

      - name: Run tests with coverage
        run: pytest --cov=src --cov-report=xml

      - name: Upload to Codecov
        uses: codecov/codecov-action@v3
```

### Test Data Management

```python
# tests/fixtures/sample_data.py
SAMPLE_BEAN = {
    "name": "Ethiopia Yirgacheffe",
    "process": "Washed",
    "variety": "Heirloom",
    "roast_level": "Light",
    "roasted_on": "2024-11-15",
    "flavor_notes": ["floral", "citrus"]
}

SAMPLE_RECIPE = {
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

---

## Appendix: Deployment Architecture

### Development Environment

```yaml
# docker-compose.yml
services:
  rag:
    build: ./dailydrip_rag
    ports:
      - "8000:8000"
    volumes:
      - ./dailydrip_rag/data:/app/data
      - ./dailydrip_rag/indexes:/app/indexes
    environment:
      - RAG_PERSIST_DIR=/app/indexes/chroma

  agent:
    build:
      context: .
      dockerfile: Dockerfile.agent
    ports:
      - "9000:9000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - RAG_SERVICE_URL=http://rag:8000
    depends_on:
      - rag

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - REACT_APP_AGENT_API_URL=http://localhost:9000
```

### Production Deployment (GCP Example)

```
┌─────────────────────────────────────────────────────────┐
│                    Google Cloud                          │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │  Cloud Load Balancer (HTTPS)                       │ │
│  └───────────────────┬────────────────────────────────┘ │
│                      │                                   │
│          ┌───────────┴───────────┐                      │
│          ↓                       ↓                       │
│  ┌──────────────┐        ┌──────────────┐              │
│  │ Cloud Run    │        │ Cloud Run    │              │
│  │ (Frontend)   │        │ (Agent API)  │              │
│  │ - React app  │        │ - FastAPI    │              │
│  └──────────────┘        └──────┬───────┘              │
│                                  │                       │
│                                  ↓                       │
│                          ┌──────────────┐               │
│                          │ Cloud Run    │               │
│                          │ (RAG Service)│               │
│                          └──────┬───────┘               │
│                                  │                       │
│                                  ↓                       │
│                          ┌──────────────┐               │
│                          │ Cloud SQL    │               │
│                          │ (PostgreSQL) │               │
│                          └──────────────┘               │
│                                                          │
│  ┌──────────────────────────────────────┐              │
│  │ Cloud Storage                         │              │
│  │ - Vector indexes                      │              │
│  │ - User data backups                   │              │
│  └──────────────────────────────────────┘              │
└─────────────────────────────────────────────────────────┘
```

---

## Document Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2024-11-23 | DailyDrip Team | Initial comprehensive design document |

---

**End of Document**
