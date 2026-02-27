---
story_id: '1.2'
epic: 'Epic 1: Causality Concept Graph & Project Foundation'
source: '_bmad-output/planning-artifacts/epics.md'
---

### Story 1.2: FastAPI Backend Scaffold with Graph API

As a **developer**,
I want a FastAPI backend that loads the knowledge graph at startup and exposes query endpoints,
So that frontend and agent components can retrieve concept data reliably.

**Acceptance Criteria:**

**Given** the FastAPI app starts
**When** startup completes
**Then** `graph.pkl` is loaded into memory and accessible across all requests

**Given** the API is running
**When** `GET /api/v1/graph/concepts/{concept_id}/prerequisites` is called
**Then** it returns the correct predecessor concepts as JSON

**Given** the API is running
**When** `GET /api/v1/graph/chapters/{chapter}/concepts` is called
**Then** it returns all concept IDs for that chapter

**Given** the API is running
**When** `GET /health` is called
**Then** it returns HTTP 200 with graph load status and node/edge counts

**Given** any request is made
**Then** all responses include proper CORS headers for the Next.js frontend origin

---
