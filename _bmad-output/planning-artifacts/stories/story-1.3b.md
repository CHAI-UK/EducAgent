# Story 1.3b: ECI Book Embedding Pipeline (Qdrant + Graph-Anchored Retrieval)

Status: done

---

## Story

As a **developer**,
I want the ECI textbook sections chunked by page, embedded with `text-embedding-3-small`, and stored in Qdrant with page-number metadata,
so that the `concept_retriever` node in LangGraph (Story 1.4) can fetch precise, section-scoped textbook passages for any concept query using Neo4j's existing `start_page`/`end_page` data on Section nodes.

---

## Acceptance Criteria

**Given** the chunker runs over `assets/ElementsOfCausalInference_sections/markdowns/`
**When** `chunk_all_sections()` is called
**Then** it returns a list of `PassageChunk` objects; each chunk has non-empty `content`, a valid `chapter` int, a `page_num` matching the global PDF page number, and a `section_heading` string (may be empty); no chunk has empty content

**Given** the ingestion script runs against a live Qdrant instance
**When** `python src/graph/eci_qdrant_ingester.py` completes
**Then** the `eci_passages` collection exists with vector size 1536 (cosine), point count equals total non-empty page chunks across all 13 chapter/appendix `.mmd` files; re-running the script produces the same count (idempotent)

**Given** the FastAPI backend starts with `QDRANT_HOST` and `QDRANT_PORT` set
**When** lifespan completes
**Then** `app.state.qdrant` holds a live `QdrantClient` and `GET /health` reflects Qdrant connectivity

**Given** `POST /api/v1/retrieve` is called with `{"concept_id": "d_separation", "query": "graphical criterion for independence", "top_k": 5}`
**When** the request is processed
**Then** it returns ≤5 passages filtered to pages within the `start_page`/`end_page` ranges of sections linked to `d_separation` via `COVERED_IN` edges in Neo4j; each passage contains `page_num`, `chapter`, `section_heading`, `content`, and `score`

**Given** `concept_id` has no `COVERED_IN` edges in Neo4j
**When** the retrieve endpoint is called
**Then** the search falls back to an unfiltered global vector search (no crash, returns top_k passages)

**Given** the full test suite ran before this story (32 passing tests)
**When** all code for this story is implemented
**Then** `conda run -n edu python -m pytest tests/ -v` reports all pre-existing 32 tests still passing plus new tests added in this story

---

## Tasks / Subtasks

### T1 — Infrastructure

- [x] T1.1 ~~`k8s/qdrant-deployment.yaml`~~ — **dropped**: Qdrant runs locally via on-disk path (`QDRANT_PATH`) or server mode; no Kubernetes manifests needed for current deployment
- [x] T1.2 Create `scripts/check_qdrant.py` — connects to Qdrant, lists collections, reports `eci_passages` point count; exits 1 on failure
- [x] T1.3 Add `qdrant_host`, `qdrant_port`, `qdrant_api_key` fields to `src/backend/settings.py`

### T2 — ECI Markdown Chunker

- [x] T2.1 `src/graph/eci_passage_chunker.py` — `PassageChunk` dataclass, `parse_toc_start_pages`, `_resolve_images`, `_get_tail_words`, `chunk_section`, `chunk_all_sections`; image-only page detection; prefix overlap (80 words)
- [x] T2.2 `tests/test_eci_passage_chunker.py` — page_num assignment, section_heading extraction, image-only skip, prefix overlap, image path/caption handling

### T3 — Qdrant Ingestion Script

- [x] T3.1 `src/graph/eci_qdrant_ingester.py` — idempotent collection creation, batch embed (50/call) using `content_for_embed`, MD5-based stable point IDs, upsert with `content` (absolute paths) in payload
- [x] T3.2 `qdrant-client>=1.17.0` present in `edu` env

### T4 — Backend: Settings + Qdrant Dependency

- [x] T4.1 `src/backend/settings.py` — added `qdrant_host`, `qdrant_port`, `qdrant_api_key`
- [x] T4.2 `src/backend/services/qdrant_client.py` — `get_qdrant(request)` dependency
- [x] T4.3 `src/backend/main.py` lifespan — Qdrant connect on startup, `close()` on shutdown

### T5 — Retrieval Service

- [x] T5.1 `src/backend/services/retrieval.py` — `PassageResult`, `concept_exists`, `get_section_page_ranges`, `embed_query`, `retrieve_passages`
  - **Note:** uses `qdrant.query_points(...)` (returns `response.points`) rather than the deprecated `qdrant.search()` specified in the original spec; both are functionally equivalent
