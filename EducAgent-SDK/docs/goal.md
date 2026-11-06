# EducAgent-SDK Goal and Design Guidelines

- **Status:** draft canonical product and architecture guideline; current working tree, not yet published
- **Reference domain:** Causality M0
- **Audience:** product, pedagogy, content, runtime, agent, and evaluation contributors

## 1. Purpose of this document

This document defines why EducAgent-SDK exists, what it is allowed to become, and the principles that must survive implementation changes.

It defines the target product and architecture; it does not claim that every capability is implemented in the current working tree. Only [`roadmap.md`](roadmap.md) records current progress and completion evidence.

- [`implementation.md`](implementation.md) owns technical contracts and implementation steps.
- [`roadmap.md`](roadmap.md) owns current progress, the active step, and completion evidence.

When documents disagree, use this file for product boundaries, `implementation.md` for technical design, and `roadmap.md` for current status.

The umbrella Portal currently exposes guided local free-text replies through the legacy `--unguarded-tutor` switch. This is no longer the earlier minimal vanilla baseline: its prompt receives phase-visible authored scene copy, the text projection of current actions/results, the learner's graph/prediction/reflection, the legal next focus, and same-attempt conversation. It does not receive the full scene or `TutorDeps` containing future outcomes or assessment answers. Replies remain plain text, with a retry for empty/overlong output rather than silent truncation. This mode is not the guarded target policy described below and does not inherit its typed-proposal or fallback guarantees. Scored evidence, scene actions, progression, and replay remain runtime/evaluator responsibilities; earlier qualification does not qualify this changed prompt.

## 2. One-sentence goal

Presentation clarification (2026-11-06): the guided reply remains a string in
the trace/API, while the Portal renders assistant text with safe CommonMark and
math support. Verified definition excerpts use semantic blockquotes and labelled
source links. Raw HTML and remote Markdown images are omitted. Historical
plain-text verified replies are formatted for display without rewriting events.

> EducAgent-SDK is an agent-first runtime for evidence-driven teaching: a Pydantic AI tutor conducts the Socratic dialogue and makes bounded pedagogical choices, while reviewed content, evaluators, replay-derived state, and runtime gates keep the learning path grounded and auditable.

The language model is the primary tutor, but it is not the final authority. It may interpret bounded, unscored free text, maintain tentative misconception hypotheses, and decide how to elicit, hint, explain, retry, reflect, or request progression. It never creates domain truth, silently mutates learner state, or grants progression or mastery by itself.

## 3. Product hypothesis

Reading, fluent explanations, and correct-looking answers do not by themselves show learning. The EducAgent hypothesis is that learning improves when a learner must:

1. inspect a bounded situation;
2. commit to an answer, prediction, or model before a reveal;
3. perform a meaningful action;
4. observe a deterministic consequence;
5. revise the same answer or artifact;
6. apply the distinction in a new situation;
7. revisit it after a delay.

In the target M0 experience, step 6 is a **transfer investigation**, not an automatically repeated
multiple-choice question. The tutor introduces an unfamiliar causal situation,
asks the learner for a plain-language explanation or prediction, and then
routes them to a declared causal-scene action or a formal evidence task. The
learner's free explanation is useful pedagogical evidence and may guide the
tutor, but it is not itself scored correctness.

The north-star outcome is **unprompted success on a delayed, previously unseen transfer task**. Completion rate, conversation length, UI richness, model preference, and an LLM judge score are not substitutes for this outcome.

The primary learner surface is a **bounded cognitive action**, not a chat
transcript. A learner should inspect a record, manipulate a declared model,
compare alternatives, make a prediction, or commit an answer; then see a
deterministic consequence and revise. The tutor uses dialogue to direct
attention to that object and to interpret the learner's move. It must not
substitute an unbounded conversational explanation for an observable learning
action. A graph, plot, simulation, or other interactive object is justified
only when it has an authored purpose, deterministic behaviour, accessible
representation, and a stated relationship to scored evidence.

### Product direction: a causal reasoning workbench

EducAgent should not compete with NotebookLM by offering a broad catalogue of
summaries, quizzes, audio, mind maps, or generic chat. Its distinctive product
is a **causal reasoning workbench**: the learner builds or changes a small
causal model, compares observational evidence with an intervention, predicts
what should change, and explains the result. The tutor makes that sequence
feel like a guided Socratic investigation rather than a sequence of multiple
choice cards.

