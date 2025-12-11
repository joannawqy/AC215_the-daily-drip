# DailyDrip: Brewing the Perfect Cup with AI-Powered Personalization

**An intelligent coffee brewing assistant that combines RAG, generative AI, and interactive visualizations to help enthusiasts dial in their perfect pour-over**

---

## The Challenge: Art Meets Science at the Coffee Bar

Coffee brewing is a delicate balance of art and science. Pour-over enthusiasts know the struggle: you've just bought a bag of Ethiopian Yirgacheffe with notes of jasmine and bergamot, but how do you unlock those flavors? What grind size? How hot should the water be? How fast should you pour? With dozens of variables affecting extraction—from water temperature and grind size to pour cadence and coffee dose—even experienced home brewers can feel overwhelmed.

The problem compounds when managing multiple beans and brewers. Each origin, processing method, and roast level demands different parameters. Keeping detailed brew logs helps, but manually referencing past successes while experimenting with new beans is tedious and error-prone. What if an AI assistant could learn from your brewing history and generate personalized recipes tailored to each bean's unique characteristics?

Enter **DailyDrip**: an AI-powered brewing assistant that makes everyday coffee brewing easier, more personalized, and more enjoyable.

---

## The Solution: RAG-Enhanced Recipe Generation

DailyDrip combines three coordinated capabilities into a cohesive system:

1. **Brewing Recipe Agent** – Generates complete pour-over recipes (temperature, grind size, dose, and pour schedule) using OpenAI's GPT-4o-mini, informed by bean metadata and retrieval-augmented generation (RAG).

2. **Visualization Agent** – Transforms recipes into intuitive timeline visualizations (HTML, Mermaid diagrams, and ASCII art) that clarify pour cadence and water distribution at a glance.

3. **RAG-Powered Knowledge Base** – Maintains a vector database of past brews and bean characteristics, enabling similarity search to ground new recommendations in proven recipes.

The result? A system that doesn't just generate generic recipes—it learns from your brewing history and adapts recommendations to your beans, your brewer, and your taste preferences.

---

## System Architecture: Modular and Scalable

DailyDrip follows a clean, layered architecture with clear separation of concerns:

```
┌──────────────────┐
│  React Frontend  │  ← User Interface
│  (Port 3000)     │     • Authentication & User Profile
│                  │     • Bean Library Management
│  Components:     │     • Recipe Generator
│  • AuthLanding   │     • Visualization Display
│  • BeanCollection│
│  • RecipeGen     │
└────────┬─────────┘
         │ HTTPS/REST
         ↓
┌──────────────────┐     ┌─────────────────┐
│  Agent Core API  │────→│   OpenAI API    │
│  (FastAPI)       │     │  (gpt-4o-mini)  │
│  Port 9000       │     └─────────────────┘
│                  │
│  Endpoints:      │     ┌─────────────────┐
│  • /auth/*       │────→│  RAG Service    │
│  • /profile      │     │  (FastAPI)      │
│  • /beans/*      │     │  Port 8000      │
│  • /brew         │     │                 │
│  • /visualize    │     │  • ChromaDB     │
│  • /feedback     │     │  • Embeddings   │
└──────────────────┘     │  • Similarity   │
         │               │    Search       │
         ↓               └─────────────────┘
┌──────────────────┐
│ Visualization    │
│ Agent V2         │
│                  │
│  • HTML Timeline │
│  • Mermaid Chart │
│  • ASCII Art     │
└──────────────────┘
```

### Technology Stack

**Backend**
- **FastAPI**: High-performance Python web framework for both Agent and RAG services
- **OpenAI API**: GPT-4o-mini for recipe generation with function calling
- **ChromaDB**: Vector database for similarity-based recipe retrieval
- **Sentence-Transformers**: `all-MiniLM-L6-v2` model for generating embeddings
- **Pydantic**: Data validation and settings management

**Frontend**
- **React 18**: Component-based UI with hooks and context
- **Tailwind CSS**: Utility-first styling for responsive design
- **Lucide React**: Beautiful, consistent iconography

