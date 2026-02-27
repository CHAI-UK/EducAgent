---
stepsCompleted: [1, 2]
inputDocuments:
  - '_bmad-output/planning-artifacts/prd.md'
  - '_bmad-output/planning-artifacts/research/domain-causality-education-agentic-teaching-platforms-research-2026-02-23.md'
  - 'docs/EducAgent_TechnicalPlan.md'
workflowType: 'architecture'
project_name: 'EducAgent'
user_name: 'Yuyang'
date: '2026-02-23'
---

# EducAgent — Architecture Decision Document

**Author:** Yuyang | **Date:** 2026-02-23

---

## Component 1: Causality Concept Graph

**Textbook:** *Elements of Causal Inference* (Peters, Janzing & Schölkopf, 2017) — 266 pages, 10 chapters + 3 appendices (A–C).

### Decision: NetworkX (MVP) → Neo4j (Production)

**Rationale:** NetworkX runs in-memory with zero infrastructure for the MVP demo. The graph (189 nodes, 332 edges) fits comfortably in RAM. Neo4j with Cypher enables production-grade prerequisite traversal and concept path queries.

**Migration path:** Graph is exported to `eci_graph.json` (node-link format) and `eci_graph.pkl` on every build. The export schema is networkx-compatible and can be ingested into Neo4j via `py2neo` with no schema changes.

### Graph Schema

```
Node types:
  Section   — section_id (e.g. "1.2"), label, chapter (1–13), depth, start_page, end_page
  Category  — umbrella grouping nodes from the index (e.g. "graph", "entropy")
  Concept   — concept_id (slugified), name, page_refs[], chapter, difficulty, misconceptions[]

Edge types:
  NEXT_IN_SEQUENCE   Section → Section      (TOC linear order; 78 edges)
  COVERED_IN         Concept → Section      (page overlap; 140 edges)
  SUBTOPIC_OF        Concept → Category     (index sub-entry hierarchy; 34 edges)
  RELATED_TO_SEE_ALSO Concept ↔ Concept     (index see-also links; 22 edges)
  RELATED_TO_ALIAS   Concept → Concept      (acronym/alias merges; 14 edges)
  PREREQUISITE_OF    Concept → Concept      (curated seed; 29 edges; LLM-extended later)
  COMMONLY_CONFUSED  Concept ↔ Concept      (bidirectional; 8 pairs / 15 edges)
```

### Build Pipeline  ✅ COMPLETE

```
Step 1  graph/eci_toc_parser.py      Parse assets/…/01_TOC/01_TOC.mmd
                                     → 79 Section nodes (13 chapter roots + 66 subsections)

Step 2  graph/eci_graph_builder.py   Parse assets/…/18_Index/18_Index.mmd
                                     → 101 Concept nodes + 9 Category nodes
                                     Build NetworkX DiGraph + all edges
                                     = 189 nodes, 332 edges

Step 3  graph/eci_visualize.py       eci_graph.pkl + eci_graph.json → eci_graph.html
                                     (interactive vis.js network with edge-type filters,
                                      chapter coloring, view presets)

Step 4  graph/eci_concept_stars.py   eci_graph.pkl → eci_uni.html
                                     (self-contained D3 "concept universe" visualization
                                      with star/nebula/sun node types)
```

**Run:** `python graph/eci_graph_builder.py` from project root.
**Visualize:** `python graph/eci_visualize.py` and `python graph/eci_concept_stars.py`

**Supporting scripts:**
- `scripts/split_pdf_by_bookmarks.py` — split ECI PDF into per-section files → `assets/ElementsOfCausalInference_sections/`
- `scripts/parse_subject_index.py` — subject index parsing utility

### Graph Statistics

