---
workflowType: 'prd'
project_name: 'EducAgent'
user_name: 'Yuyang'
date: '2026-02-23'
classification:
  projectType: web_app
  domain: edtech
  complexity: medium-high
  projectContext: greenfield
inputDocuments:
  - '_bmad-output/planning-artifacts/research/domain-causality-education-agentic-teaching-platforms-research-2026-02-23.md'
  - 'docs/EducAgent_OnePager.docx'
  - 'docs/EducAgent_TechnicalPlan.md'
stepsCompleted:
  - step-01-init
  - step-02-discovery
  - step-02b-vision
  - step-02c-executive-summary
  - step-03-success
  - step-04-journeys
  - step-05-domain
  - step-06-innovation
  - step-07-project-type
  - step-08-scoping
  - step-09-functional
  - step-10-nonfunctional
  - step-11-polish
  - step-12-complete
---

# EducAgent — Product Requirements Document

**Author:** Yuyang | **Date:** 2026-02-23 | **Status:** Complete

---

## Executive Summary

**Product:** EducAgent is an agentic causality tutoring platform grounded in Judea Pearl's *Causality* (2009).

**One-liner:** Let EducAgent help you learn causality in an interactive, adaptive, and smart way.

**Why now:** Causality education is entirely uncontested — no platform offers interactive, adaptive, knowledge-graph-grounded causality tutoring. CHAI HUB (UK) provides an ideal initial user base and institutional context for an academic impact paper.

**Core value proposition:** EducAgent delivers causality education through a multi-agent teaching team (Tutor, Critic, Dumb Student) backed by a Causality Concept Graph built from Pearl's textbook. Learners choose between two **parallel** Study Mode pathways:

- **Passive-interactive** — rich narrative text + inline quizzes (LearnYourWay-style)
- **Active-interactive** — observe and correct a live Tutor ↔ Dumb Student agent dialogue

Learners can also switch to **Agile Mode** for causal problem consulting on their own research questions.

**Learner profiling:** 2-axis adaptive framing — Background (Computer Scientist, Radiologist, Physician, Statistician) × Level (Beginner, Moderate, Expert) — content pre-generated and cached per profile signature (4×3 matrix).

**Knowledge base:** Pearl's *Causality* (2009): ~200 concepts, 11 chapters, ~80 sections. Causality Concept Graph covers the whole book upfront (NetworkX for MVP, Neo4j for production). Study Mode content generated for Chapters 1–2 for MVP.

**Timelines:** MVP demo ~28 Feb 2026 | Full release June 2026

**Team:** Yuyang (AI/backend lead) + 1 fullstack engineer + 1 design advisor

### Project Classification

| Dimension | Value |
|---|---|
| Project type | Web application (SPA) |
| Domain | EdTech |
| Complexity | Medium-high |
| Context | Greenfield |
| Innovation level | High — novel active-interactive learning paradigm |

---

## Success Criteria

### Learning Outcomes

- Learners demonstrate concept mastery via inline quizzes (per-section) and end-of-chapter comprehensive tests.
- Per-concept mastery scores (0.0–1.0) tracked in-session for MVP; persisted in PostgreSQL from Growth phase onward.
- Encouraging, reward-oriented feedback at every quiz and test checkpoint — no punitive responses.

### Product Milestones

| Milestone | Target Date | Definition |
|---|---|---|
| MVP demo | ~28 Feb 2026 | Chapter 1 Study Mode (passive-interactive) + simple Agile Mode chatbot; stateless session; built-in profile picker |
| Full release | June 2026 | Chapters 1–2 both pathways complete, active-interactive Dumb Student live, user study infrastructure ready |
| User study | Post-June 2026 | Structured evaluation with CHAI HUB participants and extended cohort across all background profiles |

### Validation Criteria

- User study participants spanning all four backgrounds confirm content adapts appropriately to their domain.
- Completion rates and quiz performance tracked per chapter and per background × level combination.
- Platform validated as suitable for academic impact paper (ICLR/CHI 2026–2027 target).

---

## Product Scope & Development Roadmap

