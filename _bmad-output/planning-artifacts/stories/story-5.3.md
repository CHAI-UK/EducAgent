---
story_id: '5.3'
epic: 'Epic 5: Agile Mode — Causal Problem Consulting'
source: '_bmad-output/planning-artifacts/epics.md'
---

### Story 5.3: Structured Consulting Response & Follow-Up

As a **learner**,
I want a structured consulting response with the ability to ask follow-up questions,
So that I get actionable guidance and can explore the reasoning in depth.

**Acceptance Criteria:**

**Given** concept gaps have been addressed (or mastery is sufficient)
**When** the `direct_consultant` node runs
**Then** a structured consulting response is generated addressing the learner's specific problem (FR28)

**Given** the consulting response is displayed
**When** the learner reads it
**Then** it explicitly references the relevant concepts (e.g. back-door criterion, adjustment set) (FR28)

**Given** the consulting response is shown
**When** the learner types a follow-up question
**Then** the system responds conversationally within the same Agile Mode session (FR29)

**Given** an Agile Mode session completes
**When** the problem is resolved
**Then** the problem and consulting exchange are logged as a worked example linked to the relevant concept nodes (FR30)

**Given** the consulting response is displayed
**Then** it is labelled "AI-generated" (NFR4)
**And** the first token streams within 3 seconds of submission (NFR7)

---
