# EducAgent Portal: Product Conclusion

**Status:** S47 with the 6 November report hotfix deployed on the existing GCP HTTPS service; full Medical Effect/Shift remote technical acceptance passed; complete scientific review and learning evaluation pending

**Last consolidated:** 2026-10-27

## Product identity

Portal begins with `Causality Foundations` for people learning causal reasoning from the beginning; no research background is required. Two authored follow-on routes cover `Effect of an intervention` and `Robust prediction or generation`. The SDK's concept backbones and runtime remain canonical. Fixed authored course packs supply this prototype rather than a second host or runtime curriculum generator.

The public promise should remain modest: Portal is designed to help a learner practise foundational causal distinctions through an action-first Socratic experience. It is not yet evidence that the learner has achieved mastery.

An earlier local Chrome walkthrough completed both M1 courses in General and
Medical: 64 scored activities, 16 practical stages and 34 actual experiment
runs, with live fictional student questions. Entry sidebars now share the
Foundations treatment. The walkthrough exposed legacy fixed-table numerical
content leaking into experimental Tutor context and deterministic openings;
both paths were repaired and retested. URL state now tracks preview exit and
module changes. See the [S29 acceptance record](../../EducAgent-SDK/output/portal-s29-20261015/verification.md)
and the SDK roadmap for exact evidence and limitations; this is not a scientific
or learning-effect qualification.

The historical S32 combined Foundations follow-up used version 1.4.0 for both profiles and
guided Tutor policy 1.5.2. Actual Chrome completed all 28 General activities;
Medical received targeted feedback, explanation, graph/probability, scene and
multi-turn chat checks. Inline authored rejection feedback and compact optional
detail are shared across profiles. Live early-scene and final-answer disclosure
defects were repaired and retested without a learner message quota. These
checks do not establish semantic non-leakage or scientific approval; see the
[S32 acceptance record](../../output/portal-s32-20261019/verification.md).

## Selected learning experience

The selected Portal content is the current SDK route:

- an optional entry diagnostic that can prioritise review without granting completion; skipping it starts the full M0 learning route and does not record diagnostic success;
- a direct `Try an exercise` entry to the existing rain/umbrella investigation without requiring the diagnostic;
- nine Causality M0 concepts, including variables, association, intervention, assumptions, DAG language, and probabilistic effects;
- explicit learner commitments and deterministic evaluation for scored activities;
- a rain, umbrella, and wet-pavement causal workbench in which the learner inspects records, chooses an explicit hypothesis, predicts and runs an intervention, compares its calculated result with a fixed reference world, and revises a final graph;
- a visible tutor conversation alongside the active learning object;
- a compact first-entry/reset profile chooser and editable General/Medical
  context across all three modules, with Quiz -> Explanation -> Challenge in
  the ordinary topic route, feedback and retry;
- objective-specific final questions, plus four stages of parameter-driven
  deterministic experiments in each M1 context;
- default open access to each module for local browsing, independent of scored
  completion or readiness;
- a Tutor panel that remains visible at completion, temporary topic review,
  and a fixed-size scrolling transcript in trace review;
- replay-derived progress and a distinction between diagnostic credit, completion, and later transfer evidence.

The SDK remains the canonical source for the exact content, event, evaluator, progression, and accessibility contracts. Portfolio documentation should describe those contracts rather than inventing a second Portal curriculum.

Most current activities remain authored choice questions, with three or four options on ordinary topic items. Feedback distinguishes `Correct` from `Model matches the supplied assumptions`; neither establishes an unseen explanation or mastery of all nine concepts. The S39 rain/umbrella mission requires at least two distinct declared hypotheses to be run under the same intervention before the final graph revision. Predictions and reflections remain unscored; only the graph representing the disclosed reference assumptions is evaluated. The supplied mechanisms and deterministic outcomes are not empirical evidence or a uniquely identified real-world graph.

The six current normal packs are General/Medical versions of each module:

