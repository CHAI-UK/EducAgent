# EducAgent SDK

For deployment of Learning, Portal and Nirvana together, start with the
[repository deployment guide](../README.md). Commands below run from
`EducAgent-SDK/`. Historical acceptance records under `output/` and private
qualification evidence are intentionally excluded from the public repository.

EducAgent SDK is an early-stage, agent-first Python SDK for evidence-driven teaching. A Pydantic AI tutor drives bounded Socratic decisions, while reviewed subject content, evaluators, replay-derived state, and runtime gates keep the learning path grounded. Causality is the first domain.

> **Current capability:** complete Causality M0 content with a reusable entry diagnostic, replay-derived completion/M1 readiness, a guarded Pydantic AI tutor, an Astryx conversational local client with JSONL resume, explainable learner profiles, content-free Logfire telemetry, deterministic quality audits, de-identified study exports, a fractions portability pack, a small M1 causal-world module, and a recorded ELM real-provider qualification.

The local Portal contains three authored courses, each with General and Medical
contexts: six separate normal content packs with versioned progress. Context
selection changes examples, not curriculum objectives or scoring standards.

| Course | Version in both contexts | Concepts / explanations | Activities per context |
| --- | --- | --- | --- |
| Causality foundations | `1.8.0` | 9 / 9 | 28, including 9 objective-specific final questions |
| Effect of an intervention | `1.4.0` | 4 / 4 | 16: 8 topic quiz/challenge items, 4 experiment stages, 4 final questions |
| Robust prediction or generation | `1.4.0` | 4 / 4 | 16: 8 topic quiz/challenge items, 4 experiment stages, 4 final questions |

S43 extends the local story-first guidance to General/Medical Effect, with one
assignment, target-mixture or analysis control per practice. Computed starting-
group counts and relevant differences remain visible after running. Unsaved
settings, predictions and comparisons survive responsive layout changes and
introduction exit/re-entry; full reload restores only saved runtime artifacts.
Historical Effect 1.2.0 progress stays separate. Remaining General Variables and
Umbrella action wording are aligned with their existing stories. The curriculum,
simulator mathematics, scoring and unlimited Tutor dialogue are unchanged.
Local and GCP acceptance are recorded separately in the roadmap.

S42 is the earlier novice-scaffolding revision of General/Medical Shift.
It preserves the four concepts and objectives, activity/answer IDs,
deterministic model and evaluator truth. The normal presentation order is
topics 1-3 Quiz/Challenge, prediction practices 1-3, topic 4 Quiz/Challenge,
generation practice 4, then four final items. Each practice exposes one relevant
control. This changes teaching sequence, not the concept curriculum. Optional
authored guide metadata and the phase-visible browser/Tutor projection are new;
historical packs retain their existing rendering and replay. Tutor dialogue
remains unlimited. S42 was accepted locally without a standalone archive;
the authorised S43 release combines that revision with Effect guidance.
Installed-target acceptance is recorded separately from package contents.

S33 applies the Foundations clarity standards to both M1 courses: short
definitions and examples, optional worked detail, plausible complete choices
and separate authored rejection guidance. It preserves concept order,
objectives, activity/answer IDs, scoring and experiment mathematics. This is
an author revision, not Kurt/Damian approval of the new M1 material or the
proposed intervention-course reorganisation.

The ordinary topic flow is Quiz -> Explanation -> Challenge. Both M1 routes
include parameter-driven deterministic experiments and a separate final assessment;
the robustness route addresses prediction and generation evaluation. All modules
are open for local browsing by default, which grants access rather than learning
credit. Historical `causality.m0.full / 1.1.0` and its traces remain unchanged and
are not migrated into the new Portal packs. S26 replaces S25's fixed-table M1
practice with operational experiments while preserving the four concepts,
four explanations and 16 activities per context. S26's provider-independent,
web/schema/build checks and targeted Chrome acceptance pass in the worktree.
See the [S26 acceptance record](output/portal-s26-20261015/verification.md).
Earlier checks are recorded in the [S25 acceptance record](output/portal-s25-20261015/verification.md); current progress is in
[`docs/roadmap.md`](docs/roadmap.md). This is not scientific approval, a full
curriculum qualification or evidence of learning effectiveness.

## Target architecture

The target learning turn is:

```text
learner evidence
  -> evaluator or typed unscored support/message
  -> append learner event
  -> replay-derived state
  -> legal teaching candidates + bounded released grounding
  -> Pydantic AI tutor
  -> typed TutorTurnProposal
  -> output validator + runtime gate
  -> append validated move event
  -> learner-facing rendering
```

The LLM is the main tutor, not the authority for domain truth or progression. It may interpret bounded, unscored free text, maintain a tentative misconception hypothesis, select a legal teaching move, and add one persisted bounded Socratic question to a legal question-oriented move. Released content constrains factual teaching; evaluators alone accept scored evidence; the runtime derives grounding and expected evidence, rechecks every move, and applies every state transition. Provider failure must preserve the learner's recorded evidence and select the legal runtime-only `hold` fallback, which is never offered as a normal tutor choice.