- [x] T5.2 `tests/test_retrieval_service.py` — mocks `query_points` (not `search`); filtered path, fallback path, field population

### T6 — FastAPI Retrieve Endpoint

- [x] T6.1 `src/backend/routers/retrieve.py` — `POST /api/v1/retrieve`; 404 for unknown concept; `RetrieveRequest` / `RetrieveResponse`
- [x] T6.2 Router registered in `src/backend/main.py` with `prefix="/api/v1"`
- [x] T6.3 `tests/test_retrieve_router.py` — happy path, 404, top_k validation

### T7 — Regression Guard

- [x] T7.1 `conda run -n edu python -m pytest tests/ -v` — **61 passed** (32 pre-existing + 29 new)

### Bonus — Standalone Search Script

- [x] `scripts/qdrant_search.py` — CLI GraphRAG search tool (not in original spec); supports pure vector and graph-anchored modes; loads `eci_graph.json` directly (no FastAPI needed); useful for smoke-testing ingestion pipeline

---

## Dev Notes

### §1 — Existing Patterns to Follow

**Environment & test runner:**
```bash
conda run -n edu python -m pytest tests/ -v
conda run -n edu python src/graph/eci_qdrant_ingester.py
```
`pytest.ini` sets `pythonpath = src` — imports from `src/` work without install.

**Dependency injection** — replicate `neo4j_client.py` exactly for Qdrant (see T4.2). Always use `request.app.state.<service>` — never create clients inside request handlers.

**Settings** — `src/backend/settings.py` uses `pydantic-settings`. `OPENROUTER_API_KEY` is **already defined** in Settings from Story 1.2. Do not re-add it. Only add the three `QDRANT_*` fields.

**Router structure** — see `src/backend/routers/concepts.py` for reference. Register routers in `main.py` with `prefix="/api/v1"`. All routers use `APIRouter()`, not `FastAPI()`.

**Mock pattern for tests** — existing `tests/` mocks Neo4j driver via `app.dependency_overrides`. Extend the same pattern for Qdrant: override `get_qdrant` with a `MagicMock()`.

**DO NOT touch:**
- `src/backend/routers/concepts.py` — fulltext search endpoint is separate, leave it alone
- `src/graph/output/` — build artifacts, never write to this directory from new code
- `assets/` — read-only input; chunker reads, never writes

**Src layout after this story:**
```
src/
  backend/
    main.py               ← modified (Qdrant lifespan)
    settings.py           ← modified (add QDRANT_* fields)
    routers/
      concepts.py         ← DO NOT TOUCH
      health.py           ← DO NOT TOUCH
      query.py            ← DO NOT TOUCH
      chapters.py         ← DO NOT TOUCH
      retrieve.py         ← NEW
    services/
      neo4j_client.py     ← DO NOT TOUCH
      text2cypher.py      ← DO NOT TOUCH
      qdrant_client.py    ← NEW
      retrieval.py        ← NEW
  frontend/               ← moved from project root; run `npm run dev` from src/frontend/
  graph/
    eci_passage_chunker.py  ← NEW
    eci_qdrant_ingester.py  ← NEW
    (existing files untouched)
k8s/
  qdrant-deployment.yaml   ← NEW (new top-level dir)
scripts/
  check_qdrant.py          ← NEW (alongside existing split_pdf_by_bookmarks.py, parse_subject_index.py)
tests/
  test_eci_passage_chunker.py   ← NEW
  test_retrieval_service.py     ← NEW
  test_retrieve_router.py       ← NEW
```

---

### §2 — TOC Page Number Parsing

**File:** `assets/ElementsOfCausalInference_sections/markdowns/01_TOC/01_TOC.mmd`

The TOC gives the global PDF start page for every section. Use this to assign `page_num` to the first chunk of each chapter `.mmd` (before the first `<--- Page Split N --->` marker, which has no inline page number).

**TOC line format:**
```
1 Statistical and Causal Models 1       ← chapter
1.1 Probability Theory and Statistics 1 ← subsection
6.3 Interventions 88
Appendix A Some Probability and Statistics 213
A.1 Basic Definitions 213
```

**Parsing regex:**
```python
import re

# Regular chapters and subsections: "6.3 Interventions 88"
SECTION_RE = re.compile(r'^(\d+(?:\.\d+)?)\s+.+?\s+(\d+)\s*$')

# Appendix chapters: "Appendix A Some Probability... 213"
APPENDIX_CHAPTER_RE = re.compile(r'^Appendix\s+([A-C])\s+.+?\s+(\d+)\s*$')

# Appendix subsections: "A.1 Basic Definitions 213"
APPENDIX_SECTION_RE = re.compile(r'^([A-C]\.\d+)\s+.+?\s+(\d+)\s*$')
```

