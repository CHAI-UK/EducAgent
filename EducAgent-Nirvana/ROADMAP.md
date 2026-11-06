# EducAgent Execution Roadmap

**Status:** guided local text repair, tests/live probes, Chrome, and local restart verified; external evaluation and deployment remain gated

**Last consolidated:** 2026-09-09

EducAgent has three layers: Portal for public causal literacy, Nirvana as the novice research front door, and existing or future specialist causal workflows for task-specific depth. Portal and Nirvana run in parallel. Specialist tools retain their own scientific ownership; Nirvana connects to them only where an observed novice problem justifies a teaching or handoff layer.

## Current snapshot

### 2026-10-15 shared-server review distribution

The user requested a Linux/Docker Compose deployment package on port 9090 for
Learning, all six Portal course/profile routes and Nirvana. The allowlisted
archive includes prebuilt public files and private runtime course packs, not
local progress or textbook source. A separate explicitly authorised private
variant carries the existing ELM configuration; it is excluded from the image
and never printed. The default shareable archive has a configuration template.
Nirvana supports a configured same-origin `/nirvana/api` without changing the
normal Windows port-8011 path. Nginx exposes neither internal backend ports nor
the local authoring/preview endpoints. See [deployment instructions](deploy/README.md).

Local checks: all 269 SDK Python tests, 14 Nirvana Python tests, 12 SDK Node
tests, five Nirvana Node UI/Markdown tests, six deployment tests and Portal
type/build checks passed. A real Ubuntu Nginx 1.24
binary passed configuration, staged static assets, request rewrites and blocked
paths against disposable mock APIs in WSL. This is not an actual Docker image
or target-server run and makes no live ELM or scientific-review claim. The
subsequent S30 runtime adds anonymous browser-session isolation with independent
controllers, diagnostic answers, module/Profile preferences, conversations and
resets; the SDK roadmap owns its acceptance. This adds no login or cross-device
sync. Keep one process per state directory; IT access control and target-server
smoke checks remain required.

### 2026-09-09 AI drafting update

Follow-up interaction refinement: chat changes now require per-field Accept/Reject, Route includes a causal-applicability summary, and Copy no longer requires confirmation (unreviewed content stays labelled draft). Tests cover unchanged fields before acceptance, rejection, and exclusion of pending edits from copied text. Initial generation still drafts automatically; follow-up editing does not.

The user authorised a working natural-language-to-Brief demo. `/api/frame` now provides structured task selection and field extraction using the shared ELM config; follow-up conversation updates the editable draft. Manual edits cancel late replies, generated revisions require review, and handoffs derive from current fields. No new dependencies, specialist engine, or automatic DG import were added. Next: evaluate extraction and follow-up fidelity across unfamiliar questions, especially missing data, mixed tasks, and image-synthesis domain shifts. Earlier 2026-09-05 text-only descriptions below are historical, not the current AI capability boundary.

| Track | Stage | State | Next decision |
|---|---|---|---|
| Shared portfolio | Ecosystem alignment | Prepared, not externally reviewed | Accept/revise/reject the Portal → Nirvana → specialist-tools story; name owners and decide capacity/order |
| Portal | A — Define | SDK M0 concept backbone and host selected; task-driven direction agreed for the next slice | Specify one authored mission and separate concept coverage from independent evidence |
| Portal | B — Build | State/entry and guided-text repairs verified through tests, live probes, Chrome, and restart | Test additional learner cases and author a fresh transfer task before a curriculum study |
| Portal | C — Validate | Not started | Run formative novice sessions only after a frozen build and approved record |
| Nirvana | A — Define | Intended effect-framing branch and proposed DG preparation boundary specified | Confirm ownership with DG Copilot colleagues, observe direct use, and review the Brief/routing boundary |
| Nirvana | B — Build | Worksheet and concise framing guidance verified through tests, live probes, Chrome, and restart | Test additional cases without implying a formal teaching loop or automatic Brief editing |
| Nirvana | C — Validate | Not started | Buy usability, comparison, handoff, and reuse evidence sequentially |

“Prepared” means an internal artifact exists. It does not mean reviewed, authorised, observed, passed, useful, or accepted by CHAI.

Local reliability and documentation repairs are authorised by the 2026-09-05 request. Do not wait for external governance decisions to fix those defects, and do not treat those fixes as permission for participant work or publication.

The earlier 2026-09-05 state/entry repair passed 148 SDK tests, four Nirvana Python tests, one Node UI-state regression, web checks/build, HTTP access checks, and Chrome flows, including scene score/Continue without full-concept or M1-readiness credit. Its vanilla live review exposed early reveal/scene drift and long Nirvana checklists; these findings motivated the subsequent prompt repair rather than being erased by the passing flow.

