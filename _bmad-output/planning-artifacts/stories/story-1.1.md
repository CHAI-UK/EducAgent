---
story_id: '1.1'
epic: 'Epic 1: Causality Concept Graph & Project Foundation'
source: '_bmad-output/planning-artifacts/epics.md'
---

### Story 1.1: Knowledge Graph Build Pipeline & Validation

As a **developer**,
I want the Causality Concept Graph built and validated from Pearl's textbook data,
So that all downstream features have a reliable, queryable knowledge backbone.

**Acceptance Criteria:**

**Given** the project is set up
**When** `python build_knowledge_graph.py` is run
**Then** it produces `graph.pkl` (≤200KB), `graph.json`, `concepts_by_chapter.json`, and `graph_summary.json`

**Given** `graph.pkl` is built
**When** it is loaded via `load_graph()`
**Then** the graph contains 672 nodes (226 Section + 446 Concept) and 3,303 edges

**Given** the graph is loaded
**When** `get_prerequisites("d_separation")` is called
**Then** it returns the correct PREREQUISITE_OF predecessor concepts

**Given** the graph is loaded
**When** `get_chapter_concepts(1)` is called
**Then** it returns the 159 concept nodes for Chapter 1

**Given** the graph is loaded
**When** `get_next_concepts("back_door_criterion")` is called
**Then** it returns the correct PREREQUISITE_OF downstream successors

---