**Chapter → int mapping for appendices:**
- `A` → 11, `B` → 12, `C` → 13

**`parse_toc_start_pages` output** (chapter_num → start_page):
```python
{1: 1, 2: 15, 3: 33, 4: 43, 5: 71, 6: 81, 7: 135,
 8: 157, 9: 171, 10: 197, 11: 213, 12: 221, 13: 225}
```
(Derived directly from the TOC file already in the repo.)

---

### §3 — Chapter Directory Mapping

| Directory | chapter int |
|---|---|
| `04_Ch01_StatisticalAndCausalModels` | 1 |
| `05_Ch02_AssumptionsForCausalInference` | 2 |
| `06_Ch03_CauseEffectModels` | 3 |
| `07_Ch04_LearningCauseEffectModels` | 4 |
| `08_Ch05_ConnectionsToMachineLearning_I` | 5 |
| `09_Ch06_MultivariateCausalModels` | 6 |
| `10_Ch07_LearningMultivariateCausalModels` | 7 |
| `11_Ch08_ConnectionsToMachineLearning_II` | 8 |
| `12_Ch09_HiddenVariables` | 9 |
| `13_Ch10_TimeSeries` | 10 |
| `14_AppA_SomeProbabilityAndStatistics` | 11 |
| `15_AppB_CausalOrderingsAdjacencyMatrices` | 12 |
| `16_AppC_Proofs` | 13 |

**Skip** (no embeddable content): `00_FrontMatter`, `01_TOC`, `02_Preface`, `03_NotationAndTerminology`, `17_Bibliography`, `18_Index`

**Hardcode the mapping** as a module-level dict — don't try to parse directory names dynamically (fragile for appendix dirs).

---

### §4 — Retrieval: Page-Range Filter Strategy

The Neo4j `Section` nodes already have `start_page` and `end_page` (loaded by `eci_neo4j_importer.py`). This eliminates any need for a static `section_id → dir_name` lookup.

**Cypher for retrieval (T5.1b):**
```cypher
MATCH (c:Concept {concept_id: $concept_id})-[:COVERED_IN]->(s:Section)
RETURN s.start_page AS start_page, s.end_page AS end_page
```

**Qdrant filter construction:**
```python
from qdrant_client.models import Filter, FieldCondition, Range

# Each (start, end) range from Neo4j becomes a `should` condition
qdrant_filter = Filter(
    should=[
        FieldCondition(key="page_num", range=Range(gte=start, lte=end))
        for start, end in page_ranges
    ]
) if page_ranges else None
# None → unfiltered global search (fallback for concepts with no COVERED_IN edges)
```

**Qdrant payload schema** (stored per point):
```python
{
    "chapter": int,          # 1–13
    "page_num": int,          # global PDF page number (with prefix overlap baked into content)
    "section_heading": str,   # nearest ## heading (may be "")
    "content": str,           # full markdown; image tags use absolute paths (frontend-renderable)
                              # e.g. ![](assets/ElementsOfCausalInference_sections/markdowns/05_Ch02_.../images/4_0.jpg)
                              # NOT stored: content_for_embed — only used at ingestion time for the embedding API
}
```

**Alias note (future improvement):** 14 `RELATED_TO_ALIAS` edges exist. If a concept is an alias of another, its source sections are identical. Extending the Cypher to follow one RELATED_TO_ALIAS hop would broaden coverage with no false positives — leave as a TODO comment in the retrieval service.

---

### §5 — Kubernetes Manifest (WRITE; human deploys)

**File:** `k8s/qdrant-deployment.yaml`

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: qdrant
  labels:
    app: qdrant
spec:
  replicas: 1
  selector:
    matchLabels:
      app: qdrant
  template:
    metadata:
      labels:
        app: qdrant
    spec:
      containers:
      - name: qdrant
        image: qdrant/qdrant:v1.12.6
        ports:
        - containerPort: 6333
        volumeMounts:
        - name: qdrant-storage
          mountPath: /qdrant/storage
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "2Gi"
            cpu: "1"
      volumes:
      - name: qdrant-storage
        emptyDir: {}    # Replace with PVC for persistence
---
apiVersion: v1
kind: Service
metadata:
  name: qdrant-service