| Module | Version | Concepts / explanations | Activities per context |
| --- | --- | --- | --- |
| Foundations | `1.8.0` | 9 / 9 | 28, including 9 final questions |
| Effect of an intervention | `1.4.0` | 4 / 4 | 8 topic items + 4 experiment stages + 4 final questions |
| Robust prediction or generation | `1.4.0` | 4 / 4 | 8 topic items + 4 experiment stages + 4 final questions |

S43 extends the one-control guide and stable App draft ownership to Effect in
both profiles. The four original experiment configurations and deterministic
calculations are retained; relevant differences and computed starting-group
counts support prediction, run and comparison. Historical 1.2.0 evidence is not
migrated. General Variables and Umbrella action copy stay within their current
stories. The curriculum, evaluator authority and unlimited dialogue are unchanged.
The SDK roadmap records complete local Effect acceptance and targeted authorised
GCP HTTPS acceptance independently. Both profiles passed live fictional Tutor
checks; the earlier image and a private learner-data backup are retained.

S42 changes the local Shift presentation sequence to topics 1-3 Quiz/Challenge,
prediction practices 1-3, topic 4 Quiz/Challenge, generation practice 4, then
four final items. Each practice starts with a concrete story and purpose and
exposes one relevant control. Optional authored guide metadata and phase-visible
browser/Tutor projection are new; the four concepts and objectives,
activity/answer IDs, deterministic model and evaluator truth remain unchanged.
Historical Shift 1.2.0 packs and progress retain their existing behavior and are
not migrated into 1.3.0. Tutor dialogue remains unlimited. S43 selects introduction
and illustration catalogs 1.3.0 and 1.4.0. S42 was accepted locally without a
standalone archive; S43 combines both guided M1 revisions. Installed-target
acceptance is recorded separately in the SDK roadmap.
This technical release is not renewed expert approval or learning-effect evidence.

Each final item is required by its own objective rather than granting broad
credit through a `covered_concept_ids` label. A single mission, targeted review
and full route still have different completion scopes; neither access nor
completion establishes mastery. The optional starting check transparently reuses
practice questions and is not an independent alternate assessment bank.

Historical `causality_m0_full.json / 1.1.0` and its traces are retained unchanged.
In that historical pack, integrated and delayed probes credit only
`association-is-not-causation`, and no M1-readiness requirements are configured.
Existing evidence is not migrated or reinterpreted as evidence for the new
Portal `1.2.0` final assessments.
The historical first Damian feedback revision produced `1.3.0` Foundations files and
retains the original `1.2.0` outputs and evidence unchanged. It simplifies
General/Medical entry wording and probability explanations, revises the museum
common-cause example, and repairs completed-route topic review so its challenge
is not skipped. That umbrella view explicitly contrasted 240 retained
intervention records with the 96 original carriers that filtering would retain.
Its result was prewritten teaching content, not calculated from the student's
graph. See the [feedback disposition](../../EducAgent-SDK/docs/expert-review-20261019.md).
This limited feedback does not approve all Medical content or either M1 course;
the proposed intervention-course reorganisation still awaits a concrete outline.

The historical combined Kurt/Damian follow-up selected new `1.4.0` Foundations files,
preserving both `1.2.0` and `1.3.0` evidence. It clarifies all nine topics in
both profiles without changing the curriculum or objective IDs. Variable
questions use concrete lists of recorded variables, not an undefined
"fixed story detail" category. Short definitions/examples are visible by
default, with worked detail available on demand. Feedback remains authored
and scoring remains deterministic; Tutor chat does not award credit.
Earlier M1 `1.0.0` and `1.1.0` packs/traces are retained without migration
into the new `1.2.0` files.
The original `0.1.0` M1 seed files remain available.

## Authored course scope and next review

Organise the learner-facing experience around fixed, reviewed missions while retaining the nine stable concept IDs behind it. A future sequence can move from checking an everyday claim, to designing a useful comparison, to comparing and revising causal explanations, and finally to independent transfer. Difficulty should increase through ambiguity, alternative explanations, missing information, and reduced scaffolding, not simply more terminology.

