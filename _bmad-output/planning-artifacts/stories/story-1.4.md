---
story_id: '1.4'
epic: 'Epic 1: Causality Concept Graph & Project Foundation'
source: '_bmad-output/planning-artifacts/epics.md'
---

### Story 1.4: LangGraph Agent Skeleton + OpenRouter Integration

As a **developer**,
I want LangGraph `StudyModeGraph` and `AgileModeGraph` skeletons wired to OpenRouter,
So that agent invocations follow the defined topology and LLM routing is correct from day one.

**Acceptance Criteria:**

**Given** `StudyModeGraph` is invoked with a profile and concept_id
**When** it executes
**Then** nodes fire in order: `profile_loader → concept_retriever → prerequisite_checker → tutor_generator → critic_validator → content_renderer`

**Given** `AgileModeGraph` is invoked with a problem description
**When** it executes
**Then** nodes fire in order: `problem_intake → concept_identifier → mastery_checker → mini_teacher → direct_consultant → response_formatter`

**Given** OpenRouter is configured
**When** the Tutor node calls the LLM
**Then** `anthropic/claude-sonnet-4-6` is the primary model; `openai/gpt-4.1` is the fallback (NFR11)

**Given** a provider failure is simulated
**When** the primary model returns an error
**Then** the fallback model is invoked automatically within 5 seconds without surfacing the error to the caller (NFR11)

**Given** a session is initialised
**When** the session state schema is created
**Then** it contains `session_id`, `profile`, `mastery` dict, and `history` list — with no PII fields (NFR1)

---