The first M0 workbench is deliberately narrow. It is a content-authored
**causal scene** with a small set of variables, permitted DAG edits, a fixed
observational view, and declared intervention results. It may render a graph,
table, or plot, but those are views of the same deterministic scene—not
independent AI-generated tools. The user-authorised S39 extension computes
the same intervention under three explicitly declared Boolean hypotheses and
a separately fixed reference world. It reuses the existing finite SCM engine;
it does not infer mechanisms from arbitrary learner arrows. Historical preset
scenes keep their meaning. This keeps observations reproducible, grounded and
separate from a claim that the displayed data identify a unique graph.

The longer-term direction can include guided parameter notebooks, executable
causal packages, and richer visualisations. Those are domain extensions only
when they have a sandboxing, provenance, accessibility, and replay contract.
An arbitrary code cell or an LLM-generated tool is not part of M0.

If a simpler reading or source-grounded Socratic chat condition matches EducAgent on a predeclared delayed-transfer measure, the structured runtime has not justified its additional complexity and should be simplified.

### Portal audience and other SDK consumers

The current public Portal targets people new to causal reasoning, without requiring a research background. Everyday authored tasks should carry the zero-to-one learning route. A new PhD student or clinician may be a later SDK consumer with separately reviewed framing and examples; those audiences are not the eligibility definition for the public Portal. Nirvana independently serves researchers bringing their own problems and is not a prerequisite or compulsory next stage.

Vocabulary, examples, and theme may adapt to a declared audience; causal structure, evaluation standard, and transfer difficulty must not silently change.

### Task-driven curriculum direction

Keep the nine stable M0 concept IDs as an authoring backbone and organise the learner experience around fixed, reviewed missions with inspectable outputs. Start with one coherent rain/umbrella mission, not a second curriculum engine or runtime-generated tasks. Explicitly distinguish supplied synthetic-world assumptions from conclusions supported by the displayed observations and interventions; reproducing the supplied model is not discovery of a uniquely identified real-world DAG.

A later authored sequence may ask learners to check an everyday causal claim, design a useful comparison, compare and revise alternative explanations, and then transfer independently. Increase difficulty through ambiguity, hidden information, competing explanations, and reduced scaffolding. An example, a partially completed task, and an independent task can use the same concepts at different levels.

Maintain separate evidence for concepts encountered, practised, and demonstrated independently. The present pack still relies mostly on binary classification activities. Neither listing a concept in `covered_concept_ids` nor selecting a correct answer proves reasoning across all listed concepts. A fresh independent transfer task remains an authoring and review deliverable before a new curriculum-effect claim.

## 4. What is generic and what is domain-specific

EducAgent represents a general form of **agentic pedagogy**. Causality is its first topic, not the definition of the SDK.

| Concept | Meaning |
| --- | --- |
| Agentic pedagogy | the general loop that observes evidence and selects the next bounded teaching move |
| Topic/domain | the subject being taught; Causality M0 is the first reference domain |
| Theme/skin | vocabulary, story, and visual framing that do not change truth or evaluation |
| Domain extension | a subject-specific evaluator, simulator, oracle, or tool exposed through a small runtime boundary |
| Causal world/tools | causality extensions and harness capabilities; they are not generic runtime responsibilities |

Generality must come from small stable contracts, not from weakening causal rigor or creating a plugin framework before a second real domain exists. After the first causality slice is stable, a second tiny non-causal pack must prove portability without changing core progression code.

## 5. Authority and ownership

Each kind of knowledge has one owner.

| Layer | Owns | Must not own |
| --- | --- | --- |
| Content pack | reviewed claims, objectives, activities, hints, explanations, examples, sources | session state, model calls, mastery |
| Evaluator/domain extension | accepted evidence, structured gaps, deterministic consequences, domain facts | teaching tone, UI, progression policy |
| Tutor agent | interpretation, tentative learner hypotheses, and selection of one grounded Socratic turn from runtime-provided candidates | domain truth, direct cursor mutation, release authority, progression, mastery |
| Pedagogy contract | permitted teaching purposes, support budgets, reveal rules, expected evidence, and escape conditions | model wording, correctness, progression eligibility |
| Runtime | legal candidates, state transitions, budgets, gates, fallback, replay, append-only trace | invented subject facts or hidden learner labels |
| Renderer and learning object | accessible presentation, learner input, and a deterministic rendering of an authored domain scene | evaluation truth, invented scene state, reveal authority, final progression decisions |