## Requirements

- Python 3.12 or newer
- Conda
- `pip`

Run all commands from the repository root. The examples below use PowerShell.

## Install for development

```powershell
conda create --name educagent-sdk python=3.13 pip -y
conda activate educagent-sdk
python -m pip install --build-constraint build-constraints.txt -c constraints.txt -e .
```

Reuse the existing `educagent-sdk` environment instead of creating it again. `pyproject.toml` declares the compatible dependency range. `constraints.txt` pins the validation dependencies used to verify this checkout, while `build-constraints.txt` pins the isolated build backend. A first installation may still need network access to obtain those pinned packages; tests and content validation do not.

## Validate a content pack

```python
from educagent_sdk import load_content_pack, validate_release

pack = load_content_pack("content/causality_m0.json")
report = validate_release(pack)
print(pack.pack_id, pack.version)
print(report.unused_resource_ids)
```

`load_content_pack()` performs strict structural validation: unknown fields, implicit scalar coercion, duplicate JSON keys, duplicate IDs within each ID namespace, unresolved concept references, incomplete feedback references, and activities without exactly one correct choice fail immediately.

`validate_release()` then checks the complete activity → teaching resource → claim → source chain. Missing, draft, incompatible, or unreviewed references raise `ReleaseValidationError`; a successful report lists any unused resources. This split lets an author load an unfinished draft without letting the runtime treat it as released content.

Release validation checks the declarations stored in the pack; it does not prove reviewer identity, method existence, source-file availability, or legal permission. The seed records the textbook's stated license and uses independently authored summaries, but external distribution still requires a separate rights review.

Schema v3 adds content-owned concept objectives and the activity evidence needed for `completed` and `m1_ready` status. It remains a one-way replacement for the unreleased v1/v2 seeds: activities store resource IDs instead of inline teaching prose. The root package exposes the small release boundary shown above; nested authoring models such as `Activity`, `Choice`, `Claim`, and `TeachingResource` remain available from `educagent_sdk.contracts` when direct Python construction is needed.

Typed `lessons` link released hook, worked-step, definition, pitfall, takeaway
and optional hypothetical-graph resources to each concept's practice and
transfer activity. `foundation_profiles.load_foundation_profiles()` compiles
`content/foundation_profiles.json` into General and Medical teaching sources.
`authoring/build_foundation_course.py` builds the versioned normal Portal packs
from those sources and the retained historical M0 pack, adding one final item
for each objective. `authoring/build_m1_courses.py` builds the four authored M1
context packs. Legacy `lesson` and `lesson_samples.load_lesson_samples()` retain
the earlier one-concept authoring samples.
`lesson_view()` supplies JSON-ready lecture copy without scoring keys or feedback;
`lesson_lecture_context()` supplies an immutable lecture-only tutor snapshot.
The explanations retain `author_draft` metadata; scientific review is pending.
Resource release flags describe the prototype grounding contract, not expert
approval. The learner pages retain source links without repeating a draft-status
caption in each explanation.

## Evaluate evidence and gate a move

Public learner evidence uses stable IDs rather than a displayed answer number:

```python
from educagent_sdk import (
    ChoiceEvidence,
    allowed_teaching_moves,
    evaluate_choice,
    load_content_pack,
    validate_teaching_move,
)

pack = load_content_pack("content/causality_m0.json")
evidence = ChoiceEvidence(
    activity_id="observation-vs-intervention.01",
    option_id="association-proves-intervention",
)
evaluation = evaluate_choice(pack, evidence)
allowed = allowed_teaching_moves(
    pack,
    evidence,
    curriculum_requirements_met=False,
)
move = validate_teaching_move(
    pack,
    evidence,
    allowed[0],
    curriculum_requirements_met=False,
)
print(evaluation.accepted, evaluation.consequence_resource_id)
print(move.strategy, move.resource_id)
```

The evaluator returns semantic IDs, not feedback prose. The runtime gate recomputes from the evidence and accepts only an exact canonical move. `curriculum_requirements_met` is trusted runtime/curriculum state, never learner or policy input. Normal selectors cannot choose the runtime-only `hold` fallback.

## Record and replay a learning turn

S4 uses a plain in-memory list as the append-only authority:

