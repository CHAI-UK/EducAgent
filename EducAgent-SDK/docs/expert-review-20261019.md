# Kurt and Damian feedback disposition

Review date: 2026-10-19. This is an implementation disposition, not scientific
approval of the full curriculum. All four supplied Word files are unchanged.
Damian's three files contain body-text suggestions and screenshots, not native
Word comments or tracked revisions. Kurt's quiz document contains 61 native
comments; its extracted evidence is in `../../output/kurt-review-20261019/`.
Damian's extracted evidence is in
`../../output/expert-review-20261019/`.

## Scope and disposition

| Feedback | Implementation |
| --- | --- |
| General and Medical entry questions are difficult to read | Rewrite the nine practice questions reused by the optional entry quiz; use complete, question-matching answer options. Keep objective IDs, answer IDs and evaluator truth unchanged. |
| Resting heart "could be" a variable | Use "Could resting heart rate be a variable?"; retain the full feature name rather than the review's apparent omission of "rate". |
| Shorter submission and success copy | Use "Submit" and "Continue when you're ready." for ordinary classification feedback. |
| Entry result does not explain the learner's choices clearly | Use "Choose where to begin", explain selected-topic review versus the full course, and treat all-correct results separately without claiming mastery. |
| Explanation skips the challenge after entry quiz | Repair temporary topic review to contain the authored quiz and challenge, not only the first quiz. Exclude the module final and preserve normal saved progress. |
| Repeated "fictional" is unnecessary | Remove the repeated adjective from current Foundations learner copy. Retain teaching-model provenance, Sources & rights and the distinction between a hypothetical effect and real clinical evidence. |
| Museum common-cause example is ambiguous | Use donations and cafe sales as the observed variables, with visitor numbers as the proposed shared explanation. Do not present this as an identified causal graph. |
| Probabilistic-effect explanation is too technical | Use a plainly hypothetical treatment example, explain changed chances versus guarantees, and use a digital-service tutorial in the General challenge. |
| Final association answer is too categorical | Use "These records suggest that attendance and score may be associated" and distinguish the observed group means from population-wide or causal claims. |
| "Arrivals" and the umbrella what-if are unclear | Define one record as a campus arrival; show totals and explicitly distinguish keeping 240 records under an assigned carrying value from filtering 96 original carriers. |

The S31 Foundations outputs are newly versioned `1.3.0` files. Historical
`1.2.0` course outputs, the `1.1.0` full pack and the original profile compiler
source remain unchanged. Old traces are not migrated to the revised questions;
their different content version must remain visible during any later analysis.
At S31 the two M1 courses kept their structure and assessment packs; the later
author-led wording revision is recorded under S33 below.

## Scientifically careful adaptations

Two suggestions are implemented for clarity but not copied literally:

- Mentioning a treatment and an outcome is not enough to make a question causal.
  The correct answer says the question asks what **changing the dose would do**
  to recovery.
- A drawn arrow represents a **proposed causal relationship**. The drawing
  does not establish that the relationship is true.

The probabilistic example says "Suppose" rather than turning an assumed effect
into an observational or clinical finding. These changes preserve the review's
plain-language intent without weakening the taught distinctions.

## Umbrella discrepancy to clarify with the reviewer

The inspected screenshot and current authored records are numerically
consistent with setting carrying, not with filtering:

| Comparison | Retained records | Wet records | Wet proportion |
| --- | ---: | ---: | ---: |
| Original observations | 240 | 96 | 40% |
| Filter original observations to umbrella=yes | 96 | 96 | 100% |
| Supplied intervention result, carrying=yes for everyone | 240 | 96 | 40% |

The 144 originally dry, non-carrying arrivals remain in the intervention
table and are now marked as carrying. Nevertheless, the runtime reveals a
**prewritten teaching-model result**, not a structural causal calculation
from the learner's graph. The revised copy states both facts explicitly.
It does not claim that this test uniquely identifies Rain -> Umbrella and
Rain -> Wet, or that handing someone an umbrella guarantees they carry it.

Please confirm whether the reviewer intended to request a genuinely
graph-driven simulator. That is a separate practical-module redesign, not
something that should be claimed as fixed by wording alone. Also confirm
whether arrival events are an appropriate beginner unit; changing them to
independent days would require a coordinated scenario/model revision.

