---
story_id: '1.5'
epic: 'Epic 1: Causality Concept Graph & Project Foundation'
source: '_bmad-output/planning-artifacts/epics.md'
---

### Story 1.5: Audit Logging Foundation

As a **compliance officer**,
I want every AI-generated decision logged with timestamps,
So that the platform meets EU AI Act HIGH RISK classification requirements from day one.

**Acceptance Criteria:**

**Given** any Tutor output is generated
**When** content is produced
**Then** an audit log entry is written containing: `event_type`, `concept_id`, `profile_code`, `model_used`, `timestamp` (ISO 8601), `output_hash` — never PII (NFR3, NFR1)

**Given** any Critic validation runs
**When** it produces a result
**Then** an audit log entry records: `validation_result`, `concept_id`, `timestamp`

**Given** any mastery score update occurs
**When** it is written to session state
**Then** an audit log entry records: `concept_id`, `old_score`, `new_score`, `trigger_event`, `timestamp`

**Given** the API serves any Tutor-generated content
**When** the response is returned
**Then** it includes an `X-AI-Generated: true` header and the UI renders an "AI-generated" label on all Tutor output (NFR4)

---
