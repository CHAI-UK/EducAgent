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

### Decision: NetworkX (MVP) → Neo4j (Production)

**Rationale:** NetworkX runs in-memory with zero infrastructure for the MVP demo. The full graph (672 nodes, 3,303 edges) fits comfortably in RAM (~162 KB pickle). Neo4j with Cypher enables production-grade prerequisite traversal and concept path queries.

**Migration path:** Graph is exported to `graph.json` (node-link format) and `graph.pkl` on every build. The export schema is networkx-compatible and can be ingested into Neo4j via `py2neo` with no schema changes.

### Graph Schema

```
Node types:
  Section   — section_id (e.g. "1.2.3"), title, chapter, depth, start_page, end_page
  Concept   — concept_id (slugified), name, page_refs[], subentries{}, see_also[], difficulty, misconceptions[]

Edge types:
  NEXT_IN_SEQUENCE   Section → Section      (TOC linear order; 169 edges)
  COVERED_IN         Concept → Section      (page overlap; 1,545 edges)
  ILLUSTRATES        Section → Concept      (inverse of COVERED_IN; 1,545 edges)
  PREREQUISITE_OF    Concept → Concept      (curated seed; 28 edges; LLM-extended later)
  COMMONLY_CONFUSED  Concept ↔ Concept      (bidirectional; 10 pairs / 20 edges)
```

### Build Pipeline

```
Step 1  graph/toc_parser.py       Parse 07_Contents.pdf       → 226 Section nodes
                                  11 chapters, 65 sections, 150 subsections

Step 2  graph/index_parser.py     Parse 24_Subject_Index.pdf  → 431 parsed Concept nodes
        graph/curated_additions.py                            + 15 curated key concepts
                                                              = 446 Concept nodes total

Step 3  graph/graph_builder.py    Build NetworkX DiGraph + all edges
                                  672 nodes, 3,303 edges (0 skipped prerequisites)

Step 4  graph/export.py           graph.pkl (162 KB), graph.json (535 KB),
                                  concepts_by_chapter.json, graph_summary.json
```

**Run:** `python build_knowledge_graph.py` from project root.

### Graph Statistics

| Metric | Value |
|---|---|
| Total nodes | 672 |
| Section nodes | 226 |
| Concept nodes | 446 |
| Total edges | 3,303 |
| NEXT_IN_SEQUENCE | 169 |
| COVERED_IN | 1,545 |
| ILLUSTRATES | 1,545 |
| PREREQUISITE_OF | 28 (curated seed) |
| COMMONLY_CONFUSED | 20 (10 pairs) |

### Concepts per Chapter

| Chapter | Concepts | Title |
|---|---|---|
| 1 | 159 | Introduction to Probabilities, Graphs, and Causal Models |
| 2 | 57 | A Theory of Inferred Causation |
| 3 | 122 | Causal Diagrams and the Identification of Causal Effects |
| 4 | 53 | Actions, Plans, and Direct Effects |
| 5 | 72 | Causality and Structural Models in Social Science and Economics |
| 6 | 31 | Simpson's Paradox, Confounding, and Collapsibility |
| 7 | 104 | The Logic of Structure-Based Counterfactuals |
| 8 | 33 | Imperfect Experiments: Bounding Effects and Counterfactuals |
| 9 | 29 | Probability of Causation |
| 10 | 24 | The Actual Cause |
| 11 | 130 | Reflections, Elaborations, and Discussions with Readers |

### Key PREREQUISITE_OF Chains

```
probability_theory
  → conditional_independence → graphoids
  → conditional_independence → d_separation
  → bayesian_networks_probabilistic → d_separation
                                    → causal_bayesian_networks → intervention → do_calculus

d_separation
  → back_door_criterion → do_calculus
  → front_door_criterion → do_calculus
  → markov_condition

structural_equations → functional_models → counterfactuals → probability_of_causation
                                                           → actual_causation
                      → functional_models → direct_effects
                      → functional_models → intervention

confounding_bias      → back_door_criterion
confounders           → back_door_criterion
simpson_s_paradox     → confounding_bias
collider              → d_separation
causal_discovery      → stability
instrumental_variables → do_calculus
potential_outcome_framework → counterfactuals
```

### COMMONLY_CONFUSED Pairs (Dumb Student misconception library)

| Pair | Misconception |
|---|---|
| `confounders` ↔ `collider` | confounders open paths; colliders block them |
| `back_door_criterion` ↔ `front_door_criterion` | front-door handles unmeasured confounders |
| `d_separation` ↔ `conditional_independence` | d-sep is graphical; CI is probabilistic |
| `causation` ↔ `correlation` | correlation does not imply causation |
| `counterfactuals` ↔ `potential_outcome_framework` | different formalisms, same quantities |
| `intervention` ↔ `conditioning` | do(x) ≠ P(Y\|X=x) |
| `direct_effects` ↔ `total_effects` | direct effects exclude mediated paths |
| `confounding_bias` ↔ `selection_bias` | different sources, different corrections |
| `simpson_s_paradox` ↔ `collapsibility` | reversal vs. aggregation phenomenon |
| `causal_bayesian_networks` ↔ `bayesian_networks_probabilistic` | causal BNs support do(·) |

### Tutor Agent Graph API

```python
from graph.export import load_graph

G = load_graph()  # loads graph/data/graph.pkl

def get_prerequisites(concept_id: str) -> list[str]:
    return [u for u, v, d in G.in_edges(concept_id, data=True)
            if d["edge_type"] == "PREREQUISITE_OF"]

def get_covered_sections(concept_id: str) -> list[str]:
    return [v for _, v, d in G.out_edges(concept_id, data=True)
            if d["edge_type"] == "COVERED_IN"]

def get_chapter_concepts(chapter: int) -> list[str]:
    concepts = set()
    for n, d in G.nodes(data=True):
        if d.get("node_type") == "Section" and d.get("chapter") == chapter:
            for _, c, ed in G.out_edges(n, data=True):
                if ed["edge_type"] == "ILLUSTRATES":
                    concepts.add(c)
    return sorted(concepts)

def get_next_concepts(concept_id: str) -> list[str]:
    return [v for _, v, d in G.out_edges(concept_id, data=True)
            if d["edge_type"] == "PREREQUISITE_OF"]
```

### Planned Graph Enhancements

1. **PREREQUISITE_OF expansion (LLM):** Prompt LLM over section text pairs to extract ~100–150 total edges. Script: `graph/llm_prerequisite_extractor.py`.
2. **Difficulty scoring:** LLM assigns `difficulty` (1–5) to each Concept node.
3. **Misconception library:** Expand `misconceptions[]` on key Concept nodes for Dumb Student agent.
4. **Section text chunking → Qdrant:** Parse per-chapter PDFs into subsection-level chunks; embed with `text-embedding-3-small`; store in Qdrant.
5. **Neo4j migration:** Import `graph.json` via `py2neo` when moving to production.

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