**Infrastructure**
- **Docker & Docker Compose**: Containerization and orchestration
- **GitHub Actions**: CI/CD with automated testing and coverage reporting
- **pytest & Jest**: Comprehensive test suites for backend and frontend
- **Codecov**: Test coverage tracking and visualization

---

## Key Technical Innovations

### 1. Evaluation-Aware RAG Reranking

Unlike traditional RAG systems that rely solely on embedding similarity, DailyDrip implements **evaluation-aware reranking** that considers past brew quality metrics alongside semantic similarity.

When retrieving reference recipes, the system:
1. Fetches `k × retrieval_multiplier` candidates from ChromaDB (e.g., 9 recipes when k=3)
2. Computes a **combined score** for each candidate:
   ```python
   combined_score = (similarity_weight × similarity_score) + 
                    (evaluation_weight × normalized_evaluation_score)
   ```
3. Re-ranks candidates by combined score and returns the top k

The evaluation score incorporates:
- **Liking** (0-10 scale): User's overall satisfaction (60% weight)
- **JAG metrics** (1-5 scale): Flavor intensity, acidity, mouthfeel, sweetness, and purchase intent (40% weight)

This approach ensures that highly-rated recipes are prioritized, even if they're slightly less similar semantically—because a great-tasting brew is more valuable than a merely similar one.

```python
def _compute_evaluation_score(evaluation: Optional[Dict[str, Any]]) -> float:
    """Compute normalized evaluation score (0-1) from liking and JAG metrics."""
    if not evaluation:
        return 0.0
    
    score = 0.0
    weights_sum = 0.0
    
    # Liking (0-10) → 60% weight
    liking = evaluation.get("liking")
    if liking is not None:
        normalized_liking = float(liking) / 10.0
        score += normalized_liking * 0.6
        weights_sum += 0.6
    
    # JAG metrics (1-5) → 40% weight
    jag = evaluation.get("jag", {})
    if isinstance(jag, dict):
        jag_values = []
        for key in ["flavour_intensity", "acidity", "mouthfeel", "sweetness", "purchase_intent"]:
            val = jag.get(key)
            if val is not None:
                normalized_val = (float(val) - 1.0) / 4.0
                jag_values.append(normalized_val)
        
        if jag_values:
            jag_avg = sum(jag_values) / len(jag_values)
            score += jag_avg * 0.4
            weights_sum += 0.4
    
    return score / weights_sum if weights_sum > 0 else 0.0
```

### 2. Dual RAG Access Modes

DailyDrip supports two complementary RAG access patterns:

**Local Index Mode** (Development & Offline Use)
- Direct access to ChromaDB persistent index
- Zero network latency
- Ideal for local development and testing

**Remote Service Mode** (Production & Multi-Tenant)
- HTTP-based RAG service with `/rag` endpoint
- Supports user-specific filtering (multi-tenancy)
- Scalable for production deployments
- Enables centralized index management

The system gracefully falls back to local mode when the service is unavailable, ensuring robust operation in all scenarios.

### 3. Structured Recipe Generation with Function Calling

Rather than parsing free-form text responses from the LLM, DailyDrip uses OpenAI's **function calling** feature to enforce structured JSON output that matches a Pydantic schema:

```python
completion = client.chat.completions.create(
    model=model,
    messages=messages,
    temperature=temperature,
    top_p=top_p,
    functions=[{
        "name": "generate_recipe",
        "description": "Generate a coffee brewing recipe",
        "parameters": Recipe.model_json_schema()
    }],
    function_call={"name": "generate_recipe"}
)
```

This approach guarantees:
- **Type safety**: Every field is validated against the schema
- **Consistency**: No parsing errors or malformed responses
- **Maintainability**: Schema updates automatically propagate to LLM prompts

Post-generation validation catches common mistakes (e.g., pour totals not matching target water) before recipes reach users.

### 4. Multi-Format Visualization Pipeline

The Visualization Agent V2 (`visualization_agent_v2.py`) demonstrates thoughtful design for presentation flexibility:

- **HTML Timeline**: Interactive, styled brew guide suitable for web display
- **Mermaid Diagram**: Gantt-chart format for documentation and sharing
- **ASCII Art**: Terminal-friendly visualization for CLI workflows

Critically, the visualization agent is **dependency-free**—it uses only Python's standard library, making it trivial to integrate anywhere without adding heavyweight dependencies.

```python
class CoffeeBrewVisualizationAgent:
    """
    Generate beautiful brewing visualizations without external dependencies.
    
    Supports:
    - HTML with inline CSS styling
    - Mermaid.js Gantt charts
    - ASCII art timelines
    """
    
    def generate_html_visualization(self) -> str:
        """Creates a self-contained HTML document with inline styling."""
        # ...
        
    def generate_mermaid_flowchart(self) -> str:
        """Produces a Mermaid Gantt chart for embedding in docs."""
        # ...
        
    def generate_ascii_flowchart(self) -> str:
        """Renders a terminal-friendly ASCII timeline."""
        # ...
```

### 5. Integrated User Management with Token-Based Auth

DailyDrip implements a lightweight but secure authentication system:

- **Password hashing**: SHA-256 hashing for credential security
- **Token-based auth**: Secure, URL-safe tokens using `secrets.token_urlsafe(32)`
- **Header flexibility**: Supports both `X-Auth-Token` and `Authorization: Bearer` patterns
- **JSONL persistence**: Simple, human-readable user store for development

User beans are stored per-account, enabling:
- Personal bean library management (CRUD operations)
- Taste preference tracking (flavor notes, roast level)
- Recipe history tied to specific users

---

## Implementation Highlights

### RAG Pipeline: Ingest → Chunk → Index → Serve

The `dailydrip_rag` module implements a complete RAG pipeline in four stages:

**1. Ingest** (`src/ingest.py`)
- Reads raw data from CSV (UC Davis coffee dataset) and JSON (user brew logs)
- Normalizes to canonical JSONL format
- Output: `data/processed/records.jsonl`

**2. Chunk** (`src/chunk.py`)
- Splits records into semantic chunks
- Constructs bean-focused text representations
- Output: `data/processed/chunks.jsonl`

**3. Index** (`src/index.py`)
- Generates embeddings using `all-MiniLM-L6-v2`
- Builds ChromaDB vector index with metadata
- Output: `indexes/chroma/` (persistent database)

**4. Serve** (`src/service.py`)
- FastAPI service exposing `/rag` endpoint
- Similarity search with evaluation reranking
- Health checks and collection statistics

```bash
# Run the complete pipeline
make pipeline

# Or run stages individually
docker compose up ingest
docker compose up chunk
docker compose up index

# Start the RAG service
make rag
```

### Frontend: Context-Driven State Management

The React frontend leverages Context API for clean state management:

```javascript
// AuthContext.js - Global authentication state
const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('authToken'));
  const [loading, setLoading] = useState(true);
  
  // Auto-load user profile on mount
  useEffect(() => {
    if (token) {
      loadUserProfile();
    } else {
      setLoading(false);
    }
  }, [token]);
  
  const login = async (email, password) => { /* ... */ };
  const logout = () => { /* ... */ };
  
  return (
    <AuthContext.Provider value={{ user, token, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};
```

Components like `BeanCollection` and `RecipeGenerator` consume this context, enabling seamless authentication flows and user-specific data fetching.

### Graceful Error Handling

Both Agent and RAG services implement comprehensive error handling:

- **HTTP exceptions**: Appropriate status codes (401 Unauthorized, 404 Not Found, 500 Internal Error)
- **Validation errors**: Detailed error messages for malformed requests
- **Service unavailability**: Graceful fallbacks when RAG service is offline
- **Retry logic**: Resilient API calls with timeout handling