The earlier repairs revised the rain/umbrella mission and added one worked
General/Medical sample, then nine-topic context integration. S25 introduced new
versioned normal course packs with per-objective final questions and complete
authored M1 teaching routes. General and Medical change the scenario wording
while preserving each module's objectives and evaluation contract. This is
explicit context selection, not inferred expertise or runtime personalised
generation. The rain/umbrella investigation remains a shared neutral case.

`Effect of an intervention` teaches intervention specification, average effects,
confounding/adjustment and identification through its four-topic route. `Robust
prediction or generation` teaches shift, causal/spurious features, scoped
invariance and failure/evaluation criteria, including generation fidelity.
Each retains four explanation pages, topic quizzes/challenges, four practical
stages and four separate final questions. S26 replaces S25's fixed-table practice
with a server-owned deterministic experiment at each practical stage. Learners
commit a typed configuration and unscored prediction, run the model, inspect its
computed result, change settings and rerun, then record a comparison after two
distinct configurations. The existing scored concept check opens afterwards;
the prediction and comparison never award correctness by themselves. Tutor
discussion remains available throughout without a dialogue quota.

S33 applies the same clarity standards to General and Medical M1 material:
short first-read definitions and examples, optional worked detail, plausible
complete answer choices and separate authored guidance after rejection. The
four concepts, objectives, order, 16 activities, answer IDs and experiment
mathematics remain unchanged. Learners use `Save my prediction` and
`Run experiment`, change a setup and run again, compare saved settings with
their results, then explicitly choose `Record my comparison`. Those actions
remain unscored prerequisites to the existing concept check. New files are
`m1_effect_course_{general,medical}_1_2_0.json` and
`m1_shift_course_{general,medical}_1_2_0.json`.

This is an author-led application of the Foundations feedback, not a new
Kurt/Damian scientific review of M1. Damian's proposed intervention-course
reorganisation still awaits a concrete outline. Historical S34 guided Tutor policy
was `1.6.0`, with Tutor `1.14.0`, prompt `1.15.0`, unlimited dialogue and no
chat-based grading or progression. Its public Shift quantity definitions distinguish reference,
measurement, prediction, source fidelity and coverage, and instruct the Tutor
to correct earlier chat that conflicts with those meanings. They expose no
private coefficients or unrun outcomes and add no conversation gate; experiment
results and scoring remain unchanged. Before a scored final submission, the
opening and `Explain this concept` also reuse final-safe concept-only context
instead of the item's accepted explanation. The support button and recorded
support event remain available; evaluator/schema contracts are unchanged.
This closes the identified entry-point bypass, not every possible semantic
answer leak. S32's earlier `1.5.2` evidence retains its historical version.

S34 addresses generated adjustment analogies that silently changed their
common-cause variable. The internal typed `AdjustmentExampleReply` carries
short role labels and a teaching step; a deterministic renderer uses one
common-cause field for its role header, causal premise, grouping and target
weighting clauses. A safe replay-derived latest-example anchor persists beyond
the twelve-message recent context. Ordinary chat and unanswered-final
Explanation share the same safe history. A new example remains permitted when
explicitly announced, and ordinary conceptual text replies remain available.
Instructions keep the active hypothetical example separate from the page's
experiment names, numbers and revealed results. This narrows one consistency
failure, not the correctness of arbitrary prose or every semantic answer leak.
It changes no curriculum, content versions, event schema, evaluator or learner
dialogue quota. Technical and Chrome acceptance for S34 must be recorded
separately after the checks; older evidence does not qualify this new policy.
The [S34 local record](../../output/portal-s34-20261019/verification.md) records
359 offline SDK tests and actual Chrome frozen-runtime dialogue: eleven General
and twelve Medical messages plus Explanation support, without dialogue-count
refusal. Explicit new examples and returns preserved the requested roles, and
the sampled page-result contamination was retested. Some requested Socratic
questions still receive explanation; this is not a qualified Socratic policy.

S35 additionally repairs repeated explicit Explanation, bounded request recovery
and mobile chat/input usability without limiting learner turns. Runtime 0.9.1
retains earlier replay; Tutor 1.15.0 / prompt 1.16.0 / guided policy 1.7.0 add a
narrow preference check for explicit one-question requests, not a general
Socratic or scientific guarantee.

