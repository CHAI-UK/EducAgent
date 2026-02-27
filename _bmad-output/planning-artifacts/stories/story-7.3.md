---
story_id: '7.3'
epic: 'Epic 7: Admin Dashboard & Analytics *(Phase 2)*'
source: '_bmad-output/planning-artifacts/epics.md'
---

### Story 7.3: Anonymised Data Export

As an **admin**,
I want to export anonymised session data,
So that I can analyse learning outcomes and publish research findings.

**Acceptance Criteria:**

**Given** the admin requests a data export
**When** the export is generated
**Then** it includes: concept mastery scores, completion rates, and background × level distribution — all anonymised (FR37)

**Given** the export is inspected
**Then** it contains no PII (no names, emails, or institution identifiers) (NFR1, GDPR)

**Given** the export file is produced
**When** the admin downloads it
**Then** it is in a structured format (CSV or JSON) suitable for statistical analysis

**Given** the export is requested
**When** an audit log entry is checked
**Then** the export action is recorded with timestamp and admin identifier (NFR3)
