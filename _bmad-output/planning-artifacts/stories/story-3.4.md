---
story_id: '3.4'
epic: 'Epic 3: Concept Navigation & Discovery'
source: '_bmad-output/planning-artifacts/epics.md'
---

### Story 3.4: Next Concept Recommendation

As a **learner**,
I want the system to suggest what to study next based on the knowledge graph,
So that I follow a logical learning path through Pearl's causality concepts.

**Acceptance Criteria:**

**Given** a learner reaches the end of a concept page
**When** next concepts are shown
**Then** they are based on PREREQUISITE_OF and NEXT_IN_SEQUENCE graph edges (FR9)

**Given** a learner is at `d_separation`
**When** next concepts are displayed
**Then** `back_door_criterion` and `front_door_criterion` appear as recommendations (FR9)

**Given** next concept recommendations are displayed
**When** the learner clicks one
**Then** they navigate to that concept's page

---
