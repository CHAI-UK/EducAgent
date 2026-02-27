---
story_id: '2.3'
epic: 'Epic 2: Learner Profile & Session Management'
source: '_bmad-output/planning-artifacts/epics.md'
---

### Story 2.3: Profile Switching Without Position Loss

As a **learner**,
I want to change my background or level at any point,
So that I can explore how the same concept is explained to different audiences without losing my place.

**Acceptance Criteria:**

**Given** a learner is on a concept page
**When** they switch background from Computer Scientist to Radiologist
**Then** the content reloads with Radiologist-adapted content for the same concept (FR4)
**And** their current concept position is preserved — not reset to chapter start (FR4)

**Given** a learner is on a concept page
**When** they switch level from Beginner to Expert
**Then** the content reloads with Expert-level framing for the same concept
**And** mastery scores accumulated in the session are preserved (FR4)

**Given** the profile picker is accessible from any page
**When** the learner opens it
**Then** the currently active background and level are shown as selected

---
