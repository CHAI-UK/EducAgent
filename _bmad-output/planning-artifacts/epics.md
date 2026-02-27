---
stepsCompleted:
  - step-01-validate-prerequisites
  - step-02-design-epics
  - step-03-create-stories
  - step-04-final-validation
status: complete
inputDocuments:
  - '_bmad-output/planning-artifacts/prd.md'
  - '_bmad-output/planning-artifacts/architecture.md'
workflowType: 'epics-and-stories'
project_name: 'EducAgent'
user_name: 'Yuyang'
date: '2026-02-24'
---

# EducAgent - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for EducAgent, decomposing the requirements from the PRD and Architecture into implementable stories.

## Requirements Inventory

### Functional Requirements

FR0: First screen should be the profile selection (profile 1, 2, and more)
FR1: Learner can select a background profile (Computer Scientist, Radiologist, Physician, Statistician) from a built-in picker without creating an account, or add their custom background.
FR2: Learner can select an expertise level (Beginner, Moderate, Expert) independent of background selection, or add their custom level.
FR3: System loads content pre-adapted to the selected background × level profile combination.
FR4: Learner can change background or level at any point; content adapts accordingly without losing current position.
FR5: System preserves session state in-browser (stateless MVP) so a page refresh does not reset mastery progress.
FR6: Learner can navigate the knowledge points from the knowledge graph.
FR7: Learner can jump directly to any concept node by name or keyword search (MVP: all unlocked; Growth: unlock gating).
FR8: System displays concept prerequisites before presenting a concept, allowing learner to review gaps first.
FR9: System recommends a next concept based on NEXT_IN_SEQUENCE and PREREQUISITE_OF graph edges.
FR10: Learner can bookmark concepts for later review (session-level for MVP; persistent from Growth Phase).
FR11: Learner can read narrative content for each concept rendered in rich text with domain-adapted analogies.
FR12: System embeds 2–3 inline quiz checkpoints within each concept's narrative.
FR13: System provides immediate, encouraging feedback on inline quiz answers — explanation included for both correct and incorrect responses.
FR14: Learner can view a domain-adapted worked example (CS / medical / statistical framing) for each concept.
FR15: Learner can view a diagram or DAG description for concepts that have visual representations.
FR16: System presents an end-of-chapter comprehensive test upon completion of all concepts in a chapter.
FR17: System tracks per-concept mastery score (0.0–1.0) within the current session.
FR18: Learner can activate the active-interactive pathway for any concept, triggering a Tutor ↔ Dumb Student dialogue.
FR19: System streams the Tutor and Dumb Student dialogue in real time, visually distinguishing the two agents.
FR20: Learner can pause the dialogue at any point and intervene with a correction or clarification.
FR21: Critic agent validates the learner's intervention — confirms if correct, explains if not.
FR22: Correct learner interventions increment mastery score for the relevant concept.
FR23: Dumb Student agent expresses misconceptions drawn from the curated misconception library linked to the concept graph.
FR24: Learner can replay a dialogue or request a new dialogue variation for the same concept.
FR25: Learner can switch to Agile Mode from any screen and describe a causal problem in natural language.
FR26: System identifies relevant concept nodes from the Causality Concept Graph based on the problem description.
FR27: System checks learner mastery of relevant concepts; if gaps exist, delivers a targeted mini-teach before consulting.
FR28: System provides a structured consulting response to the learner's causal problem.
FR29: Learner can ask follow-up questions in a conversational interface within Agile Mode.
FR30: System logs each Agile Mode problem as a worked example linked to relevant concept nodes.
FR31: System displays per-concept mastery status (unseen / in-progress / mastered) across all explored concepts.
FR32: System generates an end-of-chapter test spanning all concepts in the chapter.
FR33: System provides a chapter completion summary showing mastery distribution and concepts to revisit.
FR34: System awards encouraging completion indicators (badges, progress milestones) upon chapter test completion.
FR35: Admin can view aggregate mastery analytics segmented by background profile and level.
FR36: Admin can edit Tutor agent prompt templates for specific concepts to improve content quality.
FR37: Admin can export anonymised session data (concept mastery, completion rates) for research analysis.