| Metric | Value |
|---|---|
| Total nodes | 189 |
| Section nodes | 79 |
| Category nodes | 9 |
| Concept nodes | 101 |
| Total edges | 332 |
| NEXT_IN_SEQUENCE | 78 |
| COVERED_IN | 140 |
| SUBTOPIC_OF | 34 |
| RELATED_TO_SEE_ALSO | 22 |
| RELATED_TO_ALIAS | 14 |
| COMMONLY_CONFUSED | 15 |
| PREREQUISITE_OF | 29 (curated seed) |

### Concepts per Chapter

| Chapter | Concepts | Title |
|---|---|---|
| 1 | 4 | Statistical and Causal Models |
| 2 | 12 | Assumptions for Causal Inference |
| 3 | 2 | Cause-Effect Models |
| 4 | 5 | Learning Cause-Effect Models |
| 5 | 1 | Connections to Machine Learning, I |
| 6 | 23 | Multivariate Causal Models |
| 7 | 19 | Learning Multivariate Causal Models |
| 8 | 2 | Connections to Machine Learning, II |
| 9 | 14 | Hidden Variables |
| 10 | 8 | Time Series |
| App A (11) | 4 | Some Probability and Statistics |
| App B (12) | 0 | Causal Orderings and Adjacency Matrices |
| App C (13) | 0 | Proofs |

### Key PREREQUISITE_OF Chains (ECI curated seed, 29 edges)

```
random_variable
  → structural_causal_model_scm
  → conditional_independence → d_separation → causal_markov_condition → faithfulness
                                                                        → causal_minimality
  → conditional_independence → causal_markov_condition

directed_acyclic_graph_dag
  → d_separation
  → structural_causal_model_scm → interventions
                                → counterfactuals → potential_outcomes
                                → total_causal_effect_ace
                                → granger_causality → transfer_entropy
  → maximal_ancestral_graph_mag → fci_algorithm

d_separation → backdoor_criterion → adjustment
                                   → propensity_score_matching

markov_property → causal_markov_condition
markov_equivalence → pc_algorithm
                   → greedy_equivalence_search_ges

faithfulness → causal_learning → pc_algorithm
                                → greedy_equivalence_search_ges
additive_noise_model_anm → causal_learning
kolmogorov_complexity → additive_noise_model_anm
linear_non_gaussian_acyclic_model_lingam → independent_component_analysis_ica
instrumental_variable → total_causal_effect_ace
```

### COMMONLY_CONFUSED Pairs (Dumb Student misconception library)

| Pair | Misconception |
|---|---|
| `granger_causality` ↔ `total_causal_effect_ace` | Granger causality is predictive, not interventional |
| `markov_condition` ↔ `causal_markov_condition` | causal version implies directionality |
| `structural_causal_model_scm` ↔ `structural_equation_model` | SEM absorbed into SCM; SCM supports do(·) |
| `counterfactuals` ↔ `potential_outcomes` | different formalisms, same quantities |
| `d_separation` ↔ `conditional_independence` | d-sep is graphical; CI is probabilistic |
| `common_cause` ↔ `collider` | common cause opens paths; collider blocks them |
| `faithfulness` ↔ `markov_property` | Markov is necessity; faithfulness adds sufficiency |
| `adjustment` ↔ `inverse_probability_weighting` | different estimators for the same causal quantity |

### Tutor Agent Graph API

```python
import pickle
from pathlib import Path

G = pickle.load(open("graph/output/eci_graph.pkl", "rb"))

def get_prerequisites(concept_id: str) -> list[str]:
    return [u for u, v, d in G.in_edges(concept_id, data=True)
            if d["edge_type"] == "PREREQUISITE_OF"]

def get_covered_sections(concept_id: str) -> list[str]:
    return [v for _, v, d in G.out_edges(concept_id, data=True)
            if d["edge_type"] == "COVERED_IN"]

def get_chapter_concepts(chapter: int) -> list[str]:
    """Return concept node IDs covered in a given chapter."""
    return [
        n for n, d in G.nodes(data=True)
        if d.get("type") == "concept" and d.get("chapter") == chapter
    ]

def get_next_concepts(concept_id: str) -> list[str]:
    return [v for _, v, d in G.out_edges(concept_id, data=True)
            if d["edge_type"] == "PREREQUISITE_OF"]
```

