# Test Coverage Gaps

This document identifies functions and modules not fully covered by tests. Current coverage: **Agent Core 77%**, **DailyDrip RAG 67%**.

---

## Agent Core (77% coverage)

### `agent.py` (69% coverage)

**Uncovered Functions/Areas:**
- **RAG Service Integration** (lines 364-414, 465-541): `_fetch_references_via_service()`, `_fetch_references_via_local_index()` - Error handling paths for RAG service failures, httpx not installed scenarios
- **Error Handling** (lines 1184-1189): `brew_endpoint()` exception handlers (EnvironmentError, RuntimeError, generic Exception)
- **User Store Operations** (lines 1001, 1047, 1086-1090, 1092-1093): `_persist_user_store()`, `_load_user_store()` - User store persistence and loading
- **Authentication Helpers** (lines 135-163, 223, 233-237): `_hash_password()`, `_issue_token()`, `_require_authenticated_user()` - Password hashing and token generation edge cases
- **CLI Interface** (lines 1283-1387): `main()` function - Command-line argument parsing and CLI execution paths
- **Feedback Endpoint** (lines 1229-1279): `submit_feedback()` - Error handling and RAG service integration
- **Visualization Endpoint** (lines 1192-1203): `visualize_endpoint()` - Error handling for invalid formats
- **Bean Management** (lines 1144, 1158): `delete_bean()` - Error paths for bean deletion

### `integrated_agent.py` (41% coverage)

**Uncovered Functions/Areas:**
- **RAG Integration** (lines 173-216): RAG service calls and error handling
- **Recipe Generation** (lines 225-324): `generate_complete_recipe()` - Complex recipe generation scenarios and RAG fallback logic

### `visualization_agent_v2.py` (69% coverage)

**Uncovered Functions/Areas:**
- **Timeline Generation** (lines 40-71, 76): Timeline chart generation logic
- **Error Handling** (lines 643, 669, 696, 753-765, 770, 790-806, 810): Error paths for invalid recipe formats and visualization failures

---

## DailyDrip RAG (67% coverage)

### `src/index.py` (56% coverage)

**Uncovered Functions/Areas:**
- **Index Initialization** (lines 29-50, 53): `_populate_default_data()`, `_get_collection()` - Error handling for missing directories and empty collections

### `src/ingest.py` (59% coverage)

**Uncovered Functions/Areas:**
- **File Processing** (lines 65, 75, 91, 97-118, 121-140, 147-160, 167): `ingest_records()` - File reading error paths, malformed data handling, edge cases in record processing

### `src/query.py` (55% coverage)

**Uncovered Functions/Areas:**
- **Query Building** (lines 42-43): `_build_query_text()` - Edge cases for missing or malformed query data
- **Query Execution** (lines 107-206, 209): `_run_query()` - Reranking logic, metadata reconstruction, error handling for empty results
- **Extraction Helpers**: `_extract_brewing()`, `_extract_evaluation()` - Complex data extraction scenarios

### `src/service.py` (81% coverage)

**Uncovered Functions/Areas:**
- **Service Initialization** (lines 75, 78, 96-113): `_get_client()`, `_populate_default_data()` - Directory creation and initial data loading
- **Error Handling** (lines 121, 133-134, 147-148, 157, 210-211): FastAPI startup events and error response paths
- **Query Processing** (lines 313-315, 331, 352-367, 378-380, 389): `_run_query()` - Error paths and reranking edge cases

### `src/chunk.py` (95% coverage)

**Uncovered Functions/Areas:**
- **Text Chunking** (line 24): Edge case in `chunk_text()` or `_split_text_into_chunks()`

---

## Summary

**Priority Areas for Additional Testing:**
1. **Error Handling**: Exception handlers in API endpoints (brew, visualize, feedback)
2. **RAG Service Integration**: Service call failures, network errors, missing dependencies
3. **User Store Operations**: Persistence, loading, and locking mechanisms
4. **CLI Interface**: Command-line argument parsing and execution
5. **Complex Query Logic**: Reranking, metadata extraction, and edge cases in query processing