### NonFunctional Requirements

NFR1: No PII (name, email, institution) included in any prompt sent to external LLM providers. Only anonymised concept IDs, mastery scores, and profile codes transmitted.
NFR2: All API communication between frontend and backend uses HTTPS/TLS 1.2+.
NFR3: Audit logs record all AI-generated content decisions (Tutor output, Critic validation, mastery updates) with timestamps — required for EU AI Act HIGH RISK compliance.
NFR4: All AI-generated content is labelled "AI-generated" in the UI (EU AI Act transparency requirement).
NFR5: No emotion recognition or inferred affective state derived from learner behaviour.
NFR6: Pre-generated cached concept content (by profile signature) loads within 2 seconds for cached profiles.
NFR7: Real-time Tutor/Dumb Student dialogue streams first token within 3 seconds; OpenRouter fallback activates within 5 seconds on provider failure.
NFR8: UI meets WCAG 2.1 Level AA for all primary learner flows (profile selection, reading mode, quiz interaction).
NFR9: All quiz interactions are keyboard-navigable; no mouse-only interactions.
NFR10: Colour is not the sole means of conveying quiz feedback — correct/incorrect states include text labels and icons.
NFR11: OpenRouter integration implements automatic provider fallback; single-provider failure must not surface to the learner.
NFR12: LangGraph checkpointing preserves session state across network interruptions; learner does not lose in-progress concept mastery on page reload.

### Additional Requirements

- Greenfield project — no starter template; stack is Next.js 14 App Router (TypeScript) + FastAPI (Python)
- Knowledge Graph build pipeline: `python build_knowledge_graph.py` → produces `graph.pkl` (162KB), `graph.json` (535KB), `concepts_by_chapter.json`, `graph_summary.json`
- NetworkX in-memory graph (672 nodes, 3,303 edges) loaded at FastAPI startup from `graph.pkl`
- Content caching by `hash(concept_id + background + level)` key; MVP = in-memory Python dict
- LangGraph v1.0 two graphs: `StudyModeGraph` (profile_loader → concept_retriever → prerequisite_checker → tutor_generator → critic_validator → content_renderer) and `AgileModeGraph` (problem_intake → concept_identifier → mastery_checker → mini_teacher → direct_consultant → response_formatter)
- OpenRouter multi-provider LLM routing: Tutor = claude-sonnet-4-6 / gpt-4.1; Critic = gemini-2.0-flash / claude-haiku-4-5; Quiz gen = gpt-4.1-mini; Answer eval = claude-haiku-4-5; Embeddings = text-embedding-3-small
- Server-Sent Events (SSE) for real-time streaming of Tutor/Dumb Student dialogue
- Structured Content JSON format per concept per profile: sections array of type narrative / inline_quiz / diagram, plus end_quiz and next_concepts
- Qdrant self-hosted vector store for subsection-level embeddings
- Audit logging infrastructure required from day one for EU AI Act HIGH RISK classification (target Aug 2026)
- Graph Neo4j migration path via `graph.json` export (py2neo ingest) — MVP uses NetworkX only
- PREREQUISITE_OF expansion via LLM (`graph/llm_prerequisite_extractor.py`) — planned enhancement post-MVP

### FR Coverage Map