S37 (2026-10-21) removes answer cues found in a Chrome re-check of the expert
feedback. Foundations `1.5.0` rewrites answer-bearing stems, adds a third
plausible option to former two-option topic items, varies answer positions and
uses "Not yet." feedback that does not state the answer; a rejected quiz stays
on its answers. Guided policy 1.8.0 withholds learner-copied current final
wording from the model. Paraphrased requests and close analogies can still
hint at an answer; this is not a semantic non-leakage guarantee. Recorded values
now appear as tables (also in the entry quiz), and pages use one readable column:
scenario, window-capped picture and table first, then the question directly
above the answers; picture and table share one card when a question has both. Long valid role labels use explicit aliases;
public chat shows readable first/new-example details while raw saved text keeps
the role anchor. Static scored submissions still use deterministic local checks.
See the historical [S35 review](../../output/portal-s35-20261019/review.md) for
that slice's findings and scope. S35 preserved the curriculum and then-current
pack versions; S37 introduced the separately versioned Foundations 1.5.0 revision.
Learning and Nirvana received separate storage/request/draft recovery
repairs, with no state transfer or downstream execution.

S36 restores compact Quiz/Challenge illustrations through an exact pack/version
presentation catalog and the existing image-only teaching overlay. Six new
built-in imagegen illustrations match IT records, college support, library
reminders, rehabilitation, parcel imaging and hospital imaging; unsuitable old
scene pictures are not used as a whole-course fallback. The scored packs,
curriculum, versions, evaluator and stored evidence remain unchanged. Directory
checkmarks now describe topic Quiz/Challenge completion separately from final
and full-course credit. Completed topics open temporary review even before a
course ends; returning restores the saved attempt, and new-topic navigation
restores visible canvas focus. The SDK roadmap owns acceptance status.

S38 subsequently completed image coverage for all 68 ordinary Quiz/Challenge
items across the six profiles, adding six neutral context scenes and 17 missing
bindings without changing the then-current 1.5.0 Foundations packs. Current
illustration catalog 1.2.0 retains those historical mappings and adds matching
1.6.0 bindings; it never changes scoring or supplies numerical experiment evidence.

S39 retains the nine concepts, objective IDs, order and 28 activities in new
General/Medical Foundations 1.6.0 packs. Its shared umbrella investigation uses
three declared Boolean structural models: rain causes both umbrella carrying
and wetness; umbrella carrying causes wetness; or wetness causes carrying.
Each includes an explicit generation rule and reproduces the same observational
table. The existing `do(Umbrella carried = yes)` action is computed independently
for the selected learner hypothesis and a fixed reference world. The resulting
wetness is respectively 40%, 100% and 40%, while the reference stays at 40%.
A graph alone is not treated as enough to calculate numerical effects. After
two distinct hypothesis runs, the learner compares the results and represents
the disclosed reference assumptions in the final graph. Agreement with one
intervention does not identify a unique DAG. Predictions, runs and reflection
do not by themselves award correctness. This finite teaching simulator does
not execute learner equations/code or establish real clinical effects.

Runtime 0.10.0 retains earlier replay; guided policy 1.9.0 keeps the selected
hypothesis and recorded results separate from reference assumptions and does
not limit learner dialogue. Tutor 1.15.0 / prompt 1.16.0 remain unchanged.
Dynamic-scene button actions record canonical current-phase feedback directly
through the SDK, without a provider call or generated extra question. Free-text
Tutor conversation remains model-driven. Old recorded automatic questions still
replay unchanged; only new action feedback follows this deterministic path.
Public hypothesis metadata gives each model's root variable and active nodes,
keeping the wet-pavement root of the reverse model distinct from Rain and
making Rain's absence in the direct/reverse models explicit. Tutor requests use
a read-only projection with the latest four runs plus a representative per
distinct tested hypothesis before the 24,000-character context-size check;
the full runtime/API history and replay are unchanged. This is not a learner
run or dialogue quota. Provider-independent tests cover twelve runs and twelve
mock replies per profile and per-model request capture, not live dialogue quality.
Historical 1.5.0 pack bytes and prewritten-result behavior are retained, without
importing their completion into 1.6.0. The SDK roadmap owns current verification
and packaging evidence; historical Chrome results do not qualify this new slice.

