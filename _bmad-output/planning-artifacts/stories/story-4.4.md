---
story_id: '4.4'
epic: 'Epic 4: Passive-Interactive Study Mode & Assessment'
source: '_bmad-output/planning-artifacts/epics.md'
---

### Story 4.4: Per-Concept Mastery Tracking

As a **learner**,
I want my mastery of each concept tracked across quizzes and interactions,
So that I can see how well I understand each topic throughout my session.

**Acceptance Criteria:**

**Given** a learner has not visited a concept
**When** they view their progress
**Then** that concept shows status "unseen" (FR31)

**Given** a learner has started a concept but not completed all quizzes
**When** they view progress
**Then** that concept shows status "in-progress" (FR31)

**Given** a learner answers all inline quizzes for a concept correctly
**When** mastery is updated
**Then** the concept mastery score increases towards 1.0 (FR17)

**Given** a learner's mastery scores are stored in session state
**Then** no PII is included — only `concept_id` and score float (NFR1)

---