### MVP Strategy

**Approach:** Problem-solving MVP — demonstrate core value (adaptive causality tutoring, Chapter 1) to CHAI HUB stakeholders before June release.

**Resource constraints:** 3-person team; MVP deliverable in days (demo ~Feb 28), not months.

### Phase 1 — MVP (~28 Feb 2026)

**Core journeys supported:**

- Learner selects background + level from built-in profile picker (stateless, no login)
- Passive-interactive Study Mode for Chapter 1: adaptive text + inline quizzes + end-of-chapter test
- Simple Agile Mode: chatbot-style causal Q&A interface

**Must-have capabilities:**

- Causality Concept Graph (NetworkX) seeded for all Pearl chapters (TOC + Subject Index parsed)
- Chapter 1 content generated and cached per profile signature
- LangGraph orchestration: Tutor + Critic agents with stateless session checkpointing
- OpenRouter LLM routing (Claude 4.6 Sonnet, GPT-5.3, Gemini 3.1)
- Inline quiz interactions with encouraging feedback
- End-of-chapter comprehensive test
- Profile selection UI (no auth required)

**Explicitly out of scope for MVP:**

- Active-interactive pathway (Dumb Student agent) — Phase 2
- Login / persistent accounts — Phase 2
- Admin dashboard — Phase 2
- Chapter 2+ content generation — Phase 2
- *Causality in the Sciences* second knowledge base — Phase 3

### Phase 2 — Growth (post-June 2026)

- Active-interactive pathway (Tutor ↔ Dumb Student; learner intervention)
- Chapter 2 Study Mode content (both pathways)
- User login and persistent student model (PostgreSQL via Supabase)
- Admin dashboard: user management, content management, usage analytics
- Concept graph visualiser (mastery heatmap, node explorer)
- Spaced repetition scheduling

### Phase 3 — Expansion

- *Causality in the Sciences* as a second knowledge base (use cases + domain examples)
- All 11 Pearl chapters content-complete
- Structured Agile Mode task templates (back-door check, DAG builder, confounding diagnosis)
- Multi-institution deployment; enterprise compliance hardening

### Risk Mitigation

| Risk | Mitigation |
|---|---|
| LLM content quality | Critic agent validates every section; human spot-check on Chapter 1 before demo |
| Graph construction accuracy | NetworkX prototype validated before Neo4j migration; PREREQUISITE_OF edges human-reviewed |
| Team capacity | MVP scoped to Chapter 1 + stateless session; no auth/admin complexity until Phase 2 |
| EU AI Act compliance (deadline Aug 2026) | Audit logging and transparency labels designed in from day one; no emotion recognition |

---

## User Journeys

### Journey 1 — Aisha: PhD Student, Passive-Interactive Study

**Profile:** Computer Scientist / Moderate | **Phase:** MVP

Aisha opens EducAgent, selects "Computer Scientist / Moderate" from the profile picker, and navigates to Chapter 1. She reads rich narrative content adapted for CS readers — analogies drawn from probability theory and ML models. Inline quiz checkpoints maintain engagement without breaking flow. An incorrect answer triggers an encouraging "Not quite — here's the intuition..." response with a short explanation. After completing the chapter she takes the end-of-chapter test, receives a completion indicator, and sees which concepts to revisit.

Key interactions: Profile selection → Chapter 1 passive-interactive → inline quizzes → chapter test → revisit suggestions.

### Journey 2 — Marcus: ML Engineer, Active-Interactive Concept Jump

**Profile:** Computer Scientist / Expert | **Phase:** Growth (Phase 2)

Marcus skips directly to "Back-door Criterion" in the concept navigator. He activates the active-interactive pathway and watches the Tutor explain the back-door criterion to a Dumb Student making the classic "blocking all paths" error. Marcus clicks "Intervene" to correct it. The Critic validates his correction and awards mastery credit. Marcus jumps to front-door criterion.

Key interactions: Concept jump → active-interactive activation → observe dialogue → intervene → Critic validation → mastery update.