Effect experiments distinguish the fixed source cohort, self-selected versus
balanced random assignment, common target weights and pooled versus standardized
analysis. Target weights change the target estimate rather than rewriting the
source cohort. Robustness experiments vary cue reliability, measurement error
and required-context availability, select prediction and report-generation rules,
and expose actual computed source/report pairs, source contradictions,
unsupported additions and withholding/coverage tradeoffs. Source-faithful output
is distinct from agreement with the teaching model's preset reference, which
is not a real clinical review. Outcomes, metrics, cases and
template-generated reports are calculated by the server and recorded in the
trace; the browser renders them. This is neither LLM report generation nor
arbitrary code execution, real clinical data or new scientific review.
Foundations is unchanged by S26.

The following S27 orientation slice adds General/Medical openings for both M1
courses: a motivating question and case, why to learn it, planned learner
actions and a comparison with the other course. Effect concerns changing an
action; Robustness concerns evaluating predictions/reports across specified
changes of setting. A service may need both questions. A content-owned sidecar
catalog keeps these non-scored introductions separate from frozen assessment
packs, so the then-current `1.1.0` traces and scoring remained unchanged. S33's
introduction catalog is version `1.1.0`; its revised openings distinguish an
action's effect from prediction and rule-based report generation under change.
The introduction is still not an assessment or an extra prerequisite. Learners can
reopen the introduction without restarting an attempt. Two original imagegen
illustrations provide fictional context, not evidence or clinical advice.
Implementation and acceptance status remain in the SDK roadmap.
The [S27 acceptance record](../../EducAgent-SDK/output/portal-s27-20261015/verification.md)
documents profile-specific openings, first entry and non-destructive review,
including retained unsubmitted drafts and final responsive/focus checks.

The umbrella graph displays editable permitted arrows, and the later DAG
explanation recalls the same example to name nodes, arrows and directed paths.
The course builders are `EducAgent-SDK/authoring/build_foundation_course.py` and
`EducAgent-SDK/authoring/build_m1_courses.py`; their `--check` modes check derived
pack freshness. Historical M0 inputs and the original M1 seeds remain available. Scientific
review and frozen-build learner evaluation are the next substantive review
steps. The earlier S25 fixed-table checks are recorded in the
[acceptance record](../../EducAgent-SDK/output/portal-s25-20261015/verification.md).
S26 passes provider-independent, web/schema/build and targeted Chrome checks;
see the [S26 acceptance record](../../EducAgent-SDK/output/portal-s26-20261015/verification.md).
The SDK roadmap owns its current status.

Maintain an authoring coverage map that distinguishes concepts encountered, practised, and demonstrated independently. An activity's `covered_concept_ids`, completion flag, or one binary answer cannot supply independent evidence for every listed concept. Hold the tutor mode constant when evaluating a curriculum change so that a simultaneous prompt change does not obscure what helped.

## Sources and release boundary

The declared reference is Peters, Janzing, and Schölkopf's *Elements of Causal Inference* (MIT Press, 2017), licensed under [CC BY-NC-ND 4.0](https://creativecommons.org/licenses/by-nc-nd/4.0/). Project-authored teaching material and synthetic tasks must be distinguished from third-party text and figures. Attribution and a license label are not evidence that any particular adaptation or public use has been cleared.

Keep textbook PDFs, extracted full text, authoring figures, development configuration, and learning traces outside the public asset set. A local source copy is not a learner-facing resource merely because it exists in the workspace. A public release still requires a specific rights review.

The course context variants use independently authored synthetic scenarios and
source-linked explanations. They retain `author_draft` metadata and are not
scientifically approved. Repeated draft-status captions are removed from the
lesson pages while source links and rights remain. Their PNG illustrations were AI-generated as neutral context; the
hypothetical DAG is rendered from authored nodes and edges. Neither is evidence
of a real clinical effect. The asset provenance file is
`EducAgent-SDK/web/public/media/foundation-samples/README.md`.