| FR | Epic | Description |
|---|---|---|
| FR0 | E2 | Profile selection as first screen |
| FR1 | E2 | Background picker |
| FR2 | E2 | Level picker |
| FR3 | E2 | Content loads per profile |
| FR4 | E2 | Profile switch without position loss |
| FR5 | E2 | Session state preserved in-browser |
| FR6 | E3 | Knowledge graph navigation |
| FR7 | E3 | Concept search / direct jump |
| FR8 | E3 | Prerequisites display before concept |
| FR9 | E3 | Next concept recommendation |
| FR10 | E3 | Bookmarks (session-level MVP) |
| FR11 | E4 | Narrative content (profile-adapted) |
| FR12 | E4 | Inline quiz checkpoints (2–3 per concept) |
| FR13 | E4 | Encouraging quiz feedback |
| FR14 | E4 | Domain-adapted worked example |
| FR15 | E4 | Diagram / DAG description |
| FR16 | E4 | End-of-chapter comprehensive test |
| FR17 | E4 | Per-concept mastery score tracking |
| FR18 | E6 | Activate active-interactive pathway |
| FR19 | E6 | Streaming Tutor ↔ Dumb Student dialogue |
| FR20 | E6 | Learner pause + intervention |
| FR21 | E6 | Critic validation of intervention |
| FR22 | E6 | Mastery increment on correct intervention |
| FR23 | E6 | Dumb Student misconception library |
| FR24 | E6 | Replay / new dialogue variation |
| FR25 | E5 | Agile Mode entry + problem description |
| FR26 | E5 | Concept node identification from problem |
| FR27 | E5 | Mastery gap detection + mini-teach |
| FR28 | E5 | Structured consulting response |
| FR29 | E5 | Follow-up conversational interface |
| FR30 | E5 | Worked example logging |
| FR31 | E4 | Per-concept mastery status display |
| FR32 | E4 | Chapter test generation |
| FR33 | E4 | Chapter completion summary |
| FR34 | E4 | Completion badges / indicators |
| FR35 | E7 | Admin mastery analytics |
| FR36 | E7 | Admin prompt template editing |
| FR37 | E7 | Anonymised data export |

## Epic List

### Epic 1: Causality Concept Graph & Project Foundation
The graph build pipeline is the first deliverable — running `python build_knowledge_graph.py` to produce the full 672-node / 3,303-edge NetworkX graph (Section + Concept nodes, all edge types including PREREQUISITE_OF and COMMONLY_CONFUSED) is Story 1.1. Everything else in Epic 1 — Next.js + FastAPI scaffold, LangGraph skeletons, OpenRouter wiring, Qdrant, audit logging — is scaffolded around and after the graph. No downstream epic can deliver value without the graph queryable.
Delivers: *A running application where the full Causality Concept Graph is built, loaded in-memory at FastAPI startup, and queryable via the Tutor Agent Graph API — the knowledge backbone for all learning features.*
**FRs covered:** None directly | **NFRs:** NFR1, NFR2, NFR3, NFR11
**Story order:** 1) Graph build pipeline · 2) FastAPI scaffold + graph at startup · 3) Next.js scaffold + API connectivity · 4) LangGraph skeleton + OpenRouter integration · 5) Qdrant setup + audit logging foundation

### Epic 2: Learner Profile & Session Management
Learners can select their background × level profile from the first screen, switch profiles without losing position, and have session state preserved across page reloads.
Delivers: *Personalised, persistent learning sessions without requiring an account.*
**FRs covered:** FR0, FR1, FR2, FR3, FR4, FR5 | **NFRs:** NFR8, NFR9, NFR12

### Epic 3: Concept Navigation & Discovery
Learners can navigate the full causality knowledge graph, search concepts by name or keyword, view prerequisite chains before diving in, receive next-concept recommendations, and bookmark items for later review.
Delivers: *Self-directed exploration of Pearl's causality knowledge graph.*
**FRs covered:** FR6, FR7, FR8, FR9, FR10 | **NFRs:** NFR8, NFR9

### Epic 4: Passive-Interactive Study Mode & Assessment
Learners can read rich, profile-adapted narrative content per concept, engage with inline quizzes with encouraging feedback, view worked examples and diagrams, take end-of-chapter tests, track per-concept mastery, see progress summaries, and earn completion indicators.
Delivers: *The full core MVP learning experience — Chapter 1 complete.*
**FRs covered:** FR11, FR12, FR13, FR14, FR15, FR16, FR17, FR31, FR32, FR33, FR34 | **NFRs:** NFR4, NFR6, NFR8, NFR9, NFR10