### Journey 3 — Dr. Chen: Radiologist, Agile Mode Problem Consulting

**Profile:** Radiologist / Beginner | **Phase:** MVP (simple chatbot) / Growth (full structured)

Dr. Chen has a concrete problem: does his observational CT-scan study control for confounders? In Agile Mode he describes his study design in plain language. The platform identifies relevant concept nodes (confounder, d-separation, back-door criterion), detects mastery gaps, delivers a brief clinician-adapted mini-teach, then helps him audit his adjustment set.

Key interactions: Agile Mode entry → problem intake → concept gap detection → mini-teach → structured consulting response.

### Journey 4 — Yuyang: Admin, User Study Monitoring

**Profile:** Admin | **Phase:** Growth (Phase 2)

Yuyang logs into the admin dashboard and views aggregate mastery heatmaps across Chapter 1 concepts, segmented by background profile. He identifies that Radiologist / Beginner learners struggle with d-separation (mastery < 0.4). He edits the Tutor prompt template for that concept to include a medical imaging analogy, then exports anonymised session data for the impact paper.

Key interactions: Admin login → mastery analytics → content editing → data export.

### Journey Traceability

| Journey | Mode | Phase | Key FRs |
|---|---|---|---|
| Aisha — passive-interactive | Study Mode, passive | MVP | FR1–FR5, FR6–FR10, FR11–FR17, FR31–FR34 |
| Marcus — active-interactive | Study Mode, active | Phase 2 | FR1–FR5, FR6–FR10, FR18–FR24 |
| Dr. Chen — Agile Mode | Agile Mode | MVP/Phase 2 | FR1–FR5, FR25–FR30 |
| Yuyang — Admin | Admin dashboard | Phase 2 | FR35–FR37 |

---

## Domain-Specific Requirements

### Regulatory Compliance

**EU AI Act — HIGH RISK**

Education AI systems are classified HIGH RISK (applicable Aug 2026). Requirements: mandatory audit logging of all AI decisions; human oversight mechanisms; transparency labels ("AI-generated content") on all Tutor output; no emotion recognition or affective state inference. Full release (June 2026) must include audit infrastructure.

**GDPR**

No PII transmitted to LLM providers — only anonymised concept IDs, mastery scores, and profile codes in prompts. Learners may request data export or deletion (Growth Phase, once persistent accounts exist). MVP is stateless — no personal data stored.

**FERPA**

Applicable for US academic institution users. Student records remain under institutional control; OpenRouter must not retain student data. Design: student model in institutional PostgreSQL; no identifying data in LLM calls.

**COPPA**

Platform targets adult professionals (not children under 13). Minimum age check at registration enforced in Growth Phase.

### Technical Constraints

- All LLM calls route through OpenRouter; no hard dependency on a single provider.
- Concept graph queryable in-memory (NetworkX MVP) without external graph DB dependency.
- Content cached by `(concept_id, background, level)` signature to reduce LLM cost at scale.
- Section-level text chunking at subsection granularity (e.g. 3.3.1) stored in Qdrant vector store.

### Integration Requirements

| System | Purpose | Notes |
|---|---|---|
| OpenRouter | Multi-provider LLM routing | Auto-fallback; Claude 4.6 Sonnet, GPT-5.3, Gemini 3.1 |
| LangGraph v1.0 | Stateful multi-agent orchestration | Checkpointing for session state |
| Qdrant | Self-hosted vector store | Section-level embeddings per chapter |
| NetworkX | MVP graph storage | Export to JSON for Neo4j migration |
| Neo4j | Production graph storage | Cypher queries for prerequisite traversal |

---

## Innovation & Novel Patterns

### 1. Active-Interactive Learning Paradigm

Learners observe a live Tutor ↔ Dumb Student agent dialogue and actively intervene to correct deliberate misconceptions — transforming passive observation into engaged error-detection. No existing EdTech platform implements learner intervention in a live agent dialogue. GraphMASAL (Nov 2025) uses multi-agent tutoring but has no learner intervention mechanism. Validated by EMNLP 2025: Socratic questioning + active error correction improves retention over passive reception.