spec:
  selector:
    app: qdrant
  ports:
  - name: http
    port: 6333
    targetPort: 6333
  type: ClusterIP
```

**Human deployment commands** (run after dev agent writes the manifest):
```bash
kubectl apply -f k8s/qdrant-deployment.yaml
kubectl rollout status deployment/qdrant

# Port-forward to run ingestion locally
kubectl port-forward svc/qdrant-service 6333:6333 &

# Verify
python scripts/check_qdrant.py

# Run ingestion (needs OPENROUTER_API_KEY in env)
QDRANT_HOST=localhost QDRANT_PORT=6333 \
  OPENROUTER_API_KEY=<your-key> \
  conda run -n edu python src/graph/eci_qdrant_ingester.py

# Verify collection
curl http://localhost:6333/collections/eci_passages

# Set QDRANT_HOST=qdrant-service in backend .env when backend runs in-cluster
```

> ⚠️ `emptyDir` is ephemeral — embeddings are lost on pod restart. Replace with a `PersistentVolumeClaim` to avoid re-ingesting. Re-ingestion is safe (idempotent via stable MD5 IDs) but takes time and API calls.

---

### §6 — Qdrant Client API Reference (v1.17.0)

```python
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams,
    PointStruct,
    Filter, FieldCondition, Range,
)

client = QdrantClient(host="localhost", port=6333)

# Idempotent collection creation
if not client.collection_exists("eci_passages"):
    client.create_collection(
        collection_name="eci_passages",
        vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
    )

# Upsert
client.upsert(
    collection_name="eci_passages",
    points=[PointStruct(id=<int>, vector=[...], payload={...})],
)

# Filtered search
results = client.search(
    collection_name="eci_passages",
    query_vector=query_embedding,
    query_filter=qdrant_filter,   # None for unfiltered
    limit=top_k,
)
# result.score, result.payload["content"], result.payload["page_num"]
```

---

### §7 — OpenRouter Embedding (openai SDK pattern)

`OPENROUTER_API_KEY` is **already** in `src/backend/settings.py` (added in Story 1.2, env var `OPENROUTER_API_KEY`). Use `settings.openrouter_api_key` in the retrieval service — do not add a new settings field.

```python
from openai import OpenAI

def _make_embed_client(api_key: str) -> OpenAI:
    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )

# Fallback: if OpenRouter rejects embedding model, use OpenAI directly:
# OpenAI(base_url="https://api.openai.com/v1", api_key=os.environ["OPENAI_API_KEY"])
```

Model: `"openai/text-embedding-3-small"` → 1536 dimensions. Matches Qdrant collection and Neo4j `concept_embedding` stub exactly.

---

### §9 — Chunking Strategy: Prefix Overlap + Two-Field Image Handling

#### Prefix overlap (80 words)

Each chunk for page N is prefixed with the last ~80 words of page N-1's **raw text** (before image resolution). This prevents context loss at page boundaries — critical for a math textbook where definitions and proofs routinely span page breaks.

- `page_num` tag remains the primary page (unambiguous for the Range filter)
- The overlap is baked into `content` and `content_for_embed` transparently
- 80 words ≈ 3–5 sentences ≈ ~120 tokens — negligible embedding cost, high boundary-context benefit
- The first page of each chapter has no prefix (nothing to prepend)

```
page 88 chunk = [last 80 words of page 87] + "\n\n" + [page 88 content]
                 ─── context prefix ────                ─── primary ────
page_num = 88   ← filter still correct
```

#### Two-field image handling

The `.mmd` files contain relative image tags: `![](images/4_0.jpg)`. These are:
- **Meaningless to `text-embedding-3-small`** — the model cannot see images and gets no value from the filename string
- **Ambiguous for display** — `images/4_0.jpg` is relative to its chapter directory; once the content is stored in Qdrant it has no directory context

Two fields solve both problems independently:

| Field | Transformation | Purpose |
|---|---|---|
| `content` | `![](images/4_0.jpg)` → `![](assets/.../05_Ch02_.../images/4_0.jpg)` | Frontend rendering — absolute path always resolves |
| `content_for_embed` | `![](images/4_0.jpg)\nFigure 1.1: ...` → `[Figure: Figure 1.1: ...]` | Embedding API — semantic signal from caption, not filename |

**Caption extraction regex** (applied in `_resolve_images`):
```python
import re

IMG_RE = re.compile(r'!\[([^\]]*)\]\(images/([^)]+)\)')
CAPTION_RE = re.compile(r'^(Figure\s[\d.]+[:\s].+)$', re.MULTILINE)

