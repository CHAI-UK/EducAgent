---
story_id: '3.1'
epic: 'Epic 3: Concept Navigation & Discovery'
source: '_bmad-output/planning-artifacts/epics.md'
---

### Story 3.1: Knowledge Graph Navigation View

As a **learner**,
I want to browse the causality knowledge graph organised by chapter,
So that I can understand the full scope of what I'm learning and navigate to any concept.

**Acceptance Criteria:**

**Given** a learner opens the navigation view
**When** the page loads
**Then** concepts are displayed organised by chapter (FR6)

**Given** the navigation view is loaded
**When** a learner clicks on a concept
**Then** they are navigated to that concept's content page

**Given** Chapter 1 contains 4 concepts (per ECI graph: random_variable, structural_causal_model_scm, conditional_independence, directed_acyclic_graph_dag)
**When** the learner browses Chapter 1
**Then** all 4 concepts are accessible from the navigation view

**Given** the navigation view is rendered
**When** accessed via keyboard
**Then** all concept items are focusable and activatable with keyboard alone (NFR8, NFR9)

---
