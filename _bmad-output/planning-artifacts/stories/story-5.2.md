---
story_id: '5.2'
epic: 'Epic 5: Agile Mode — Causal Problem Consulting'
source: '_bmad-output/planning-artifacts/epics.md'
---

### Story 5.2: Concept Identification & Mastery Gap Detection

As a **learner**,
I want the system to identify the causality concepts relevant to my problem and teach me any gaps,
So that I receive targeted preparation before the consulting response.

**Acceptance Criteria:**

**Given** a learner submits "I want to check if my CT scan study controls for confounders"
**When** the `concept_identifier` node runs
**Then** it identifies relevant concept nodes: `confounder`, `d_separation`, `back_door_criterion` (FR26)

**Given** relevant concepts are identified
**When** the `mastery_checker` node runs
**Then** it checks session mastery scores for each identified concept (FR27)

**Given** the learner has mastery < 0.5 for `d_separation`
**When** a mastery gap is detected
**Then** a brief, profile-adapted mini-teach on `d_separation` is delivered before the consulting response (FR27)

**Given** the mini-teach is displayed
**When** it renders
**Then** it is labelled "AI-generated" (NFR4)
**And** the underlying LLM prompt contains no PII — only `concept_id` and `profile_code` (NFR1)

---