```python
from educagent_sdk import (
    ChoiceEvidence,
    close_attempt,
    complete_session,
    load_content_pack,
    record_choice_response,
    replay,
    select_s4_move,
    start_attempt,
    start_session,
)

pack = load_content_pack("content/causality_m0.json")
events = []
start_session(events, pack, session_id="demo.01")
start_attempt(events, pack, attempt_id="attempt.01")
record_choice_response(
    events,
    pack,
    attempt_id="attempt.01",
    request_id="request.01",
    evidence=ChoiceEvidence(
        activity_id="observation-vs-intervention.01",
        option_id="association-only",
    ),
    curriculum_requirements_met=True,
)
select_s4_move(events, pack, request_id="request.01")
close_attempt(events, pack, attempt_id="attempt.01", status="completed")
complete_session(events, pack)
state = replay(events)
print(state.status, state.completed_activity_ids)
```

The response event is appended before move selection. Reusing the same request ID with identical content is idempotent; changing its content is a conflict. If execution stops after learner input, `recover_pending_turn()` appends one validated runtime-only `hold` without losing the input or granting progression. `replay()` performs no writes and rejects invalid sequences, forged evaluations, noncanonical moves, and illegal lifecycle transitions.

## Run the guarded tutor

Call the tutor only after recording learner input. This provider-independent example uses Pydantic AI's `TestModel`:

```python
import asyncio

from pydantic_ai.models.test import TestModel

from educagent_sdk import build_tutor_deps, run_tutor_turn

deps = build_tutor_deps(events, pack, request_id="request.01")
model = TestModel(
    custom_output_args={"candidate_id": deps.candidates[0].candidate_id}
)
result = asyncio.run(
    run_tutor_turn(
        events,
        pack,
        request_id="request.01",
        model=model,
    )
)
print(result.rendered_turn.text)
```

`TutorTurnProposal` contains a candidate ID, an optional evidence-backed misconception hypothesis, and—only for a legal question-oriented move—one bounded Socratic question. The runtime rebuilds the candidate set, validates selector scope and question shape, derives grounding/framing/expected evidence, and appends the move. Learner-visible M0 factual text comes from released resources; the generated question cannot score, name an answer, or grant progression. Invalid output, timeout, or provider failure appends one runtime-only `hold` without losing learner input or granting progression.

The SDK includes Pydantic AI's OpenAI-compatible client for the concrete ELM qualification path. An application can construct an ELM model with `load_elm_settings()` and `build_elm_model()` or pass another configured Pydantic AI model to `run_tutor_turn()`. To emit the SDK's content-free decision metadata after application startup has configured Logfire, pass `observer=logfire_tutor_observer`. The SDK never calls `logfire.configure()` on import. See [`docs/logfire.md`](docs/logfire.md) for the startup configuration.

## Run the playable local demo

The built-in demo is a local-only Astryx action-first learning workspace over
the same event runtime. It begins with an optional nine-question Causality M0 starting
snapshot, then opens a targeted M0 review of the concepts it missed. Diagnostic
success is route credit, not M0 scored evidence, completion, readiness, or
mastery. Free-text teaching requires a configured Pydantic AI tutor; fixed scored
choices are checked deterministically. This does not change evidence evaluation, resource
grounding, or progression gates: the runtime remains their authority.

```powershell
npm install
npm run web:build
$env:PYTHONPATH = "src"
conda run -n educagent-sdk python examples/playable_demo.py
```

Open `http://127.0.0.1:8000`. Use Tab, Space, and Enter to complete the entry
snapshot and M0 choices. The reset control explicitly clears the local M0
JSONL trace for the selected context and restarts its entry snapshot; otherwise
a browser reload resumes the trace. A completed entry diagnostic starts its
preferred targeted-review route. The demo loads the
modules declared by `content/modules.json`; use `--registry` for another valid
registry or `--events-root` for an isolated local run. The normal launcher now
uses anonymous browser sessions under `browser-sessions/`. Startup rejects the
legacy `--reset` switch; use Reset progress in the intended browser instead.
Module access is open by default; `--enforce-module-prerequisites` restores the
declared prerequisite access checks. Neither access option grants scored credit.

Configure the ELM variables described above before starting the demo. Fixed
scored-choice checks are evaluated and selected locally through the versioned
fixed-policy runtime, so they return immediately. The tutor selects a validated
teaching move for the opening, free learner messages, explanation requests, and
scene actions. The tutor may add one persisted, validated Socratic question to
a released turn. Each browser session owns a persistent async runtime and model
client, with serialized requests inside that session. Independent sessions do
not share a client across incompatible loops.

For local comparison with ordinary model behaviour, add `--unguarded-tutor`.
Only free-text messages use this path: the model receives guided instructions,
phase-visible authored context and current-attempt dialogue, then returns plain
text without the guarded typed-proposal validator. A sample lesson supplies
released lecture copy, not hidden quiz answers. Scored responses, scene actions, progression, and replay
continue to use the normal SDK runtime. This is an experimental demo mode, not
the default tutor policy or a production safety claim.

For a causal-scene free-text reply, the runtime—not the model—also records the
current legal interaction focus and dialogue job. This keeps an unguarded reply
compatible with the same replay contract as a guarded scene turn.