### Planned Graph Enhancements

1. **PREREQUISITE_OF expansion (LLM):** Prompt LLM over ECI section text pairs to extract ~100–150 total edges. Script: `graph/eci_llm_prerequisite_extractor.py` (planned).
2. **Difficulty scoring:** LLM assigns `difficulty` (1–5) to each Concept node based on ECI section content.
3. **Misconception library:** Expand `misconceptions[]` on key Concept nodes for Dumb Student agent.
4. **Section text chunking → Qdrant:** Parse per-chapter ECI PDFs (in `assets/ElementsOfCausalInference_sections/`) into subsection-level chunks; embed with `text-embedding-3-small`; store in Qdrant.
5. **Neo4j migration:** Import `eci_graph.json` via `py2neo` when moving to production.

---

## Component 2: LLM & Agent Stack

### Decision: LangGraph v1.0 + OpenRouter

LangGraph provides stateful multi-agent graphs with built-in checkpointing matching the Tutor/Critic/Dumb Student architecture. OpenRouter provides multi-provider fallback.

### LLM Routing

| Agent | Primary Model | Fallback |
|---|---|---|
| Tutor (content generation) | `anthropic/claude-sonnet-4-6` | `openai/gpt-4.1` |
| Critic (accuracy check) | `google/gemini-2.0-flash` | `anthropic/claude-haiku-4-5` |
| Quiz generation | `openai/gpt-4.1-mini` | `google/gemini-2.0-flash` |
| Answer evaluation | `anthropic/claude-haiku-4-5` | `openai/gpt-4.1-mini` |
| Embeddings | `openai/text-embedding-3-small` | — |

### Agent Graph (LangGraph)

```
StudyModeGraph:
  profile_loader → concept_retriever → prerequisite_checker
                                            ↓ gaps?
                                      prereq_teacher → tutor_generator → critic_validator
                                                                 ↑ (revision loop, max 2)
                                                       content_renderer

AgileModeGraph:
  problem_intake → concept_identifier → mastery_checker
                                            ↓ gap?
                                      mini_teacher → direct_consultant → response_formatter
```

### Session State Schema (MVP: stateless / Growth: PostgreSQL)

```python
SessionState = {
    "session_id": str,
    "profile": {"background": str, "level": str, "custom": bool},
    "mastery": {"concept_id": float},   # 0.0–1.0 per concept
    "history": list[dict],
}
```

### Content Caching

Cache key: `hash(concept_id + background + level)` → cached content JSON.

- MVP: in-memory Python dict (process-scoped)
- Growth: Redis or Supabase storage

---

## Component 3: Web Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 14 App Router (TypeScript) + Vercel AI SDK |
| Backend API | FastAPI (Python) |
| Content streaming | Server-Sent Events |
| Auth (Growth) | Clerk (OAuth, magic link) |
| DB (Growth) | PostgreSQL via Supabase |
| Vector store | Qdrant (self-hosted) |
| Graph (MVP) | NetworkX in-memory (`graph.pkl` loaded at startup) |
| Graph (Production) | Neo4j |

### Content JSON Format

```json
{
  "concept_id": "back_door_criterion",
  "profile": {"background": "Computer Scientist", "level": "Moderate"},
  "sections": [
    {"type": "narrative", "content": "..."},
    {"type": "inline_quiz", "question": "...", "options": [...], "correct": 0, "explanation": "..."},
    {"type": "diagram", "description": "...", "svg": "..."},
    {"type": "narrative", "content": "..."},
    {"type": "inline_quiz", "question": "...", "options": [...], "correct": 2, "explanation": "..."}
  ],
  "end_quiz": [...],
  "next_concepts": ["front_door_criterion", "do_calculus"]
}
```

---

*Architecture document is live — updated as implementation decisions are made.*