The final guided-text repair passed 152 SDK tests in 6.557 s, eight Nirvana Python tests, one Node UI-state regression, TypeScript checks, and the launch script's web build. Five Portal probes with the existing ELM `gpt-5.6-luna` configuration returned 48–74 words apart from a 20-word action response, did not name hidden rain, and kept results separate from assumptions. Direct Nirvana probes returned 44/53 words for ordinary intake/follow-up and 156 words when detail was requested. Final Chrome checks also passed: Portal gave neutral help without advance/credit; Nirvana's roughly 69-/55-word replies carried weekly journeys/adult residents/six months forward and asked for the missing comparison. The local 4173 demo and 8011 health endpoint are running after restart without `-Reset` or changes to user traces. Earlier tuning failures remain in the track records. These are targeted observations, not a general semantic guarantee, new qualification, or participant study.

## 0 — Align the ecosystem narrative

Use `docs/portfolio-conclusion.md` for one bounded discussion with the supervisor/CHAI-facing reviewer. Record:

- accept, revise, or reject Portal and Nirvana as two entry routes within a wider CHAI learning/tool ecosystem;
- the public role and name of each layer;
- whether specialist tools such as the Domain Generalization Copilot should be visible destinations from Nirvana;
- which knowledge and decisions remain owned by each specialist tool team;
- one observable simplification or stop result for each active route;
- one named owner per active route;
- whether capacity supports both routes now, or which route is parked and what would reopen it.

Do not send the full repository. A corrected conclusion and one next review are enough.

## A — Define and choose the smallest credible route

### Portal A

1. Keep EducAgent-SDK as the host and its nine M0 concepts as the content backbone; reshape one existing mission around learner actions and an inspectable output.
2. Keep the SDK as the source of truth for its nine concepts, workbench, evaluation, progression, and accessibility contracts.
3. Freeze whether a study uses guarded dialogue, guided-local text, or a separately restored/versioned vanilla baseline before collecting data; do not treat those as interchangeable.
4. Confirm the data record and institutional route for any formative study.
5. Review an unfamiliar immediate/delayed task before claiming transfer; concept coverage, route completion, and independent performance are different measures.

### Nirvana A

1. Confirm with Damian/Kurt what the DG framework and Copilot own, the intended user, known novice assumptions, and what a useful upstream handoff would contain.
2. Observe 4–5 causal novices using the existing DG Copilot directly with synthetic prediction-under-shift cases before building an integration.
3. Identify repeated blockage in task recognition, prediction target/environment definition, graph concepts, shift assumptions, stability interpretation, or recommendation understanding. Treat successful direct use as evidence that no Nirvana prelude is needed for that step.
4. Review Nirvana’s primary user, manual task choices and intended future recognition, effect-framing branch, Brief fields, stopping boundary, and derived handoffs with product, causal, and education expertise.
5. Use synthetic effect-question cases to compare a static Brief worksheet and a low-fidelity guided route.
6. If the DG gap check finds a repeated novice blockage, prototype only the smallest plain-language prelude and user-reviewed handoff; leave augmented-graph, feasibility, and deployment logic inside DG Copilot.
7. Confirm the institutional route before any participant contact or real unpublished question.
8. Decide: no DG prelude needed, content/link only, bounded Nirvana prelude, and independently static/deterministic/LLM-assisted delivery for the supported effect branch.

Portal A and Nirvana A may proceed concurrently only when the shared reviewers and implementers have real, named capacity.

## B — Build one vertical slice

### Portal B

- use the existing SDK Portal build rather than creating a second tutorial implementation;
- repair the rain mission's context and supplied-model assumptions; keep the current classification items labelled as narrow responses, not proof of reasoning or nine-concept mastery;
- make diagnostic skipping start the full route without granting diagnostic success or deleting old progress;
- begin task-driven authoring with fixed missions and a concept-coverage map; do not generate personalised curricula in this repair;
- retain responsive local free-text with phase-visible context and same-attempt history; preserve scored/runtime authority and version this guided policy separately from the earlier vanilla baseline;
- preserve keyboard, mobile, replay, and explicit progression behaviour;
- make the research-question route optional and transfer no content automatically;
- keep provider failures visible instead of replacing them with a successful-looking canned response.

### Nirvana B

- retain manual task selection alongside the newly authorised AI extraction; a diagnostic teaching loop remains a later product decision;
- distinguish synthetic examples from a fresh user problem, clear stale assumptions/context, and expose unknown information;
- require explicit review for confirmation, invalidate it after edits, and keep preview/copy tied to the same revision;
- add a DG Copilot prelude only for the repeated blockage observed in Phase A;
- preserve item origin, user review, support status, and uncertainty separately;
- keep a complete manual editing path;
- derive methodologist, LLM, or specialist-tool handoff from one confirmed Brief revision;
- begin with a user-reviewed link/copy handoff to DG Copilot; do not build automatic transfer without observed re-entry burden and an agreed interface;
- support one bounded next step and stop before identification or analysis;
- add an LLM proposal adapter only if Phase A selected it and structured-output, privacy, provider, and recovery checks pass.