If a free-text tutor call fails, the server preserves the learner message as a
pending turn and returns a safe failure category plus its request ID. The
browser names that pending state and its retry control resends the exact same
request ID, so it neither loses nor duplicates the learner's message. The
browser never receives raw provider details; the local server log records the
request ID alongside the complete exception for diagnosis.

### Manual demo checks

1. Complete the nine-question entry diagnostic and confirm that it reports a
   starting snapshot, then opens targeted review for the missed concepts.
2. Ask a question in your own words and confirm that your
   message appears before one tutor response, while the answer choices remain
   available.
3. Reload the browser after a message or answer, then continue; the local JSONL
   trace should resume without a request-ID conflict.
4. With a deliberately unavailable local tutor, submit a free-text message,
   reload, and use `Retry saved message`. Confirm the request ID is named in
   the safe browser error, the message appears once, and the local server log
   has the matching request ID and exception.
5. Choose a wrong answer, request a fuller explanation, and retry. It should
   never mark progress until deterministic evidence and a validated `advance`
   exist.
6. Complete a diagnostic item correctly and confirm that the learning route
   calls it `Entry check correct`, not completed topic/course evidence.
7. Restart without `--reset` and confirm that persisted progress resumes.

### Course contexts, developer preview and authoring

From the umbrella launch on port 4173, open
`http://127.0.0.1:4173/portal/` and choose General or Medical in the first-entry
dialog. All three courses use the same workspace, profile controls and topic
sequence: answer the quiz, inspect its explanation and feedback, then attempt a
new-case challenge. Wrong answers can revisit the explanation and retry. The optional Foundations entry quiz
uses the selected context's practice questions; it is not an independent
assessment bank. Medical's rain/umbrella challenge deliberately remains a
shared general case. Clinical stories and simulator effects are fictional,
not clinical findings or advice.

Both M1 courses open with a General/Medical introduction explaining why the
course is useful, a motivating case, the learner's planned actions and how the
two questions differ. Effect asks what an action would change; Robustness asks
whether predictions or reports remain dependable under specified changes of
setting. They are complementary, not mutually exclusive routes. `Course
introduction` reopens this orientation during learning; returning preserves the
current attempt. The normal start button still starts the existing course.
The introduction is not an assessed activity or an additional prerequisite.
Unstarted M1 introductions share Foundations' entry sidebar: EducAgent identity,
the active course route, and links to the other modules. Reopening an introduction
during a started course retains its actual Tutor conversation instead.

Its independently versioned source is `content/course_introductions.json`
(catalog version `1.2.0`),
validated against the registered profile packs and their released claim IDs.
This orientation catalog alone does not modify `ContentPack`, scoring,
Tutor inputs or trace versions.
Edit this orientation JSON separately; it is not part of ContentPack editor
exports. Two built-in imagegen illustrations and their exact prompts live in
[`web/public/media/course-openings/`](web/public/media/course-openings/README.md).
These illustrations supply fictional context rather than evaluation evidence.
The [S27 acceptance record](output/portal-s27-20261015/verification.md) records
255 Python tests, six editor tests and targeted Chrome entry/resume checks.

Question and explanation artwork is explicitly bound by pack identity/version
in `content/course_illustrations.json` (catalog `1.5.0`). The normal launcher
applies image-only teaching overlays; the overlay itself changes neither scored
pack bytes nor JSONL evidence. Catalog 1.3.0 retains the earlier bindings,
including Foundations 1.5.0/1.6.0, and adds exact-version General/Medical Shift
1.3.0 bindings. Historical packs are not rewritten. Quiz/Challenge never inherit
an unrelated lesson's picture. Optional entry checks use the same question image without changing
their evaluator pack. Twelve built-in imagegen illustrations, exact prompts
and scope notes are in
[`web/public/media/question-context/README.md`](web/public/media/question-context/README.md).
All 68 ordinary Quiz/Challenge questions in the six current profiles have
explicit context art, including the two integrated transfer challenges. S38
added six neutral scenes and filled 17 missing question images without changing
the then-current pack versions. Final assessments, staged scenes and experiment results retain
their existing deterministic presentation rather than a generic image fallback.

Questions with an explicitly written, forward-arrow chain also show that public
chain as labelled nodes above the context picture. This includes the Causal
graphs Quiz/Challenge in both profiles and their entry-quiz reuse. Wide views
use a row; narrow views use a column so labels stay readable. The graph's
accessible name states its arrow endpoints, not an answer. No lesson/answer
graph is substituted, and unsupported chains retain their text. Course content,
versions, scoring and saved progress are unchanged by this presentation.