## Still awaiting expert input

1. The screenshot proposes major reorganisation of *Effect of an intervention*
   but supplies no replacement outline. Request the intended objective order,
   missing concepts, replacement cases and assessment expectations before
   restructuring it.
2. The submitted documents cover both entry quizzes and the General basic
   course, not a complete Medical learning-route or M1 scientific review.
   Apply shared clarity fixes but do not label those other routes reviewed.
3. All learner-facing text still needs a complete editorial/scientific pass
   before publication on the main CHAI website. Demo usability, software
   tests and an implemented wording suggestion are not that approval.

## Verification

Implementation and acceptance status are recorded in the S31 entry of
`roadmap.md`. Default tests and the browser fixture use offline models;
this revision does not authorize a new live ELM test or remote deployment.
Previously produced deployment archives remain unchanged. A fresh,
credential-free `output/educagent-server-20261019.tar.gz` contains the reviewed
local build; use the server's existing ELM configuration when installing it.
Changing the local registry or building this archive does not update an
installed server.

## S32 combined learner-experience revision

The S32 normal Foundations release is 1.4.0 for both contexts. It preserves
the nine concepts, objective order and existing activity IDs. It retains all
1.2.0 and 1.3.0 files rather than reinterpreting their answers. The current
revision helper is `authoring/foundation_learner_revision.py`.

Native comment IDs refer to `output/kurt-review-20261019/comments.json`, not
renumbered prose suggestions from Damian's documents.

| Kurt comment IDs | Disposition |
| --- | --- |
| 0-2, 5-16, 18-21, 23-33, 35-38, 41-48, 50-58 | Implemented in the new content/shared UI. In particular 32 uses "Everyone carries an umbrella" and 47 displays "Causal graphs" while retaining its stable concept ID. |
| 3 | Four complete variable-list alternatives use the existing single-choice contract instead of introducing multi-select; setting identity is scoped to the particular table. |
| 4 | Use Damian's shorter "Submit" rather than requiring a literal "Submit my answer". |
| 17, 49 | Bold the compact first-read definition rather than individually styling every new term. |
| 22 | Retain the scientific limitation that a possible common cause does not prove the absence of another effect; the fuller explanation remains available on demand. |
| 34 | Permit keeping the learner's arrows, but require an explanation of the comparison; do not invent a claim that the original unscored prediction was correct. |
| 39 | Use a short definition, example and optional detail rather than a strict one-paragraph page; a necessary graph remains visible. |
| 40 | Tutor invitation and placement improved and multi-turn help sampled; whether learners notice/use it still requires real learner observation. |
| 59-60 | Final-phase help and sampled over-disclosure defects repaired and retested, with unlimited conversation. Semantic answer leakage and learning behavior remain expert-sampling questions, not a claim of complete prevention. |

| Combined concern | Disposition |
| --- | --- |
| Wrong responses were unclear or silently opened an explanation | Project the current attempt's evaluator-selected consequence as inline feedback. Show the selected option, rejection and a retry action; do not award credit or advance on rejection. |
| Variable/value questions used the unexplained category "fixed story detail" | Ask which list contains the table's recorded variables, contrasting feature names with values and setting labels. General uses an IT-service table; Medical uses clinical fields. A clinic can be a variable in a different study that records clinic identity. |
| Answer options rely on terminology or grammatical clues | Use question-matching, complete statements in both profiles; retain the existing deterministic choice contract. |
| Too much text before a simple idea | Show a short definition and example by default. Keep detailed worked steps, pitfalls, takeaways and citations in an optional disclosure. Bold the first-read definition. |
| Data, causal question, intervention, model and assumption were unclear | Define them in ordinary language and distinguish measured values from a proposed generating explanation, actively setting a value from selecting existing records, and a causal question from a group comparison. |
| DAG jargon and paths need introduction | Begin with a causal graph; define directed/acyclic, path and directed path explicitly. Revisit the umbrella assumptions as a model, not a graph proven by its records. |
| Population variation was confused with stochastic mechanisms | Test changed chances versus individual guarantees; explicitly avoid inferring deterministic/random mechanisms from heterogeneous outcomes. |
| Scene hierarchy, duplicate questions and opaque controls | Remove phase jargon, duplicate mission copy and fake single-table switching. Keep one initial question; distinguish discussion from viewing data. Use a human-readable intervention action. |
| Correct initial reasoning should not require an artificial revision | Offer an editable "Keep my explanation" starter; require the learner's reason and explicit submission. It does not change arrows, score the prose or claim the initial prediction was correct. |
| Park illustration anatomy | Use a versioned imagegen correction of the cream-shirt woman's arms. Preserve the old image for old content; retain the exact edit prompt in asset provenance. |
| Tutor should help without giving away an unanswered final | Keep ordinary explanations and unlimited dialogue. Derive the final phase from authored server metadata; before submission provide concepts or another example, after submission explain recorded feedback. Chat never grades or advances. |

