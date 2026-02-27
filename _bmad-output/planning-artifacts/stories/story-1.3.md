---
story_id: '1.3'
epic: 'Epic 1: Causality Concept Graph & Project Foundation'
source: '_bmad-output/planning-artifacts/epics.md'
---

### Story 1.3: Next.js Frontend Scaffold with API Connectivity

As a **developer**,
I want a  next.js 16 App Router frontend scaffold connected to the FastAPI backend,
So that the UI layer is ready for feature development with consistent API access patterns.

**Acceptance Criteria:**

**Given** the project is set up
**When** `npm run dev` starts
**Then** the Next.js app loads without errors and renders a placeholder home page

**Given** the frontend is running
**When** a fetch call is made to the FastAPI backend
**Then** the response is received without CORS errors

**Given** the app is built
**When** TypeScript compilation runs (`tsc --noEmit`)
**Then** it completes with zero errors

**Given** the App Router is configured
**Then** route structure includes `/` (home), `/learn` (study mode), and `/agile` (agile mode) with placeholder pages

**Given** Vercel AI SDK is installed
**Then** the SSE streaming utility is importable and correctly typed

---
