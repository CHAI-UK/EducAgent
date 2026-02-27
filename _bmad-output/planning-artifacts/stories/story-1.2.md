---
story_id: '1.2'
status: 'done'
epic: 'Epic 1: Causality Concept Graph & Project Foundation'
source: '_bmad-output/planning-artifacts/epics.md'
updated: '2026-02-27'
update_reason: 'Revised to Neo4j + GraphRAG best practices (template retrievers + text2Cypher), replacing original NetworkX in-memory approach'
---

### Story 1.2: Neo4j Graph Backend + GraphRAG API

As a **developer**,
I want a FastAPI backend that imports the ECI knowledge graph into Neo4j at first run and exposes both template Cypher retrievers and a text2Cypher endpoint,
So that the tutor agent can query prerequisites, chapter concepts, and ask ad-hoc natural-language questions against the graph with production-grade reliability.

---

## Background & Design Decisions

The original story spec proposed loading `eci_graph.pkl` (NetworkX) into memory at startup.
Updated to follow GraphRAG best practices (per *Essential GraphRAG*, Manning 2025):

1. **Neo4j as primary graph store** — replaces the NetworkX in-memory approach.
   - Graph (189 nodes, 332 edges) fits on AuraDB Free or local Docker.
   - Cypher traversal handles prerequisite chains and chapter filtering natively.
   - Migration path: `eci_graph.json` (already produced by Story 1.1) → Neo4j via `MERGE` (idempotent, re-runnable).

2. **Template retrievers over text2Cypher for known patterns** — GraphRAG best practice: hardcode fast, reliable Cypher for high-frequency, well-understood queries; use text2Cypher only for ad-hoc or novel queries.

3. **Text2Cypher for agent ad-hoc queries** — schema-in-prompt + causal-inference terminology mapping + few-shot examples guard against LLM misinterpretation of the ECI schema.

4. **Fulltext index on Concept names** — enables fast keyword lookup and will support hybrid search once embeddings are added (Epic 2, Qdrant).

5. **Vector index stub on Concept nodes** — created now so the schema is ready when `text-embedding-3-small` embeddings are added. No embeddings yet (deferred to Epic 2 text-chunk ingestion pipeline).

6. **Uniqueness constraints** — `CREATE CONSTRAINT IF NOT EXISTS` ensures re-import is safe and query performance is fast.

---

## Neo4j Setup

**Development (Docker):**
```bash
docker run \
  -p 7474:7474 -p 7687:7687 \
  -d \
  -v $HOME/neo4j/data:/data \
  -e NEO4J_AUTH=neo4j/educagent \
  -e 'NEO4J_PLUGINS=["apoc"]' \
  neo4j:5.26.0
# Browser: http://localhost:7474  |  Bolt: bolt://localhost:7687
```

**Cloud (AuraDB Free Tier):** Suitable for demos; no local Docker required.

**Required plugin:** APOC (schema inference, used by text2Cypher schema query).

**Environment variables (`.env`):**
```
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=educagent
OPENROUTER_API_KEY=...
```

---

## Graph Import Pipeline

**Script:** `src/graph/eci_neo4j_importer.py`