Use `Change profile` to switch and resume each context independently. Reset
clears only the selected module/context and asks for a profile again. Profile
switching is available in Foundations and both M1 courses. Foundations uses
`causality.m0.general.course / 1.8.0` and
`causality.m0.medical.course / 1.8.0`. Effect uses
`m1_effect_course_{general,medical}_1_4_0.json`; local Shift uses
`m1_shift_course_{general,medical}_1_4_0.json`. Previous Shift 1.2.0 packs and
progress remain unchanged and are not migrated into 1.3.0.
The retained `foundation_*_course_1_5_0.json` outputs combined Kurt/Damian clarity feedback,
including concrete variable-list choices and shorter default explanations, with
the S37 answer-cue revision: no answer-bearing stems, a third plausible option on
former two-option topic items, varied answer positions and "Not yet." feedback
that does not state the answer. A rejected quiz stays on its answers; its
Explanation opens only on request. Recorded values appear in small tables
(including in the entry quiz) rather than in long headings. Each page shows the
scenario as its title, then a wide picture capped to the window height and any
table, then the question in bold directly above the answers, in one reading
column of about 70-80 characters per line. A question with a picture
and a table shows both in one scenario card so the answers stay on screen;
supporting text is 14px. Retained `foundation_*_course_1_6_0.json` preserves those
questions and adds only the bounded dynamic umbrella investigation described below.
The `1.5.0` and `1.4.0` outputs, the first expert-feedback `1.3.0` outputs and original
`foundation_*_course.json / 1.2.0` remain frozen, with no automatic migration
or reinterpretation of their answers. In particular, 1.5.0 completion is not
shown as 1.6.0 completion; the earlier records remain available with their matching release.
Retained `foundation_*_course_1_7_0.json` keeps the model-identification Quiz and
replaces only the World/data/model Challenge with a paired data/world question
in both profiles. Recorded readings are data; the physical device and its
processes belong to the world; the engineer's explanatory sketch is a model.
This changed assessment uses separate versioned progress and does not inherit
1.6.0 credit. Both 1.6.0 files remain frozen; back up browser-session directories
before switching versions to retain their diagnostic selections for rollback.
The 1.7.0 draft also supplies small example-record tables for the Data
and assumptions Quiz and Challenge in both profiles. Tables contain only the
two recorded variables; the proposed common cause remains an assumption. These
presentation examples do not change option IDs, verdicts or completion rules.
Current local Foundations 1.8.0 and M1 1.4.0 distinguish each topic's Quiz and
Challenge facets. Required distinctions appear in the default definition/hook;
optional worked steps remain available in the source sidebar. Changed Challenge
meanings use new answer IDs; already complementary pairs remain intact. Quizzes,
final assessments, curriculum and interactive models remain unchanged. Earlier
1.7.0/1.3.0 files and records are retained without credit migration. The SDK
roadmap links the per-topic review and local acceptance evidence.
Each module/context/version has its own JSONL. Historical M0 and one-concept
sample packs and traces are neither migrated, merged nor deleted. Earlier M1
`1.0.0` and `1.1.0` packs/traces are retained separately, without migration
into `1.2.0`; the original `0.1.0` M1 seed files remain available.

The normal playable launcher now isolates progress, diagnostics, dialogue and
module/Profile preferences using a random HttpOnly, SameSite=Lax session cookie.
Different browser Profiles/browsers and separate private-browsing contexts get
independent records; tabs in the same browser Profile share one session. Refresh
and server restart resume compatible saved state while the cookie remains.
Closing the browser normally expires a session cookie, but session restore may
retain it. Clearing cookies creates a new record; no login, cross-device sync or
cookie-loss recovery is provided. Old shared traces are preserved but not
automatically adopted by a new browser. Temporary preview/review returns to
normal course state after cache eviction/restart. Use restricted access/TLS
for shared-server review, and only one process per state directory.
The lower-level `create_module_hub_server` keeps its explicit legacy single-hub
contract for existing SDK consumers.

The topic directory marks `Completed` once its declared Quiz and Challenge have
accepted evidence, including an accepted current Challenge before Continue.
This is topic-practice completion, not proof that its final question, the full
course or mastery is complete. The underlying formal credit remains unchanged.
Clicking a completed topic opens temporary review even before the course ends;
an unfinished topic opens its remaining normal activity. `Back to my course`
restores the saved attempt/answer. Review retains the original checkmarks and
does not rewrite the course JSONL; its dialogue/practice do not grant course
credit or survive a service restart. Tutor discussion remains available without
a learner message quota. New-activity navigation restores canvas scroll/focus,
while ordinary chat and experiment updates do not move the learning canvas.

`Final check` is a separate bottom directory section in all three courses. Its
header, highlight and completion marker are independent of the topic being
assessed. Before an unanswered first final question, a transition offers
`Start the final check` or `Review course topics`; it congratulates completed
topics only when their practice is finished. Existing answers and later final
questions resume directly. Clicking the completed Final check opens temporary
review without changing saved grades or adding a curriculum concept.
`Review my trace` uses the same separate Final check section after the topics.
It groups final dialogue by the pack's authored final activity IDs before using
concept IDs, so a final question never appears in its earlier lesson transcript.
Existing records are regrouped on read without rewriting events. Trace selection
is scoped to the current module, profile and pack version.