The Tutor's narrow private output check detects normalized complete answer
copies and some explicit short-label selections. It does not establish
semantic non-leakage: paraphrases, option letters, numerical answers and
multilingual/indirect hints still require live and expert sampling. No
per-learner turn quota has been added. An answer-copy retry limit concerns one
model generation only and recovers to visible conceptual help, not a learner
conversation limit.

The final live follow-up found that refusing to select an option was not enough:
the Tutor then mapped the concept directly onto the current question. Policy
1.5.2 now withholds that stem/table until submission, retains conceptual help
with another case, and excludes older-policy Tutor replies from that phase's
model history. A separate scene-only check covers unrevealed authored variable
labels. Both fixes were retested with the same requests; their narrow lexical
and semantic limitations remain documented, not presented as a complete
anti-cheating guarantee.

The supplied umbrella outcome remains prewritten teaching-model content; it
is not a graph-driven simulator. The 240-versus-96 distinction is retained.
M1 curriculum restructuring remains pending the expert's concrete outline;
no claim of complete Medical/M1 scientific approval is made.

S32 acceptance evidence, Chrome coverage and the newly named deployment
archive are recorded in `../../output/portal-s32-20261019/verification.md`.
The user explicitly authorized real ELM dialogue tests for this follow-up;
default regressions remain provider-independent. No installed remote service
is changed by producing the archive.

## S33 author-led M1 clarity revision

The clarity standards from the Foundations feedback now inform the General
and Medical versions of both M1 courses. This is not a claim that Kurt or
Damian reviewed or approved the new M1 wording. Damian's proposed major
reorganisation of *Effect of an intervention* is not implemented; a concrete
replacement outline is still needed before changing the curriculum.

The four normal packs use version `1.2.0` in new
`m1_effect_course_{general,medical}_1_2_0.json` and
`m1_shift_course_{general,medical}_1_2_0.json` files. Each retains its four
concepts, objectives, order and 16 activities: eight topic quiz/challenge
items, four interactive experiment stages and four final questions. Activity
and answer IDs, correctness, evaluator contracts, initial configurations and
experiment mathematics are unchanged. The old `1.1.0` files and traces remain
available for historical replay, without automatic migration or regrading.
The separate introduction catalog is `1.1.0`; it explains why the routes
differ and distinguishes prediction from rule-based report generation.

| Clarity concern | Author revision |
| --- | --- |
| Terminology arrives before an accessible idea | Use a short definition and concrete example by default; retain worked steps, assumptions, pitfalls and sources in optional detail. Define the terms when first introduced. |
| Correct answers are obvious from wording or length | Use complete question-matching choices with plausible conceptual confusions; do not make the correct option uniformly longest. |
| Wrong-answer feedback repeats the full answer | Provide separate authored rejection guidance and a retry, rather than copying the accepted explanation. Rejection never grants scored credit. |
| Practice feels like a passive table exercise | State which parameter to change, save a prediction, run two distinct configurations, compare settings and results, then explicitly record the comparison before the scored check. |