These boundaries are more important than any framework choice.

An interactive learning object belongs to the renderer and its content/domain
extension: it renders a released scenario and records only the learner action
the runtime has declared. It cannot infer causal truth or completion from a
click. The tutor may choose a grounded teaching move around that object, but
may not invent a new tool, simulation result, or visual explanation at runtime.

The tutor may use a small, read-only tool surface over the frozen causal-scene
snapshot: inspect the learner's current graph/action, retrieve the released
observation or deterministic intervention result, and list the currently
legal next actions. It may propose a teaching turn around that focus; the
runtime derives and trace-records the sole phase-legal interaction focus. It
cannot execute learner actions, call an arbitrary causal package, write scene
state, or expose a tool that has not been declared by the active content pack.

When authorities conflict, deterministic domain results and released evaluation rules come first, followed by a reviewed rubric or released claim, then a provenance-bearing source excerpt, and only then model interpretation or generated wording.

## 6. Non-negotiable invariants

1. EducAgent is agent-first: the Pydantic AI tutor is the default pedagogical orchestrator, not a late optional embellishment.
2. The safety kernel and default tests remain provider-independent; a provider outage cannot erase learner evidence, fabricate completion, or bypass a gate.
3. Content packs own licensed subject matter and learner-visible factual teaching resources.
4. The tutor proposes one typed teaching turn; it does not directly award correctness, progression, or mastery.
5. The runtime owns progression eligibility and applies every state transition.
6. Rejected evidence can never advance, regardless of policy or model output.
7. Accepted evidence may make progression possible; it does not force progression.
8. Learner responses, failures, hints, revisions, decisions, and transfer attempts remain in an append-only trace.
9. Each learner attempt is an explicit boundary; its action, dialogue, hints, rubric, evaluation, and decisions must not mix with another attempt.
10. Learner state is a replay-derived summary, not an irreversible label inferred from one response.
11. Completion is not called mastery. Mastery requires repeated, delayed, previously unseen transfer.
12. Every learner-visible factual claim must resolve to a released resource, reviewed claim, or deterministic result. In M0, conversational framing comes from the versioned headless turn catalog. A tutor-selected move carries runtime-derived grounding resources and claims and may persist one bounded natural-language `tutor_reply` that is instructed to use only that frozen grounding, plus one legal Socratic question where appropriate. The reply is non-authoritative: it cannot mark an answer accepted, award correctness, or advance. Its trace records the derived grounding closure for audit; it is not a claim-support evaluator.
13. Only an evaluator/domain extension may emit `Evaluation.accepted`. M0 free-form learner text is unscored; the tutor may form a typed, traceable hypothesis from it only to choose among already-legal moves.
14. Agent output is a proposal, never a state mutation. Invalid, ungrounded, timed-out, or unavailable output selects a runtime-only legal `hold` fallback through the same scoped validator; `hold` is never offered as a normal tutor choice and cannot advance the learner.
15. Pydantic AI message history is execution context, not the source of truth for learner state; replayed learning events are authoritative.
16. Progression permission is bound to the current pending accepted scored-evidence event. An unscored support/message input or any non-advance move clears it; stale accepted evidence can never license a later `advance`.

## 7. Socratic pedagogy guideline

Socratic mode is a guarded agent loop around a learner action, not unrestricted
chat and not a second runtime. A master prompt establishes the tutor's voice
and teaching method, but the interaction contract supplies the concrete scene,
the learner's prediction/action, the observed result, the legal next actions,
and the hint position. Prompting without those facts tends to repeat the
initial question instead of moving an investigation forward.