### Epic 5: Agile Mode — Causal Problem Consulting
Learners can switch to Agile Mode from any screen, describe a real causal problem in natural language, receive concept identification + mastery-gap mini-teaches, get a structured consulting response, ask follow-up questions, and have worked examples logged.
Delivers: *Applied causal consulting for researchers and practitioners — the MVP chatbot-style Agile Mode.*
**FRs covered:** FR25, FR26, FR27, FR28, FR29, FR30 | **NFRs:** NFR1, NFR4, NFR7

### Epic 6: Active-Interactive Study Mode *(Phase 2)*
Learners can activate live Tutor ↔ Dumb Student streaming dialogues for any concept, pause and intervene with corrections, receive Critic validation, earn mastery credit for correct interventions, and replay or request new dialogue variations.
Delivers: *The novel active error-correction learning paradigm — the Dumb Student live.*
**FRs covered:** FR18, FR19, FR20, FR21, FR22, FR23, FR24 | **NFRs:** NFR4, NFR7

### Epic 7: Admin Dashboard & Analytics *(Phase 2)*
Administrators can view aggregate mastery analytics segmented by background × level, edit Tutor prompt templates for specific concepts, and export anonymised session data for research analysis.
Delivers: *Institutional oversight and research data infrastructure for the user study.*
**FRs covered:** FR35, FR36, FR37 | **NFRs:** NFR3

---

## Epic 1: Causality Concept Graph & Project Foundation

The graph build pipeline is the first deliverable — the full 672-node / 3,303-edge NetworkX graph is built, loaded in-memory at FastAPI startup, and queryable via the Tutor Agent Graph API. The web stack scaffold, LangGraph agent skeletons, OpenRouter wiring, and audit logging foundation are all built around it. No downstream epic delivers value without this in place.

### Story 1.1: Knowledge Graph Build Pipeline & Validation

As a **developer**,
I want the Causality Concept Graph built and validated from Pearl's textbook data,
So that all downstream features have a reliable, queryable knowledge backbone.

**Acceptance Criteria:**

**Given** the project is set up
**When** `python build_knowledge_graph.py` is run
**Then** it produces `graph.pkl` (≤200KB), `graph.json`, `concepts_by_chapter.json`, and `graph_summary.json`

**Given** `graph.pkl` is built
**When** it is loaded via `load_graph()`
**Then** the graph contains 672 nodes (226 Section + 446 Concept) and 3,303 edges

**Given** the graph is loaded
**When** `get_prerequisites("d_separation")` is called
**Then** it returns the correct PREREQUISITE_OF predecessor concepts

**Given** the graph is loaded
**When** `get_chapter_concepts(1)` is called
**Then** it returns the 159 concept nodes for Chapter 1

**Given** the graph is loaded
**When** `get_next_concepts("back_door_criterion")` is called
**Then** it returns the correct PREREQUISITE_OF downstream successors

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

### Story 1.3: Next.js Frontend Scaffold with API Connectivity

As a **developer**,
I want a Next.js 14 App Router frontend scaffold connected to the FastAPI backend,
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

## Epic 2: Learner Profile & Session Management

Learners can select their background × level profile from the first screen, switch profiles without losing position, and have session state preserved across page reloads.
Delivers: *Personalised, persistent learning sessions without requiring an account.*

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

### Story 2.2: Profile-Adapted Content Loading

As a **learner**,
I want the system to load content adapted to my background and level,
So that explanations use analogies and framing relevant to my domain expertise.

**Acceptance Criteria:**

**Given** a learner has selected Computer Scientist / Moderate
**When** they navigate to a concept
**Then** the narrative content uses ML and probability theory analogies (FR3)

**Given** a learner has selected Radiologist / Beginner
**When** they navigate to the same concept
**Then** the narrative uses patient cohort / medical imaging analogies instead (FR3)

**Given** content is requested for a cached profile signature
**When** it is retrieved
**Then** it loads within 2 seconds (NFR6)

**Given** content for a profile is not yet cached
**When** it is first requested
**Then** the system generates it via the Tutor agent and caches it by `hash(concept_id + background + level)` for subsequent requests

---

### Story 2.3: Profile Switching Without Position Loss

As a **learner**,
I want to change my background or level at any point,
So that I can explore how the same concept is explained to different audiences without losing my place.

