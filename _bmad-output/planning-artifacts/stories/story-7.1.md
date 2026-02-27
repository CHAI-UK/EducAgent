---
story_id: '7.1'
epic: 'Epic 7: Admin Dashboard & Analytics *(Phase 2)*'
source: '_bmad-output/planning-artifacts/epics.md'
---

### Story 7.1: Admin Mastery Analytics Dashboard

As an **admin**,
I want to view aggregate mastery analytics segmented by background profile and level,
So that I can identify which learner groups struggle with which concepts and prioritise content improvements.

**Acceptance Criteria:**

**Given** an admin accesses the analytics dashboard
**When** the page loads
**Then** aggregate mastery data is displayed segmented by background × level (FR35)

**Given** mastery data is displayed
**When** filtered by "Radiologist / Beginner"
**Then** the mastery distribution across Chapter 1 concepts is shown for that profile combination

**Given** the dashboard data is rendered
**Then** it contains no PII — only `profile_code × concept_id × aggregate_mastery_score` (NFR1, NFR3)

---