```text
learner action
  -> renderer applies one declared object action, or evaluator returns closed-form evaluation
  -> runtime appends the learner event
  -> replay derives current learner state
  -> runtime exposes legal candidates, bounded released grounding, and a frozen object snapshot
  -> Pydantic AI tutor may read the declared scene and proposes one structured Socratic turn; the runtime derives the sole legal next interaction focus
  -> output validator and runtime gate recheck grounding, reveal, budget, and progression
  -> runtime appends the validated move event
  -> renderer presents the turn and relevant object state; the learner acts, retries, reflects, transfers, or advances
```

The policy must follow these rules:

- obtain a learner attempt before a content hint, except for explicit clarification, explanation, or accessibility requests;
- use one teaching purpose and at most one main question per turn;
- increase support monotonically within a bounded hint budget;
- provide a direct-teaching or worked-example escape when questioning is no longer productive;
- require a new learner action after direct teaching;
- accept an initially correct scored classification without requiring a
  meaningless second submission; require revision only after rejected scored
  evidence when the activity declares `requires_revision`;
- keep free-text dialogue available while gently returning attention to the
  scored control or declared object action when further questioning would not
  create new evidence; a message quota is not a learning budget;
- reject exact and semantic near-repetition of an attempt's recent Socratic
  teaching focus before the move is appended;
- begin each new causal scene with a hook and a learner prediction; after an
  object action, explicitly ask the learner to compare their prediction with
  the observed result before moving on;
- choose one of four visible dialogue jobs per turn—orient, elicit a
  prediction, interpret an observed consequence, or consolidate and route to
  the next action—rather than restating the original activity question;
- provide a small content-owned hint ladder and a direct explanation escape
  after a bounded number of unproductive turns; direct teaching must point
  back to a fresh learner action;
- never reveal an answer during elicitation or hinting;
- treat `advance` as a request that the runtime rechecks;
- provide the agent only frozen value snapshots of the current replay state, legal candidate moves, bounded recent learner turns, support budget, and released resources/claims needed for this turn; never provide a store, cursor, callback, or mutable session object;
- treat learner messages and retrieved passages as low-trust data rather than dynamic system instructions;
- require a strict `TutorTurnProposal` with an exact tutor-selectable candidate ID, an optional validated misconception hypothesis, a bounded grounded `tutor_reply`, and at most one persisted bounded Socratic question; do not accept a free-form fallback;
- derive grounding closure and expected-evidence predicates from the canonical runtime candidate rather than trusting agent-supplied IDs;
- record the evidence, agent/model/prompt versions, candidate ID, validated move, framing catalog/version and framing ID, derived grounding IDs, expected next evidence, validation result, retries, latency, and fallback source.

## 8. Content and source guideline

External textbooks and uploaded material are source material, not runtime truth. They must pass through an authoring and review process before they can license feedback or scoring.

The target content boundary uses:

- **Pydantic models** as the authoritative Python contract;
- **JSON files** as human-authored and distributed content packs;
- **generated JSON Schema** for editors and non-Python tooling.

The JSON Schema is derived from Pydantic and never hand-edited. Retrieval may help authors find source passages, but retrieved text does not automatically become a released claim.

S1 introduced the Pydantic contract and first authored JSON seed; S2 added reviewed claims, teaching resources, and release validation. These released resources, not the concept-graph index or whole textbook, form the runtime grounding boundary.

The declared reference textbook, *Elements of Causal Inference* (Peters, Janzing, and Schölkopf, MIT Press, 2017), is licensed under CC BY-NC-ND 4.0. Distinguish independently authored explanations and synthetic tasks from third-party text and figures. Keep textbook PDFs, extracted text, authoring figures, and research traces outside the public asset set. Accurate metadata and attribution do not substitute for a rights review of a particular adaptation or deployment.

## 9. Evidence and evaluation guideline

Keep three kinds of evaluation separate:

| Track | Question | Authority |
| --- | --- | --- |
| Subject correctness | Was the learner evidence accepted, and was feedback licensed? | declared evaluator/domain extension; the tutor never emits acceptance, and M0 free-form learner text is unscored |
| Pedagogy protocol | Did the tutor elicit, avoid reveal, respect hints, bottom out, and request the right evidence? | executable trace rules plus sampled review |
| Learning outcome | Can the learner transfer the idea without support now and later? | frozen immediate and delayed transfer tasks |

Verified assessment evidence and ordinary observations are different. Observations may influence routing, but only evidence produced under the declared evaluator and rubric can support completion, readiness, or future mastery claims.