The repaired umbrella launch serves a public-only `.demo-site/` staging directory. The SDK HTTP handler also checks allowed routes, file types, and resolved paths. The canonical Sources & rights notice is `EducAgent-SDK/web/public/sources.html`, exposed from Learning and Portal. These controls prevent development assets from becoming public web resources; they do not certify that every distributed asset has legal clearance.

## Guided local free-text experiment

The umbrella keeps the legacy `--unguarded-tutor` switch, but it now selects guided local free-text rather than the earlier minimal vanilla prompt. The model receives the current activity, phase-visible authored resources, `scene_text_projection`, the learner's recorded graph/prediction/reflection, the legal next focus, and same-attempt history. The latest message appears once. The full scene and `TutorDeps` are not sent because they also contain future results and assessment answers.

The prompt asks for a concise response to the actual question, permits direct conceptual help, and keeps hidden variables/results and real-world speculation separate from the supplied scene. Ordinary replies remain text; S34's typed adjustment-example output is rendered into the same existing text event. An empty or overlong reply triggers a bounded retry within the existing 1200-character event limit rather than silent truncation. Scored answers, scene actions, progression, and replay still use the SDK runtime and evaluator. This context/instruction repair is not a semantic grounding validator, the old guarded proposal path, or the final production policy.

M1 experiment dialogue receives the same phase-visible snapshot as the browser:
committed settings, unscored predictions, recorded outcomes, recent runs and
reflection. Unrun results, model coefficients and scored answer keys are excluded.
Legacy fixed-table appendices are also excluded from operational-practice
questions, shared grounding and deterministic opening/fallback rendering.
Earlier generated mistakes remain in historical events; they do not become
current numerical evidence.
Experiment actions compute locally without an ELM call; free Tutor messages
remain available in every experiment phase.

The current-concept lecture supplies released context without scoring keys or quiz
feedback. Checked completion evidence survives ordinary follow-up dialogue,
explanation and reload; failed optional discussion can be retried or closed
through a traceable recovery before continuing. Unscored discussion cannot grant
correctness. State/input errors are distinguished from tutor/provider failures.
General and Medical normal routes have separate profile/version progress. A
memory-only developer preview, accessible only through explicit `?preview=1`,
bypasses prerequisites and lets developers inspect
declared activities without writing to normal learning traces. Normal module
browsing is open by default as well; access grants no scored credit. The local content
editor now preserves imported non-form fields and delegates final HTTP
validation to SDK structure/release checks. The GUI edits compiled ContentPacks,
not the raw sample compiler source; its lesson/graph metadata remains preserved
outside the forms. The typed sample graph supports a three-node common-cause
fork, not arbitrary DAG rendering. First entry or selected-profile reset opens
a compact General/Medical chooser; Change profile resumes each independent route. Reset
checks profile/pack/version and clears only the selected trace. The normal UI
does not expose a Testing preview button or require a sample workflow.

S30 changes the normal launcher to anonymous browser-session isolation rather
than a shared learner controller. Each browser cookie selects its own complete
hub, versioned traces and validated module/Profile/diagnostic preferences.
Refresh/restart can resume while the session cookie is retained; other browsers
do not inherit its choices, chat, scores or reset. Same-browser tabs share one
session. This is not account authentication, cross-device sync or recovery after
cookie loss. Historical shared traces remain private and are not auto-imported.
The deployment still requires institutional access control/TLS and one process
per data directory; scientific and production-scale validation remain separate.

The 2026-10-14 first-stage local slice passed 181 provider-independent Python tests, five
Node editor tests and type/build/schema/diff checks. Chrome student checks
received nine General and ten Medical live learner replies, exercised
direct/Socratic help, off-topic redirection, post-answer dialogue and both fresh
challenges, and retried offline Medical input without a duplicate learner event.
The GUI round trip retained the full pack semantically and labelled an exported
non-releasable draft. Preview exit restored the same normal question/attempt and
prerequisite locks. See the [verification record](../../output/portal-goal-20261014/verification.md).
These are historical observations for that earlier slice, not results for the
six S25 packs before S26 replaced the M1 practical implementation.

