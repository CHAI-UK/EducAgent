---
story_id: '3.2'
epic: 'Epic 3: Concept Navigation & Discovery'
source: '_bmad-output/planning-artifacts/epics.md'
---

### Story 3.2: Concept Search & Direct Jump

As a **learner**,
I want to search for any concept by name or keyword and jump directly to it,
So that I can access specific topics without browsing the full graph.

**Acceptance Criteria:**

**Given** the learner types "d-separation" in the search field
**When** results appear
**Then** `d_separation` is listed in the results (FR7)

**Given** the learner types a partial keyword like "back door"
**When** results appear
**Then** `back_door_criterion` is included in the results (FR7)

**Given** the learner selects a search result
**When** they click or press Enter on it
**Then** they are navigated directly to that concept's content page

**Given** the MVP has all concepts unlocked
**When** any concept is searched
**Then** it is accessible without unlock gating (FR7 MVP note)

---
