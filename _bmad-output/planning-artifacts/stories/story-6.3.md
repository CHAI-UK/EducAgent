---
story_id: '6.3'
epic: 'Epic 6: Active-Interactive Study Mode *(Phase 2)*'
source: '_bmad-output/planning-artifacts/epics.md'
---

### Story 6.3: Learner Intervention & Critic Validation

As a **learner**,
I want to pause the dialogue and intervene with a correction,
So that I can actively practise identifying and fixing causal reasoning errors.

**Acceptance Criteria:**

**Given** the dialogue is streaming
**When** the learner clicks the "Intervene" button
**Then** the dialogue pauses and an input field appears for the learner's correction (FR20)

**Given** the learner submits a correction
**When** the Critic agent evaluates it
**Then** it returns a validation result: correct or incorrect (FR21)

**Given** the learner's correction is correct
**When** the Critic confirms it
**Then** an encouraging confirmation is shown
**And** the relevant concept's mastery score is incremented (FR22)

**Given** the learner's correction is incorrect
**When** the Critic explains it
**Then** a non-punitive explanation is provided without reducing mastery below the current score

---
