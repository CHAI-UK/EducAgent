# EducAgent — Technical Plan

*Based on Pearl (2009) + EducAgent_OnePager. Addressing all four components in priority order.*

---

## Understanding the Material

Pearl's *Causality* has a natural pedagogical skeleton already:
- **TOC** gives a sequential chapter/section hierarchy (11 chapters, ~80 sections)
- **Subject Index** gives ~200 cross-cutting concepts with page-level references — this is the concept vocabulary
- The two together let you build a **bipartite graph**: concepts ↔ sections, plus prerequisite edges *between* concepts

---

## Component 1: Causality Concept Knowledge Graph

### Why GraphRAG is the right call

Standard RAG retrieves flat chunks. GraphRAG lets you answer: *"What do I need to know before learning the back-door criterion?"* and *"Which chapters reinforce conditional independence?"* — exactly what an adaptive tutor needs.

### Graph Schema

```
Node types:
  Concept       — name, definition_excerpt, difficulty (1-5), misconceptions[]
  Section       — chapter_num, section_num, title, page_range, depth_level
  Misconception — description, why_it_occurs

Edge types:
  PREREQUISITE_OF   (Concept A → Concept B)      # A must come before B
  COVERED_IN        (Concept → Section)           # via subject index page refs
  NEXT_IN_SEQUENCE  (Section → Section)           # from TOC order
  COMMONLY_CONFUSED (Concept ↔ Concept)           # e.g. confounder vs collider
  ILLUSTRATES       (Section → Concept)           # section teaches this concept
```

### Construction Pipeline (Phase 1)

**Step 1: Seed from structured sources (no LLM needed)**
- Parse TOC → `Section` nodes with chapter hierarchy and page ranges
- Parse Subject Index → `Concept` nodes with page references
- Cross-reference pages → auto-generate `COVERED_IN` edges
- TOC linear order → `NEXT_IN_SEQUENCE` edges

**Step 2: LLM extraction for prerequisite edges**
For each concept pair, prompt an LLM with the relevant section text:
> *"Does understanding [d-separation] require prior knowledge of [conditional independence]? Answer yes/no with a 1-sentence reason."*

This creates `PREREQUISITE_OF` edges — the most important ones for adaptive teaching.

**Step 3: Misconception injection**
Manually or semi-automatically populate a misconception library: *collider bias, Simpson's paradox, "correlation → causation"*, etc. Link them to concept nodes.

### Tooling

| Layer | Choice | Reason |
|---|---|---|
| Graph DB | **Neo4j** (production) / **NetworkX** (prototype) | Neo4j has Cypher queries; NetworkX is zero-infra for MVP |
| Vector store | **Qdrant** (self-hosted) | Fast ANN, supports named collections per chapter |
| Embedding | `openai/text-embedding-3-small` via OpenRouter | Cheap, high quality |
| Section chunking | Per-subsection (e.g. 3.3.1, 3.3.2) | Already split by chapter — split further at section level |

**Recommended first step**: Use NetworkX for the prototype graph, export to JSON, validate structure, then migrate to Neo4j for production.

---

## Component 2: Adaptive Content Generation

### Student Model (the core adaptive mechanism)

Store per-user, persist across sessions:

```python
StudentModel = {
  "user_id": str,
  "role": "student" | "clinician" | "ml_engineer" | "economist",
  "background": {
    "probability": 0-5,    # self-reported + quiz-inferred
    "statistics": 0-5,
    "domain": "medicine" | "tech" | "social_science"
  },
  "mastery": {
    "concept_id": {
      "level": 0.0-1.0,    # 0=unseen, 1=mastered
      "attempts": int,
      "errors": ["common_error_1", ...]  # feeds later courses
    }
  },
  "session_history": [...]
}
```

### Content Generation Per Concept

Each concept node triggers a **content generation pipeline**:

```
Student Model + Concept Node + Section Text
        ↓
   [Tutor Agent]
        ↓
   Immersive narrative (800–1500 words)
   + 2–3 inline quiz checkpoints
   + 1 worked example (domain-adapted: medical/ML/econ)
   + 1 DAG/diagram description (rendered as SVG or image)
        ↓
   [Critic Agent] reviews for accuracy
        ↓
   Final content JSON → stored (cached per concept × background profile)
```

**Caching strategy**: Hash `(concept_id, role, probability_background, domain)` → reuse generated content across users with the same profile signature. This cuts LLM costs significantly for common profiles.

### Agentic Framework: LangGraph

**Recommendation: LangGraph** (Python, by LangChain team)

Why over alternatives:
- Native **stateful multi-agent graphs** — matches Tutor/Critic/DumbStudent architecture exactly
- Supports **cycles** (Critic can send back to Tutor for revision)
- Built-in **checkpointing** (student state persists between sessions trivially)
- Works natively with OpenRouter via `langchain-openai` with `base_url` override
- LangSmith tracing for debugging pedagogical flows