The historical S25 local technical checks completed in the worktree. The full 230-test
provider-independent Python suite, six Node editor tests, web type/build checks
and schema/generator freshness checks passed. The final content/UI refinements
were followed by 24 focused tests and schema freshness verification. Real Chrome
checks exercised wrong-quiz explanation/retry, challenge continuation, three
consecutive novice Tutor replies and a saved Medical Effect message retry after
the shared-misconception fix, retaining accepted credit. General/Medical M1 quiz
and explanation pages, all four M1 practical views, final-question samples and
the nine-question Foundations final heading were inspected. An ordinary Medical
umbrella route completed and retained the Tutor. Long and empty trace logs both
measured 977.78 by 456.70 CSS pixels with internal scrolling rather than outer
panel growth. Portal and Nirvana health returned 200 at handoff.

These are targeted local acceptance checks, not a Chrome walkthrough of every
activity, a full curriculum qualification, scientific expert approval or a
learning-effect result. The [S25 acceptance record](../../EducAgent-SDK/output/portal-s25-20261015/verification.md)
owns the detailed evidence; the SDK roadmap owns progress status.

S26's repeated full suite passed all 246 provider-independent Python tests in
39.624 s. Six Node editor tests, schema/M1 generator freshness and web type/build
checks also passed. Real Chrome operations exercised a practical sample in each
M1 course/context. General Effect changed the source contrast from -6 percentage
points under self-selection to +15 under random assignment while the common
target contrast remained +15. Medical Effect changed the target high-risk share
from 20% to 80%, moving the target contrast from +12 to +18 percentage points
while the source contrast stayed +15. General robustness reversed a cue and
changed reference accuracy from 90% to 10%. Medical robustness compared fluent
and grounded rules: full-report coverage changed from 100% to 60%, unsupported
additions from 40% to 0%, and reference accuracy remained 70%; reducing measurement
error from 30% to 0% then raised accuracy to 100%.

Medical robustness also received three consecutive live Tutor replies without
stopping the conversation. A wrong concept check was retried successfully, after
which experiment controls froze. These are targeted local acceptance results,
not a walkthrough of every activity, scientific approval or evidence of learning
effectiveness. Report outputs came from the deterministic templates, not live
LLM report generation. See the
[S26 acceptance record](../../EducAgent-SDK/output/portal-s26-20261015/verification.md).

Guided local text is not one of the four frozen SDK v1 study arms and is not
covered by earlier guarded qualification or the original vanilla observations.
S26 uses runtime `0.9.0`, retaining `0.8.x` replay, guided-chat policy `1.3.0`
and guarded prompt `1.13.0`. These changed versions do not inherit an earlier
policy's qualification. Historically, the first-stage guided replies used
`1.0.0` and nine-topic context integration used `1.1.0`; those records retain
their original versions. During a causal scene no lecture is sent because it is
not displayed there; only current-phase scene data and profile/version metadata
are supplied. Historical General full and delayed packs remain `1.1.0`;
pre-repair packs and their original traces remain private historical material.
The local and S47 deployed Portal select Foundations `1.8.0`, Effect `1.4.0` and Shift `1.4.0`,
with separate versioned progress. S41 remains a frozen rollback release using
M1 `1.2.0`; the SDK roadmap and GCP handover record installed-target acceptance.
Foundations 1.7.0 replaces only the World/data/model Challenge with paired
data/world identification in General and Medical, retaining the model Quiz and
the nine-concept curriculum. Earlier 1.6.0 packs and records remain frozen;
their credit is not migrated. Back up the browser-session directory before
version changes because diagnostic selections are stored in selection.json.
This follow-up is included in S46 RC1, deployed on 27 October 2026.
The revision also shows small example-record tables for both
profiles' Data and assumptions Quiz and Challenge, with the proposed cause
outside the measured columns. Their existing option IDs, accepted answers and
completion contracts are unchanged; a measured association does not establish
the team's causal explanation.
S46 retains this table support while revising redundant Challenges to another
facet within the same topic and teaching it in the default definition/hook.
Pairs that already test distinct facets remain intact. Quizzes, final checks,
interactive models and curriculum are unchanged; old 1.7.0/1.3.0 packs and
progress remain separate. The S46 RC1 deployment retained the actual S44 image and a private
whole-Portal backup, along with the existing Caddy/TLS configuration, Secure
cookies and data volume. The SDK roadmap and
[S46 remote acceptance record](../../output/gcp-s46-20261027/verification.md)
separate local coverage from targeted remote API, Chrome and live-model checks.
This is not another full six-course walkthrough or a new expert qualification.

