---
story_id: '1.1'
status: 'complete'
epic: 'Epic 1: Causality Concept Graph & Project Foundation'
source: '_bmad-output/planning-artifacts/epics.md'
completed: '2026-02-27'
---

### Story 1.1: Knowledge Graph Build Pipeline & Validation ✅ COMPLETE

As a **developer**,
I want the ECI Causality Concept Graph built and validated from *Elements of Causal Inference* (Peters, Janzing & Schölkopf, 2017),
So that all downstream features have a reliable, queryable knowledge backbone.

**Status: DONE** — Graph built, all outputs committed to `graph/output/`.

**Acceptance Criteria:**

**Given** the project is set up
**When** `python graph/eci_graph_builder.py` is run
**Then** it produces `graph/output/eci_graph.pkl`, `eci_graph.json`, `eci_graph.html`, and `eci_uni.html` ✅

**Given** `eci_graph.pkl` is built
**When** it is loaded via `pickle.load()`
**Then** the graph contains 189 nodes (79 Section + 9 Category + 101 Concept) and 332 edges ✅

**Given** the graph is loaded
**When** `get_prerequisites("d_separation")` is called
**Then** it returns `conditional_independence` and `directed_acyclic_graph_dag` as PREREQUISITE_OF predecessors ✅

**Given** the graph is loaded
**When** `get_chapter_concepts(6)` is called
**Then** it returns the 23 concept nodes for Chapter 6 (Multivariate Causal Models) ✅

**Given** the graph is loaded
**When** `get_next_concepts("causal_learning")` is called
**Then** it returns `pc_algorithm` and `greedy_equivalence_search_ges` as PREREQUISITE_OF successors ✅

**Additional deliverables completed:**
- `graph/eci_toc_parser.py` — TOC → 79 Section nodes
- `graph/eci_concept_stars.py` — D3 "concept universe" visualization
- `graph/eci_visualize.py` — Interactive vis.js HTML knowledge graph
- `scripts/parse_subject_index.py` — Subject index parser
- `scripts/split_pdf_by_bookmarks.py` — PDF section splitter

---