S39's umbrella investigation is shared by General and Medical without changing
the nine-concept curriculum or 28 activities. Learners choose from three declared
Boolean structural models, each with arrows and an explicit generation rule:
rain causes both variables, umbrella carrying causes wetness, or wetness causes
umbrella carrying. Each reproduces the same 240 observational arrivals, including
96 wet arrivals. A DAG alone is not treated as enough to calculate an outcome.
The versioned finite kernel calculates both the learner hypothesis and a separate,
fixed reference world for the existing action `do(Umbrella carried = yes)`.
Changing the hypothesis cannot rewrite the reference world. The three hypothesis
results are respectively 40%, 100% and 40% wetness; the reference remains 40%.
At least two distinct hypotheses must be run before the final revision. Predictions,
comparisons and reflections are unscored; only the final graph is evaluated against
the then-disclosed reference assumptions. Agreement with one intervention does not
identify a unique DAG. This is a finite teaching simulator, not arbitrary equations,
learner code, real-world causal discovery or a clinical model. The historical 1.5.0
scene retains its original prewritten-result behavior and replay.

Dynamic-scene button actions record the sole authored current-phase feedback
through the SDK without an LLM request or generated extra question. This keeps
a previous hypothesis from contaminating the next prediction prompt. Free-text
Tutor conversation remains model-driven and has no dialogue-turn quota.

The final umbrella graph uses editable permitted arrows, and the later DAG
explanation revisits the same example to name nodes, arrows and paths. Authored
lecture graphs retain their typed three-node, two-edge common-cause contract;
arbitrary DAG authoring is not supported by that lecture renderer.
Each M1 practical stage commits a typed configuration and an
unscored prediction, runs a server-owned deterministic model, then lets the
learner change settings and rerun. After two distinct configurations and a
written comparison, the existing scored concept check becomes available.
Effect retains its existing workbench: `Save my prediction` -> `Run experiment`,
followed
by a changed setup and `Save my next prediction` -> `Run experiment` ->
`Record my comparison`. Local Shift 1.3.0 uses `Start practice` ->
`Save my prediction` -> `Run this test` -> `Change one setting and test again`
-> `Record my comparison` -> the scored interpretation check. Exit/resume
does not reset progress or award credit. Saved settings and results can be
compared together;
neither the prediction nor the reflection itself earns scored credit.
Free Tutor discussion remains available throughout; there is no dialogue quota.
The current S39 guided Tutor policy is `1.9.0`, with Tutor `1.15.0` and prompt
`1.16.0` (runtime `0.10.0`, retaining earlier replay). Dynamic-scene context keeps
selected hypotheses, completed runs and the reference world distinct, with
reference mechanisms disclosed only at the comparison/revision stage.
Public hypothesis metadata names each model's root variable and active nodes,
so Tutor grounding does not silently substitute Rain for the wet-pavement root
in the reverse-causation model or add Rain to a model where it is absent.
Read-only Tutor context retains the latest four simulation runs plus one
representative per distinct tested hypothesis before the 24,000-character
context check. The full runtime/API snapshot and append-only replay retain all
runs; this projection is not a run or conversation quota. Provider-independent
regressions exercise twelve runs and twelve mock replies per profile, with
per-model request captures checking mechanism-specific context. These checks
do not establish the quality of live generated dialogue.
Its Shift context retains
public quantity definitions separating reference targets, noisy measurements,
predictions, source fidelity and coverage, and instructs the Tutor to correct
conflicting earlier chat. Before a final answer is submitted, openings and
`Explain this concept` use the same concept-only context as final-safe chat,
and learner-copied current stem/option wording is replaced by
`[withheld final-check text]` before it reaches the model (a lexical copy
boundary, not paraphrase detection),
rather than rendering the current item's accepted explanation. The explanation
button and recorded support request remain available. This is a narrow repair,
not a guarantee against semantic answer leakage. It adds no learner turn quota
or new conversation gate; M1 experiment parameters, results and scoring remain
unchanged. S39 adds optional typed simulation declarations and run records for
the newly versioned Foundations packs rather than rewriting older traces.

Guided requests have a 15-second application deadline; failed chat keeps its
saved input for idempotent retry, without a learner question quota. Repeated
explicit Explanation remains an explanation. Explicit one-question requests
receive a narrow preference check/recovery, not a qualified Socratic guarantee.
Public chat shows readable role details for first/new worked examples, while
private saved text retains the exact anchor. Mobile chat scrolls internally;
the labelled composer preserves per-attempt drafts across responsive/profile/
module changes and does not send when confirming an IME candidate. These are
in-memory drafts, not durable storage across reload or temporary-review closure.