### 2. Dumb Student Architecture

A dedicated agent that deliberately expresses curated misconceptions from the Pearl textbook (collider bias, Simpson's paradox inversion, "correlation implies causation"). Its misconception library is linked to concept nodes in the Causality Concept Graph, ensuring pedagogically targeted errors. Unlike uniformly competent multi-agent systems, the Dumb Student is a pedagogical foil by design.

### 3. Domain-Specific GraphRAG Tutoring

The Causality Concept Graph (PREREQUISITE_OF, COVERED_IN, COMMONLY_CONFUSED, NEXT_IN_SEQUENCE edges) drives all content generation and retrieval. The Tutor agent queries prerequisites before teaching any concept — enabling genuine adaptive sequencing. Applied to causal inference — a domain with precise formal semantics — GraphRAG is especially critical for hallucination resistance (CausalRAG ACL 2025; GraphMASAL Nov 2025).

### 4. Two-Axis Adaptive Framing for Adult Professionals

Background (4 options) × Level (3 options) = 12 profile combinations, each generating domain-specific analogies. Google Learn Your Way (K-12) uses level + hobby/theme. EducAgent adapts this for adult domain professionals — Background provides deep domain analogy (ML models for CS; patient cohorts for clinicians) rather than surface theme adaptation. Content pre-generated and cached per profile signature for low-latency delivery.

---

## Web Application Requirements

### Architecture

- SPA: Next.js + Vercel AI SDK (App Router, TypeScript)
- Backend API: FastAPI (Python) — aligned with LangGraph/NetworkX ecosystem
- Content streaming: Server-Sent Events for real-time Tutor/Dumb Student dialogue
- Content rendering: custom JSON renderer (narrative + inline quiz + diagram sections)

### Browser & Platform Support

- Evergreen desktop browsers: Chrome 120+, Firefox 120+, Safari 17+, Edge 120+
- Desktop-primary (academic professional audience); mobile-responsive but not mobile-first for MVP

### Authentication & Data Infrastructure

- MVP: no auth required; profile selection via built-in picker (stateless)
- Growth Phase: Clerk for Next.js-native authentication (OAuth, magic link)
- PostgreSQL via Supabase: student model persistence (Growth Phase)
- Qdrant: self-hosted vector store
- NetworkX (MVP) → Neo4j (production): graph storage migration path

---

## Functional Requirements

### User Onboarding & Profile Setup

- **FR0**: First screen should be the profile selection, profile 1 and 2 and more
- **FR1**: Learner can select a background profile (Computer Scientist, Radiologist, Physician, Statistician) from a built-in picker without creating an account, or add their custom background.
- **FR2**: Learner can select an expertise level (Beginner, Moderate, Expert) independent of background selection, or add their custom level.
- **FR3**: System loads content pre-adapted to the selected background × level profile combination.
- **FR4**: Learner can change background or level at any point; content adapts accordingly without losing current position.
- **FR5**: System preserves session state in-browser (stateless MVP) so a page refresh does not reset mastery progress.


### Content Navigation

- **FR6**: Learner can navigate the knowledge point from the knowledge graph.
- **FR7**: Learner can jump directly to any concept node by name or keyword search. This is only for MVP, later we want people to unlock, only the inital ones are unlocked.
- **FR8**: System displays concept prerequisites before presenting a concept, allowing learner to review gaps first.
- **FR9**: System recommends a next concept based on NEXT_IN_SEQUENCE and PREREQUISITE_OF graph edges.
- **FR10**: Learner can bookmark concepts for later review (session-level for MVP; persistent from Growth Phase).

### Passive-Interactive Study Mode

- **FR11**: Learner can read narrative content for each concept rendered in rich text with domain-adapted analogies.
- **FR12**: System embeds 2–3 inline quiz checkpoints within each concept's narrative.
- **FR13**: System provides immediate, encouraging feedback on inline quiz answers — explanation included for both correct and incorrect responses.
- **FR14**: Learner can view a domain-adapted worked example (CS / medical / statistical framing) for each concept.
- **FR15**: Learner can view a diagram or DAG description for concepts that have visual representations.
- **FR16**: System presents an end-of-chapter comprehensive test upon completion of all concepts in a chapter.
- **FR17**: System tracks per-concept mastery score (0.0–1.0) within the current session.

### Active-Interactive Study Mode

- **FR18**: Learner can activate the active-interactive pathway for any concept, triggering a Tutor ↔ Dumb Student dialogue.
- **FR19**: System streams the Tutor and Dumb Student dialogue in real time, visually distinguishing the two agents.
- **FR20**: Learner can pause the dialogue at any point and intervene with a correction or clarification.
- **FR21**: Critic agent validates the learner's intervention — confirms if correct, explains if not.
- **FR22**: Correct learner interventions increment mastery score for the relevant concept.
- **FR23**: Dumb Student agent expresses misconceptions drawn from the curated misconception library linked to the concept graph.
- **FR24**: Learner can replay a dialogue or request a new dialogue variation for the same concept.

### Agile Mode

- **FR25**: Learner can switch to Agile Mode from any screen and describe a causal problem in natural language.
- **FR26**: System identifies relevant concept nodes from the Causality Concept Graph based on the problem description.
- **FR27**: System checks learner mastery of relevant concepts; if gaps exist, delivers a targeted mini-teach before consulting.
- **FR28**: System provides a structured consulting response to the learner's causal problem.
- **FR29**: Learner can ask follow-up questions in a conversational interface within Agile Mode.
- **FR30**: System logs each Agile Mode problem as a worked example linked to relevant concept nodes.

### Assessment & Progress Tracking

- **FR31**: System displays per-concept mastery status (unseen / in-progress / mastered) across all explored concepts.
- **FR32**: System generates an end-of-chapter test spanning all concepts in the chapter.
- **FR33**: System provides a chapter completion summary showing mastery distribution and concepts to revisit.
- **FR34**: System awards encouraging completion indicators (badges, progress milestones) upon chapter test completion.

### Knowledge Graph & Content Management (Admin — Growth Phase)

- **FR35**: Admin can view aggregate mastery analytics segmented by background profile and level.
- **FR36**: Admin can edit Tutor agent prompt templates for specific concepts to improve content quality.
- **FR37**: Admin can export anonymised session data (concept mastery, completion rates) for research analysis.

---

## Non-Functional Requirements

### Security

- **NFR1**: No PII (name, email, institution) included in any prompt sent to external LLM providers. Only anonymised concept IDs, mastery scores, and profile codes transmitted.
- **NFR2**: All API communication between frontend and backend uses HTTPS/TLS 1.2+.
- **NFR3**: Audit logs record all AI-generated content decisions (Tutor output, Critic validation, mastery updates) with timestamps — required for EU AI Act HIGH RISK compliance.
- **NFR4**: All AI-generated content is labelled "AI-generated" in the UI (EU AI Act transparency requirement).
- **NFR5**: No emotion recognition or inferred affective state derived from learner behaviour.

### Performance

- **NFR6**: Pre-generated cached concept content (by profile signature) loads within 2 seconds for cached profiles.
- **NFR7**: Real-time Tutor/Dumb Student dialogue streams first token within 3 seconds; OpenRouter fallback activates within 5 seconds on provider failure.

### Accessibility

- **NFR8**: UI meets WCAG 2.1 Level AA for all primary learner flows (profile selection, reading mode, quiz interaction).
- **NFR9**: All quiz interactions are keyboard-navigable; no mouse-only interactions.
- **NFR10**: Colour is not the sole means of conveying quiz feedback — correct/incorrect states include text labels and icons.

### Integration Reliability

- **NFR11**: OpenRouter integration implements automatic provider fallback; single-provider failure must not surface to the learner.
- **NFR12**: LangGraph checkpointing preserves session state across network interruptions; learner does not lose in-progress concept mastery on page reload.

---

*This PRD is the capability contract for EducAgent. All design, architecture, and development work should trace back to the requirements and vision documented here. Update as planning continues.*