Alternative: **smolagents** (HuggingFace) for a lighter footprint, but LangGraph's state management is more mature for this use case.

### LLM Selection via OpenRouter

| Task | Model | Rationale |
|---|---|---|
| Content generation (Tutor) | `anthropic/claude-3.5-sonnet` | Best for long-form educational prose |
| Accuracy checking (Critic) | `anthropic/claude-3.5-sonnet` or `google/gemini-2.0-flash` | Fast, cheap, good at factual checks |
| Quiz generation | `openai/gpt-4o-mini` | Cheap, reliable structured output |
| Student answer evaluation | `anthropic/claude-3-haiku-20240307` | Very cheap for short evaluations |
| Embeddings | `openai/text-embedding-3-small` | Standard, cheap |

Use OpenRouter's **fallback routing** to avoid downtime from any single provider.

### Content Format (Google LearnYourWay-style)

Output each concept as structured JSON that the frontend renders:

```json
{
  "concept_id": "backdoor_criterion",
  "sections": [
    { "type": "narrative", "content": "..." },
    { "type": "inline_quiz", "question": "...", "options": [...], "correct": 1, "explanation": "..." },
    { "type": "diagram", "description": "...", "svg": "..." },
    { "type": "narrative", "content": "..." },
    { "type": "inline_quiz", "..." : "..." }
  ],
  "end_quiz": [ "..." ],
  "next_concepts": ["frontdoor_criterion", "do_calculus"]
}
```

---

## Component 3: Web Interface (Phase 3 — plan now, build later)

### Stack

| Layer | Choice |
|---|---|
| Frontend | ** next.js 16+** (App Router, TypeScript) |
| Content rendering | **MDX** or custom JSON renderer |
| Backend API | **FastAPI** (Python) — keeps it in same ecosystem as agents |
| Auth | **Clerk** (easiest Next.js integration) |
| Student DB | **PostgreSQL** (via Supabase for fast setup) |
| Graph / Vector | **Neo4j** + **Qdrant** |
| Streaming | Server-Sent Events or Vercel AI SDK |

DeepTutor uses a document-centric chat UI — EducAgent's UI is different: more **course-flow-centric** with a side panel showing progress on the knowledge graph.

### Key UI Concepts
- **Knowledge graph explorer**: visual node map, color-coded by mastery level
- **Immersive reading mode**: full-screen, inline quiz interactions, no distractions
- **Study vs Agile toggle**: top-level mode switch
- **Progress dashboard**: mastery heatmap across concept graph

Layout concept:
- Left panel: concept graph navigator
- Center: immersive content renderer
- Right: student notes / quiz history

---

## Component 4: Agile Mode

Shares the same infrastructure as Study Mode but with different routing:

```
User brings problem
  → Problem intake agent
  → Identifies relevant concept nodes in graph
  → Checks student mastery of those concepts
  → If gap: mini-teach first → then help with problem
  → If mastered: directly help → log as worked example
```

### Task Templates

| Template | Description |
|---|---|
| `check_adjustment_set` | User provides DAG + adjustment set; agent checks back-door criterion |
| `diagnose_confounding` | User describes study design; agent identifies confounders/colliders |
| `explain_result_change` | "My coefficient changed when I added Z" — agent diagnoses mediator/collider issue |
| `build_dag` | Collaborative DAG construction for user's domain |

---

## Recommended Build Order (Phase 1–2)

```
Week 1–2:   Parse TOC + Subject Index → NetworkX graph (seed nodes + COVERED_IN edges)
Week 3–4:   Section-level text chunking + embeddings → Qdrant
Week 5–6:   LLM extraction of PREREQUISITE_OF edges → validate graph structure
Week 7–8:   LangGraph agent setup (Tutor + Critic) + OpenRouter integration
Week 9–10:  Student model + first 3 concepts of Chapter 1 generated end-to-end
Week 11–12: First-chapter demo (Study Mode, CLI or simple Streamlit UI)
```

---

## Key Decisions to Make Now

1. **Graph storage for MVP**: NetworkX (zero infra, good for first 3 months) vs. Neo4j (production-ready but overhead). Recommend NetworkX → export to JSON → migrate later.

2. **Content granularity**: Generate content at the **subsection level** (e.g., 3.3.1 Backdoor Criterion) rather than chapter level — gives ~80 learnable units from the book, the right granularity for adaptive teaching.

3. **First domain adaptation**: Pick one user role (ML engineer is likely the first pilot user base) and generate content for that role first before generalizing.

4. **Runtime graph access**: The concept graph should be loaded into memory (NetworkX graph object) and queried by the Tutor agent to decide "what to teach next" and "what prerequisites are missing."