```python
@app.post("/brew", response_model=BrewResponse)
async def brew_endpoint(payload: BrewRequest, current_user: Dict[str, Any] = Depends(get_authenticated_user)) -> BrewResponse:
    try:
        return await run_in_threadpool(
            brew_with_options,
            payload.bean,
            payload.brewer,
            note=payload.note,
            rag_enabled=payload.rag_enabled,
            rag_service_url=payload.rag_service_url,
            rag_persist_dir=payload.rag_persist_dir,
            rag_k=payload.rag_k,
            model=payload.model,
            temperature=payload.temperature,
            top_p=payload.top_p,
            user_id=current_user["user_id"],
        )
    except EnvironmentError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
```

---

## Quality Assurance: Comprehensive Testing

DailyDrip maintains **high code coverage** across all modules:

### Backend Testing (pytest)

**Agent Core** (`agent_core/tests/`)
- `test_agent.py`: Core agent logic and API endpoints
- `test_agent_logic.py`: Helper functions and utilities
- `test_integrated_agent.py`: End-to-end integration tests
- `test_agent_api_integration.py`: API contract tests

**RAG Pipeline** (`dailydrip_rag/tests/`)
- `test_ingest.py`: Data ingestion and normalization
- `test_chunk.py`: Text chunking and representation
- `test_index.py`: Vector indexing and persistence
- `test_service.py`: RAG service endpoints
- `test_query.py`: Query utilities
- `test_service_comprehensive.py`: Complex RAG scenarios

Coverage tracking via Codecov:
```bash
pytest tests/ -v --cov=src --cov-report=term --cov-report=html
```

### Frontend Testing (Jest + React Testing Library)

**Components** (`frontend/src/components/`)
- `AuthLanding.test.js`: Login/registration flows
- `BeanCollection.test.js`: Bean CRUD operations
- `RecipeGenerator.test.js`: Recipe generation UI
- `Profile.test.js`: User profile management

**Context & Services**
- `AuthContext.test.js`: Authentication state management
- `agentClient.test.js`: API client layer

**Comprehensive Tests**
- `App.comprehensive.test.js`: Full application flows
- `BeanCollection.comprehensive.test.js`: Complex bean scenarios
- `RecipeGenerator.comprehensive.test.js`: Recipe edge cases

```bash
npm test -- --coverage --watchAll=false
```

### CI/CD Pipeline (GitHub Actions)

**Python CI** (`.github/workflows/python-ci.yml`)
- Linting with flake8 and black
- Unit tests with pytest
- Coverage reporting to Codecov

**Frontend CI** (`.github/workflows/frontend-ci.yml`)
- Linting with ESLint
- Unit tests with Jest
- Coverage reporting

**Docker CI** (`.github/workflows/docker-ci.yml`)
- Build verification for all services
- Multi-stage build testing

All workflows run on push and pull requests, maintaining code quality throughout development.

---

## Results and User Experience

### Typical User Journey

1. **Registration & Setup**
   - User creates account with email/password
   - Sets taste preferences (e.g., "chocolate, caramel, nutty" with "Medium" roast preference)

2. **Bean Library Management**
   - Adds beans with details: name, origin, process, roast date, flavor notes
   - System automatically calculates days since roast
   - Beans persist across sessions

3. **Recipe Generation**
   - Selects a bean from library or enters details manually
   - Chooses brewer (V60, April, Orea, Origami)
   - Optionally adds custom notes (e.g., "I prefer bright acidity")
   - System queries RAG for similar past brews
   - GPT-4o-mini generates personalized recipe considering:
     - Bean characteristics (process, roast level, age)
     - Brewer specifications (V60 = slower pour, April = flatter bed)
     - Retrieved reference recipes
     - User taste preferences

4. **Visualization & Brewing**
   - Receives detailed recipe with:
     - Temperature (88-96°C)
     - Grind size (Comandante clicks, 20-28)
     - Dose (grams of coffee)
     - Water amount (ml)
     - Pour schedule (start/end times and water amounts)
   - Views HTML timeline showing pour cadence
   - Follows recipe step-by-step while brewing

