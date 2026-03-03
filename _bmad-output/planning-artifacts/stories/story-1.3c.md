# Story 1.3c: Interactive Knowledge Graph View (EgoGraph + AI Explanation Panel)

Status: done

---

## Story

As a **learner**,
I want an interactive `/graph` page where I can search for a causal concept, see its 1-hop ego-graph, and click any node to stream an AI explanation sourced from the textbook,
So that I can visually explore the ECI knowledge graph and understand how concepts relate to each other.

---

## Acceptance Criteria

**Given** the user navigates to `/graph`
**When** they type at least 2 characters in the search bar
**Then** a debounced dropdown appears with matching concepts (chapter shown); selecting one loads the ego-graph

**Given** an ego-graph is loaded
**When** it renders
**Then** the center concept is shown in bright gold, neighboring Concept nodes in gold, Section nodes in blue; edges are coloured by relationship type

**Given** the user clicks a gold (Concept) neighbor node
**When** the click fires
**Then** the graph reloads centered on that concept and the ExplainPanel opens, making the graph fully navigable without the search bar

**Given** the ExplainPanel is open
**When** the AI explanation streams in
**Then** inline LaTeX delimiters `\( ... \)` and `\[ ... \]` are rendered via KaTeX; a blinking cursor shows while streaming

**Given** streaming completes
**When** source passages arrive via the `event: sources` SSE event
**Then** source cards appear at the bottom of the panel showing Ch.N · p.N · score%, full section heading, and a 250-char content snippet

**Given** `GET /api/v1/graph/ego/{concept_id}` is called
**When** the concept exists
**Then** it returns center + all 1-hop Concept/Section/Category neighbors + edges in one Cypher round-trip; 404 if unknown

**Given** `POST /api/v1/explain` is called
**When** the concept exists
**Then** it streams SSE tokens from `openai/gpt-4o-mini` (via OpenRouter) using Qdrant passages as context; sources sent as `event: sources` after streaming; 404 if concept unknown

**Given** the full test suite ran before this story (61 passing)
**When** all code for this story is implemented
**Then** `conda run -n edu python -m pytest tests/ -v` reports ≥ 67 passing

---

## Tasks / Subtasks

### T1 — Backend: Graph Router

- [x] T1.1 `src/backend/routers/graph_router.py` — `GET /api/v1/graph/ego/{concept_id}` (EgoGraphResponse) + `POST /api/v1/explain` (SSE StreamingResponse)
  - Ego-graph: single Cypher round-trip with `OPTIONAL MATCH`, null-neighbor filtering, label-aware node ID resolution
  - Explain: `AsyncOpenAI` (not sync) inside async generator; model `openai/gpt-4o-mini` via OpenRouter; response headers `Cache-Control: no-cache`, `X-Accel-Buffering: no`
  - SSE format: `data: {token}\n\n` → `event: sources\ndata: {json}\n\n` → `data: [DONE]\n\n`
  - Sources payload includes `page_num`, `chapter`, `section_heading`, `score`, `snippet` (first 250 chars of content)
- [x] T1.2 `src/backend/main.py` — registered `graph_router` with `prefix="/api/v1"`
- [x] T1.3 `tests/test_graph_router.py` — 6 tests: 200 center-only, 200 with neighbors, 404 unknown, null-neighbor filtering, explain 404, explain SSE format; **67 total passing**

### T2 — Frontend: Types + API

- [x] T2.1 `src/frontend/lib/api.ts` — added `GraphNode`, `GraphEdge`, `EgoGraphResponse` interfaces + `fetchEgoGraph(conceptId)` function

### T3 — Frontend: EgoGraph Canvas Component

- [x] T3.1 `npm install react-force-graph-2d` (v1.29.1) in `src/frontend/`
- [x] T3.2 `src/frontend/components/EgoGraph.tsx`
  - `dynamic(() => import('react-force-graph-2d'), { ssr: false })` — mandatory for Next.js (library accesses `window` at import time)
  - Nodes cloned with spread in `useMemo` (library mutates node objects in place with simulation coords)
  - `nodeCanvasObjectMode={() => 'replace'}` prevents double-draw
  - `ResizeObserver` on wrapper div for responsive canvas dimensions
  - Node colours: center `#dfc07a`, concept `#c9a95f`, section `#4a8fff`; selected ring highlight
  - `onNodeClick` fires only for `node.node_type === 'Concept'` nodes

### T4 — Frontend: ExplainPanel Component

- [x] T4.1 `src/frontend/components/ExplainPanel.tsx`
  - SSE consumed with `fetch` + `ReadableStream.getReader()` — buffer-based line parser handles TCP chunking
  - `AbortController` cleanup on unmount or `conceptId` change
  - KaTeX math rendering: `renderMath()` helper splits text on `\( ... \)` and `\[ ... \]` patterns; `throwOnError: false` for graceful fallback; `katex/dist/katex.min.css` imported directly
  - Sources footer pinned outside scrollable body (`flex-shrink: 0`) — always visible regardless of explanation length
  - Sources cards: Ch.N · p.N · score% match + full section heading + 250-char snippet

### T5 — Frontend: Graph Page Route

- [x] T5.1 `src/frontend/app/graph/page.tsx` — new `/graph` route
  - Concept search with 250ms debounce; outside-click via `useRef` + `.contains()` check (reliable vs `stopPropagation`)
  - `handleNodeClick`: center node → open panel only; neighbor node → fetch new ego graph + open panel (full graph navigation)
  - Search bar updates to reflect currently-centered concept when navigating by click
  - Errors surfaced visibly (search errors, load errors — no silent swallowing)
- [x] T5.2 `src/frontend/app/layout.tsx` — added "Graph" nav link between Study and Agile

### T6 — Frontend: Styling

