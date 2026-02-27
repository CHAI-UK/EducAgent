---
story_id: '2.1'
epic: 'Epic 2: Learner Profile & Session Management'
source: '_bmad-output/planning-artifacts/epics.md'
---

### Story 2.1: Profile Selection Screen

As a **learner**,
I want to see a profile selection screen as the first thing when I open EducAgent,
So that my learning experience is personalised from the very start without creating an account.

**Acceptance Criteria:**

**Given** the learner opens EducAgent
**When** the home page loads
**Then** the profile selection screen is displayed as the first screen (FR0)
**And** it shows background options: Computer Scientist, Radiologist, Physician, Statistician, and a "Custom" option (FR1)

**Given** the learner views the level options
**When** the profile screen renders
**Then** Beginner, Moderate, Expert, and a "Custom" option are displayed independently of background selection (FR2)

**Given** the learner selects a background and level
**When** they confirm their selection
**Then** they are navigated to the main learning view with their profile active

**Given** the learner selects "Custom" for background or level
**When** they enter a custom value
**Then** the system accepts it and uses it as their profile identifier

**Given** the profile selection UI is rendered
**When** navigated with keyboard only
**Then** all options are reachable and selectable via Tab and Enter (NFR9)

---
