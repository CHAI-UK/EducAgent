---
story_id: '3.5'
epic: 'Epic 3: Concept Navigation & Discovery'
source: '_bmad-output/planning-artifacts/epics.md'
---

### Story 3.5: Concept Bookmarking

As a **learner**,
I want to bookmark concepts for later review,
So that I can flag topics I want to return to without losing them.

**Acceptance Criteria:**

**Given** a learner is on a concept page
**When** they click the bookmark icon
**Then** the concept is added to their bookmarks list (FR10)

**Given** a learner has bookmarked a concept
**When** they view their bookmarks list
**Then** the bookmarked concept appears and is clickable to navigate there

**Given** a learner refreshes the page
**When** bookmarks were set in-session
**Then** the bookmarks list is preserved (session-level persistence, FR10 MVP)

**Given** a learner clicks the bookmark icon on an already-bookmarked concept
**When** they click it
**Then** the bookmark is removed (toggle behaviour)

---