**Acceptance Criteria:**

**Given** a learner is on a concept page
**When** they switch background from Computer Scientist to Radiologist
**Then** the content reloads with Radiologist-adapted content for the same concept (FR4)
**And** their current concept position is preserved — not reset to chapter start (FR4)

**Given** a learner is on a concept page
**When** they switch level from Beginner to Expert
**Then** the content reloads with Expert-level framing for the same concept
**And** mastery scores accumulated in the session are preserved (FR4)

**Given** the profile picker is accessible from any page
**When** the learner opens it
**Then** the currently active background and level are shown as selected

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

## Epic 3: Concept Navigation & Discovery

Learners can navigate the full causality knowledge graph, search concepts by name or keyword, view prerequisite chains, receive next-concept recommendations, and bookmark items for later review.
Delivers: *Self-directed exploration of Pearl's causality knowledge graph.*

### Story 3.1: Knowledge Graph Navigation View

As a **learner**,
I want to browse the causality knowledge graph organised by chapter,
So that I can understand the full scope of what I'm learning and navigate to any concept.

**Acceptance Criteria:**

**Given** a learner opens the navigation view
**When** the page loads
**Then** concepts are displayed organised by chapter (FR6)

**Given** the navigation view is loaded
**When** a learner clicks on a concept
**Then** they are navigated to that concept's content page

**Given** Chapter 1 contains 159 concepts
**When** the learner browses Chapter 1
**Then** all 159 concepts are accessible from the navigation view

**Given** the navigation view is rendered
**When** accessed via keyboard
**Then** all concept items are focusable and activatable with keyboard alone (NFR8, NFR9)

---

### Story 3.2: Concept Search & Direct Jump

As a **learner**,
I want to search for any concept by name or keyword and jump directly to it,
So that I can access specific topics without browsing the full graph.

**Acceptance Criteria:**

**Given** the learner types "d-separation" in the search field
**When** results appear
**Then** `d_separation` is listed in the results (FR7)

**Given** the learner types a partial keyword like "back door"
**When** results appear
**Then** `back_door_criterion` is included in the results (FR7)

**Given** the learner selects a search result
**When** they click or press Enter on it
**Then** they are navigated directly to that concept's content page

**Given** the MVP has all concepts unlocked
**When** any concept is searched
**Then** it is accessible without unlock gating (FR7 MVP note)

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

### Story 3.4: Next Concept Recommendation

As a **learner**,
I want the system to suggest what to study next based on the knowledge graph,
So that I follow a logical learning path through Pearl's causality concepts.

**Acceptance Criteria:**

**Given** a learner reaches the end of a concept page
**When** next concepts are shown
**Then** they are based on PREREQUISITE_OF and NEXT_IN_SEQUENCE graph edges (FR9)

**Given** a learner is at `d_separation`
**When** next concepts are displayed
**Then** `back_door_criterion` and `front_door_criterion` appear as recommendations (FR9)

**Given** next concept recommendations are displayed
**When** the learner clicks one
**Then** they navigate to that concept's page

---

### Story 3.5: Concept Bookmarking

As a **learner**,
I want to bookmark concepts for later review,
So that I can flag topics I want to return to without losing them.

**Acceptance Criteria:**

**Given** a learner is on a concept page
**When** they click the bookmark icon
**Then** the concept is added to their bookmarks list (FR10)

**Given** a learner has bookmarked a concept
**When** they view their bookmarks list
**Then** the bookmarked concept appears and is clickable to navigate there

**Given** a learner refreshes the page
**When** bookmarks were set in-session
**Then** the bookmarks list is preserved (session-level persistence, FR10 MVP)

**Given** a learner clicks the bookmark icon on an already-bookmarked concept
**When** they click it
**Then** the bookmark is removed (toggle behaviour)

---

## Epic 4: Passive-Interactive Study Mode & Assessment

Learners can read rich, profile-adapted narrative content, engage with inline quizzes, view worked examples and diagrams, take end-of-chapter tests, track mastery, and earn completion indicators.
Delivers: *The full core MVP learning experience — Chapter 1 complete.*

