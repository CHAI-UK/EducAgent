---
story_id: '6.4'
epic: 'Epic 6: Active-Interactive Study Mode *(Phase 2)*'
source: '_bmad-output/planning-artifacts/epics.md'
---

### Story 6.4: Dialogue Replay & Variation

As a **learner**,
I want to replay a dialogue or request a new variation of it,
So that I can reinforce learning through repetition with different misconception patterns.

**Acceptance Criteria:**

**Given** a dialogue has completed
**When** the learner clicks "Replay"
**Then** the same dialogue replays from the beginning (FR24)

**Given** a dialogue has completed
**When** the learner clicks "New Variation"
**Then** a new dialogue is generated for the same concept using a different misconception from the library (FR24)

**Given** a new variation is requested
**Then** it uses a different COMMONLY_CONFUSED pair or `misconceptions[]` entry from the concept node

---
