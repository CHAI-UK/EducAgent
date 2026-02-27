---
story_id: '3.3'
epic: 'Epic 3: Concept Navigation & Discovery'
source: '_bmad-output/planning-artifacts/epics.md'
---

### Story 3.3: Prerequisite Chain Display

As a **learner**,
I want to see which concepts I should know before studying a new one,
So that I can review gaps before diving in and build understanding in the right order.

**Acceptance Criteria:**

**Given** a learner navigates to `d_separation`
**When** the concept page loads
**Then** its prerequisites are displayed (e.g. `conditional_independence`, `bayesian_networks_probabilistic`) (FR8)

**Given** prerequisites are shown
**When** the learner clicks a prerequisite concept
**Then** they navigate to that concept's page

**Given** a concept has no prerequisites
**When** its page loads
**Then** the prerequisites section is either hidden or shows "No prerequisites required"

---