### Story 4.1: Tutor Content Generation & Caching Pipeline

As a **developer**,
I want the Tutor agent to generate and cache concept content per profile signature,
So that learners receive fast, profile-adapted content on every visit.

**Acceptance Criteria:**

**Given** a `concept_id`, background, and level are provided
**When** the `StudyModeGraph` Tutor node is invoked
**Then** it generates a Content JSON with sections: narrative, inline_quiz (2–3), diagram (if applicable), end_quiz, and next_concepts (FR11, FR12, FR14, FR15)

**Given** content has been generated for a profile signature
**When** the same `hash(concept_id + background + level)` is requested again
**Then** it is returned from the in-memory cache without invoking the LLM (NFR6)

**Given** cached content is returned
**When** measured from request to first byte
**Then** it loads within 2 seconds (NFR6)

**Given** content is generated
**When** the Critic validator node runs
**Then** it reviews accuracy and either approves or triggers a revision loop (max 2 revisions per architecture)
**And** an audit log entry is written (NFR3)

---

### Story 4.2: Concept Content Page Rendering

As a **learner**,
I want to read rich, profile-adapted narrative content for each concept,
So that I understand causality through analogies from my own domain.

**Acceptance Criteria:**

**Given** a learner with Computer Scientist / Moderate profile navigates to `back_door_criterion`
**When** the content page renders
**Then** they see narrative sections with ML-framing analogies (FR11)
**And** a domain-adapted worked example (FR14)
**And** a DAG description or diagram where the concept has a visual representation (FR15)

**Given** AI-generated content is displayed
**When** the page renders
**Then** an "AI-generated" label is visible on all Tutor output sections (NFR4)

**Given** the content page is rendered
**When** checked against WCAG 2.1 Level AA
**Then** colour contrast, heading structure, and focus indicators meet Level AA (NFR8)

---

### Story 4.3: Inline Quiz Checkpoints

As a **learner**,
I want inline quiz checkpoints within each concept's narrative,
So that I can check my understanding at natural breakpoints without disrupting reading flow.

**Acceptance Criteria:**

**Given** a learner reads a concept page
**When** they reach a quiz checkpoint
**Then** a multiple-choice question (2–3 options) is displayed inline within the narrative (FR12)

**Given** a learner selects a correct answer and submits
**When** feedback is shown
**Then** an encouraging confirmation message with a brief reinforcing explanation is displayed (FR13)

**Given** a learner selects an incorrect answer and submits
**When** feedback is shown
**Then** an encouraging, non-punitive message (e.g. "Not quite — here's the intuition…") with explanation is displayed (FR13)

**Given** quiz feedback conveys correct/incorrect state
**When** it is rendered
**Then** the state is communicated via text label and icon — not colour alone (NFR10)

**Given** a learner uses keyboard only
**When** interacting with a quiz
**Then** all answer options and the submit action are reachable via Tab and Enter (NFR9)

---

### Story 4.4: Per-Concept Mastery Tracking

As a **learner**,
I want my mastery of each concept tracked across quizzes and interactions,
So that I can see how well I understand each topic throughout my session.

**Acceptance Criteria:**

**Given** a learner has not visited a concept
**When** they view their progress
**Then** that concept shows status "unseen" (FR31)

**Given** a learner has started a concept but not completed all quizzes
**When** they view progress
**Then** that concept shows status "in-progress" (FR31)

**Given** a learner answers all inline quizzes for a concept correctly
**When** mastery is updated
**Then** the concept mastery score increases towards 1.0 (FR17)

**Given** a learner's mastery scores are stored in session state
**Then** no PII is included — only `concept_id` and score float (NFR1)

---

### Story 4.5: End-of-Chapter Test & Completion

As a **learner**,
I want an end-of-chapter test and completion summary after finishing all Chapter 1 concepts,
So that I can validate my understanding and celebrate my progress.

**Acceptance Criteria:**

**Given** a learner has completed all concepts in Chapter 1
**When** they reach the end of the chapter
**Then** an end-of-chapter comprehensive test is presented (FR16, FR32)