The visible practice actions are `Save my prediction`, `Run experiment`,
`Save my next prediction` and `Record my comparison`. Predictions and
reflections remain unscored. Effect copy distinguishes pooled/standardized
comparisons, target weights, percentage points, individual versus average
effects and the assumptions needed for causal interpretation. Robustness
copy does not present a causal feature or a stable relation as a reliability
guarantee or causal proof. Its reference labels are preset teaching-model
values, not clinical expert reviews; content inputs are noisy measurements,
and reference-group error rates do not directly test an outcome-given-features
relationship. Source fidelity does not establish independent factual truth;
withholding reports changes coverage rather than validating missing facts.

Guided Tutor policy is `1.5.4` for the S33 follow-up, with unlimited learner
dialogue. Public quantity definitions in the Shift Tutor context distinguish
the preset reference target from the noisy recorded measurement, prediction,
source text, source fidelity and coverage. The instructions require correcting
earlier chat that conflicts with those definitions rather than carrying its
mistakes forward as evidence. This is terminology grounding, not a new
conversation gate or turn quota; private model coefficients and unrun results
remain excluded. Historical dialogue and experiment numbers are unchanged.
The follow-up also routes unsubmitted final-assessment openings and
`Explain this concept` through the same final-safe concept-only context as
ordinary dialogue. These entries no longer render the current item's accepted
explanation before submission. The button and `SupportRequested` event remain;
the support event may carry the existing `tutor_reply` field without a schema
or evaluator change. Useful conceptual explanations remain available. This
repairs the identified alternate entry point, not every possible semantic
answer leak, and adds no conversation quota. Historical S32 `1.5.2` evidence
keeps its original version.
Chat does not grade, advance or alter the experiment model. Scientific review,
learning-effect evaluation and Damian's curriculum-outline decision remain
separate outstanding work. S33 browser/test evidence is recorded separately
after the actual checks; this disposition does not predeclare their results.

The planned follow-up deployment artifact is the new credential-free
`output/educagent-server-20261019-s33-r3.tar.gz`. Retain
`output/educagent-server-20261019-s33-r2.tar.gz`, the original
`output/educagent-server-20261019-s33.tar.gz` and their checksums rather than
overwriting them. Keep all earlier archives,
the server's private ELM configuration and the existing Portal data volume;
neither packaging nor a local registry change updates the installed server.

## S37 answer-cue follow-up (2026-10-21)

A Chrome re-check of the current Portal against both reviews found that three
concerns had been only partly resolved. This revision applies the existing
standards; it is not a new expert review or approval.

| Concern | Disposition |
| --- | --- |
| Kurt 59-60: copying a final into chat still yields the answer | The live Tutor refused to choose but then classified the three distractors. For an unanswered final, learner-copied stem/option wording is now withheld from the model's message and same-attempt history (guided policy 1.8.0). Paraphrased or retyped options remain outside this lexical boundary. |
| Kurt 44/57: retry after a wrong answer has no friction | A rejected quiz now stays on its answers instead of opening the Explanation, and the single retry action remains. Rejection feedback and final hints nudge toward the distinction ("Not yet. ...") instead of stating the answer. Former two-option topic items have a third plausible misconception, so one rejection no longer reveals the answer by elimination. |
| Kurt 20 / Damian's quiz notes: stems and layout reveal answers | Observation/intervention stems no longer say the team did not change anything; association items require reading values and include a causal over-reading; world/data/model avoids repeating "explanation"; data-versus-assumption challenges use different options; probability distractors use the common "some failures mean no effect" confusion instead of contradicting the stem. Correct-answer display positions vary across quiz, challenge, entry quiz and final. |

Damian's Q2 suggestion is applied in substance: the observed-association item
now contrasts the recorded pattern with a causal reading, while still testing
the direction of the association. The revised 1.5.0 packs keep option IDs and
their correctness; saved 1.4.0 progress remains on disk but is not shown or
regraded under 1.5.0.

A presentation follow-up applies Kurt 53 ("minimal header, a question text,
extra info if necessary") to the same items. Values formerly written into stems
appear in small tables, also in the entry quiz. The question sentence is the
heading and its scenario is body text. Entry-quiz and course questions share one
heading size. Pages use one reading column of about 70-80 characters per line.
The scenario is the page title, followed by a wide picture capped to the window
height and any table; the question sits last in bold, directly above the answers. Where a
question also has recorded values, picture and table share one card so the
answers stay on screen at 100% zoom. Supporting text is 14px.
