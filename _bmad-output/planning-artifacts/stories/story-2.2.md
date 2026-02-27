---
story_id: '2.2'
epic: 'Epic 2: Learner Profile & Session Management'
source: '_bmad-output/planning-artifacts/epics.md'
---

### Story 2.2: Profile-Adapted Content Loading

As a **learner**,
I want the system to load content adapted to my background and level,
So that explanations use analogies and framing relevant to my domain expertise.

**Acceptance Criteria:**

**Given** a learner has selected Computer Scientist / Moderate
**When** they navigate to a concept
**Then** the narrative content uses ML and probability theory analogies (FR3)

**Given** a learner has selected Radiologist / Beginner
**When** they navigate to the same concept
**Then** the narrative uses patient cohort / medical imaging analogies instead (FR3)

**Given** content is requested for a cached profile signature
**When** it is retrieved
**Then** it loads within 2 seconds (NFR6)

**Given** content for a profile is not yet cached
**When** it is first requested
**Then** the system generates it via the Tutor agent and caches it by `hash(concept_id + background + level)` for subsequent requests

---