**Given** the chapter test is displayed
**When** it renders
**Then** it spans questions across all Chapter 1 concepts (FR32)

**Given** the learner completes the chapter test
**When** results are shown
**Then** a chapter completion summary displays mastery distribution and which concepts to revisit (FR33)

**Given** the learner completes the chapter test
**When** the completion screen is shown
**Then** an encouraging completion indicator (badge or milestone) is awarded (FR34)
**And** it is accessible — text description provided alongside any icon or badge (NFR8)

---

## Epic 5: Agile Mode — Causal Problem Consulting

Learners can switch to Agile Mode from any screen, describe a causal problem, receive concept identification + mastery-gap mini-teaches, get a structured consulting response, and ask follow-up questions.
Delivers: *Applied causal consulting for researchers and practitioners — the MVP chatbot-style Agile Mode.*

### Story 5.1: Agile Mode Entry & Problem Intake

As a **learner**,
I want to switch to Agile Mode from any screen and describe my causal problem in natural language,
So that I can get expert help on my own research questions at any point in my learning journey.

**Acceptance Criteria:**

**Given** a learner is on any page
**When** they click the Agile Mode button or tab
**Then** they are taken to the Agile Mode interface without losing their Study Mode position (FR25)

**Given** the learner is in Agile Mode
**When** the interface loads
**Then** a conversational text input is displayed for describing their causal problem (FR25)

**Given** the learner submits a problem description
**When** it is received
**Then** the problem text is displayed in the conversation history with a visible processing indicator

**Given** the Agile Mode interface is rendered
**When** accessed via keyboard
**Then** the text input and submit action are fully keyboard-navigable (NFR9)

---

### Story 5.2: Concept Identification & Mastery Gap Detection

As a **learner**,
I want the system to identify the causality concepts relevant to my problem and teach me any gaps,
So that I receive targeted preparation before the consulting response.

**Acceptance Criteria:**

**Given** a learner submits "I want to check if my CT scan study controls for confounders"
**When** the `concept_identifier` node runs
**Then** it identifies relevant concept nodes: `confounder`, `d_separation`, `back_door_criterion` (FR26)

**Given** relevant concepts are identified
**When** the `mastery_checker` node runs
**Then** it checks session mastery scores for each identified concept (FR27)

**Given** the learner has mastery < 0.5 for `d_separation`
**When** a mastery gap is detected
**Then** a brief, profile-adapted mini-teach on `d_separation` is delivered before the consulting response (FR27)

**Given** the mini-teach is displayed
**When** it renders
**Then** it is labelled "AI-generated" (NFR4)
**And** the underlying LLM prompt contains no PII — only `concept_id` and `profile_code` (NFR1)

---

### Story 5.3: Structured Consulting Response & Follow-Up

As a **learner**,
I want a structured consulting response with the ability to ask follow-up questions,
So that I get actionable guidance and can explore the reasoning in depth.

**Acceptance Criteria:**

**Given** concept gaps have been addressed (or mastery is sufficient)
**When** the `direct_consultant` node runs
**Then** a structured consulting response is generated addressing the learner's specific problem (FR28)

**Given** the consulting response is displayed
**When** the learner reads it
**Then** it explicitly references the relevant concepts (e.g. back-door criterion, adjustment set) (FR28)

**Given** the consulting response is shown
**When** the learner types a follow-up question
**Then** the system responds conversationally within the same Agile Mode session (FR29)

**Given** an Agile Mode session completes
**When** the problem is resolved
**Then** the problem and consulting exchange are logged as a worked example linked to the relevant concept nodes (FR30)

**Given** the consulting response is displayed
**Then** it is labelled "AI-generated" (NFR4)
**And** the first token streams within 3 seconds of submission (NFR7)

---

## Epic 6: Active-Interactive Study Mode *(Phase 2)*

Learners can activate live Tutor ↔ Dumb Student streaming dialogues, pause and intervene with corrections, receive Critic validation, earn mastery credit, and replay or request new dialogue variations.
Delivers: *The novel active error-correction learning paradigm — the Dumb Student live.*

