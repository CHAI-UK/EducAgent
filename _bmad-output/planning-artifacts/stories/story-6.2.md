---
story_id: '6.2'
epic: 'Epic 6: Active-Interactive Study Mode *(Phase 2)*'
source: '_bmad-output/planning-artifacts/epics.md'
---

### Story 6.2: Streaming Tutor ↔ Dumb Student Dialogue

As a **learner**,
I want to watch a live streaming dialogue between the Tutor and Dumb Student agents,
So that I can observe misconceptions being introduced and understand the correct reasoning.

**Acceptance Criteria:**

**Given** the active-interactive pathway is active
**When** the dialogue begins
**Then** Tutor and Dumb Student messages stream in real time via SSE (FR19)
**And** the two agents are visually distinguished by different labels, colours, or avatars

**Given** the dialogue is streaming
**When** the Dumb Student speaks
**Then** its messages express a misconception drawn from the misconception library linked to the concept node (FR23)

**Given** the dialogue streams
**When** the first token arrives
**Then** it is displayed within 3 seconds of activation (NFR7)

**Given** dialogue content is displayed
**Then** all Tutor and Dumb Student output is labelled "AI-generated" (NFR4)

---