- [x] T6.1 `src/frontend/app/globals.css` — appended all new CSS:
  - `.graph-page`, `.graph-search-area`, `.search-results`, `.search-result-item`
  - `.graph-container` (fills viewport), `.graph-container.panel-open { width: calc(100% - 420px) }` with transition
  - `.explain-panel` (fixed right, `z-index: 100`, slide-in animation), `.explain-panel-body` (`min-height: 0` — required for flex child scroll to work)
  - `.explain-sources` (pinned footer `flex-shrink: 0; max-height: 55%; overflow-y: auto`)
  - `.explain-source-item` (vertical card with left-border hover), `.explain-source-loc`, `.explain-source-heading`, `.explain-source-snippet`
  - `@keyframes slide-in-right`, `@keyframes blink-cursor`

### T7 — Bug Fix: Section Heading Propagation

- [x] T7.1 `src/graph/eci_passage_chunker.py` — `chunk_section()`: added `current_heading` carry-forward; continuation pages (within same section, no `## ` heading) now inherit the last seen heading instead of returning `""`
- [x] T7.2 Qdrant payload patch — ran `client.set_payload()` loop over all 238 points to update `section_heading` without re-embedding; verified ch6 pages p83–p87 all show `"6.2 Structural Causal Models"`

---

## Dev Notes

### Architecture
- Panel layout: `.explain-panel` (flex col) → `.explain-panel-header` (shrink:0) → `.explain-panel-body` (flex:1, min-height:0, scrollable) → `.explain-sources` (shrink:0, pinned)
- `min-height: 0` on flex children with `overflow-y: auto` is mandatory in Chrome/Safari; without it the child expands to content height and overflow never activates
- Graph navigation uses `useCallback([egoGraph])` dependency — fresh reference on every graph load, which is correct since the callback needs to compare against current center

### Key Implementation Decisions
- `AsyncOpenAI` (not `OpenAI`) inside async generator — sync client would block the event loop
- Qdrant `set_payload()` for heading fix avoids re-embedding (238 points patched in seconds vs ~10min re-ingest)
- Sources footer extracted from scrollable body to guarantee visibility regardless of explanation length
- `react-force-graph-2d` node objects must be cloned (`{...n}`) before passing as graph data — library mutates them with simulation state

---

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Completion Notes

- TypeScript `tsc --noEmit` passes clean throughout
- 67 backend tests passing (61 pre-existing + 6 new in `test_graph_router.py`)
- KaTeX `@types/katex` installed alongside `katex@0.16.33`
- Section heading bug confirmed fixed: Qdrant ch6 p83–p87 all return `"6.2 Structural Causal Models"`
- Graph navigation (click neighbor → new ego graph) implemented and verified

### File List

**New files:**
- `src/backend/routers/graph_router.py`
- `src/frontend/app/graph/page.tsx`
- `src/frontend/components/EgoGraph.tsx`
- `src/frontend/components/ExplainPanel.tsx`
- `tests/test_graph_router.py`

**Modified files:**
- `src/backend/main.py` (registered graph_router)
- `src/frontend/lib/api.ts` (GraphNode, GraphEdge, EgoGraphResponse types + fetchEgoGraph)
- `src/frontend/app/globals.css` (graph page + panel CSS)
- `src/frontend/app/layout.tsx` (Graph nav link)
- `src/graph/eci_passage_chunker.py` (section heading carry-forward fix)

**Data patched (no file change):**
- Qdrant `eci_passages` collection — `section_heading` updated for all 238 points via `set_payload()`

---

### Review Follow-ups (AI) — Code Review 2026-03-03

All HIGH and MEDIUM issues fixed automatically:

- [x] [AI-Review][HIGH] `explain_concept` called sync `concept_exists`, `execute_query`, `retrieve_passages` inside `async def`, blocking the event loop — wrapped all three in `asyncio.to_thread()` [graph_router.py:149-168]
- [x] [AI-Review][MEDIUM] `event_stream()` had no error handling for LLM API failures — added `try/except` that yields `event: error\ndata: {detail}\n\n`; ExplainPanel updated to parse and display it [graph_router.py:168; ExplainPanel.tsx:126-133]
- [x] [AI-Review][MEDIUM] `fetchEgoGraph` calls had no `AbortController` — rapid navigation caused race conditions where an earlier response could overwrite a later one — `graphFetchRef` added to `page.tsx`; `fetchEgoGraph` and `apiFetch` accept optional `AbortSignal`; `AbortError` filtered in catch [page.tsx; api.ts]
- [x] [AI-Review][MEDIUM] SSE test only checked `"event: sources" in body` — sources JSON schema not validated — test now parses the JSON and asserts all 5 fields (`page_num`, `chapter`, `section_heading`, `score`, `snippet`) [test_graph_router.py:154-166]

Low issues noted but not fixed (acceptable for current scope):
- [ ] [AI-Review][LOW] Dead CSS class `.explain-source-score` (globals.css:839) — never referenced in JSX; safe to delete
- [ ] [AI-Review][LOW] Non-null assertions `node.x!` / `node.y!` in EgoGraph.tsx:84 — add `if (!node.x || !node.y) return` guard in nodeCanvasObject
- [ ] [AI-Review][LOW] Missing test for `top_k` out-of-range (ge=1, le=10) — add `test_explain_top_k_validation`
- [ ] [AI-Review][LOW] `_ego_row` mock's `lambda self, key` pattern is fragile — prefer `mock.__getitem__.side_effect = lambda key: {...}[key]`

---

## Change Log

- 2026-03-03: Story created post-implementation to capture GraphRAG branch work; status: **done**
- 2026-03-03: Code review (adversarial) — 1 HIGH + 3 MEDIUM issues found and fixed; 4 LOW items logged; 67 tests still passing; status: **done**