S47 is now activated with Tutor `1.15.1`. Its phase-correct practice opening
uses the released prediction guide before the scored check becomes available,
without changing content versions, calculations, credit or unlimited dialogue.
Local ordinary Medical Effect Chrome verified the new opening; manifest,
configuration and full localhost/public checks passed on GCP. The actual S46
image and a new whole-Portal backup are retained, with the same Caddy/TLS,
Secure-cookie setting and data volume. Actual GCP Chrome completed each Medical
course's 16 activities, including four two-configuration practices, four finals,
completion and separate final trace review in each course. Exit/reload retained saved practice
artifacts; completed-final review retained course credit; 390px inner scrolling
and fictional multi-turn Tutor checks passed. General received targeted profile
isolation, restored practice and a fresh pre-run opening check, not a full S47
walkthrough. The [S47 record](../../output/gcp-s47-20261027/verification.md)
records the exact coverage. This is technical acceptance, not renewed scientific
approval or evidence of learning effectiveness.

Earlier 2026-09-05 vanilla testing completed the scene but revealed the rain/common-cause explanation early and introduced umbrella-dripping possibilities outside it. The subsequent guided prompt's first iteration still named rain as a hypothesis; that was revised before the final five live probes using the existing `gpt-5.6-luna` configuration.

The final probes produced 48, 58, 20, 53, and 74 words: they did not name hidden rain before intervention, defined confounding neutrally, gave a concrete next action, marked dripping as absent from the exercise, and compared the revealed result with the prediction while separating supplied assumptions from graph identification. All five retained `can_continue=False`. Final real Chrome checks also gave neutral help for an incorrect causal idea and a confounding-definition request without revealing hidden rain or granting advance/credit. The final SDK rerun passed 152 tests in 6.557 s; TypeScript checks and the launch build passed. The 4173 demo restarted without resetting user progress. These targeted improvements do not establish general no-leakage guarantees, a new qualification, or learning effectiveness.

## Relationship to Nirvana

Portal begins with authored learning activities. Nirvana begins with the researcher's own problem and builds an editable Causal Research Brief. A person may use either route directly; Portal is not a prerequisite for Nirvana, and no answer, profile, or hidden session context transfers automatically.

The public navigation is:

```text
Learning Resources
├─ Books
├─ Online courses
└─ Practical resources
EducAgent Portal -> /portal/
Causal Research Framing -> /nirvana/
```

## Evidence and data boundary

The local implementation proves that the selected Portal can be built, served, and connected to ELM. It does not prove usability, learning, comparative value, CHAI adoption, or mastery.

Before a public or research release:

1. freeze the exact Portal build and experimental tutor mode being evaluated;
2. complete the existing SDK S11 study decision and approved participant route;
3. observe causal novices using the route with keyboard, mobile, and ordinary dialogue;
4. review the adequacy of the immediate/delayed assessment, then freeze tasks, rubrics, exposure rules, and analysis before measuring transfer; the authored objective-specific questions and completion records do not establish validated mastery or delayed transfer;
5. compare guarded, guided-local, or a separately restored/versioned vanilla baseline only if the exact comparison answers a real product decision.

Free-text dialogue and research records require explicit governance before collection outside this local demo. The current local JSONL trace is development state, not an approved learner-data store.