For generated adjustment examples, the internal `AdjustmentExampleReply`
output supplies treatment, outcome, pre-treatment common-cause and target
labels plus a teaching step. A deterministic renderer creates the role header
and explanation clauses from those same fields, rather than silently changing
the grouping variable. Safe replay-derived history supplies the latest active
example anchor even beyond the twelve-message recent context; ordinary chat
and unanswered-final `Explain this concept` use the same history filter.
The Tutor can explicitly announce a new example, and ordinary conceptual text
answers remain available. Instructions keep that hypothetical example separate
from the visible experiment's names, numbers and recorded results. This bounds
one role-continuity failure, not the scientific validity of arbitrary prose or
every semantic answer leak. Course content, evaluator authority and unlimited
learner dialogue are unchanged; current acceptance evidence belongs in the
roadmap rather than being inferred from this behavior description.

The server computes outcomes, records, metrics and template-generated reports;
the browser renders those snapshots and never supplies scores or results.
Both Tutor context and deterministic opening/fallback rendering exclude the
legacy fixed-table appendix in operational practice. Before the first run only
settings and tentative predictions are available; numerical evidence comes
from actually revealed runs, not older reference tables or generated dialogue.

Effect experiments distinguish a fixed source cohort, selected or balanced
random assignment, common target weights and pooled or standardized analysis.
Robustness experiments vary cue reliability, measurement error and context
availability, select prediction and report-generation rules, and expose actual
source/report pairs, unsupported additions and withholding/coverage tradeoffs.
Source-faithful reporting is distinct from agreement with an independent
reference. These are declared teaching models and templated outputs, not an
LLM report-generation service, arbitrary code execution or real clinical data.
Foundations is unchanged by S26. AI-generated PNGs provide context and never serve as evaluation evidence.
Trace review keeps its chat transcript in a fixed-size scrolling pane.

The normal route has no `Testing preview` button. Explicit `/portal/?preview=1`
is developer QA: it permits arbitrary activity selection
and bypasses module prerequisites using controllers with no event store. Preview
still uses ordinary deterministic scoring and tutor conversation, but writes no
learning credit to saved progress. Leaving preview restores the normal module,
profile and attempt present on entry; server restart discards preview state.
Preview entry/exit and successful module changes replace their URL parameters
without adding a history entry. Returning to learning removes the preview flag
so a later refresh cannot silently enable it again. Local student walkthroughs
use normal saved progress by default, as explicitly authorised by the user.
Preview is an explicit developer inspection entry. Normal module browsing is
already open by default, while preview additionally isolates all attempt writes.
Legacy one-concept lesson entries are visible only in that developer route.

The editor is available locally at
`http://127.0.0.1:4173/authoring/content-pack-editor.html` (or port 8000 for the
SDK-only demo). Imported content retains images, scenes, classification types,
deterministic derivations, optional lessons and fields outside the form. Editing
changes only the targeted fields. HTTP validation/export calls the same-origin
`POST /api/validate-content-pack` for strict SDK structure and release checks;
validation does not install or modify content on the server. Direct `file:` use
can export a draft but explicitly reports that SDK validation has not run.
The editor page is loopback-only and is not part of the public staged assets.
It edits schema-v3 ContentPack JSON. `foundation_profiles.json` and
`foundation_lesson_samples.json` are raw
compiler input, not an importable ContentPack. Experts can edit compiled resource
and activity text in the GUI; sample-source fields and lesson/graph structure
currently require JSON editing. These non-form fields survive GUI round trips.

Regenerate the normal course packs after changing their authored sources, or use
the freshness checks below from the SDK root:

```powershell
$env:PYTHONPATH = "src"
python authoring/build_foundation_course.py --check
python authoring/build_m1_courses.py --check
```

Without `--check`, each generator writes its derived course packs. The historical
`content/causality_m0_full.json` remains a retained input, not a generated target.

After an accepted scored answer, ordinary follow-up dialogue, explanation and
reload retain the recorded completion evidence. A new scored judgment replaces
that evidence. If optional discussion fails, the learner can retry the saved
request or continue from the already checked answer; continuing appends a
runtime recovery event before closing the attempt. State conflicts and invalid
requests now have distinct error categories and recovery guidance, rather than
being presented as an undifferentiated tutor disconnection. None of these paths
lets unscored text create correctness or completion.

