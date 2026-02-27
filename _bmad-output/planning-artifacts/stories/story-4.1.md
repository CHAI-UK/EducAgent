---
story_id: '4.1'
epic: 'Epic 4: Passive-Interactive Study Mode & Assessment'
source: '_bmad-output/planning-artifacts/epics.md'
---

### Story 4.1: Tutor Content Generation & Caching Pipeline

As a **developer**,
I want the Tutor agent to generate and cache concept content per profile signature,
So that learners receive fast, profile-adapted content on every visit.

**Acceptance Criteria:**

**Given** a `concept_id`, background, and level are provided
**When** the `StudyModeGraph` Tutor node is invoked
**Then** it generates a Content JSON with sections: narrative, inline_quiz (2–3), diagram (if applicable), end_quiz, and next_concepts (FR11, FR12, FR14, FR15)

**Given** content has been generated for a profile signature
**When** the same `hash(concept_id + background + level)` is requested again
**Then** it is returned from the in-memory cache without invoking the LLM (NFR6)

**Given** cached content is returned
**When** measured from request to first byte
**Then** it loads within 2 seconds (NFR6)

**Given** content is generated
**When** the Critic validator node runs
**Then** it reviews accuracy and either approves or triggers a revision loop (max 2 revisions per architecture)
**And** an audit log entry is written (NFR3)

---