The scope of that evidence must also be valid: a deterministic score can establish whether a response matches its rule, not whether one binary item measures nine distinct concepts. Current integrated/delayed items are limited probes. Freeze reviewed independent tasks and exposure rules before claiming broad immediate or delayed transfer, and do not retrospectively reinterpret historical results after content changes.

## 10. What we borrow

EducAgent combines small mechanisms rather than adopting one reference platform:

- explicit Socratic state and an escape hatch from OpenTutor;
- attempt-scoped dialogue and evidence from LibreTutor;
- verified-versus-observed evidence, pure decisions, and atomic state boundaries from tutor-mcp;
- trajectory records and failure reasons from SocraticBench;
- bounded hints, recovery, and executable pedagogy gates from supertutor;
- typed learning artifacts and publish/verify discipline from DeepTutor and Personal Tutor;
- deliberate context contracts and teacher controls from Artemis;
- a transparent deterministic control arm from whale-tutor;
- explicit asked-question context, deterministic near-duplicate filtering, and
  code-enforced interaction budgets from socrates-pen; EducAgent does not adopt
  its open-ended, unscored completion model.

These are design inputs, not runtime dependencies.

## 11. Explicit non-goals for M0

M0 will not build:

- a second LMS or general learning workspace;
- a multi-agent teaching team;
- a generic plugin or tool registry;
- a general-purpose Jupyter kernel, arbitrary learner code execution, or an
  LLM-generated causal-tool platform;
- a chat-first lesson in which text conversation substitutes for a learner
  prediction, causal-model action, and deterministic observation;
- arbitrary textbook-to-course generation at runtime;
- a vector database or RAG system as a correctness dependency;
- simultaneous BKT, FSRS, IRT, knowledge tracing, and knowledge-graph models;
- arbitrary generated executable activities;
- a single LLM judge as the authority for correctness, progression, or mastery;
- a general-purpose causal-world, graph-oracle, adjustment or counterfactual
  engine in M0; the explicitly authorised finite S39 scene adapter reuses the
  existing M1 Boolean kernel without expanding the curriculum.

## 12. Delivery strategy

Build the smallest coherent agentic vertical slice and prove each boundary before expanding it. Preserve S1–S3 as the safety kernel, add agent-ready events and replay in S4, then build one guarded Pydantic AI tutor in S5 and one complete replayable episode in S6. Expand the reviewed curriculum and renderer only after that loop works. Test a second domain before introducing generic extension abstractions. Exact steps, dependencies, and progress live in [`implementation.md`](implementation.md) and [`roadmap.md`](roadmap.md).

Every proposed feature must answer five questions:

1. Does it improve verifiable learner evidence?
2. Does it improve the tutor's pedagogical reasoning or its guardrails?
3. Does domain truth and progression authority remain with content, evaluators, and runtime gates?
4. Can its effects be traced and replayed?
5. Is its complexity justified by a current requirement or a second real implementation?

If not, defer it.

## 13. Target M0 success boundary

The declared Causality M0 curriculum scope uses these stable topic IDs:

- `variables-and-values`;
- `observed-association`;
- `association-is-not-causation`;
- `treatment-and-outcome`;
- `observation-vs-intervention`;
- `world-data-model`;
- `data-vs-assumptions`;
- `basic-dag-language`;
- `probabilistic-effects`.

These IDs define curriculum coverage, not released subject truth. Reviewed claims and deterministic results remain the teaching authorities.

M0 is successful only when:

- its required causal distinctions are taught through learner action, consequence, revision, and unseen transfer;
- every scored activity has a deterministic evaluator;
- every factual teaching resource has reviewed provenance;
- rejected evidence cannot advance;
- direct teaching is followed by another learner action;
- session and learner state replay from append-only events;
- a Pydantic AI tutor completes the experience through typed, grounded, runtime-validated turns;
- provider failure preserves evidence and returns a legal runtime-only, scoped-validator-approved `hold` fallback;
- completion, M1 readiness, and future mastery remain distinct;
- the evaluation package can compare EducAgent with reading and source-grounded chat on immediate and delayed transfer.

The implementation sequence and current evidence for these conditions live in [`implementation.md`](implementation.md) and [`roadmap.md`](roadmap.md).