This first-stage slice passed 181 provider-independent Python tests, five Node
editor regressions, type/build/schema checks and real Chrome checks. General and
Medical live conversations covered nine and ten learner turns respectively;
post-answer dialogue, explanation, continuation, offline retry and both sample
challenges were exercised. Chrome also verified preview return and a lossless
full-pack GUI round trip, including a clearly labelled non-releasable draft
export. See the [verification record](../output/portal-goal-20261014/verification.md).
These are historical first-stage results. The subsequent S25 local technical
checks are complete in the worktree: 230 provider-independent Python tests, six
Node editor tests, web type/build checks and schema/generator freshness checks
passed. After the final content/UI refinements, 24 focused tests and schema
freshness passed again. Chrome verified the General wrong-answer -> explanation
-> retry -> challenge -> next-topic flow, three consecutive live novice Tutor
replies, M1 profile/explanation and practical/final samples, saved-message retry
with accepted credit preserved, and a complete ordinary Medical umbrella
mission. Completion retained the Tutor; long and empty trace logs kept the same
bounded dimensions and internal scrolling. Portal and Nirvana health returned
200 at handoff. These are targeted checks, not a Chrome walkthrough of every
activity. Scientific review and learning-effect evaluation remain outstanding.
See the [S25 acceptance record](output/portal-s25-20261015/verification.md).
Those fixed-table M1 observations are historical. S26's operational M1 practice
passes all 246 provider-independent Python tests (39.624 s), six Node editor
tests, schema/M1 generator freshness and web type/build checks. Targeted Chrome
operations passed for General and Medical in both M1 courses, including changed
assignment/target weights, cue reversal, report withholding and measurement
error. Medical robustness also received three consecutive live Tutor replies;
an incorrect scored check could be retried successfully and then froze the
artifact. This was not a Chrome walkthrough of every activity. Scientific review
and learner evaluation remain outstanding. See the
[S26 acceptance record](output/portal-s26-20261015/verification.md).

## Run the complete M0 episode in tests

[`content/causality_m0_episode.json`](content/causality_m0_episode.json) is the first complete headless episode. It asks a learner to classify observed clinic data, records a concrete consequence, requires a revision of the same artifact, asks what causal claim still needs an assumption, and finishes with an unseen software scenario. `ClassificationEvidence` records both the stable classification ID and the learner artifact it revises; runtime replay rejects a future, cross-session, or different-artifact reference.

The end-to-end provider-independent contract test is:

```powershell
$env:PYTHONPATH = "src"
python -m unittest tests.test_episode -v
```

It uses `TestModel` and `FunctionModel`, not a live provider. The separate ELM S6/S9 qualification uses the same episode without bypassing `record_*`, `run_tutor_turn()`, `close_attempt()`, or `complete_session()`.

After configuring ELM credentials, run the separate qualification command. It
is deliberately outside the default suite;
it completes the S6 episode, exercises the direct-instruction escape, checks
the frozen quality thresholds, and writes a non-secret record only on success:

```powershell
$env:PYTHONPATH = "src"
python examples/qualify_guarded_tutor.py --output docs/evidence/elm-qualification.json --logfire
```

The command reads `BASE_URL`, `MODEL`, and `ELM_API_KEY` from `.env` (or from
the process environment, which takes precedence). For an ELM proxy key, set
`BASE_URL=https://elm.edina.ac.uk/api/v1`; do not commit the key. `--model`
only overrides `MODEL` for a deliberate one-off qualification run.

The command only calls a provider when you invoke it. It does not print or
store API keys, learner text, prompts, event IDs, or Logfire credentials.

## Test

```powershell
$env:PYTHONPATH = "src"
python -m unittest discover -s tests -v
python scripts/generate_schema.py --check
```

The default unit tests and schema check require no live model provider, API key, or network connection after dependencies are installed. Tutor tests use Pydantic AI `TestModel` and `FunctionModel` and explicitly forbid real provider requests; real-provider qualification is a separate integration path.

## Build a wheel

```powershell
python -m pip wheel --build-constraint build-constraints.txt --no-deps --wheel-dir dist .
```

The wheel is written to `dist/`, which is ignored by Git. `build-constraints.txt` pins the build backend used for verification. The wheel contains the Python SDK package; the seed JSON and generated schema remain repository-level authoring artifacts and are not bundled as package data.

## Regenerate JSON Schema

Pydantic models are the only authored structural schema. Regenerate the derived artifact after an intentional contract change:

```powershell
$env:PYTHONPATH = "src"
python scripts/generate_schema.py
python scripts/generate_schema.py --check
```

Do not edit `schemas/content-pack-v3.schema.json` or
`schemas/diagnostic-plan-v1.schema.json` by hand.

JSON Schema exposes the portable field structure. Cross-field structural rules are enforced by Pydantic; cross-registry release rules are enforced by `validate_release()` and their tests.

## Project documents

The README is for external setup and usage. Internal design and progress live in:

1. [`docs/goal.md`](docs/goal.md) — product goal, authority boundaries, and design rules.
2. [`docs/implementation.md`](docs/implementation.md) — ordered implementation steps and exit conditions.
3. [`docs/roadmap.md`](docs/roadmap.md) — current status and completion evidence.
4. [`docs/study-protocol.md`](docs/study-protocol.md) — M0 pilot protocol and the research-owner decisions required before enrollment.
