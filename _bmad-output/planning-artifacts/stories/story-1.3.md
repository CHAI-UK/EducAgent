---
story_id: '1.3'
epic: 'Epic 1: Causality Concept Graph & Project Foundation'
source: '_bmad-output/planning-artifacts/epics.md'
---

### Story 1.3: Next.js Frontend Scaffold with API Connectivity

As a **developer**,
I want a next.js 16 App Router frontend scaffold connected to the FastAPI backend,
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

## Tasks / Subtasks

- [x] T1: Next.js project scaffold
  - [x] T1.1 Create `frontend/package.json` with Next.js 15, React 19, Vercel AI SDK, Jest dev deps
  - [x] T1.2 Create `frontend/tsconfig.json`, `frontend/next.config.ts`, `frontend/.env.local.example`
  - [x] T1.3 Run `npm install` in `frontend/`
- [x] T2: App Router route pages
  - [x] T2.1 `frontend/app/layout.tsx` — root layout
  - [x] T2.2 `frontend/app/page.tsx` — `/` home placeholder
  - [x] T2.3 `frontend/app/learn/page.tsx` — `/learn` study mode placeholder
  - [x] T2.4 `frontend/app/agile/page.tsx` — `/agile` agile mode placeholder
- [x] T3: API client + streaming utility
  - [x] T3.1 `frontend/lib/api.ts` — typed fetch helper for FastAPI (health + concept endpoints)
  - [x] T3.2 `frontend/lib/streaming.ts` — re-export Vercel AI SDK SSE utility with local type alias
- [x] T4: Tests and TypeScript validation
  - [x] T4.1 `frontend/__tests__/api.test.ts` — Jest unit tests for `lib/api.ts` (mocked fetch)
  - [x] T4.2 `tsc --noEmit` passes with zero errors
  - [x] T4.3 Jest test suite passes (5/5)

---

## Dev Agent Record

### Implementation Plan

- Frontend at `frontend/` (project root sibling to `src/`)
- Next.js 15 App Router (TypeScript strict mode)
- API base URL from `NEXT_PUBLIC_API_URL` env var (default: `http://localhost:8000`)
- Vercel AI SDK `ai` package for SSE streaming (useStreamableValue / streamText)
- Jest + ts-jest for unit tests; `tsc --noEmit` for type-check
- No CORS proxy needed: browser fetches directly to FastAPI; CORS already enabled in backend

### Debug Log

### Completion Notes

---

## File List

- `frontend/package.json`
- `frontend/tsconfig.json`
- `frontend/next.config.ts`
- `frontend/.env.local.example`
- `frontend/app/layout.tsx`
- `frontend/app/page.tsx`
- `frontend/app/learn/page.tsx`
- `frontend/app/agile/page.tsx`
- `frontend/lib/api.ts`
- `frontend/lib/streaming.ts`
- `frontend/__tests__/api.test.ts`

---

## Change Log

- 2026-02-27: Story created from epics; status set to in-progress
- 2026-03-02: Story implemented and verified — status: **done**
  - 5/5 Jest tests pass, `tsc --noEmit` exits 0