def _resolve_images(text: str, images_dir: Path) -> tuple[str, str]:
    dir_name = images_dir.parent.name  # e.g. "05_Ch02_AssumptionsForCausalInference"
    abs_prefix = f"assets/ElementsOfCausalInference_sections/markdowns/{dir_name}/images/"

    content = IMG_RE.sub(lambda m: f"![{m.group(1)}]({abs_prefix}{m.group(2)})", text)

    def replace_for_embed(text_block: str) -> str:
        # Replace each image tag + optional following caption line
        lines = text_block.split("\n")
        result, skip_next = [], False
        for i, line in enumerate(lines):
            if skip_next:
                skip_next = False
                continue
            m = IMG_RE.match(line.strip())
            if m:
                # Look ahead for caption
                next_line = lines[i + 1].strip() if i + 1 < len(lines) else ""
                cap_m = CAPTION_RE.match(next_line)
                if cap_m:
                    result.append(f"[Figure: {cap_m.group(1)}]")
                    skip_next = True
                else:
                    result.append("[Figure]")
            else:
                result.append(line)
        return "\n".join(result)

    content_for_embed = replace_for_embed(text)
    return content, content_for_embed
```

**Image-only page detection** (skip at T2.1e):
A page is "image-only" if after replacing all image tags with `[Figure...]`, the remaining text is empty or only punctuation/whitespace. Skip these from the output — they embed poorly and add noise.

---

### §8 — Frontend Path Change (Story 1.3 follow-up)

`frontend/` has been moved to `src/frontend/`. Update any scripts or docs that reference `frontend/`:
- `.gitignore` already updated (`src/frontend/__tests__/*` etc.)
- Run dev server: `cd src/frontend && npm run dev` (was `cd frontend && npm run dev`)
- Story 1.3's file list is historical — the move is tracked in git history

---

### References

- Architecture §1 "Planned Graph Enhancements" (Qdrant + embeddings spec): [`_bmad-output/planning-artifacts/architecture.md`](_bmad-output/planning-artifacts/architecture.md)
- Architecture §2 LLM Routing (`text-embedding-3-small`): same file
- Graph schema (Section `start_page`/`end_page`): same file, Component 1 §Graph Schema
- Neo4j importer (Section node fields, `concept_embedding` stub): [`src/graph/eci_neo4j_importer.py`](src/graph/eci_neo4j_importer.py)
- Existing dependency pattern: [`src/backend/services/neo4j_client.py`](src/backend/services/neo4j_client.py)
- TOC with exact page numbers: [`assets/ElementsOfCausalInference_sections/markdowns/01_TOC/01_TOC.mmd`](assets/ElementsOfCausalInference_sections/markdowns/01_TOC/01_TOC.mmd)
- Story 1.2 (settings, OPENROUTER_API_KEY, COVERED_IN edges): [`_bmad-output/planning-artifacts/stories/story-1.2.md`](_bmad-output/planning-artifacts/stories/story-1.2.md)
- Story 1.4 (LangGraph consumer — concept_retriever): [`_bmad-output/planning-artifacts/stories/story-1.4.md`](_bmad-output/planning-artifacts/stories/story-1.4.md)
- qdrant-client v1.17.0: [https://pypi.org/project/qdrant-client/](https://pypi.org/project/qdrant-client/)

---

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

### Completion Notes List

- T1.1 (`k8s/qdrant-deployment.yaml`) dropped — Qdrant runs via on-disk path or server mode; no k8s manifests required
- T5.1d: implementation uses `qdrant.query_points()` (modern API returning `response.points`) instead of the deprecated `qdrant.search()` called for in the spec; tests updated to match
- `conftest.py` `mock_qdrant` fixture updated: `query_points.return_value = MagicMock(points=[])` instead of `search.return_value = []`
- Final test count: 61 passed (32 pre-existing + 29 new)

### File List

- `scripts/check_qdrant.py` (new)
- `scripts/qdrant_search.py` (new — bonus standalone CLI tool)
- `src/backend/settings.py` (modified)
- `src/backend/main.py` (modified)
- `src/backend/services/qdrant_client.py` (new)
- `src/backend/services/retrieval.py` (new)
- `src/backend/routers/retrieve.py` (new)
- `src/graph/eci_passage_chunker.py` (new)
- `src/graph/eci_qdrant_ingester.py` (new)
- `tests/conftest.py` (modified)
- `tests/test_eci_passage_chunker.py` (new)
- `tests/test_retrieval_service.py` (new)
- `tests/test_retrieve_router.py` (new)