**Source:** `src/graph/output/eci_graph.json` (produced by Story 1.1's `eci_graph_builder.py`).

### Step 1: Constraints (run once, idempotent)

```cypher
-- Section keyed by node_id (the "sec_1" style id used by edges, not the "1.1" section_id)
CREATE CONSTRAINT IF NOT EXISTS FOR (s:Section)  REQUIRE s.node_id IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (c:Category) REQUIRE c.name IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (c:Concept)  REQUIRE c.concept_id IS UNIQUE;
```

### Step 2: Indexes

```cypher
-- Fulltext index for concept name lookup and future hybrid search
CREATE FULLTEXT INDEX concept_fulltext IF NOT EXISTS
  FOR (c:Concept) ON EACH [c.name, c.concept_id];

-- Vector index stub (dimensions set for text-embedding-3-small; no embeddings yet)
CREATE VECTOR INDEX concept_embedding IF NOT EXISTS
  FOR (c:Concept) ON (c.embedding)
  OPTIONS {indexConfig: {`vector.dimensions`: 1536, `vector.similarity_function`: 'cosine'}};
```

### Step 3: Node import (MERGE — idempotent)

```python
# Section nodes
MERGE (s:Section {section_id: $section_id})
SET s.label = $label, s.chapter = $chapter,
    s.depth = $depth, s.start_page = $start_page, s.end_page = $end_page

# Category nodes
MERGE (c:Category {name: $name})

# Concept nodes
MERGE (c:Concept {concept_id: $concept_id})
SET c.name = $name, c.chapter = $chapter,
    c.page_refs = $page_refs, c.difficulty = $difficulty,
    c.misconceptions = $misconceptions
```

### Step 4: Edge import (MERGE — idempotent)

```cypher
-- NEXT_IN_SEQUENCE  (Section → Section) — matched by node_id, not section_id
MATCH (a:Section {node_id: $from}), (b:Section {node_id: $to})
MERGE (a)-[:NEXT_IN_SEQUENCE]->(b)

-- COVERED_IN  (Concept → Section) — Section matched by node_id
MATCH (c:Concept {concept_id: $concept}), (s:Section {node_id: $section})
MERGE (c)-[:COVERED_IN]->(s)

-- SUBTOPIC_OF  (Concept → Category)
MATCH (c:Concept {concept_id: $concept}), (cat:Category {name: $category})
MERGE (c)-[:SUBTOPIC_OF]->(cat)

-- RELATED_TO_SEE_ALSO  (Concept ↔ Concept)
MATCH (a:Concept {concept_id: $from}), (b:Concept {concept_id: $to})
MERGE (a)-[:RELATED_TO_SEE_ALSO]->(b)

-- PREREQUISITE_OF  (Concept → Concept)
MATCH (a:Concept {concept_id: $from}), (b:Concept {concept_id: $to})
MERGE (a)-[:PREREQUISITE_OF]->(b)

-- COMMONLY_CONFUSED  (Concept ↔ Concept)
MATCH (a:Concept {concept_id: $from}), (b:Concept {concept_id: $to})
MERGE (a)-[:COMMONLY_CONFUSED]-(b)
```

**Run:** `python src/graph/eci_neo4j_importer.py` (or `make import-graph`) — safe to re-run; MERGE is idempotent.

---

## FastAPI Application

**File:** `backend/main.py`

### Startup / lifespan

```python
from neo4j import GraphDatabase
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.neo4j = GraphDatabase.driver(
        settings.NEO4J_URI,
        auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
    )
    app.state.neo4j.verify_connectivity()
    yield
    app.state.neo4j.close()

app = FastAPI(lifespan=lifespan)
```

### CORS

```python
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js dev origin
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## API Endpoints

### Template Retrievers (hardcoded Cypher — fastest, most reliable)

These cover all high-frequency query patterns identified from the ECI graph use cases.

#### `GET /api/v1/concepts/{concept_id}/prerequisites`
Returns direct prerequisite concepts (PREREQUISITE_OF predecessors).

```cypher
MATCH (prereq:Concept)-[:PREREQUISITE_OF]->(c:Concept {concept_id: $concept_id})
RETURN prereq.concept_id AS concept_id, prereq.name AS name,
       prereq.chapter AS chapter, prereq.difficulty AS difficulty
ORDER BY prereq.chapter
```

#### `GET /api/v1/concepts/{concept_id}/next-concepts`
Returns concepts that depend on this concept (PREREQUISITE_OF successors).

```cypher
MATCH (c:Concept {concept_id: $concept_id})-[:PREREQUISITE_OF]->(next:Concept)
RETURN next.concept_id AS concept_id, next.name AS name,
       next.chapter AS chapter, next.difficulty AS difficulty
ORDER BY next.chapter
```

#### `GET /api/v1/concepts/{concept_id}/related`
Returns see-also and commonly-confused neighbors.

```cypher
MATCH (c:Concept {concept_id: $concept_id})-[r:RELATED_TO_SEE_ALSO|COMMONLY_CONFUSED]-(related:Concept)
RETURN related.concept_id AS concept_id, related.name AS name,
       type(r) AS relation_type
```

#### `GET /api/v1/concepts/{concept_id}/sections`
Returns the textbook sections that cover this concept.

```cypher
MATCH (c:Concept {concept_id: $concept_id})-[:COVERED_IN]->(s:Section)
RETURN s.section_id AS section_id, s.label AS label,
       s.chapter AS chapter, s.start_page AS start_page, s.end_page AS end_page
ORDER BY s.chapter, s.depth
```

#### `GET /api/v1/chapters/{chapter}/concepts`
Returns all concepts covered in a given chapter.

```cypher
MATCH (c:Concept {chapter: $chapter})
RETURN c.concept_id AS concept_id, c.name AS name,
       c.difficulty AS difficulty, c.page_refs AS page_refs
ORDER BY c.concept_id
```

#### `GET /api/v1/concepts/search?q={query}&limit=10`
Fulltext search on concept name and concept_id.

```cypher
CALL db.index.fulltext.queryNodes('concept_fulltext', $query, {limit: $limit})
YIELD node, score
RETURN node.concept_id AS concept_id, node.name AS name,
       node.chapter AS chapter, score
ORDER BY score DESC
```

#### `GET /api/v1/concepts/{concept_id}`
Single concept detail with all properties.

```cypher
MATCH (c:Concept {concept_id: $concept_id})
RETURN c.concept_id AS concept_id, c.name AS name,
       c.chapter AS chapter, c.difficulty AS difficulty,
       c.page_refs AS page_refs, c.misconceptions AS misconceptions
```

---

### Text2Cypher Endpoint (ad-hoc agent queries)

**`POST /api/v1/query`**

For use by the LangGraph tutor agent when template retrievers don't cover the question.
Follows GraphRAG best practice: schema-in-prompt + terminology mapping + few-shot examples.

**Request body:**
```json
{"question": "Which concepts share a chapter with d-separation?"}
```

**Response body:**
```json
{
  "cypher": "MATCH (c:Concept {concept_id: 'd_separation'}) ...",
  "results": [...],
  "question": "Which concepts share a chapter with d-separation?"
}
```

**Implementation pattern:**

```python
ECI_SCHEMA = """
Node labels and properties:
  Concept  {concept_id: STRING, name: STRING, chapter: INTEGER,
            difficulty: INTEGER, page_refs: LIST, misconceptions: LIST}
  Section  {section_id: STRING, label: STRING, chapter: INTEGER,
            depth: INTEGER, start_page: INTEGER, end_page: INTEGER}
  Category {name: STRING}

Relationship types:
  PREREQUISITE_OF   (no properties)
  COVERED_IN        (no properties)
  SUBTOPIC_OF       (no properties)
  RELATED_TO_SEE_ALSO (no properties)
  COMMONLY_CONFUSED (no properties)
  NEXT_IN_SEQUENCE  (no properties)

The relationships:
  (:Concept)-[:PREREQUISITE_OF]->(:Concept)
  (:Concept)-[:COVERED_IN]->(:Section)
  (:Concept)-[:SUBTOPIC_OF]->(:Category)
  (:Concept)-[:RELATED_TO_SEE_ALSO]->(:Concept)
  (:Concept)-[:COMMONLY_CONFUSED]-(:Concept)
  (:Section)-[:NEXT_IN_SEQUENCE]->(:Section)
"""

ECI_TERMINOLOGY = """
TERMINOLOGY MAPPING (causal inference domain):
- "concept" or "topic" → node with label Concept
- "section" or "chapter subsection" → node with label Section
- "prerequisite" or "required concept" or "must know first" → follow PREREQUISITE_OF edges backwards
  (i.e., MATCH (:Concept)-[:PREREQUISITE_OF]->(target))
- "next concept" or "what to learn after" or "depends on" → follow PREREQUISITE_OF edges forwards
- "textbook section" or "covered in" or "appears in" → follow COVERED_IN edges
- "commonly confused with" or "often mixed up" → follow COMMONLY_CONFUSED edges
- "related to" or "see also" → follow RELATED_TO_SEE_ALSO edges
- concept_id values are slugified: use underscores (e.g., "d_separation", "backdoor_criterion")
"""

ECI_FEW_SHOT = """
Question: What are the prerequisites of d-separation?
Cypher: MATCH (prereq:Concept)-[:PREREQUISITE_OF]->(c:Concept {concept_id: 'd_separation'}) RETURN prereq.concept_id, prereq.name

Question: Which concepts are in chapter 6?
Cypher: MATCH (c:Concept {chapter: 6}) RETURN c.concept_id, c.name ORDER BY c.concept_id

Question: What should I learn after mastering conditional independence?
Cypher: MATCH (c:Concept {concept_id: 'conditional_independence'})-[:PREREQUISITE_OF]->(next:Concept) RETURN next.concept_id, next.name

Question: Which concepts are commonly confused with counterfactuals?
Cypher: MATCH (c:Concept {concept_id: 'counterfactuals'})-[:COMMONLY_CONFUSED]-(other:Concept) RETURN other.concept_id, other.name
"""
```

**Prompt template:**
```python
TEXT2CYPHER_PROMPT = """
Instructions:
Generate a Cypher statement to query the ECI knowledge graph to answer the following question.
Use ONLY the provided relationship types and properties. Do not use any others.
ONLY RESPOND WITH CYPHER — NO CODE BLOCKS, NO EXPLANATIONS.

Graph database schema:
{schema}

{terminology}

Examples:
{examples}

User question: {question}
"""
```

**Safety:** Wrap execution in a try/except; return HTTP 422 with error message on Cypher syntax failure. Do not expose raw Neo4j exceptions to clients.

---

### Health Check

#### `GET /health`

Returns Neo4j connectivity status and graph statistics.

```cypher
MATCH (n) RETURN labels(n)[0] AS label, count(n) AS count
UNION ALL
MATCH ()-[r]->() RETURN type(r) AS label, count(r) AS count
```

Response:
```json
{
  "status": "ok",
  "neo4j": "connected",
  "graph": {
    "nodes": {"Concept": 101, "Section": 79, "Category": 9},
    "edges": {
      "PREREQUISITE_OF": 29, "COVERED_IN": 140, "NEXT_IN_SEQUENCE": 78,
      "SUBTOPIC_OF": 34, "RELATED_TO_SEE_ALSO": 22,
      "RELATED_TO_ALIAS": 14, "COMMONLY_CONFUSED": 15
    }
  }
}
```

---

## Acceptance Criteria

**Given** Neo4j is running and `NEO4J_URI` is set
**When** `python src/graph/eci_neo4j_importer.py` (or `make import-graph`) is run
**Then** it imports 189 nodes (101 Concept, 79 Section, 9 Category) and 332 edges without errors ✓

**Given** the importer is run a second time
**When** it completes
**Then** node/edge counts remain 189 / 332 (MERGE is idempotent — no duplicates) ✓

**Given** the FastAPI app starts
**When** startup completes
**Then** the Neo4j driver is connected and `/health` returns HTTP 200 with `"status": "ok"` and correct node/edge counts ✓

**Given** the API is running
**When** `GET /api/v1/concepts/d_separation/prerequisites` is called
**Then** it returns `conditional_independence` and `directed_acyclic_graph_dag` ✓

**Given** the API is running
**When** `GET /api/v1/chapters/6/concepts` is called
**Then** it returns 23 concept nodes (chapter 6: Multivariate Causal Models) ✓

**Given** the API is running
**When** `GET /api/v1/concepts/causal_learning/next-concepts` is called
**Then** it returns `pc_algorithm` and `greedy_equivalence_search_ges` ✓

**Given** the API is running
**When** `GET /api/v1/concepts/search?q=causal` is called
**Then** it returns a ranked list of concepts whose name or concept_id contains "causal" ✓

**Given** the API is running
**When** `POST /api/v1/query` is called with `{"question": "What are the prerequisites of d-separation?"}`
**Then** it returns a Cypher query and results containing `conditional_independence` and `directed_acyclic_graph_dag` ✓

**Given** `POST /api/v1/query` is called with an unanswerable or malformed question
**When** Neo4j returns an error
**Then** the API returns HTTP 422 with a user-friendly error message (no raw Neo4j stack trace) ✓

**Given** `POST /api/v1/query` is called but the LLM API is unavailable or `OPENROUTER_API_KEY` is not set
**When** `generate_cypher()` raises an exception
**Then** the API returns HTTP 503 with a "LLM service error" message ✓

**Given** `POST /api/v1/query` is called but `OPENROUTER_API_KEY` is empty
**When** `generate_cypher()` is invoked
**Then** a `ValueError` is raised with a message directing the user to set the env var ✓

**Given** any request is made
**Then** all responses include proper CORS headers for `http://localhost:3000` ✓

---

## File Layout

Note: all source code lives under `src/` (Python src-layout). `PYTHONPATH=src` is set via `pytest.ini` for tests and the `Makefile` for uvicorn.

```
src/
├── backend/
│   ├── main.py               # FastAPI app, lifespan, CORS, router includes
│   ├── settings.py           # pydantic-settings: NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, OPENROUTER_API_KEY, CORS_ORIGINS
│   ├── routers/
│   │   ├── concepts.py       # Template retriever endpoints for /concepts/*
│   │   ├── chapters.py       # Template retriever endpoint for /chapters/*
│   │   ├── health.py         # GET /health
│   │   └── query.py          # text2Cypher endpoint /query (503 on LLM error, 422 on Cypher error)
│   └── services/
│       ├── neo4j_client.py   # driver wrapper + execute_query helper
│       └── text2cypher.py    # prompt assembly, lazy singleton OpenAI client, LLM call
└── graph/
    ├── eci_neo4j_importer.py # One-time import: eci_graph.json → Neo4j
    └── output/
        └── eci_graph.json    # 189 nodes, 332 edges

Makefile                      # make serve / make test / make import-graph
pytest.ini                    # pythonpath = src
```

---

## Tasks / Subtasks

- [x] T1: Neo4j graph import pipeline
  - [x] T1.1 Create `graph/eci_neo4j_importer.py` — read `graph/output/eci_graph.json`, create constraints + indexes, MERGE all nodes and edges
  - [x] T1.2 Verify import: 189 nodes (101 Concept, 79 Section, 9 Category) and 332 edges, idempotent on re-run
- [x] T2: FastAPI app scaffold
  - [x] T2.1 `backend/settings.py` — pydantic-settings with NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, OPENROUTER_API_KEY
  - [x] T2.2 `backend/services/neo4j_client.py` — driver wrapper with `execute_query` helper
  - [x] T2.3 `backend/main.py` — lifespan (connect/disconnect Neo4j), CORS for localhost:3000, router includes
- [x] T3: Template retriever endpoints (`backend/routers/concepts.py`, `backend/routers/chapters.py`)
  - [x] T3.1 `GET /api/v1/concepts/{concept_id}/prerequisites`
  - [x] T3.2 `GET /api/v1/concepts/{concept_id}/next-concepts`
  - [x] T3.3 `GET /api/v1/concepts/{concept_id}/related`
  - [x] T3.4 `GET /api/v1/concepts/{concept_id}/sections`
  - [x] T3.5 `GET /api/v1/concepts/search?q={query}&limit=10`
  - [x] T3.6 `GET /api/v1/concepts/{concept_id}` (single concept detail)
  - [x] T3.7 `GET /api/v1/chapters/{chapter}/concepts`
- [x] T4: Text2Cypher endpoint
  - [x] T4.1 `backend/services/text2cypher.py` — ECI_SCHEMA, ECI_TERMINOLOGY, ECI_FEW_SHOT, prompt assembly, OpenAI call
  - [x] T4.2 `backend/routers/query.py` — `POST /api/v1/query` with error handling (HTTP 422 on Cypher failure)
- [x] T5: Health endpoint — `GET /health` returns Neo4j status + node/edge counts
- [x] T6: Tests
  - [x] T6.1 `tests/conftest.py` — mock neo4j driver fixture
  - [x] T6.2 `tests/test_concepts.py` — endpoint tests for all concept routes (mock driver)
  - [x] T6.3 `tests/test_chapters.py` — chapter concepts endpoint test
  - [x] T6.4 `tests/test_health.py` — health endpoint test
  - [x] T6.5 `tests/test_query.py` — text2Cypher endpoint test (mock LLM + driver)
  - [x] T6.6 `tests/test_importer.py` — importer unit tests (mock driver)

---

## Dev Agent Record

### Implementation Plan

- JSON graph source: `graph/output/eci_graph.json` — keys: `nodes` (189), `edges` (332)
- Section nodes: `id`="sec_1", `section_id`="1"; Concept nodes: `id`="adjustment" (= concept_id); Category: `id`="entropy" (= name)
- Edge `source`/`target` reference node `id` field
- All tests use `unittest.mock.patch` on the neo4j driver — no live Neo4j required for test suite
- Text2Cypher uses `openai` client (OpenRouter-compatible base URL) with schema+terminology+few-shot prompt

### Debug Log

- Fixed naming collision in `/concepts/search`: renamed Cypher param `$query` → `$search_term` to avoid conflict with `execute_query(driver, query, **params)` function signature.
- Discovered `eci_graph.json` uses `edges` key (not `links`) — updated importer accordingly.
- Section nodes have two ID fields: `id` ("sec_1" style, used by edges) and `section_id` ("1.1" style, human-readable). Importer stores both as `node_id` and `section_id` properties.

### Completion Notes

All 32 tests passing (8 importer + 5 health/settings + 14 concept/chapter + 5 query).
All acceptance criteria satisfied. Full test suite uses mock Neo4j driver — no live DB required.
AuraDB connected and tested successfully — `python src/graph/eci_neo4j_importer.py` loads 189 nodes + 332 edges.
Code review fixes applied: H1 (LLM try/except), M1 (singleton client), M2 (API key guard), M3 (test mock key corrected). Tests now 34/34 passing.

---

## File List

Note: all source files moved to `src/` layout during implementation.

- `src/graph/__init__.py` (new)
- `src/graph/eci_neo4j_importer.py` (new — Neo4j import pipeline)
- `src/backend/__init__.py` (new)
- `src/backend/main.py` (new — FastAPI app, lifespan, CORS configurable via CORS_ORIGINS)
- `src/backend/settings.py` (new — pydantic-settings + CORS_ORIGINS)
- `src/backend/routers/__init__.py` (new)
- `src/backend/routers/health.py` (new — GET /health)
- `src/backend/routers/concepts.py` (new — 6 concept endpoints)
- `src/backend/routers/chapters.py` (new — GET /chapters/{chapter}/concepts)
- `src/backend/routers/query.py` (updated — 503 for LLM errors, 422 for Cypher errors)
- `src/backend/services/__init__.py` (new)
- `src/backend/services/neo4j_client.py` (new — driver wrapper + dependency)
- `src/backend/services/text2cypher.py` (updated — lazy singleton client, API key guard)
- `tests/__init__.py` (new)
- `tests/conftest.py` (new — mock driver + TestClient fixture)
- `tests/test_importer.py` (new — 8 tests)
- `tests/test_health.py` (updated — mock key fixed to "cnt")
- `tests/test_concepts.py` (new — 11 tests)
- `tests/test_chapters.py` (new — 3 tests)
- `tests/test_query.py` (updated — 7 tests including 503 and API key guard tests)
- `pytest.ini` (new — pythonpath = src)
- `Makefile` (new — serve / test / import-graph targets)
- `README.md` (new — k8s + AuraDB setup guide)
- `.env.example` (new)
- `.gitignore` (updated — .env, *.pkl)
- `_bmad-output/planning-artifacts/stories/story-1.2.md` (updated — tasks, dev record, status)

---

## Change Log

- 2026-02-27: Story created with Neo4j + GraphRAG spec; status set to in-progress
- 2026-02-27: All tasks implemented; 32/32 tests passing; status set to review
- 2026-02-27: Code review — 4 HIGH + 4 MEDIUM + 3 LOW issues found and resolved; src/ layout applied; AuraDB connected and verified; 34/34 tests passing; status set to done

---

## Future Enhancements (out of scope for this story)

- **Concept embeddings + hybrid search**: When text chunks are ingested (Epic 2), embed Concept names with `text-embedding-3-small`, store on `c.embedding`, and activate the vector index created in this story. Add hybrid endpoint combining `db.index.vector.queryNodes` + `db.index.fulltext.queryNodes` with RRF score normalization.
- **Agentic retriever router**: Story 1.4 (LangGraph) will register template retrievers and the text2Cypher endpoint as tools in the LangGraph agent tool registry.
- **Few-shot example expansion**: As the tutor agent uses text2Cypher in production and discovers failure patterns, add examples to `ECI_FEW_SHOT` incrementally.

---
