---
story_id: '2.4'
epic: 'Epic 2: Learner Profile & Session Management'
source: '_bmad-output/planning-artifacts/epics.md'
---

### Story 2.4: In-Browser Session State Persistence

As a **learner**,
I want my session progress preserved if I refresh the page,
So that I don't lose my mastery scores or current position mid-session.

**Acceptance Criteria:**

**Given** a learner has visited 3 concepts and answered quizzes
**When** they refresh the page
**Then** their mastery scores for those concepts are restored from in-browser storage (FR5)

**Given** a learner is viewing a concept page
**When** they refresh
**Then** the page returns to the same concept — not the profile selection screen (FR5)

**Given** a learner's session is persisted in-browser
**Then** no mastery data, session ID, or profile code is sent to a server — stored client-side only (NFR1, stateless MVP)

**Given** LangGraph checkpointing is used
**When** a network interruption occurs mid-session
**Then** on reconnection the learner's in-progress mastery is not lost (NFR12)

---