5. **Feedback Loop** (Future Enhancement)
   - Evaluates brew quality (liking score, JAG metrics)
   - System stores evaluation alongside recipe
   - Future recipes benefit from quality-weighted reranking

### Performance Characteristics

- **Recipe Generation**: ~2-4 seconds (OpenAI API latency)
- **RAG Retrieval**: ~200-500ms (local) / ~400-800ms (service)
- **Visualization Generation**: <100ms (pure Python, no external dependencies)
- **Frontend Rendering**: Instant (client-side React)

### Sample Recipe Output

```json
{
  "brewing": {
    "brewer": "V60",
    "temperature": 93,
    "grinding_size": 22,
    "dose": 15,
    "target_water": 240,
    "pours": [
      {"start": 0, "end": 30, "water_added": 45},
      {"start": 30, "end": 75, "water_added": 65},
      {"start": 75, "end": 120, "water_added": 65},
      {"start": 120, "end": 165, "water_added": 65}
    ]
  }
}
```

Interpretation:
- **Bloom**: 45g at 0:00-0:30 (wetting the grounds)
- **First pour**: 65g at 0:30-1:15 (building the bed)
- **Second pour**: 65g at 1:15-2:00 (maintaining flow)
- **Final pour**: 65g at 2:00-2:45 (reaching target)
- **Total brew time**: ~3-4 minutes including drawdown

---

## Technical Challenges and Solutions

### Challenge 1: Inconsistent LLM Output Format

**Problem**: Early experiments with free-form text responses led to parsing errors and inconsistent recipe structures.

**Solution**: Adopted OpenAI function calling with strict Pydantic schemas. The LLM's response is automatically validated against the schema, guaranteeing type safety and structural consistency. Post-generation validation catches domain-specific errors (e.g., pour totals, grind size ranges).

### Challenge 2: RAG Relevance vs. Quality Tradeoff

**Problem**: Similarity-only retrieval surfaced semantically similar recipes that produced mediocre brews.

**Solution**: Implemented evaluation-aware reranking that balances semantic similarity with past brew quality. By fetching more candidates (`k × retrieval_multiplier`) and reranking by combined scores, the system prioritizes proven recipes while maintaining semantic relevance.

### Challenge 3: Multi-Service Coordination

**Problem**: Managing dependencies between Frontend → Agent API → RAG Service required careful orchestration.

**Solution**: 
- **Docker Compose**: Defines service dependencies and startup order
- **Graceful degradation**: Agent works without RAG if service is unavailable
- **Health checks**: Services expose `/health` endpoints for monitoring
- **Environment-based configuration**: URLs and ports configurable via env vars

### Challenge 4: Testing Async API Calls

**Problem**: Frontend API calls and backend async operations required careful mocking and testing.

**Solution**:
- **Backend**: `run_in_threadpool` for CPU-bound operations (OpenAI calls)
- **Frontend**: MSW (Mock Service Worker) for API mocking in tests
- **Integration tests**: Full request/response cycle testing
- **Fixtures**: Reusable test data and mock responses

---

## Future Enhancements

### 1. Adaptive Learning with User Feedback

Currently, the feedback endpoint accepts brew evaluations but doesn't actively retrain models. Future work includes:
- **Automated reindexing**: New feedback immediately updates ChromaDB
- **User-specific fine-tuning**: Personalized models based on taste history
- **Collaborative filtering**: "Users who liked this recipe also enjoyed..."

### 2. Advanced Brew Analysis

- **TDS (Total Dissolved Solids) prediction**: Estimate extraction percentage
- **Flavor wheel integration**: Map recipes to SCA flavor wheel coordinates
- **Comparison view**: Side-by-side recipe analysis for experimentation

### 3. Hardware Integration

- **Smart scale integration**: Real-time pour guidance via Bluetooth scales
- **Temperature sensor support**: Precise water temperature tracking
- **Camera-based grind size estimation**: Computer vision for grind consistency

### 4. Community Features

- **Public recipe sharing**: Browse and save community recipes
- **Roaster partnerships**: Official profiles from specialty roasters
- **Brew challenges**: Monthly brewing competitions and leaderboards

