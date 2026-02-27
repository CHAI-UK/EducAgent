---
story_id: '7.2'
epic: 'Epic 7: Admin Dashboard & Analytics *(Phase 2)*'
source: '_bmad-output/planning-artifacts/epics.md'
---

### Story 7.2: Tutor Prompt Template Editor

As an **admin**,
I want to edit the Tutor agent's prompt template for specific concepts,
So that I can improve content quality for concept-profile combinations where learners are struggling.

**Acceptance Criteria:**

**Given** the admin navigates to a concept in the admin panel
**When** they open the prompt template editor
**Then** the current Tutor prompt template for that concept is displayed (FR36)

**Given** the admin edits the template and saves
**When** the next Tutor invocation for that concept runs
**Then** it uses the updated template

**Given** a template is updated
**When** the admin views version history
**Then** the previous version is accessible so changes are reversible

**Given** the template editor is used
**Then** no learner PII or session data is exposed (NFR1)

---