Portal receives phase-visible authored context. Nirvana now uses the structured ELM framing adapter for task recognition, Brief drafting and follow-up edits; the text-only endpoint remains for compatibility. It has no external action tools or persistence. A formal diagnostic/teach-back loop remains unimplemented, and the local adapter is not a qualified study arm.

The DG copy is a preparation note for manual entry into a form-and-graph workflow, not a prompt accepted or executed by DG Copilot. The first-test limits of one concept intervention, a 15-minute session, and one next step are test constraints, not permanent product rules. Full item-level provenance and teach-back assessment are still target capabilities.

Do not add RAG, long-term memory, multi-agent behaviour, file ingestion, analysis tooling, a shared Portal/Nirvana runtime, or duplicate DG feasibility/deployment rules in the first slice.

## C — Validate one claim at a time

### Portal C

1. Observe 5–8 causal novices using the frozen tutorial.
2. Measure completion, time, help, held-out transfer, and critical misconceptions.
3. If the active format must justify its cost, compare it with a concise explanation-only page using fresh items and independent assignment.
4. Keep one unit, add one bounded adaptation, simplify, or stop.

### Nirvana C

1. **C1 usability:** observe 5–8 eligible researchers; require a usable Brief, teach-back, acceptable burden, and no critical authority or privacy failure.
2. **C2 comparative value:** only after C1, use a task-matched baseline. For effect questions, compare against the selected strong worksheet, capable-LLM prompt, or document-grounded route. For prediction-under-shift, compare direct DG Copilot with Nirvana-prelude-plus-DG-Copilot. Do not pool these task classes.
3. **C2b handoff utility:** only after C2, test whether the actual next consumer—methodologist, capable LLM, or specialist tool—recovers the intended task, assumptions, and uncertainty better from a Brief than from the raw starting question.
4. **C3 verified reuse:** only after C2b and governance approval, observe corroborated edit, share, tool use, or changed/abandoned research action.

A good demo can be shown after C1 without claiming comparative or downstream value. Later protocols existing on paper are not a reason to run them.

## Continue, simplify, or stop

Continue only when the current stage’s evidence supports its exact claim. Simplify or stop when:

- Portal’s active tutorial is no better than the explanation-only page;
- Nirvana’s worksheet or strong LLM prompt is equally useful with less burden;
- causal novices can already enter and understand DG Copilot directly, making a Nirvana prelude unnecessary;
- users cannot distinguish suggestions from established causal knowledge;
- researchers do not recognise problem formulation as a real blockage;
- the Brief looks polished but users cannot explain it;
- handoff consumers gain only extra words rather than clearer decisions and uncertainty;
- governance or shared-team capacity is missing.

## Conditional later work

Only repeated observed needs can justify more tutorial topics, background adaptation, additional causal question classes, document inputs, automatic specialist-tool integrations, memory, dashboards, analysis tools, or a general tutoring platform.

A CHAI `Learning` navigation entry, public adoption, or funding application is a separate decision. It requires an exact released version, appropriate evidence for the claim, named technical and scientific owners, accessibility/privacy/security checks, maintenance and retirement arrangements, and current mechanism-specific eligibility. Thematic alignment alone is not adoption, endorsement, or an award.

## Immediate ordered actions

1. Retain the verified guided-text repair and test additional learner/research cases. Preserve earlier baseline failures and final targeted retests; do not turn prompt improvements into an untested global guarantee.
2. Verify public-only `.demo-site/` staging and the HTTP path/type allowlist; preserve textbook authoring material and historical progress privately. Keep revised pack evidence separate from old traces and qualification.
3. In parallel, shape one Portal mission around an observable learner task and review the Nirvana effect-framing worksheet. A fresh independent transfer task remains a follow-up authoring deliverable, not a completed result of bug fixes.
4. Confirm the layered story and capacity with the supervisor; hold a bounded DG ownership/interface conversation with Damian/Kurt.
5. Arrange a direct-use DG gap check only under an approved observation route. Choose a prelude or integration only for an observed blockage.
6. Freeze the exact content, tutor mode, UI, assessment, and study route before collecting user evidence. Use the existing five documents to record the resulting decision rather than creating more planning layers.
# Latest implemented slice — 9 September 2026

- Eight task-specific Briefs plus an unclear route; output-intent classification rules.
- Four additional literature-inspired examples with primary-source links.
- Dedicated discovery, policy, counterfactual and prediction specs and handoffs.
- Review regression coverage and opt-in live classification smoke suite.
- Next: evaluate ambiguous multi-goal questions and richer task-specific specs
  (for example effect-transport evidence and mediation contrasts) with domain experts.