### 5. Mobile Application

- **Native iOS/Android apps**: On-the-go recipe access
- **Offline mode**: Download recipes for offline brewing
- **Timer integration**: Built-in brew timers with haptic feedback

### 6. Production Deployment

- **Kubernetes orchestration**: Scalable cloud deployment
- **PostgreSQL backend**: Replace JSONL with production database
- **Redis caching**: Cache frequently accessed recipes
- **CDN integration**: Fast static asset delivery

---

## Lessons Learned

### 1. RAG Isn't Just About Similarity

Our evaluation-aware reranking fundamentally changed system behavior. Pure similarity retrieval surfaced "close enough" recipes that sometimes produced poor results. By incorporating quality metrics, we bias toward proven recipes while maintaining semantic relevance. This insight applies broadly to RAG systems in domains where outcome quality is measurable.

### 2. Structured Outputs Beat Parsing

Function calling transformed our LLM integration from brittle to reliable. Rather than fighting with regex and JSON parsing, we get type-safe, validated responses every time. The slight overhead in schema design pays enormous dividends in maintainability.

### 3. Multi-Service Architecture Requires Graceful Degradation

Network failures happen. Our dual-mode RAG access (local index fallback) ensures the system remains functional even when the RAG service is down. This resilience is critical for user trust—nobody wants a coffee recipe generator that fails because a microservice is restarting.

### 4. Developer Experience Matters

Thoughtful decisions like dependency-free visualization, comprehensive test fixtures, and clear documentation significantly accelerated development. When new team members could `make run` and have a working system in 60 seconds, iteration velocity increased dramatically.

### 5. Domain Constraints Improve LLM Outputs

Our system prompt explicitly constrains grind size (20-28 clicks), temperature (88-96°C), and brew ratios (1:15 to 1:17). These domain-specific guardrails prevent the LLM from hallucinating unrealistic recipes. Don't trust LLMs to know your domain's physical constraints—encode them explicitly.

---

## Conclusion

DailyDrip demonstrates how thoughtful integration of retrieval-augmented generation, structured LLM outputs, and user-centric design can solve real-world problems in specialized domains. By combining semantic search over past brews with quality-aware reranking and personalized recipe generation, we've built a system that genuinely helps coffee enthusiasts brew better coffee.

The modular architecture—separating RAG pipeline, agent logic, visualization, and frontend—ensures each component can evolve independently. Comprehensive testing and CI/CD maintain code quality as the system grows. And the use of modern frameworks (FastAPI, React, ChromaDB) positions DailyDrip for scalable deployment.

Most importantly, DailyDrip shows that AI-assisted creativity doesn't replace expertise—it amplifies it. The system doesn't claim to know "the perfect recipe" but rather helps users explore the parameter space intelligently, learning from past successes and adapting to new beans. This human-AI collaboration model feels right for craft-focused domains where variability and experimentation are features, not bugs.

**Try DailyDrip yourself:**
```bash
git clone https://github.com/joannawqy/AC215_the-daily-drip.git
cd AC215_the-daily-drip
export OPENAI_API_KEY="your-key-here"
make run
cd frontend && npm install && npm start
```

Open [http://localhost:3000](http://localhost:3000) and brew your best cup yet.

---

## Project Information

**Team**: DailyDrip Collective (Even Li, Joanna Wang, Jessica Wang, Zicheng Ma)  
**Course**: AC215 – MLOps, Harvard University  
**GitHub**: [github.com/joannawqy/AC215_the-daily-drip](https://github.com/joannawqy/AC215_the-daily-drip)  
**Coverage**: [![codecov](https://codecov.io/gh/joannawqy/AC215_the-daily-drip/branch/milestone4/graph/badge.svg)](https://codecov.io/gh/joannawqy/AC215_the-daily-drip)  
**License**: MIT

---

*This post describes the Milestone 4 implementation of DailyDrip, representing the culmination of a semester-long project exploring MLOps practices, RAG architectures, and production-ready AI systems.*