### Story 6.1: Active-Interactive Pathway Activation

As a **learner**,
I want to activate the active-interactive pathway for any concept,
So that I can learn through observing and correcting a live agent dialogue.

**Acceptance Criteria:**

**Given** a learner is on a concept page
**When** they click "Active Learning" / "Watch Dialogue"
**Then** the active-interactive pathway is activated for that concept (FR18)

**Given** the pathway is activated
**When** the interface loads
**Then** a dialogue view is displayed showing Tutor and Dumb Student as visually distinct participants (FR19)

**Given** the pathway entry point is rendered
**When** accessed via keyboard
**Then** the activation button is focusable and activatable (NFR9)

---

### Story 6.2: Streaming Tutor ↔ Dumb Student Dialogue

As a **learner**,
I want to watch a live streaming dialogue between the Tutor and Dumb Student agents,
So that I can observe misconceptions being introduced and understand the correct reasoning.

**Acceptance Criteria:**

**Given** the active-interactive pathway is active
**When** the dialogue begins
**Then** Tutor and Dumb Student messages stream in real time via SSE (FR19)
**And** the two agents are visually distinguished by different labels, colours, or avatars

**Given** the dialogue is streaming
**When** the Dumb Student speaks
**Then** its messages express a misconception drawn from the misconception library linked to the concept node (FR23)

**Given** the dialogue streams
**When** the first token arrives
**Then** it is displayed within 3 seconds of activation (NFR7)

**Given** dialogue content is displayed
**Then** all Tutor and Dumb Student output is labelled "AI-generated" (NFR4)

---

### Story 6.3: Learner Intervention & Critic Validation

As a **learner**,
I want to pause the dialogue and intervene with a correction,
So that I can actively practise identifying and fixing causal reasoning errors.

**Acceptance Criteria:**

**Given** the dialogue is streaming
**When** the learner clicks the "Intervene" button
**Then** the dialogue pauses and an input field appears for the learner's correction (FR20)

**Given** the learner submits a correction
**When** the Critic agent evaluates it
**Then** it returns a validation result: correct or incorrect (FR21)

**Given** the learner's correction is correct
**When** the Critic confirms it
**Then** an encouraging confirmation is shown
**And** the relevant concept's mastery score is incremented (FR22)

**Given** the learner's correction is incorrect
**When** the Critic explains it
**Then** a non-punitive explanation is provided without reducing mastery below the current score

---

### Story 6.4: Dialogue Replay & Variation

As a **learner**,
I want to replay a dialogue or request a new variation of it,
So that I can reinforce learning through repetition with different misconception patterns.

**Acceptance Criteria:**

**Given** a dialogue has completed
**When** the learner clicks "Replay"
**Then** the same dialogue replays from the beginning (FR24)

**Given** a dialogue has completed
**When** the learner clicks "New Variation"
**Then** a new dialogue is generated for the same concept using a different misconception from the library (FR24)

**Given** a new variation is requested
**Then** it uses a different COMMONLY_CONFUSED pair or `misconceptions[]` entry from the concept node

---

## Epic 7: Admin Dashboard & Analytics *(Phase 2)*

Administrators can view aggregate mastery analytics by background × level, edit Tutor prompt templates, and export anonymised session data for research.
Delivers: *Institutional oversight and research data infrastructure for the user study.*

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

### Story 7.2: Tutor Prompt Template Editor

As an **admin**,
I want to edit the Tutor agent's prompt template for specific concepts,
So that I can improve content quality for concept-profile combinations where learners are struggling.

**Acceptance Criteria:**

**Given** the admin navigates to a concept in the admin panel
**When** they open the prompt template editor
**Then** the current Tutor prompt template for that concept is displayed (FR36)

**Given** the admin edits the template and saves
**When** the next Tutor invocation for that concept runs
**Then** it uses the updated template

**Given** a template is updated
**When** the admin views version history
**Then** the previous version is accessible so changes are reversible

**Given** the template editor is used
**Then** no learner PII or session data is exposed (NFR1)

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
