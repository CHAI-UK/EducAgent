# EducAgent-SDK Roadmap

- **Status:** S47-based November report/context/definition hotfixes are deployed (guided policy 1.9.4); S48 General walkthrough and numerical Tutor repair remain in progress; expert content review and learning evaluation remain pending
- **Last updated:** 2026-10-27
- **Last completed technical step:** S47 phase-correct practice opening, preserved GCP deployment and full Medical Effect/Shift Chrome acceptance, 2026-10-27
- **Active step:** S48 General Effect/Shift practice/final/trace acceptance, numerical-reply repair and preserved S48 deployment
- **Next step:** obtain the intervention-course replacement outline, complete expert review of all course text, then freeze a build for learner evaluation. Learner-depth adaptation and runtime personalised generation remain separate.
- **Implementation details:** [`implementation.md`](implementation.md)
- **Product guideline:** [`goal.md`](goal.md)

## 1. Status rules

| Status | Meaning |
| --- | --- |
| `DONE` | every checklist item and exit condition passed, with recorded evidence |
| `DONE IN WORKTREE` | implemented and tested locally but not yet committed/reproduced |
| `IN PROGRESS` | the only step currently being closed |
| `NEXT` | begins after the active step passes its exit gate |
| `LATER` | ordered but deliberately not started |
| `BLOCKED` | cannot proceed without a named decision or external change |

Only this file records current progress. Design completion in another document does not make an implementation step complete.

Update rules:

1. keep at most one step `IN PROGRESS`;
2. check an item only after its implementation and test evidence exist;
3. record the commit evidence and relevant environment for a completed step; a checkpoint may identify itself as the commit containing its roadmap snapshot;
4. never describe uncommitted work as published;
5. add newly discovered work to the relevant step instead of silently widening the active step;
6. change the goal or step order only through an explicit design decision recorded here.

## 2. Current snapshot

### S48 General walkthrough and numerical Tutor reply repair - IN PROGRESS

Markdown quotation follow-up (2026-11-06): verified definition replies now use
CommonMark blockquotes and labelled publisher links. The existing ReactMarkdown
renderer styles blockquotes with the shared palette and wraps long text. A
presentation-only adapter also formats the saved plain-text verified replies,
without changing stored events. Raw HTML and remote Markdown images are omitted;
learner messages remain plain text. See `../../output/markdown-quote-fix-20261106.md`
for tests and deployment acceptance. Definition scope and S48 status are unchanged.
Type/build, 41 UI tests and 493 offline Python tests passed. The new GCP image
verified 197 manifest files and all public routes. Actual Chrome displayed a
semantic blockquote and clickable publisher link without horizontal transcript
overflow at the checked desktop width. Existing data and rollback were preserved.

Definition quotation follow-up (2026-11-06, guided policy 1.9.4): explicit
association/dependence/independence and correlation definition requests use
verified textbook excerpts with book, section and printed page, followed by a
separately labelled explanation. The deterministic reply does not inspect quiz
options, invoke a provider, grade or advance. Source verification, exact scope,
tests and deployment acceptance are tracked in
`../../output/definition-quote-fix-20261106.md`. Other definitions still use the
existing guided path; this is not arbitrary textbook retrieval. S48 remains open.
All 493 offline Python tests passed; the exact overlay passed three focused
tests. GCP activation, 198 manifest hashes, full public route checks and actual
Chrome display of the association quotation/source/page passed. The previous
image and stopped-state whole-Portal backup are retained. No live ELM call was
made for this deterministic definition acceptance.

Topic-context follow-up (2026-11-06, guided policy 1.9.3): unanswered/rejected
ordinary lessons now project `topic_before_answer`, omit the full lecture,
worked graph, takeaway and fallback concept explanation, and omit pre-fix Tutor
history from the model input without rewriting stored events. Why/how/help turns
request one question; their validator rejects an explanatory sentence before it.
Explicit definition/example requests retain concept-help instructions. Scene,
experiment and final-check projections retain their separate boundaries.
All 491 existing offline Python tests passed in 85.562 seconds; the two focused
lesson-context checks also passed, including the newly added sales-question
regression. Candidate deployment extends the actual report-hotfix image, keeping
pending local S48 numerical changes out of the release. No live ELM test is claimed.
The actual server now runs policy 1.9.3, verified inside the installed module;
198 bundle hashes and all three health endpoints passed. The previous image and
stopped-state Portal backup are retained. See `../../output/topic-context-fix-20261106.md`.

Report hotfix (2026-11-06): the Learning entry hides both Nirvana links;
lesson topics use a heading with the Quiz/Explanation/Challenge sequence below;
authored definitions use a blockquote with visible adapted-source attribution.
The guided reply instructions now elicit one missing inference before supplying
an unanswered Quiz/Challenge mechanism, including the two-sales common-cause
example. Explicit definitions and requested learning explanations remain available;
final-assessment boundaries remain unchanged. This prompt change is not a
guarantee of semantic non-disclosure. Type checking, web build and 40 Portal UI
tests passed; complete Python checks and actual deployment are recorded separately.
The deployed report hotfix is derived from frozen S47 and changes only the shared
reply introduction and public Learning/Portal assets, preserving pending S48 work.
All 491 offline Python tests passed. The actual GCP container was healthy, verified
198 bundle files, and loaded the revised installed Tutor prompt. Public health
checks and Chrome Learning/topic-layout checks passed; existing chat was retained.
No live ELM dialogue was tested. See `../../output/report-hotfix-20261106.md`.

The user authorised a full ordinary Chrome walkthrough of both General M1
courses. A live Tutor reply described a change from 90% to 50% as `half as many`.
It corrected that wording after the learner's fourth turn to a decrease of
40 percentage points, about 44.4% relative to the original 90%. That later correction
does not repair the original reply or establish that numerical paraphrases are
reliable; retain the recorded conversation and repair the guidance separately.

The planned narrow repair strengthens numerical instructions in the shared
guided reply policy: distinguish absolute percentage-point changes from
relative percentage changes, state the baseline and avoid unsupported ratio
phrases. Target guided policy `1.9.1`, preserving recognition of earlier final-
safe history, including `1.9.0`. Keep curriculum, content versions, authored
numbers, experiment mathematics, evaluator authority and unlimited dialogue
unchanged. Do not rewrite old replies or introduce an arithmetic claim validator
under the description of a prompt repair.

- [x] Record the observed numerical paraphrase error and later correction.
- [ ] Complete General Effect and Shift topic items, operational practices, finals, completion and separate final traces in actual GCP Chrome.
- [ ] Implement the minimal numerical instruction and guided-policy/history compatibility changes with focused provider-independent checks.
- [ ] Pass full offline regressions and verify fresh post-repair fictional numerical replies, reporting finite observed results separately from guarantees.
- [ ] Freeze/audit a new immutable S48 bundle, retain the actual S47 image, take a new stopped-state whole-Portal backup and preserve private configuration, Caddy/TLS, Secure cookies and the named volume.
- [ ] Activate and verify S48 on GCP, including saved General/Medical state and the requested targeted live/browser checks.

S47 remains installed. No S48 completion, archive or image/deployment result is
claimed here. Current General browser evidence is collected under
`output/gcp-s47-general-20261027/`; the subsequent
[S48 acceptance record](../../output/gcp-s48-20261027/verification.md)
will distinguish the S47 walkthrough from post-repair/S48 acceptance. The S47
Medical completion below remains historical evidence, not a full S48 rewalk or
new scientific approval.

### S47 Phase-correct guided-practice openings and Medical acceptance - DONE IN WORKTREE; deployed 2026-10-27

The user authorised fixing the premature practice opening and completing the
Medical Effect and Shift operational practices, finals and traces in GCP Chrome.
The automatic orientation had reused the scored interpretation prompt before
the learner ran the tests, producing past-tense claims such as `You compared...`.
Tutor dependencies now use the released prediction guide before the check is
available and restore the scored prompt after the required recorded comparison.
Eligible automatic openings reuse that authored question with explicit
`.authored-experiment-orientation` provenance, without a model request. Ordinary
Tutor messages remain available without a dialogue quota.

Only `tutor.py` and focused experiment-guidance tests change runtime behaviour.
Legacy unguided activities and old saved dialogue remain unchanged. Content
bytes/versions, curriculum, mathematics, evaluator truth, gates and progress
contracts are preserved. The current six packs and four registry/catalog/
diagnostic JSON files remain byte-identical to S46.

- [x] Repair pre-check question projection and automatic opening provenance.
- [x] Verify all current guided practices open before results without a model call, restore the scored prompt after comparison, and retain replay/legacy behaviour.
- [x] Pass 487 provider-independent SDK tests (169.771 seconds), 79 frontend tests, six deployment tests (32.815 seconds), TypeScript and production build.
- [x] Verify the corrected fresh practice opening in ordinary local Medical Effect Chrome after all eight topic items.
- [x] Freeze/audit `educagent-server-20261027-s47`, preserve actual S46 image and current whole-Portal state/TLS, then activate and pass basic target checks.
- [x] Complete the requested Medical Effect and Shift practices, finals, completion and trace flow in actual GCP Chrome with authorised fictional Tutor dialogue.

S47 is activated. Its immutable archive is 136,474,214 bytes, SHA-256
`6df3ceeda059b1f1a7315560443756c4036b1b9a19659facee2950fe9289513a`.
Independent package audit found only three changes from S46: `tutor.py`,
the deployment guide and MANIFEST. All content and other runtime/assets remain
unchanged. Actual new image:
`sha256:13886af4e2e08889b97fa0681b2ab3c684bd13928107555fa7d297e8b4eede97`.
Actual S46 image
`sha256:7512a7ae6430e83ef5b24fea2e66b386f4ed62b4edb6afa76421875bec34ead7`
is retained as `educagent-review-educagent:s46-pre-s47-20261027T110432Z`.
The new stopped-state whole-Portal backup, including browser selections, is
under `/srv/educagent/backups/pre-s47-20261027T110432Z`.

VM build/preflight, all 190 manifest files and full localhost/public checks
passed. Actual Tutor version is `1.15.1`. Caddy identity/configuration,
loopback-only 9090, private configuration, the named volume and Secure-cookie
setting are preserved. The frozen archive retains its build-time candidate
guide; these later workspace status updates do not alter that archive.

Actual GCP Chrome completed all 16 activities in each Medical course: eight
topic items, four operational practice checks and four final questions.
All eight practices recorded two distinct configurations, predictions,
computed runs and comparisons before the correct interpretation. A tested
practice retained both runs, prediction and comparison after exit and reload.
Both completed finals allowed first-item review/re-answer and returned to
the course with all 16 completions and the final checkmark intact after reload.
The four final answers and a fictional marker appeared in the separate final
trace section, absent from the first topic. Desktop logs scrolled internally;
the 390px mobile page had no horizontal overflow and its inner log scrolled
with an actual wheel action. Three consecutive fictional Tutor turns in each
course, plus generation/final support, received replies without a turn quota.

General received targeted checks: Shift remained independently unstarted;
Effect restored its saved first practice, then a fresh second-practice attempt
showed the corrected prediction opening before any run. Returning to Medical
preserved both completed courses. General was not rewalked end to end in S47;
earlier broader/targeted evidence remains in the S46 and historical records.
See the [S47 acceptance record](../../output/gcp-s47-20261027/verification.md)
for exact browser and live-model scope. This completes the requested technical
acceptance, not renewed causal-expert approval or evidence of learning effect.

### S45 Consistent entry actions and current learner copy - DONE IN WORKTREE; included in S46 RC1 deployment

The user requested one shared style for the three Foundations entry actions,
installation and application of Humanizer, and deployment after validation.
At S45's start, S44 had changed the umbrella Learning entry only; the SDK
implementation baseline was S43. Use existing Button components and review the current six course
packs and public UI without changing curriculum, scoring or Tutor behaviour.

- [x] Install/read Humanizer 3.1.0 and scope it to current user-visible prose.
- [x] Unify the three entry buttons while preserving handlers and disabled state.
- [x] Review Learning, Portal and Nirvana copy, including both course profiles.
- [x] Pass complete offline checks, builder freshness and current/historical invariants.
- [x] Verify local Chrome buttons, copy and responsive rendering without resetting progress.
- [x] Deliver the changes in a new immutable S46 RC1 release, preserve GCP data/TLS/rollback and test remotely; the frozen S45 archive itself was not deployed.

26 October local follow-up: the user requested actual question-level Humanizer
editing after a screenshot showed a stem that the earlier general copy review
had retained. Review every current activity in both profiles, including entry
diagnostic reuse, question/option/hint/feedback copy and practice instructions.
Record changed and retained items individually; keep all numerical facts,
assessment truth/IDs/order, source metadata, curriculum and model rules intact.

- [x] Complete and record all 120 current activity reviews, including both diagnostic projections.
- [x] Pass exact prose-only/numeric/protected-byte checks and complete SDK regression.
- [x] Refresh and inspect local Chrome representative question/option samples in both profiles.

Follow-up acceptance: 105 stems and 52 of 374 reviewed options rewritten,
453 changed prose fields across the six current packs. Fifteen retained stems
have item-level reasons. All 451 SDK Python tests (129.884 seconds), 71 frontend
Node checks, TypeScript, production build and both builders passed. Exact
comparison with frozen S45 preserved non-prose/numeric fields and all 58 captured
protected file hashes. Actual Chrome verified the existing Medical Variables
practice, General's shared diagnostic wording and a 390px layout without reset
or a new ELM call. This is representative browser rendering, not all-activity
Chrome traversal. See the [question acceptance record](../../output/portal-question-humanizer-20261026/verification.md)
and its per-item reviews and exact before/after differences. The local service
was safely refreshed; versions and unlimited dialogue remain unchanged.

Local presentation follow-up (26 October): move optional explanation and
sources beside the main lesson article when enough canvas width is available,
stack it below on narrow canvases, retain the Tutor panel and use `Go to the
challenge` for initial/review reading. Source content, scoring and callbacks
remain unchanged. All 71 frontend tests, TypeScript, production build and 451
SDK tests (114.140 seconds) passed. Actual Chrome verified side-by-side reading
and sources with the Tutor retained, keyboard expansion, automatic stacking at
1280px/390px without horizontal overflow, and the new button label. The viewport
override was cleared; the existing completed-topic review preserved course
credit. No live ELM, reset or deployment occurred. See the
[layout acceptance record](../../output/portal-explanation-layout-20261026/verification.md).

Treatment question follow-up (26 October): replace the answer-like scenario
heading in both profiles with a short review context and ask the specific
intervention/outcome question below the image. The General item explicitly
retains offering extra study sessions; Medical retains a dose change and
recovery. Choices, truth, curriculum and historical files are unchanged. Local
validation and the refreshed-page evidence are recorded in the
[title acceptance record](../../output/portal-treatment-title-20261026/verification.md).

Data/world follow-up (26 October): the user requested a Challenge about data
and the world, since both current items identified a model. Keep the existing
model Quiz and replace only `world-data-model.transfer` in General and Medical.
New Foundations 1.7.0 packs give the changed assessment new option IDs and four
independent support resources; all other activities, concept requirements and
dynamic Umbrella calculations remain unchanged. This is an explicitly requested
semantic assessment revision, not part of the earlier prose-only claim.
Registry and illustration catalog 1.5.0 select 1.7.0; older 1.6.0 pack bytes and
image bindings remain frozen. Credit is separate, with no migration or reset.
Existing local browser-session directories were backed up privately before
service refresh, including diagnostic selections that are not stored by version.
See the [new Challenge acceptance record](../../output/portal-world-data-challenge-20261026/verification.md)
for final tests and browser scope. No package or GCP release is included.

Acceptance: 456 SDK tests passed (121.726 seconds), followed by all 38
Foundations checks after final scenario shortening; 15 illustration/registry
checks, 71 frontend checks, TypeScript, production build and six deployment
tests passed. Actual Chrome verified both new profiles, both wrong alternatives,
continued retry after two mistakes, correct scoring and final shortened copy
through a provider-disabled in-memory QA server. Normal 4173 Chrome entry
retained Medical preference and began the new version separately. No live Tutor
request was made. The temporary server was stopped; the normal services remain
available. This is local technical acceptance, not a published release or renewed
expert review.

Assumptions-table follow-up (26 October): the user asked to see the actual data
behind the Data and assumptions questions. Add small authored record tables to
the Quiz and Challenge in both profiles, using the existing question workbench
and its image/table layout. The two measured columns exclude the proposed common
cause; row units and time windows are explicit. Keep the existing answer IDs,
verdicts and curriculum. This is presentation support for the unpublished local
1.7.0 draft, not another changed assessment construct. Capture before snapshots,
retain all frozen 1.6.0 bytes, and record final regression and browser evidence in
the [table acceptance record](../../output/portal-assumptions-data-20261026/verification.md).
No provider request, reset, package or GCP release is part of this follow-up.

Acceptance: all 459 SDK tests passed (130.227 seconds), as did all 71 frontend
checks, TypeScript, content freshness, exact scope and historical hashes.
Chrome verified each of the four tables and correct submissions, plus Medical
wrong-answer retries. At 390px the table had no page-level horizontal overflow;
the viewport override was cleared. The temporary provider-disabled QA server
was stopped and the normal local service refreshed without Reset; the production
build passed in 14.01 seconds and Chrome confirmed the normal entrance with its
retained Medical preference. See the table
acceptance record for screenshots and precise test scope. This remains local.

This follow-up supersedes the earlier local acceptance for question wording.
The S45 archive below remains immutable and does not include these later edits;
it must not be described or deployed as the final question revision. The user
is inspecting locally; no retry of the blocked upload is part of this follow-up.

Uncommitted Windows worktree: all 450 SDK Python tests, 71 Portal frontend
checks, final TypeScript/build, both content builders, ten Nirvana/Learning Node
checks, 16 Nirvana Python tests and six deployment tests passed. Actual Chrome
checked both profiles' introductions, equal Foundations button styling and a
390px Medical entry without overflow or a progress reset. No live ELM was used.

The immutable credential-free S45 archive is 136,467,380 bytes, SHA-256
`862319832316ac409a2af00974ea9597508291f304f373cbe77d29644f3c22a0`.
Independent audit verified all 190 manifest hashes / 191 regular members and
unchanged runtime/evaluator/model, numerical and answer-truth contracts. The
Cloud Shell upload gate declined permission before any file upload; do not retry
through another surface. No S45 production mutation or data backup occurred.
The user chose to inspect the local version first. Upload permission, deployment
and actual remote checks remain outstanding; S45 is not a published release.

Retain existing versions for editorial-only current-pack maintenance; do not
rewrite historical packs, source quotations or recorded conversations. Keep
scientifically necessary contrasts, numerical conditions, hypotheses, assumptions
and uncertainty. This editorial review is not renewed expert approval, an
equivalent-assessment study claim or a guarantee against AI-style prose in
future generated Tutor replies. No live ELM test is authorised in S45.

### S46 Complementary topic Challenges and visible teaching - DONE IN WORKTREE; deployed with targeted acceptance 2026-10-27

The user requested a different facet for each topic's Challenge, explicitly
taught in Explanation, with Humanizer paraphrasing. This changes local work
priority after S45's local acceptance. At initial local acceptance, S45's remote
release was separately blocked by the upload gate and the user's local-review
preference. The user later authorised the S46 RC1 deployment on 27 October;
the separate dated acceptance below records that target-server work.

Audit all 17 topic pairs in General and Medical. Keep genuinely complementary
pairs and record why. Change repeated classification/calculation tasks to a
different application of the same objective. Required teaching must appear in
the default definition or hook, not only the collapsed worked steps. Keep
scenarios short, choices plausible and explanations independent of the exact
Challenge answer. Apply Humanizer without weakening scientific distinctions.

- [x] Record Quiz/Explanation/Challenge facet maps for all three courses.
- [x] Build separately versioned Foundations 1.8.0 and M1 1.4.0 packs with old bytes retained.
- [x] Preserve quizzes, curriculum, final assessments, interactive practices and unlimited chat.
- [x] Pass full offline checks, builder freshness, all changed choices and exact scope invariants.
- [x] Check representative explanations and challenges in Chrome for both profiles.
- [x] Refresh local services without resetting records; record the local acceptance boundary.

The pre-edit six-pack snapshots and historical hashes are in
`output/portal-complementary-challenges-20261026/`. Old completion is retained
with its matching version and is not migrated to these changed teaching routes.
No live ELM request is authorised for this authoring change.

Acceptance: 34 topic pairs audited, 14 Challenges revised and 20 already
complementary items retained. Final full SDK regression passed 476 tests in
132.641 seconds under Python 3.13.15; 71 frontend checks, TypeScript, six
deployment tests and independent six-profile scope/evaluator/history audit
passed. Chrome checked default explanations and unanswered Challenge returns,
correct submissions in all six representative profile/course cases, and Medical
mistake/retry cases. Two lesson headings were aligned after browser review and
included in the final regression. The production build passed in 17.54 seconds;
normal Chrome entry retained Medical preference after the safe restart. The
private pre-S46 browser backup remains; no Reset, live ELM or deployment occurred.
This is an uncommitted/untracked Windows worktree, not a published commit or new
expert qualification. See the [acceptance record](../../output/portal-complementary-challenges-20261026/verification.md)
and per-track facet maps for precise scope, retained reasons and screenshots.

Graph presentation follow-up: the user requested the Causal graphs Quiz and
Challenge diagrams above their scenario illustration. The shared QuestionPrompt
now draws only linear chains already disclosed as backtick-marked public text,
with horizontal/vertical layouts and accessible arrow endpoints. The exact
four General/Medical ordinary questions and the entry diagnostic reuse share
this view; public final-item chains also benefit. Unsupported chains keep their
text. Content pack bytes, versions, curriculum, evaluator and progress are
unchanged. Local checks and actual Chrome evidence are recorded in the
[graph acceptance record](../../output/portal-causal-graph-20261026/verification.md).

Graph acceptance: 476 SDK tests passed in 142.289 seconds; 73 frontend checks,
TypeScript and production build (12.18 seconds) passed. Chrome verified all four
ordinary profile/stage cases, correct grading and Medical wrong-answer retry.
The 390px Medical graph retained 16px labels without horizontal overflow; wide
view placed it above the image. Viewport overrides were cleared. The normal
service was safely refreshed without Reset, and temporary QA was stopped.
No content/version/credit migration, provider request or deployment occurred.

Final check navigation/transition follow-up: all three courses now place Final
check after their topics, with a separate header, selection and evidence-derived
completion marker. A first unanswered final question has a Congratulations
transition after completed topic practice, or neutral readiness text for early
navigation. Begin changes only the presentation; existing answers and later
questions resume directly. Completed finals use isolated review. Desktop topic
tools reveal the selected final row without moving the mobile page.

Acceptance: 482 offline SDK tests passed in 124.271 seconds; 77 frontend checks,
TypeScript and the production build (6.67 seconds) passed. Chrome checked all
six course/profile final headings and navigation, the saved Medical Foundations
question 3 review/resume path, wrong/correct final completion, completed-final
review, both-profile Congratulations and 390px layout. The local services were
refreshed without Reset. Content versions, curriculum and dialogue quotas were
unchanged; there was no live ELM request, package or deployment. See the
[Final check acceptance record](../../output/portal-final-check-navigation-20261026/verification.md).

Trace grouping follow-up: Review my trace now lists Final check after the
ordinary topics and groups final messages by pack-owned activity IDs, excluding
them from earlier lesson transcripts. Existing records are projected without
rewriting events or grades. Latest-final selection and module/profile/version
selection isolation are covered. Acceptance: 484 offline SDK tests passed in
106.368 seconds; 79 frontend checks, TypeScript and production build (6.67
seconds) passed. Chrome verified all six course/profile traces, topic/final
separation, profile changes and the user's actual completed 28-activity Medical
Foundations record. Local services were refreshed without Reset; no live model
request, package or deployment occurred. See the
[trace acceptance record](../../output/portal-final-check-trace-20261026/verification.md).

S46 release-readiness follow-up: the user requested a final feasibility review,
not a cloud update. Independent review found and fixed invisible Tutor replies
on the first-final transition; learner-requested dialogue now remains visible
without revealing the question, starting it or limiting turns. The outdated
deployment guide was aligned with the current six versioned packs.

The immutable credential-free `educagent-server-20261026-s46-rc1.tar.gz`
is 136,473,320 bytes, SHA-256
`b32222590ebfa49ef99ab12f682e76e8136df6ca1003f465d8cfd3aa62ee50c9`.
All 190 hashes / 191 regular members and canonical/generated source contracts
passed independent audit and extracted verification. Fresh checks: 484 SDK
tests (115.114 seconds), 79 Portal frontend, 16 Nirvana Python, 10 Nirvana/Learning
frontend and six deployment tests; TypeScript, fresh build and real Linux Nginx
mock-API/static-boundary preflight passed. Chrome verified transition Send/Explain
in General desktop and Medical 390px. Read-only HTTPS entries and health still
show the S43/S44 baseline. No upload, deployment or live ELM occurred; actual
GCP image/configuration, preserved state/TLS and live integration acceptance
remain pending. See the [readiness report](../../output/release-readiness-20261026/README.md).

27 October authorised GCP deployment: the same immutable S46 RC1 archive was
transferred, its SHA-256 and all 190 manifest files verified, and the complete
application image replaced behind the existing Caddy HTTPS service. The actual
new image is `sha256:7512a7ae6430e83ef5b24fea2e66b386f4ed62b4edb6afa76421875bec34ead7`;
the actual former S44 image
`sha256:5367d97b20f2f914bbf6a171dfee4ead7c6765e96394c2e54166b5518da3a00e`
is retained for rollback. A stopped-state whole-Portal copy and verified private
archive, including browser selections, were retained under
`/srv/educagent/backups/pre-s46-20261027T093503Z` before replacement.

The new container is healthy. Full in-container localhost checks passed; six
public HTTPS routes returned 200 and HTTP redirected with 308. Caddy identity
and configuration hashes, loopback-only 9090, private ELM configuration, the
named data volume and Secure session-cookie setting are preserved. The
acceptance helper checked all six current pack/profile versions and normal
final navigation, repeat-request/reload restoration and zero completion credit.
Actual Chrome checked Learning's theme switch, Medical Foundations' three
live fictional Tutor messages and Quiz -> Explanation -> Challenge completion,
visible Send/Explain replies before starting the final check, a 390px layout
without overflow and separate General profile progress. Nirvana's real framing,
field-proposal acceptance and route UI also passed. General Effect's four topic
pairs completed normally; its first practice computed -6 pp for pooled weighting
and +15 pp for common-target weighting. Predictions, the recorded comparison
and dialogue survived practice exit/re-entry, profile/module changes and reload.
Three real General Tutor turns used the same programme variables and results,
distinguished percentage points from individual benefit, and retained causal
assumptions. Both profiles' M1 introductions used the appropriate stories and
shared layout. A nonblocking follow-up remains: Effect practice 1's automatic
opening uses the past-tense interpretation prompt before the tests have run.
This is targeted remote technical acceptance, not another complete
six-course walkthrough, renewed causal-expert approval or learning-effect
evidence. See the [S46 remote acceptance record](../../output/gcp-s46-20261027/verification.md).

### S43 Effect guidance and expert-feedback follow-up - DONE IN WORKTREE, deployed 2026-10-22

User authority (2026-10-22) extends the S42 presentation approach to Effect in
General and Medical, fixes remaining story/copy drift, and authorises packaging,
GCP deployment and fictional live Tutor testing locally and remotely. Preserve
the curriculum, deterministic mathematics, evaluator authority, historical pack
bytes and unlimited learner dialogue. Reuse the existing guide projection and
stable App draft owner rather than adding a second workflow.

- [x] Repair remaining Umbrella action wording and General Variables story drift.
- [x] Add story-first, single-control Effect practices in both profiles.
- [x] Preserve scoped unsaved drafts across responsive reparenting and exit/resume.
- [x] Pass contract/content/replay/frontend/schema/build and complete offline checks.
- [x] Verify local Chrome student practices and live Tutor dialogue in both profiles.
- [x] Verify a new immutable package, deploy with rollback/data preservation, and test GCP in Chrome.

Only saved runtime artifacts survive full reload; unsaved presentation drafts
remain memory-only. Existing deployment credentials and learner data must be
retained. Technical acceptance does not replace causal-expert approval.

Uncommitted Windows worktree, Python 3.13.15: all 448 provider-independent SDK
tests, 70 frontend Node tests, TypeScript, schema/builder freshness and production
build pass. Nirvana's 16 Python and seven Node tests and six deployment tests
also pass. Actual local Chrome completed all 16 Effect activities per profile,
all eight two-run practices, four final items per profile, responsive draft
retention, exit/resume and reload restoration. Six explicit fictional learner
messages used live ELM locally, three consecutive turns per profile.

The immutable credential-free S43 archive is 136,467,409 bytes, SHA-256
`e3e4ca7325eaef8113b2db28522f3bd73603fc0572f88e3dab12eead4a212888`.
Independent verification passed all 190 manifest hashes / 191 regular members;
Cloud Shell and VM checksums and deployed integrity checks passed. S43 includes
the separately accepted S42 Shift revision; S42 has no standalone archive.

The existing GCP HTTPS front door now serves S43, retaining Caddy, its current
loopback-only 9090 override, Secure/HttpOnly session flags, private configuration,
the named data volume and the prior image. A private pre-upgrade data backup is
available. Actual remote Chrome preserved a pre-upgrade Foundations answer and
completed each Effect profile's eight topic items and first two-run practice,
scored interpretation, reload and three consecutive live Tutor messages per
profile. Remote scope is targeted, not another complete 16-activity walkthrough.
Medical responsive/exit draft checks, both Shift introductions, Medical Shift
first-quiz context, Learning and Nirvana entry checks also passed. No normal
progress reset or Testing preview was used. Historical M1 version progress is
not migrated; the same-version Foundations copy correction preserves its credit.
See [S43 acceptance](../../output/portal-s43-20261022/verification.md) and the
[GCP recovery record](../../output/gcp-deploy-20261022/README.md).

### S42 Local DG novice scaffolding - DONE IN WORKTREE, 2026-10-22

Apply Kurt's DG teaching feedback to General and Medical without deleting
interactive practice or changing the four-concept curriculum. Keep the existing
experiment engine and evaluator authority. Version revised Shift content
separately; preserve historical content and progress. Teach prediction before
the clearly separated report-generation stage. Authored story, purpose and one
relevant control guide prediction, run, comparison and interpretation; an
explicit exit returns to the course introduction without awarding credit.

- [x] Add content-owned guided-practice metadata and phase-visible projection.
- [x] Revise both Shift profiles with concrete stories and consistent short wording.
- [x] Implement staged practice, clear exit/resume and accessible compact results.
- [x] Pass content invariants, replay/runtime, frontend, schema/type/build and full offline checks.
- [x] Verify both normal local Chrome student routes, refresh, exit/resume and narrow layouts.

Uncommitted Windows worktree, Python 3.13.15: all 441 provider-independent SDK
tests, all 64 frontend Node tests, TypeScript, schema freshness, current M1
builder freshness and production build pass. Actual Chrome completed each
profile's full 16-activity route, all eight interactive practices with two
distinct configurations each, and ten explicitly authorised fictional learner
messages through the existing live ELM configuration (five per profile).
The normal route now presents prediction practices before generation teaching;
the four concepts, objectives, answer IDs/truth and experiment mathematics
remain unchanged. Historical 1.2.0 packs are preserved; local Shift is 1.3.0.

Chrome defects fixed include repeated wording, misleading final-report evidence,
heading hierarchy and responsive draft loss. Draft and introduction visibility
now belong to stable App state, with scope/revision isolation and full remount
regressions. Actual 1366/390-width checks confirmed no horizontal overflow,
retained draft/settings/step, retained reflection after exit/re-entry, and an
introduction that stays open across breakpoints. Saved results survive reload;
unsaved drafts remain intentionally memory-only. No progress reset or Testing
preview was used. See the [local acceptance record](../../output/portal-s42-20261022/verification.md).

Local-only user authority: do not build a deployment archive, upload or modify
the GCP service until the user separately approves. Tutor dialogue remains
unlimited. Live ELM testing requires explicit confirmation; default checks are
provider-independent. This work is not renewed expert approval of the content.

### S41 Aligned entry-course actions - DONE IN WORKTREE, 2026-10-22

Replace wrapping ghost actions in the shared entry sidebar with a flexible
title column and a fixed intrinsic action column, using existing Grid and
secondary Button components. Preserve all course/profile routing, busy/locked
semantics, curriculum, Tutor behavior and learning records.

- [x] Repair shared layout and add regression coverage for both profiles/all modules.
- [x] Pass frontend/type/build and full provider-independent SDK checks.
- [x] Verify actual Chrome layouts, course navigation and focus.
- [x] Produce/verify a new immutable archive and update GCP while retaining S40/data.

Uncommitted Windows worktree: all 49 frontend Node tests, TypeScript/production
build and all 426 provider-independent SDK tests pass. The credential-free
`../../output/educagent-server-20261022-s41.tar.gz` is 136,455,874 bytes, SHA-256
`d82bfaf04709ea8e9807ec8261fb218f9652d33c8d9b32150f44e156a44dd421`.
Independent verification passed all 190 manifest files / 191 regular archive
members. Only Portal entry/JS, release documentation and manifest differ from
S40; curriculum, runtime/Tutor/evaluator, Nirvana and images are byte-identical.

Actual public-HTTP Chrome verification covered all three entry routes in both
profiles, visible secondary actions, aligned right edges, click and keyboard
navigation. Desktop widths 1366 and 1100 had no row overflow; the 390-wide
mobile layout had no horizontal page overflow and retained module navigation.
General Foundations was restored and the user's original tab refreshed. No
progress reset, Testing preview or ELM request was performed for S41.

The GCP demo now runs S41 with a healthy container; all integrity, route, asset,
health and blocked-private-path checks pass. S40/S39 images and archives,
private configuration (mode 600) and the named Portal data volume are retained.
See the [GCP handover and visual evidence](../../output/gcp-deploy-20261022/README.md).
This visual repair does not add TLS, authentication or scientific approval.

### S40 Public-HTTP request ID compatibility - DONE IN WORKTREE, 2026-10-22

The user-authorised public GCP HTTP test exposed a browser capability mismatch:
`crypto.randomUUID()` is unavailable outside a secure context, so profile
submission failed before `fetch` while localhost testing worked. Preserve
native UUID generation where available; the fallback uses secure random bytes
with UUIDv4 version/variant bits and the same request prefix. No dependency,
server-validation, curriculum, runtime, grading or Tutor-policy change is intended.

- [x] Add native/fallback UUID and actual HTTP-like profile submission regressions.
- [x] Pass focused/frontend/type and provider-independent SDK checks.
- [x] Build and independently verify a new immutable artifact, preserving S39.
- [x] Verify profile submission and normal dialogue in actual public-HTTP Chrome.

Uncommitted Windows worktree: 28 focused Portal UI tests, all 47 frontend Node
tests, TypeScript/production build, diff check and all 426 provider-independent
SDK tests pass. New credential-free archive
`../../output/educagent-server-20261022-s40.tar.gz` is 136,457,002 bytes, SHA-256
`6c48f0dbb173b90b2480dff48861f628077e1d3a89b6a56fe1fd824247ba4016`.
Independent comparison verified all 190 manifest files / 191 regular tar
members; only release README, Portal entry/JS and manifest differ from S39.
Six packs, Python runtime/Tutor/evaluator, Nirvana and images are unchanged.

The user-authorised GCP Ubuntu 26.04.1 Minimal Docker deployment at
`http://35.214.18.98/` now runs S40 on host 80. Config/HTTP/blocked-path checks
pass and the non-root container is healthy. Actual Chrome completed public
HTTP profile submission, a real fictional Tutor question, correct quiz/Explanation,
refresh recovery, both profiles' M1 entries and return to saved General progress.
Nirvana's fictional classification/Brief was verified before the frontend-only
upgrade; its unchanged code and S40 routing/health were independently checked.
The original S39 archive, image and Portal volume are retained. A restrictive
extraction umask was caught by preflight; only the new release's program
permissions were normalised, with credentials still 600. See the
[GCP handover and limitations](../../output/gcp-deploy-20261022/README.md).
This test does not provide TLS, login, abuse protection, a concurrency/reboot
qualification, full expert review or scientific approval.

### S39 Dynamic Umbrella hypothesis/reference practice - DONE IN WORKTREE, 2026-10-21

The user authorised a bounded dynamic investigation in both Foundations
profiles, without changing the nine-concept curriculum or evaluator authority.

- [x] Declare three finite executable hypotheses and a separately fixed reference world.
- [x] Add server-owned computations, immutable run history and replay-safe actions.
- [x] Version Foundations as 1.6.0, preserving older files and objective/answer truth.
- [x] Add shared General/Medical prediction/run/compare/reconstruction UI.
- [x] Complete offline regression, schema and frontend checks.
- [x] Walk the normal student flow in actual Chrome in both profiles.
- [x] Update the deployment guide and generate/verify a new 9090 review archive.

Uncommitted Windows worktree, Python 3.13.15: 426 SDK tests and 44 Portal Node
tests pass, as do schema/authoring freshness, type/build and diff checks. Actual
Chrome used normal progress in both profiles, three hypotheses each, live Tutor
dialogue, General graph rejection/retry and both completion checkmarks; the
390px layout and saved-request recovery were also inspected. Follow-ups repair
long-run context growth, per-model root mixing and stale generated action
questions. Dynamic button feedback is now canonical SDK output; free chat is
still model-driven and unlimited. An upstream ModelHTTPError temporarily
interrupted Medical's fifth question; later retry succeeded without duplicate
input or lost completion. Safe upstream-status diagnostics were added, but the
original old-format error's numeric status is unknown. Evidence and final SDK
log: `../../output/portal-s39-release-20261021/verification.md` and
`sdk-tests-final.log`; Chrome proof: `../../output/portal-s39-20261021/`.

Credential-free release: `../../output/educagent-server-20261021-s39.tar.gz`,
136,455,899 bytes, SHA-256
`b848f1155ba1d2a552ca45d15e959e74204d43c7eb0f7a020726c96d4e514323`.
Independent verification passed all 190 manifest files / 191 regular tar members,
current canonical runtime/content/public assets, 9090 entry and exclusions.
All 11 older archives and 11 checksum files remain unchanged. Nirvana's 16
Python / 7 Node tests and six deployment tests also pass. Local services remain
running; Docker, IT HTTPS/SSO and live integration on the Linux server still
require target-environment verification. No remote deployment or commit made.

### S38 Missing Quiz/Challenge illustration coverage - DONE IN WORKTREE, 2026-10-21

- [x] Audit the six currently registered profile packs after image overlays.
- [x] Reuse matching existing art and generate neutral missing scenario assets with built-in imagegen.
- [x] Bind exact activity IDs without modifying scored packs, progression or saved records.
- [x] Verify asset coverage, offline regressions, build and representative Chrome layouts.
- [x] Record asset prompts, output paths, coverage and remaining exclusions.

Catalog 1.1.0 adds 17 activity bindings using six new built-in imagegen assets
and suitable existing consultation, rehabilitation and sleep-recording art.
All 68 ordinary Quiz/Challenge activities in the six registered profiles now
have explicit images. Both integrated Foundations transfer challenges are
included; binding validation accepts exact existing activities while continuing
to reject staged scenes, experiments and capstone assessments. Scored packs,
IDs, text, evaluator and historical versions are unchanged.

Windows, Python 3.13.15: 398 SDK tests passed in 114.187 s; 35 Portal Node tests,
TypeScript check and production build passed. Actual Chrome on the normal
127.0.0.1 session verified General document-transfer Challenge, Medical lab and
app-record Quiz, and Medical operation/infection Challenge artwork. The app
Quiz was also inspected at 390x844 without horizontal overflow; viewport was
restored. No progress was reset. Medical Foundations was started during normal
navigation; completed-topic checks used temporary review, not Testing preview.
At 1920x855, a picture-plus-table review Challenge still needs about 123 px
of vertical scrolling to reach Submit; this visual-only step keeps the current
layout. Prompts and asset provenance are in `web/public/media/question-context/README.md`.
Evidence: `../output/portal-s38-20261021/verification.md`. No commit, deployment
archive or remote update was produced during that illustration step.

Packaging follow-up (2026-10-21): the requested credential-free port-9090 review
archive is `output/educagent-server-20261021-s38.tar.gz` (136,441,440 bytes),
SHA-256 `4223a88bf14ee30900b256617b135df92134b43a62e64a9b15a93652fe6cab83`.
The guide now names the current versions and explicitly separates 1.4.0 from
1.5.0 progress, preserving private configuration and the Compose volume.
Fresh checks: 398 SDK tests in 115.954 s, 35 Portal Node tests, 16 Nirvana Python
tests, seven Nirvana/Learning Node tests, type/build and six deployment checks
passed. Independent verification matched all 189 manifest entries and current
canonical runtime/content/public/provenance sources, and retained all ten prior
archives/checksums. Evidence: `../output/portal-s38-release-20261021/verification.md`.
No target-server deployment, service restart, new Chrome/live ELM test or
scientific approval is claimed. Umbrella dynamic computation was assessed only;
its existing scene behavior is unchanged in this package.

### S37 Assessment answer cues and final-check copy withholding - DONE IN WORKTREE, 2026-10-21

A Chrome re-check against the Kurt/Damian feedback found three remaining leaks:
the Tutor eliminated pasted final-check options, a rejected quiz opened an
Explanation whose feedback stated the answer, and stems, distractors or fixed
display positions revealed answers. Keep curriculum, activity/option IDs and
their correctness, evaluator authority and unlimited dialogue unchanged.

- [x] Revise Foundations as new 1.5.0 packs; freeze 1.4.0 by checksum.
- [x] Keep rejected quizzes on their answers with one retry and opt-in Explanation.
- [x] Withhold learner-copied unanswered-final wording from the guided model.
- [x] Add offline content, UI and request-capture regressions; pass full suites.
- [x] Verify in Chrome on a separate localhost browser session; record limits.
- [x] Move stem values into tables (entry quiz too); unify question headings, use one reading column (scenario and picture first, question above the answers) and raise small text.

`foundation_assessment_revision.py` rewrites answer-bearing stems, adds a third
plausible misconception to former two-option topic items (new option IDs only),
varies displayed answer positions against the existing runtime reversal, and
uses "Not yet." feedback/final hints that do not state the answer. Guided policy
is 1.8.0; Tutor/prompt stay 1.15.0 / 1.16.0. Saved 1.4.0 progress stays on disk
but is not shown under 1.5.0, as with earlier version changes.

Windows, Python 3.13.15: 395 SDK tests passed in 89.859 s; 31 Portal Node
tests, TypeScript check and production build passed. Actual Chrome (Medical,
fresh 1.5.0 localhost session; General entry questions sampled) verified the
entry quiz, rejected/accepted quiz and challenge flows, rewritten association
and intervention items, the final rejection nudge and two authorised live
fictional Tutor probes. A pasted final with options received concept help with
no option choice or elimination. A paraphrased yes/no request was refused but
answered with a closely analogous example, so semantic analogy leakage remains
an expert/model-evaluation limit. No deployment archive, commit or remote
update was produced; the user's 127.0.0.1 session was not reset or used.

The presentation follow-up was folded into the unreleased 1.5.0 packs. Final
checks: 396 SDK tests passed in 123.882 s (including pack freshness), 33 Portal
Node tests, TypeScript check and the production build. A two-column trial was
replaced at the user's request by one 68ch reading column. A fold audit at
1920x911 (100% zoom, visible canvas to y=894) then found answers or Submit below
the fold on most question pages (Submit at about 1400 on picture-plus-table
pages). The follow-up uses a one-line topic header, a 2:1 picture capped at
70vh wide (at most 35vh tall), a picture-plus-table scenario card and tighter
option/section spacing. Re-measured Submit/Continue positions: association quiz
844 (was 1370), Variables challenge with four options 875 (was 1402),
picture-only quizzes 823-855 (were 994-1106), picture Explanation 828 (was 1015),
table challenge 876 and final Q2 887. A completed-topic review page with four
options still overflows by 47 px because of its extra review row; the entry
quiz was not re-measured because both test profiles had finished it. A 390 px
same-origin iframe (responsive viewport, not device emulation) showed the card
stacked as picture, context and table, with wrapped headers and no horizontal
overflow. Node tests: 33 passed, with TypeScript check and production build.
Later user-requested tweaks removed the tinted box around "Correct", removed the
page-wide focus ring on load (focus still moves for assistive technology),
and put material first: the scenario as the page title, picture/card and table,
then the question in bold (19px medium) directly above the answers. Causal-graph
chains (e.g. `Tutorial → Continued use → Renewed subscription`) are now marked in
the content and shown as highlighted inline code; the full suite then passed with
398 SDK tests and 36 Node tests. After these,
Treatment, World/data/model, Probabilistic and Variables still fit (855-883), but
items with a long scenario and two-line options scroll by 7-77 px (Causal graphs
challenge 7, Observation challenge 25, Observed association challenge 40, Data and
assumptions quiz 77). The user chose to keep the larger picture and accept this
short scroll on long items (2026-10-21). With the scenario as the 28px title,
Treatment still fits (867); the Variables challenge scrolls by 25 px and the Data
and assumptions quiz, with a four-line title, by 101 px. Node tests: 35 passed.

### S36 Question visuals and topic navigation/status - DONE IN WORKTREE, 2026-10-19

Investigate missing question imagery, ineffective topic jumps and completed
topic rows that still read pending. Keep authored curriculum, deterministic
grading, historical content versions and normal saved progress intact.

- [x] Reproduce navigation/completion mismatches and repair their authoritative owners.
- [x] Restore relevant existing images and generate neutral new context art with built-in imagegen where needed.
- [x] Separate visible topic-route completion from final/whole-course evidence without granting new credit.
- [x] Run offline regressions and Chrome General/Medical navigation, image and completion checks.
- [x] Record final asset prompts/paths and verification; preserve previous archives.

Six new built-in imagegen assets use exact presentation bindings, leaving all
six scored packs byte-identical to S35. Completed topics now open temporary
review without rewriting formal JSONL; topic Quiz/Challenge checkmarks remain
separate from final/full-course credit. New-topic navigation restores canvas
focus, including the checked 390-pixel mobile viewport. Normal saved progress
was retained without reset. Final Python 3.13.15 regression: 392 passed in
77.030 s; 30 Node tests, TypeScript/build and six deployment checks passed.
Chrome sampled all six module/profile combinations and two live fictional Tutor
messages per profile. See the [S36 acceptance record](../../output/portal-s36-20261019/verification.md).
The new port-9090 archive is `output/educagent-server-20261019-s36.tar.gz`,
SHA-256 `6109b6d6b3f043e39371751924ef9ec1ce74da6d0083465b4ecbd2d6b65dc904`;
it excludes credentials and retains all nine previous archives/checksums.
No commit or target-server/Docker/scientific qualification is claimed.

### S35 Code and learner-experience alignment - DONE IN WORKTREE, 2026-10-19

Review the current Portal as a learner and trace concrete mismatches back to
their code owners. Also inspect shared Learning/Nirvana navigation, session and
deployment boundaries. Fix reproducible issues with the smallest coherent
shared change; do not replace the curriculum, add a dialogue quota, rewrite old
records, reset saved progress, or claim scientific/public-release qualification.

- [x] Audit Tutor intent, example continuity, support semantics and failure recovery.
- [x] Audit ordinary General/Medical flows, responsive/accessibility behaviour and drafts.
- [x] Audit shared entry, Nirvana state/recovery and deployment boundaries.
- [x] Add provider-independent regressions, complete relevant suites, and verify fixes in Chrome.
- [x] Record findings, remaining limits and a fresh verified 9090 archive after freezing.

Repairs cover repeat Explanation, same-session timeout recovery, generated-role
length/identity and readable display, explicit one-question preference, later
Shift reference scope, cross-profile/full-course status projection, mobile chat,
drafts and IME input, Nirvana request/budget/retry boundaries and storage-tolerant
Learning themes. Runtime 0.9.1 preserves earlier replay; Tutor/prompt/guided
policy are 1.15.0 / 1.16.0 / 1.7.0. Curriculum, content versions, evaluator truth,
ordinary progress and unlimited learner discussion are unchanged.

Windows/Python 3.13.15: 377 SDK tests (95.516 s), 25 Portal Node tests, 16 Nirvana
Python tests, 7 Nirvana Node tests and 6 frozen deployment tests passed, plus
web check/build, syntax, generator freshness and diff checks. Actual Chrome
sampled all six module/profile routes, live fictional student dialogue, two
two-configuration practical checks, trace geometry, profile/draft recovery and
390x844 keyboard/mobile layout. This is targeted acceptance, not a new full
walkthrough of every scored activity or scientific/Socratic qualification.

New credential-free archive `educagent-server-20261019-s35.tar.gz`: 85,220,981 bytes,
SHA-256 `d659da2cf31dac130fe9a3d57cfe4c97758a4cf797a03aa112055a6fb09a2c5e`.
All 162 manifest hashes / 163 regular members and source/privacy/history checks
passed. Entry remains 9090. No remote deployment, reset, commit or new dependency.
See [review and residual limits](../../output/portal-s35-20261019/review.md) and
[archive evidence](../../output/portal-s35-20261019/bundle-verification.json).

### S34 Tutor worked-example consistency - DONE IN WORKTREE, 2026-10-19

Fix the sampled plant-type/soil-type substitution in generated adjustment
analogies. Preserve curriculum, evaluator, experiment truth and unlimited learner
dialogue. Use an internal typed role/step reply rendered from one role assignment,
shared safe chat/Explanation history, and a replay-derived example anchor beyond
the short context window. Ordinary conceptual text remains available; do not
claim this is a semantic guarantee for arbitrary model prose or real-world cases.

- [x] Verify role rendering, explicit example changes, safe history and replay offline.
- [x] Pass complete regression suites and actual Chrome General/Medical live dialogue.
- [x] Freeze and verify a new 9090 deployment archive; preserve previous archives.

Local verification: Windows, Python 3.13.15; 359 SDK tests (including twelve new
example regressions), 12 Portal Node tests, 5 Nirvana Node tests, 14 Nirvana Python
tests and 6 deployment tests passed, together with web check/build, M1 freshness
and diff checks. Actual Chrome frozen-runtime dialogue used eleven General and
twelve Medical learner messages plus Explanation support, with no question-count
refusal or request failure. Sampled role substitutions, page-result contamination
and switching/return issues were retested successfully. One Medical request for
a small question still received explanation; Socratic consistency and arbitrary
free-text scientific correctness are not qualified by this step. Evidence:
`../../output/portal-s34-20261019/verification.md`. No reset, commit or remote
deployment was performed.

New credential-free archive: `educagent-server-20261019-s34.tar.gz`, 85,218,002
bytes, SHA-256 `4f471c06a694a23445f1ea8b2e38929b9a5e330da8cec74399e6844f18580445`.
All 162 manifest file hashes and 163 regular tar members (including manifest)
passed, together with path/public-asset/privacy checks, all six expected profiles,
current runtime source hashes and preservation of prior archives. Frozen deployment
tests passed 6/6 in 20.814 seconds. Entry remains 9090. The package contains no
live credentials, learning traces, PDFs or test artifacts. The server's existing
ELM configuration/data volume must be retained during installation. Detailed
archive evidence: `../../output/portal-s34-20261019/bundle-verification.json`.

### S33 M1 clarity under the existing curriculum - DONE IN WORKTREE, 2026-10-19

Apply the already supplied Kurt/Damian clarity and feedback standards to Effect
of an intervention and Robust prediction or generation, in General and Medical.
This is an inferred editorial application, not a claim the experts reviewed or
approved these four revised routes. Preserve concept IDs, order, objectives,
16-activity structures, answer IDs and deterministic experiment models. Improve
openings, first-use definitions, compact explanations, full answer alternatives,
feedback and practical instructions together. Preserve old 1.1.0 packs/traces;
select new 1.2.0 outputs. Tutor dialogue stays unlimited and no new progression
lock is introduced. Browser checks additionally exposed a Shift quantity-definition
error and an unanswered-final support-path answer leak. The follow-up adds public
quantity context and routes final orientation/explanation through conceptual help,
without a dialogue quota or evaluator authority.

- [x] Revise all four packs and openings without changing curriculum or model truth.
- [x] Preserve historical hashes and prove new answer/feedback/experiment contracts.
- [x] Use consistent plain-language practical controls and comparison instructions.
- [x] Pass offline suites and Chrome student checks in all four combinations.
- [x] Run separately authorised fictional live Tutor probes and record limits.
- [x] Refresh the 9090 deployment package and document remaining expert decisions.

Evidence: no commit or remote deployment was created. Windows, Python 3.13.15;
347 SDK tests, 12 Node session/editor tests, 14 Nirvana tests and 6 deployment
tests passed, together with web typecheck/build, M1 freshness and diff checks.
Actual Chrome normal-session walkthroughs completed all sixteen items in Effect
General and Robustness Medical. The other two combinations completed eight
topic items and their first two-configuration experiment. Live multi-turn probes
covered every combination; six consecutive General robustness requests included
an unrelated request and return to the lesson. Policy 1.5.4 final support was
retested with repeated Explanation, subsequent chat, scoring and a fresh neutral
orientation. No conversation quota or chat-based score authority was added.

Evidence and honest coverage/limitations:
`../../output/portal-s33-20261019/verification.md`. Final shareable archive:
`../../output/educagent-server-20261019-s33-r3.tar.gz`, 85,213,402 bytes,
161 manifest entries, SHA-256
`7325537ed2ba138a8b06d0c788caac04b308a2823700736c3e80115cfc14f01e`.
All manifest hashes and six profiles were verified; credentials, traces and
textbook PDFs are excluded. Earlier archives are unchanged. Server ELM config
and data must be retained on update. Full sixty-four-item Chrome completion,
Docker execution, remote acceptance and scientific approval are not claimed.
Residual live-model issues include semantic answer leakage beyond exact-copy
checks and one generated analogy switching the stated common-cause variable;
these are recorded for expert/model evaluation, not hidden as passing evidence.

### S32 combined learner-experience feedback - DONE IN WORKTREE, 2026-10-19

Combine Kurt's 61 comments with the first Damian revision without changing the
nine-concept curriculum. Apply General/Medical revisions together: explicit
deterministic wrong-answer feedback, meaningful variable/value tasks and clear
answer alternatives, concise explanations with optional depth, plainer umbrella
actions, and final-assessment help that teaches without selecting the answer.
Keep Tutor dialogue unlimited and ordinary learning help available. Preserve
historical content, select new 1.4.0 packs and keep their evidence separate.

- [x] Show content-owned rejection feedback beside every scored response.
- [x] Revise both profiles' questions, challenges and explanations coherently.
- [x] Simplify shared scene/page hierarchy and fix the reported illustration.
- [x] Add assessment-aware Tutor support without a message quota or grading authority.
- [x] Pass offline regressions, Chrome student and authorised live Tutor checks.
- [x] Update the 9090 deployment archive and record coverage and remaining limits.

Evidence: 313 SDK Python tests, 12 editor/session/URL JavaScript tests, 14
Nirvana tests and six deployment checks passed; TypeScript, production build,
content freshness, historical hashes and archive manifest/privacy checks passed.
Actual Chrome used normal saved state and authorised fictional ELM messages.
General completed all 28 activities; Medical used targeted entry, feedback,
lesson, transfer, scene and Tutor sampling, not a full 28-activity claim.
Live probes found and repaired early rain naming and current-final semantic
answer mapping; guided policy is now 1.5.2. Concept help and multi-turn
conversation remain available, without a learner message quota. Exact lexical
checks do not establish complete semantic non-leakage.

The fresh credential-free `output/educagent-server-20261019-s32.tar.gz` stages
all three applications behind port 9090 and six course/profile packs. It does
not update a remote service automatically. Preserve server config/data and old
content evidence. No scientific/clinical approval, mobile/accessibility study,
load benchmark or target-server Docker verification is inferred. See the
[acceptance record](../../output/portal-s32-20261019/verification.md) and
[feedback disposition](expert-review-20261019.md). These changes are uncommitted
local work; no publication or commit is claimed.

### S31 first expert-feedback revision - DONE IN WORKTREE, 2026-10-19

Apply the three supplied Damian review documents to General/Medical Foundations:
plain-English entry questions and controls, clearer museum common-cause and
probability examples, and explicit conditioning/intervention distinctions in
the shared umbrella mission. Preserve historical packs and traces; select new
`1.3.0` normal packs without migrating earlier answers. Investigate the reported
diagnostic-to-explanation continuation skipping the challenge. The screenshot's
intervention-course reorganisation suggestion has no detailed replacement yet;
do not invent that redesign or claim full scientific approval.

- [x] Apply the explicit content and interface wording feedback in both profiles.
- [x] Repair and regress diagnostic -> explanation -> challenge continuation.
- [x] Distinguish 96 filtered records from the 240-record authored intervention.
- [x] Preserve historical content; pass generation, provider-independent and web checks.
- [x] Inspect revised student flows in Chrome and record unresolved review questions.

Local uncommitted Windows/Conda evidence: 281 provider-independent Python tests
passed in 60.205 s; 12 Node editor/URL/session tests, six deployment staging tests,
both course generators' freshness checks, TypeScript and production build
passed. Historical inputs and 1.2.0 outputs have unchanged SHA-256 checksums.
Chrome on the permitted 4111 offline fixture completed both nine-question
diagnostics, checked all-correct and selected-topic results, General/Medical
quiz -> explanation -> challenge, completed Medical targeted review and
reopened its topic review through the formerly broken transition. The saved
three-activity route remained intact. Chrome also inspected the simplified
Medical probability explanation and shared umbrella records, prediction,
assigned-carrying result and revision, including the 240/96 comparison. No new
live ELM evaluation or full-course scientific approval is claimed. Final web
bundle `index-DqSkSIcU.js`; normal 4173 and Nirvana 8011 endpoints return 200.
See the [feedback disposition](expert-review-20261019.md) and
[acceptance record](../../output/expert-review-20261019/verification.md).
Existing deployment archives are not silently replaced or remotely installed.
A fresh credential-free `output/educagent-server-20261019.tar.gz` was built from
the checked bundle and registry. Its archive SHA-256, every manifest entry,
revised Foundation questions and frontend bundle were verified; no `.env`,
JSONL learner history or textbook PDF is included. The documented direct
generator invocation also has a subprocess regression. Temporary test serving
and records were removed; screenshots and verification evidence remain.

### S30 browser-session-isolated Portal state - DONE IN WORKTREE, 2026-10-15

The user requests independent progress/preferences for different browsers
before shared-server deployment. Add anonymous browser-cookie isolation to
the normal Portal launcher, preserving the existing single-hub API for legacy
consumers. Scope controllers, diagnostics, selection, conversation, review,
preview and resets to the selected browser session. Preserve historical shared
traces without automatically importing them into a new visitor's record.

- [x] Isolate complete runtime state and versioned persistence by opaque cookie.
- [x] Preserve refresh/restart with the same cookie and validated preferences.
- [x] Remove stale browser-local Profile preference overriding a new session.
- [x] Verify two independent clients, reset isolation and provider-independent regressions.
- [x] Validate in Chrome and rebuild the 9090 deployment archives and guide.

Final local evidence: 269 provider-independent Python tests passed in 58.409 s,
12 SDK Node tests, TypeScript and production build passed. Six deployment tests
and Linux archive checksum/manifest verification passed. Chrome on the user's
requested 4111 address confirmed independent test-cookie progress/Profile/module
selection, refresh, B reset without changing A, and same-cookie tab sharing.
Independent cookie-jar tests also covered concurrent Tutor requests, diagnostic
and course restart recovery, cache eviction, malformed tokens and failure
cleanup. Loopback authoring remains available; the deployment gateway blocks
authoring and preview. Final frontend bundle `index-Cwwm437Y.js`.
Both 9090 archives include the same browser-session runtime; only the explicitly
requested private variant includes ELM configuration, outside the image.
See the [acceptance record](../../output/portal-s30-20261015-4111/verification.md).

Anonymous session isolation is not a login, account recovery, cross-device
sync or a production-scale load/security qualification. Same-browser tabs
intentionally share a session. Cookie retention after browser exit depends on
the browser's session-restore policy.

### S29 normal-progress M1 walkthrough and entry sidebar consistency - DONE IN WORKTREE, 2026-10-15

The user explicitly permits using existing normal learning progress instead
of Testing preview. Exercise both M1 courses in General and Medical through
introduction, interactive practice, assessment and live Tutor conversation.
Use fictional teaching questions only. Fix reproducible issues and retest.
Match the M1 entry sidebar to Foundations and remove the requested caption
sentence without changing curriculum, grades or pack versions.

- [x] Share the Foundations-style introductory Tutor/route/module sidebar.
- [x] Remove `Illustrative scenes, not evaluation data.` from both captions.
- [x] Complete four normal-progress Chrome student routes with practice and Tutor evidence.
- [x] Pass provider-independent tests, web checks/build and final Chrome layout checks.
- [x] Synchronize preview exit and module switching with reload URL state.
- [x] Show tested configuration counts as an actual count plus a minimum, not `3 of 2`.
- [x] Remove legacy fixed-table results from experiment Tutor context and deterministic orientation/fallback rendering; verify through live Chrome replies and offline controller checks.

Local uncommitted Windows/Conda evidence (Python 3.13.15): 258
provider-independent tests passed in 46.904 s, ten Node editor/URL tests,
TypeScript and production build passed. Chrome completed all four M1 routes
through their introductions, four topic sequences, four practical stages and
four final questions: 64 activities and 34 experiment runs. Sampled live
dialogue covered continuous three-turn help, pre-run uncertainty, actual-run
interpretation, errors/retries, post-score continuation, completed-topic review
and an off-topic request. The old 94%/88% table leak required a second repair
in shared deterministic rendering after the initial context-only repair;
fresh openings and subsequent run-grounded replies were rechecked. All four
normal completions restore independently; no progress was reset. Final bundle
`index-Bnoos_43.js`; both local services return 200. Chrome is left at normal
General Foundations entry, with both M1 routes available for review and no
preview URL flag. See the [S29 acceptance record](../output/portal-s29-20261015/verification.md).
This is technical/interaction coverage, not scientific approval or learning
effectiveness evidence.

### S28 square emoji profile buttons - DONE IN WORKTREE, 2026-10-15

Replace the profile dialog's horizontal radio options with equal square-like
buttons, large decorative emoji above their labels, and a visible pressed
state. Preserve confirmation, separate profile progress, and close/reopen
behavior. Validate keyboard selection, narrow layout, and the first-choice
and profile-change dialogs in Chrome without changing normal learning records.

- [x] Reuse native Astryx buttons with accessible names and `aria-pressed`.
- [x] Pass provider-independent, type/build and Chrome acceptance checks.

Local uncommitted Windows/Conda evidence: 255 provider-independent Python tests
passed in 54.392 s; TypeScript and production build passed. Chrome confirmed
square tiles (232 CSS px desktop, 167 CSS px at a 390-device-pixel viewport),
no horizontal overflow, no radio inputs, exclusive pressed state, Tab/Space/
Enter operation, cancel/reopen restoration and confirm-only application in
memory-only preview. Returned to normal General without resetting progress.
The shared first-entry/change dialog keeps its existing state/confirmation
rules; no normal first-entry reset was performed. Final bundle:
`index-bgJvVhu4.js`. See the [S28 acceptance record](../output/portal-s28-20261015/verification.md).

### S27 contextual M1 course introductions - DONE IN WORKTREE, 2026-10-15

The user requested an opening that makes the purpose and distinction of the
two M1 courses clear through examples and generated illustrations. Preserve
the existing curricula, scoring, pack versions and learning records.

- [x] Add an independently versioned, content-owned introduction catalog for
  General/Medical with motivating questions, examples, actions and a two-way
  comparison; reuse released pack claims for grounding.
- [x] Generate and inspect two editorial illustrations, preserve prompts and
  copy final assets into canonical public media with captions and alt text.
- [x] Show introductions before starting M1, allow reopening without changing
  attempts and distinguish module choices without adding a progression gate.
- [x] Verify catalog validation, state projection and unchanged trace resume;
  pass provider-independent, editor, type/build and Chrome checks.

Local uncommitted Windows/Conda evidence (Python 3.13.15): 255
provider-independent Python tests passed in 43.513 s, including nine new
orientation/preview tests; six Node editor tests, TypeScript and production
build passed. Four profile openings, the first-course start, module-purpose
labels, mobile layout and reopening with unsubmitted answers/chat/practice
drafts were exercised in Chrome. Final preview focus starts at the title;
returning restores the exact previous scroll position (845.56 CSS px in the
probe), draft text and slider value. Selecting a Tutor topic exits the intro.
Chrome exposed a preview-start session ID with a missing profile; the actual
controller profile now supplies the ID, with normal-mode profile protection
unchanged. The final staged bundle is `index-BBPhwoTq.js`; both services return
200. Normal Medical Effect is left open at its introduction without starting
or resetting its learning trace. The scored M1 packs remain `1.1.0`. See the
[S27 acceptance record](../output/portal-s27-20261015/verification.md). This
does not establish scientific approval or teaching effectiveness.

### S26 operational M1 practice experiments - DONE IN WORKTREE, 2026-10-15

The user explicitly requested hands-on practice, not fixed comparison tables
with multiple-choice responses. General and Medical retain the four-concept
backbones and independent scored checks; each practical activity now has an
attempt-scoped parameter/prediction/run/comparison/reflection artifact.

- [x] Implement two content-authored deterministic experiment models and a
  small shared action/replay boundary without altering the historical M0 scene.
- [x] Version four M1 context packs, replace result-bearing practice prompts
  with operational tasks, and preserve separate objective-specific assessment.
- [x] Render accessible parameter controls, actual generated consequences,
  previous-run comparison and source/draft inspection in the shared Portal UI.
- [x] Verify stale/cross-attempt/idempotent actions, restart replay, no pre-run
  result leakage, profile parity and scoring gates with offline tests.
- [x] Complete Chrome student operations in all four M1 contexts, check Tutor
  context and responsive layout, and restore healthy normal services.

Local, uncommitted Windows/Conda evidence (Python 3.13.15): all 246
provider-independent Python tests passed (latest run 39.624 s), six Node editor
tests, schema/M1 generator freshness, TypeScript and production build checks
passed. Chrome student operations covered one practical stage in each of the
four module/context combinations, including controlled reruns, history,
reflection, scoring and retries. Medical Robustness sustained three live Tutor
turns and an additional Tutor-suggested experiment. Duplicate SVGs caused by
sibling React key collisions and narrow-header overflow were found and fixed;
final Chrome checks retain one chart and no page-wide horizontal overflow.
Portal and Nirvana health returned 200. No normal learning progress was reset.
The workspace has no existing HEAD; this is not committed or published work.
See [S26 acceptance record](../output/portal-s26-20261015/verification.md) for
exact operations, screenshots and remaining limits. This is not every-activity
Chrome coverage, scientific approval, learner-effect evidence or tutor-policy
qualification.

### S25 shared course UI and complete M1 teaching routes - DONE IN WORKTREE, 2026-10-15

The user authorised both M1 courses in this slice, including General/Medical
contexts, worked explanations, practical investigations and final assessments.
They also requested a common question-first learning flow, compact profile
selection, aligned use of the main column, stable transcript panes and default
access to all modules for inspection. Curriculum access is independent of scored
completion. Authored content retains source/provenance metadata while repeated
draft-status captions are removed from the learning pages.

- [x] Repair shared header, lecture/question hierarchy, content alignment,
  two-button profile selection and fixed-size scrolling transcript review.
- [x] Implement Quiz -> Explanation -> Challenge with feedback and retry;
  preserve scored evidence and Tutor continuity.
- [x] Render the editable umbrella model and revisit it in the DAG lesson.
- [x] Add complete General/Medical M1 explanations, four-stage comparison
  investigations and separate four-objective final assessments.
- [x] Add nine objective-specific Foundations final questions in new versioned
  Portal packs, retaining historical source packs and traces.
- [x] Validate profile parity, coverage, scoring/replay, authoring export,
  web/schema/build and Chrome student/Tutor flows; restore normal services.

Local, uncommitted Windows/Conda worktree evidence: 230 provider-independent
Python tests, six Node editor tests, type/build/schema and generator freshness
checks passed. After the final wording/presentation refinements, all 24 focused
course/runtime tests passed again. The six real packs' 118 choice activities
exercise post-answer Tutor context and offline FunctionModel replies. Chrome
spot checks cover both contexts, ordinary question-first learning, real novice
dialogue, recovery of a failed Medical reply, practical evidence views, DAG
recall, normal mission completion and stable internally scrolling trace review.
The final staged table is inset within its panel; Portal and Nirvana health
both return 200. See [acceptance record](../output/portal-s25-20261015/verification.md)
for screenshots, exact checks and remaining scientific/product limits. This is
not an expert content approval, all-activity Chrome walkthrough or new tutor
policy qualification.

### S24c completion-page Tutor continuity - DONE IN WORKTREE, 2026-10-15

The apparent General/Medical layout mismatch was caused by their different
route states: onboarding versus completed. The completed branch replaced the
Tutor with a static route record. The common learning layout now keeps the
Tutor visible after completion and uses the same panel width and course title. Topic review
opens an independent memory-only attempt with the selected profile's normal
teaching context; saved completion and module availability remain unchanged.

- [x] Verify review dialogue, duplicate requests, profile separation, preview
  return and reset ownership with provider-independent tests.
- [x] Pass all 206 Python tests, TypeScript check and production build.
- [x] Verify completed Tutor, topic review, live dialogue and summary return in
  Chrome. Completed a fresh practical mission, entered Medical topic review,
  received two live replies and returned to the same one-activity completion
  record. General's first lesson also displayed the same Tutor structure.
  Screenshot capture timed out; no new visual screenshot is claimed. The normal
  Portal and Nirvana health endpoint returned 200 after service restoration.

### S24b normal Foundations profiles - DONE IN WORKTREE, 2026-10-14

The user authorised nine-topic Foundations only for this slice; complete M1
courses are deferred to the next round. General and Medical are editable example
contexts, not inferred expertise levels. First entry and selected-profile reset
require a choice with icons; Change profile resumes independent progress.
`foundation_profiles.json` authors nine explanations per context and all eighteen
non-scene Medical assessment questions. Stable objectives, activity IDs, answer
semantics and evaluation remain unchanged. The rain/umbrella workbench is an
explicitly shared neutral challenge, not a fabricated clinical simulator.

General keeps its original `causality.m0.full / 1.1.0` assessment and JSONL trace; a
separate read-only teaching companion supplies explanations. Medical uses
`causality.m0.medical / 1.0.0` with an independent trace and entry diagnostic.
No existing trace is migrated or reinterpreted. Ordinary learners no longer see
a Testing preview entry; explicit `?preview=1` remains memory-only developer QA.
Content is independently authored synthetic material, with expert review pending.
Current-source compilation/release checks passed for both contexts, with no
unused resources. Independent source review verified ECI locators and corrected
three lecture/challenge-overlap cases. The full provider-independent suite passed
203 tests, including the actual nineteen-activity Medical route and all nine
concept completions/replay. Five Node editor regressions, TypeScript/build,
schema freshness and whitespace checks passed. Two frontend state-isolation
fixes keep preview preference writes separate and clear diagnostic selections
across profile/pack/version boundaries.

Chrome verification then used the restored normal Portal on port 4173 (not the
isolated 4186 origin, which remained blocked by the browser tool). The first-
entry/profile-change flow, nine-question General entry diagnostic, all nine
Medical explanations and practice, the integrated rain investigation, and all
nine Medical completion routes were exercised. Medical recorded 19 completed
activities and exposed both M1 links; its progress remained separate when
switching profiles. General's entry diagnostic recorded a starting point, not
mastery. Live Tutor dialogue answered repeated concept questions, included a
guiding prompt on request, redirected an unrelated shopping question back to
course scope, and declined to recommend a real treatment decision. The normal
Portal and Nirvana health endpoint were restored and verified.

- [x] Compile the actual eighteen lecture pages and Medical questions with
  unchanged objectives, grading and shared scene.
- [x] Verify normal profile/reset/context/replay contracts and the full Medical
  route with provider-independent tests.
- [x] Verify first-entry/reset/editable profile, normal learning and live Tutor
  behaviour in Chrome on the normal Portal. The separate 4186 origin remained
  unavailable to the browser tool; no bypass was attempted. The user explicitly
  authorised starting over, and Chrome testing used the normal profile stores.
- [x] Restore normal Portal/Nirvana services and verify independent profile
  progress, Medical completion and General diagnostic state after Chrome checks.

See the [current verification record](../../output/portal-foundations-profiles-20261014/verification.md).

### S24a first-stage local slice - DONE IN WORKTREE, 2026-10-14

- Added one worked `association-is-not-causation` sample in General and Medical
  contexts: authored explanation, hypothetical common-cause DAG, practice and a
  fresh independent transfer question. The original objective and nine-concept
  M0 pack are unchanged. Sample content is `author_draft`; expert review remains
  pending. Each sample has a separate pack ID and version `1.0.0`.
- Added an optional typed lesson contract, strict sample compiler and released
  resource projection. No scoring keys or feedback enter lecture context.
  Profile/module/version progress is isolated. Preview uses memory-only
  controllers with no store, supports arbitrary declared activities and module
  access, and restores the normal module/profile/attempt saved when preview was
  entered without saving preview credit. The lesson graph contract matches the
  current renderer's three-node, two-edge common-cause fork.
- Retained checked completion evidence across optional dialogue/explanation and
  replay. Continuing after failed optional discussion appends a recovery event.
  Invalid-command/state errors now give specific categories and recovery guidance.
- Repaired the existing editor's destructive import/export path and connected
  local HTTP validation to SDK structure/release checks. Images, scenes,
  classification types, derivations and optional lesson metadata survive edits.
  The editor is local-only; validation does not install or publish content.
  The raw sample source is compiler input; the GUI edits compiled schema-v3
  ContentPacks and preserves lesson/graph metadata outside its forms.
- The two M1 entries remain four-concept binary placeholder seeds. A complete
  intervention-effect curriculum and a robust-prediction/generation curriculum
  have not been delivered. The robustness seed does not yet cover generation.

Validation in the `educagent-sdk` environment (Python 3.13.15): 181
provider-independent Python tests and five Node editor regressions passed;
`web:check`, production `web:build`, generated schema freshness and
`git diff --check` passed. Both compiled profile packs have no unused resources.
Chrome learner-role checks received nine General and ten Medical live free-text
replies, covering direct explanations, Socratic questions, confusion, Chinese
input and off-topic redirection, without a two-turn refusal. Both samples
completed wrong/correct practice, post-answer dialogue, Explain, Continue and a
fresh challenge. The offline Medical retry produced one learner event, not a
duplicate. These are targeted observations, not a semantic or learning guarantee.

The real GUI imported the full M0 pack, passed SDK validation and downloaded a
semantically identical pack. An unreviewed source produced a structurally valid
but non-releasable result with nine issues; draft export remained available and
labelled. Small-screen content wrapping was checked after repair. Preview could
open both M1 seeds; leaving a different module restored the same Foundation
alert-count question and attempt, with both M1 prerequisites locked again.

See the [consolidated verification record](../../output/portal-goal-20261014/verification.md).
This is uncommitted working-tree evidence for the first-stage slice only.
Service redeployment/progress-preservation handoff checks are not claimed by
these checks. Broader S24 depth adaptation, expert content review, new complete
M1 courses and study qualification remain outstanding. Earlier Chrome results
below refer to earlier builds only.

### Previous repair boundary — 2026-09-05

The umbrella Portal's legacy `--unguarded-tutor` flag now selects guided local free-text with phase-visible authored context and same-attempt history. It is neither the earlier minimal vanilla baseline nor the historical guarded qualification configuration. `DEMO_CHAT_POLICY_VERSION` is `1.0.0`; its reply decision trace IDs include `.guided-chat.1.0.0`, while the unchanged guarded tutor keeps version `1.12.0`. Earlier S21/S22/S23 records are historical evidence, not proof that the revised pack, renderer, and prompt are qualified together.

The authorised repair keeps the nine-concept backbone and existing rain mission. It corrects scene context and supplied-model assumptions, narrows learner feedback to the evidence actually submitted, adds direct practical-mission entry, makes diagnostic skipping enter the full route without diagnostic success, corrects source-rights metadata, and restricts static serving to public web assets. It does not build a new curriculum generator, claim nine-concept mastery from a binary probe, or authorise recruitment.

In pack `1.1.0`, integrated/delayed binary evidence applies only to `association-is-not-causation`; other concepts require their own declared practice/transfer activities. No M1-readiness requirement is configured in these revised packs. Rain-model matching is checked against supplied synthetic assumptions, while the written reflection is unscored. The diagnostic still transparently reuses practice questions; a separate independent item bank remains deferred.

Full and delayed packs move to `1.1.0`. Pre-repair pack snapshots remain private under `.educagent-demo/packs/`; the original `.educagent-demo/causality-m0-full.jsonl` is preserved. Default progress uses pack/version-specific traces; existing explicit `--events` paths are not silently rewritten. Do not replay historical evidence against altered content or overwrite old traces to make a revised demo start.

The umbrella launcher stages only public entry files, the Sources & rights notice, and built Portal/Nirvana/media assets in `.demo-site/`; it no longer serves the development workspace. The HTTP handler additionally checks allowed public routes, asset extensions, and resolved paths. PDFs, extracted text, JSONL traces, source maps, hidden files, and traversal paths are outside that serving boundary. This is a technical exposure control, not a rights or public-deployment approval.

Local verification is recorded in S23 below. A fresh independent transfer task and a reviewed curriculum study remain follow-up work, not completed repairs.

### Historical implementation checkpoints

| Item | Historical evidence |
| --- | --- |
| Branch | `codex/logfire-observability` |
| Baseline commit | `736e3a2` — documentation-only restart |
| Previous implementation | retained only in Git history before the restart |
| S1 checkpoint | `633ccdd` — authoritative Pydantic content contract |
| S2 checkpoint | `5103be2` — released claims and teaching resources |
| S3 checkpoint | `5dcc675` — typed learner evidence, evaluation, and gated teaching move |
| S4–S13 checkpoint | `2c51d5c` — guarded tutor loop, ELM qualification, curriculum, evaluation, portability, and M1 |
| S10 guarded-demo hardening | `7344a8b` — explicit guarded selector, persistent local async runtime, and JSONL replay |
| Development environment | Conda environment `educagent-sdk` |
| Verified Python | `3.13.15` |
| Python package | `educagent-sdk 0.7.0` with complete M0, replay-derived profiles, local demo/API, study export, portability proof, and an M1 causal-world module |
| Content packs | released schema-v3 Causality M0 seed, episode, full curriculum, delayed transfer, and a fractions portability pack |
| Tests | 133 provider-independent unit-test methods pass from the current working tree on 2026-08-26 |
| Contract dependency | Pydantic `2.13.4` in the verified constraints environment |
| Agent dependency | `pydantic-ai-slim 2.33.0`; the browser demo requires the configured host model through the existing guarded selector |
| Observability dependency | Logfire `4.41.0`; the application opts into content-free Pydantic AI instrumentation |
| Schema | generated `content-pack-v3.schema.json` and `--check` pass |
| Release validation | all shipped packs used in tests are releasable with no unused resources |
| Package verification | constrained `educagent_sdk-0.7.0-py3-none-any.whl` build and a fresh temporary `--target` isolated import pass |
| S14 | generic released-activity entry diagnostic, append-only LLM question trace, Astryx/React client, and an ELM/Chrome smoke path |
| S15 | explicit answer commitment, responsive chronological M0 workspace, and Chrome-tested Socratic interaction order |
| S16 | content-owned, non-evidentiary scenario images for five early M0 prompts |

## 3. Overview

| Step | Deliverable | Status | Progress | Depends on |
| --- | --- | --- | ---: | --- |
| S0 | Documentation-only restart baseline | `DONE` | 5/5 | — |
| S1 | Authoritative Pydantic content contract | `DONE` | 7/7 | S0 |
| S2 | Released claims and teaching resources | `DONE` | 7/7 | S1 |
| S3 | Typed learner evidence, evaluation, and gated teaching move | `DONE` | 7/7 | S2 |
| S4 | Agent-ready append-only events and replay | `DONE` | 7/7 | S3 |
| S5 | Guarded Pydantic AI Socratic tutor | `DONE` | 7/7 | S4 |
| S6 | One complete agentic causality episode | `DONE` | 7/7 | S5 |
| S7 | Complete Causality M0 curriculum and status semantics | `DONE` | 6/6 | S6 |
| S8 | Evidence-backed learner profile projection | `DONE` | 5/5 | S4, S7 |
| S9 | Tutor quality, grounding, and observability hardening | `DONE` | 6/6 | S5, S8 |
| S10 | Minimal API and accessible renderer | `DONE` | 7/7 | S7, S8 |
| S11 | Evaluation and export | `BLOCKED` | 5/7 | S7, S9, S10 |
| S12 | Portability proof | `DONE` | 5/5 | S8, S11 |
| S13 | Executable causal world and M1 | `DONE` | 5/5 | S11, S12 |
| S14 | Conversational M0 entry diagnostic and Astryx client | `DONE` | 8/8 | S5, S7, S10 |
| S15 | Socratic learning-workspace refinement | `DONE` | 9/9 | S14 |
| S16 | Visual scenario context for early M0 prompts | `DONE` | 4/4 | S14, S15 |
| S17 | Required-tutor workspace redesign | `DONE IN WORKTREE` | 4/4 | S14-S16 |
| S18 | Targeted-route and dialogue-convergence hardening | `DONE IN WORKTREE` | 6/6 | S17 |
| S19 | Generic dialogue safety and route semantics | `DONE IN WORKTREE` | 4/4 | S18 |
| S20 | Causal-workbench and Socratic-investigation design | `DONE IN WORKTREE` | 7/7 | S19 |
| S21 | M0 causal-scene engine and playable learning object | `DONE IN WORKTREE` | 5/5 | S20 |
| S22 | Socratic causal-scene director | `DONE IN WORKTREE` | 4/4 | S21 |
| S23 | Interactive-Socratic quality qualification | `BLOCKED` | 4/5 | S22, S11 |
| S24 | Learner depth and content adaptation | `LATER` | 0/4 | S23 |
| S24a | Bounded General/Medical worked sample and local reliability | `DONE IN WORKTREE` | 4/4 | S7, S10; user-authorised local slice |
| S24b | Normal nine-topic Foundations profile integration | `DONE IN WORKTREE` | 4/4 | S24a; user-authorised context variants, not depth adaptation |
| S24c | Shared Tutor layout and completed-course review | `DONE IN WORKTREE` | 3/3 | S24b |
| S25 | Shared course flow and complete authored M1 context routes | `DONE IN WORKTREE` | 6/6 | S24c; local technical acceptance, not scientific approval |
| S26 | Operational M1 practice experiments in both contexts | `IN PROGRESS` | 0/5 | S25; explicit hands-on practice request |

## 4. S0 — Documentation-only restart baseline

**Status:** `DONE`
**Purpose:** create one explicit empty implementation checkpoint before writing the new public contract.

- [x] Remove the legacy source, content, tests, CLI, and obsolete background document from the current tree.
- [x] Remove the console-script declaration that pointed to a missing module.
- [x] Make README capability, build, and test statements truthful for a documentation-only baseline.
- [x] Add the canonical document index to `AGENTS.md` and align the three canonical documents.
- [x] Store the reset as one reviewed commit without secrets, local reference repositories, generated caches, or executable capability claims.

**Exit evidence required:**

```text
baseline: commit containing this roadmap snapshot
tracked implementation files: none
content packs: none
tests: none by design
previous implementation: Git history only
```

## 5. S1 — Authoritative Pydantic content contract

**Status:** `DONE`
**Start only after:** S0 exit evidence is complete.

- [x] Create the installable `educagent_sdk` package and verify its wheel in an isolated environment.
- [x] Add Pydantic as the required public-contract dependency.
- [x] Model `Choice`, `Activity`, and `ContentPack` in `contracts.py` with strict, closed, frozen models.
- [x] Author one minimal Causality M0 JSON seed and load it through `model_validate_json()`.
- [x] Generate `schemas/content-pack-v1.schema.json` from the models and verify that it is current.
- [x] Pass unknown-field, strict-type, cross-reference, generated-schema, and complete provider-independent tests.
- [x] Publish only verified install, build, and test commands in README.

**Exit gate:** the package builds; Pydantic is the only authored content schema; JSON remains authored data; generated schema is reproducible; tests remain provider-independent.

**Exit evidence:**

```powershell
conda run -n educagent-sdk python -m compileall -q src scripts tests
$env:PYTHONPATH = "src"
conda run -n educagent-sdk python -m unittest discover -s tests -v
conda run -n educagent-sdk python scripts/generate_schema.py --check
conda run -n educagent-sdk python -m pip check
conda run -n educagent-sdk python -m pip wheel --build-constraint build-constraints.txt --no-deps --wheel-dir dist .
```

The same 13 tests, schema check, and `pip check` also passed after installing the wheel with `--no-index` into a fresh temporary Conda environment. The imported package resolved from that environment's `site-packages`, not from `src/`.

## 6. S2 — Released claims and teaching resources

**Status:** `DONE`

- [x] Add minimal `Source`, located `SourceRef`, `Claim`, and `TeachingResource` records, including deterministic-derivation provenance.
- [x] Move authoritative questions, hints, and explanations out of activities into stable resources.
- [x] Give every accepted and rejected evaluator outcome a released consequence resource.
- [x] Make released resources resolve only to released claims and reviewed provenance declarations.
- [x] Fail closed on draft, missing, duplicate, or incompatible references.
- [x] Report unresolved and unused resources during release validation.
- [x] Migrate the current pack through one explicit schema version and pass provider-independent contract tests.

**Exit gate:** every learner-visible factual teaching response resolves to released resource and claim IDs.

**Exit evidence:**

```powershell
$env:PYTHONPATH = "src"
conda run -n educagent-sdk python -m pip install --build-constraint build-constraints.txt -c constraints.txt -e .
conda run -n educagent-sdk python -m compileall -q src scripts tests
conda run -n educagent-sdk python -m unittest discover -s tests -v
conda run -n educagent-sdk python scripts/generate_schema.py --check
conda run -n educagent-sdk python -m pip check
conda run -n educagent-sdk python -m pip wheel --build-constraint build-constraints.txt --no-deps --wheel-dir dist .
```

The final 26-test source suite, schema check, dependency check, wheel build, and release smoke path passed. Before the review additions, the same 24-test suite also passed after a no-index wheel installation in a fresh temporary Conda environment created from the local package cache. The installed import resolved from that environment's `site-packages`. The seed release report contained no issues and no unused resources.

## 7. S3 — Typed learner evidence, evaluation, and gated teaching move

**Status:** `DONE`

- [x] Add strict `ChoiceEvidence`, stable `Evaluation`, and minimal `TeachingMove` contracts.
- [x] Evaluate the current activity by stable `activity_id` and `option_id`, independent of authored option order.
- [x] Return only deterministic semantic IDs and resolve learner-visible consequences through released resources.
- [x] Make runtime generate canonical allowed moves scoped to the exact evidence and released resource.
- [x] Rebuild the allowlist and require exact candidate membership before accepting a move.
- [x] Prove rejected evidence cannot validate `advance` and accepted evidence still requires the runtime curriculum gate.
- [x] Keep S3 provider-independent and stateless, with no CLI, policy, event, attempt, replay, or model implementation.

**Exit gate:** learner evidence, evaluator verdict, move request, and runtime progression gate are separate tested values; no later-step policy, event, or renderer behavior is required.

**Exit evidence:**

```powershell
$env:PYTHONPATH = "src"
conda run -n educagent-sdk python -m compileall -q src scripts tests
conda run -n educagent-sdk python -m unittest discover -s tests -v
conda run -n educagent-sdk python scripts/generate_schema.py --check
conda run -n educagent-sdk python -m pip check
conda run -n educagent-sdk python -m pip wheel --build-constraint build-constraints.txt --no-deps --wheel-dir dist .
```

The final 44-test source suite, schema check, dependency check, constrained wheel build, isolated wheel import, and deterministic evaluation/gate smoke path passed. At the S3 exit, the wheel metadata contained only Pydantic as a runtime dependency; later observability work changes current package metadata separately. Rejected evidence cannot validate `advance`; accepted evidence requires an explicit trusted curriculum gate before `advance` becomes canonical.

## 8. S4 — Agent-ready append-only events and replay

**Status:** `DONE`

- [x] Add versioned `LearningEvent` envelope with validated session, attempt, response, support-request, move, close, and completion event types.
- [x] Append deterministic response/evaluation—or a typed unscored support request—before any tutor-agent decision.
- [x] Add pure replay/reducer for cursor, attempt lifecycle, phase, support, last evaluation, progression permission bound to the current scored event, and completion; unscored input or non-advance moves clear that permission.
- [x] Add request idempotency and changed-payload conflict detection.
- [x] Add scoped candidates: a resource-free runtime-only `hold`, a sole-candidate deterministic S4 baseline selector for normal scored turns, selector-kind validation, and selector/tutor provenance without importing Pydantic AI.
- [x] Keep replay read-only and recover a pending scored response or support request through a separate idempotent command that rebuilds the full scoped set and appends exactly one ordinary-gate-validated runtime-only `hold`.
- [x] Prove live execution and replay produce identical state and strategy IDs.

**Exit gate:** append-only events are authority; interruptions do not lose evidence or create completion; persistence remains in memory until a second store is needed.

**Exit evidence:** the provider-independent 61-test suite covers strict event envelopes, legal transitions, deterministic re-evaluation during replay, scoped selection, idempotency/conflicts, scored and unscored recovery, stale progression clearing, completion gates, and live/replayed state equality. Compile, generated-schema, dependency, and constrained-wheel checks pass. No event-store abstraction, JSONL adapter, database, or Pydantic AI import was added.

## 9. S5 — Guarded Pydantic AI Socratic tutor

**Status:** `DONE`

- [x] Add `pydantic-ai-slim`, one named `Agent`, and the first real `clarify`/`direct_instruction` candidate builders and reducer transitions.
- [x] Add bounded, idempotent, unscored `LearnerMessage` events with explicit phase/pending/recovery semantics, and frozen `TutorDeps` snapshots with no store, cursor, callback, mutable session, or write-capable tool.
- [x] Enforce one-main-question, attempt-before-hint, monotonic support, no-reveal, direct-teaching escape, and mandatory-retry rules.
- [x] Keep `TutorTurnProposal` minimal—one tutor-selectable candidate ID plus an optional in-scope misconception hypothesis—while runtime derives framing, grounding, and expected-evidence predicates and rechecks every gate.
- [x] Add a versioned headless framing catalog, canonical resolved-turn contract, and pure turn composer; persist candidate/framing/grounding references needed to replay identical text, while S10 only presents it and M0 generates no learner-visible model prose.
- [x] Add bounded structured-output retry, whole-run timeout, and one idempotent runtime-only `hold` fallback accepted only for declared fallback selector kinds through the ordinary gate.
- [x] Cover prompt injection, invalid IDs, hypothesis scope, frozen deps, stale progression, crash-after-message, provider failure, and prove the tutor cannot emit correctness or progression.

**Exit gate:** one Pydantic AI tutor drives Socratic turns, while every accepted proposal remains typed, grounded, runtime-validated, and replayable.

**Exit evidence:** the 71-test provider-independent suite uses Pydantic AI `TestModel` and `FunctionModel` with live requests disabled. It covers valid structured selection, exact grounding/framing replay references, bounded retry, unknown fields/IDs, prompt injection, hypothesis scope, frozen deps, learner-message recovery, monotonic support, direct-teaching retry, legal advance, timeout, provider failure, and idempotent `hold`. Compile, generated-schema, dependency, constrained-wheel, isolated-wheel, and Logfire content-free smoke checks pass.

## 10. S6 — One complete agentic causality episode

**Status:** `DONE`

- [x] Implement one observation-versus-intervention episode end to end.
- [x] Add the second real response type and only then an activity discriminator.
- [x] Require commitment, consequence, revision, and a new learner action.
- [x] Add one unseen software/neutral transfer variant without a content hint.
- [x] Make all facts, consequences, and support resolve to released resources.
- [x] Prove deterministic `TestModel`/`FunctionModel` runs replay exactly.
- [x] Record one separately invoked real-provider smoke that passes the same gates; formal qualification remains S9.

**Exit gate:** one real learning episode proves the entire content-evidence-pedagogy-runtime-trace contract.

**Current evidence:** `content/causality_m0_episode.json` contains three released activities: committed classification and revision, an assumption judgment, and a software transfer classification. `ClassificationEvidence` records an artifact and an optional prior response-event reference; replay rejects a missing, future, cross-session, or different-artifact revision reference. The provider-independent suite covers the complete episode with `TestModel` and `FunctionModel`, including released consequence reflection, direct-teaching retry, and live/replayed state equality. The separate ELM run completed the episode through the bounded Pydantic AI tutor with no fallback; its non-secret record is [`evidence/elm-qualification.json`](evidence/elm-qualification.json).

## 11. S7 — Complete Causality M0 curriculum and status semantics

**Status:** `DONE`

- [x] Teach all nine M0 concepts under the expanded contract.
- [x] Add reviewed action-consequence-revision episodes, W/D/M classification, and a first-model activity.
- [x] Give every concept accepted evidence, evaluator, misconception resource, claims with located `SourceRef` anchors, and transfer mapping.
- [x] Add final unseen integrated transfer and frozen M1-readiness rubric.
- [x] Derive `completed` and `m1_ready` from closed-attempt predicates; `mastered` remains unavailable.
- [x] Complete the entire curriculum through the guarded tutor with deterministic scoring and runtime progression gates.

**Exit gate:** full Causality M0 content/domain definition of done passes; no first session can award mastery.

**Current evidence:** `content/causality_m0_full.json` has 9 concepts, 19 released activities, and a final integrated transfer. `tests/test_curriculum.py` completes it through the guarded tutor and proves the replay-derived completed/M1-ready status.

## 12. S8 — Evidence-backed learner profile projection

**Status:** `DONE`

- [x] Derive attempts, evidence, support, hint dependence, revision, and transfer from events.
- [x] Represent misconceptions only as hypotheses with supporting event IDs.
- [x] Preserve failure and hint-dependent success as distinct evidence.
- [x] Provide a bounded redacted policy/developer view.
- [x] Prove live and replayed projections match without BKT, FSRS, IRT, or learning-style labels.

**Exit gate:** every learner-state field is explainable from events, and one response cannot create a permanent label.

## 13. S9 — Tutor quality, grounding, and observability hardening

**Status:** `DONE`

- [x] Make tutor context assembly explicit, bounded, and measurable.
- [x] Add redacted Pydantic AI/Logfire traces with stable agent, model, prompt, validation, usage, latency, retry, and fallback metadata.
- [x] Evaluate grounding violations, premature reveal, illegal advance, irrelevant/repeated questions, and fallback rate.
- [x] Qualify at least one real provider/model configuration against the frozen agent-quality set.
- [x] Do not add generated grounded paraphrase: released-resource composition meets the implemented teaching needs.
- [x] Publish and test the versioned fixed-policy control that uses the same runtime candidate gate.

**Exit gate:** the tutor has measurable quality and grounding thresholds; provider failure cannot lose evidence; model output still has no direct correctness, progression, or mastery authority.

**Current evidence:** `examples/qualify_guarded_tutor.py` reads an ELM OpenAI-compatible proxy configuration from `.env` without emitting its key, and records a completion trace and direct-instruction escape only if both pass the frozen automatic quality thresholds. The recorded ELM `gpt-5.6-luna` run has seven accepted decisions, zero fallback, and zero violations of every frozen quality risk; see [`evidence/elm-qualification.json`](evidence/elm-qualification.json). Its Logfire instrumentation excludes content.

## 14. S10 — Minimal API and accessible renderer

**Status:** `DONE`

- [x] Add start, respond, continue, and resume boundaries using the stable headless contracts.
- [x] Add a redacted development trace view.
- [x] Add local JSONL as the second event-store implementation.
- [x] Build a local, semantic one-page renderer with radio controls, buttons, and live regions.
- [x] Require a recorded response and validated move before a turn is rendered or an activity can continue.
- [x] Pass controller tests for restart, reload/JSONL resume, complete keyboard-style choice flow, and loopback server startup.
- [x] Add explicit `--agent` mode that routes only candidate selection through the guarded Pydantic AI tutor, owns one local-server async runtime across browser turns, and appends tutor-selected moves to JSONL before returning the receipt.

**Exit gate:** client remains a renderer; runtime remains the authority; provider failure remains recoverable without losing evidence or advancing.

**Current evidence:** the 93-test provider-independent suite covers agent selection,
JSONL replay of a tutor-selected move, and an HTTP server using its persistent
async runtime. A Chrome run through the configured ELM model completed the
three-activity episode with `reflect`, `socratic_hint`, and `advance` moves;
each move had `selector_kind="tutor"`, and a reload resumed the persisted
state. Checkpoint: `7344a8b`.

## 15. S11 — Evaluation and export

**Status:** `BLOCKED` — requires research-owner approval of the primary
comparison plan, then a real pilot before a decision.

- [x] Export versioned de-identified events and derived outcomes.
- [x] Implement reading, source-chat, deterministic fixed-policy control, and guarded-agent arm manifests.
- [x] Freeze immediate and delayed unseen transfer tasks and rubric.
- [x] Report subject correctness, pedagogy protocol, and learning outcome separately.
- [x] Record pack/evaluator/policy/model/renderer/runtime versions per run.
- [ ] Freeze the concrete primary-comparison analysis criterion and study-host configuration in the reviewed `study-protocol.md` pre-pilot decisions.
- [ ] Record the evidence-based decision to retain, revise, or reject the guarded-agent design after a pilot.

**Current evidence:** the exported event rows and separate subject, pedagogy,
and outcome reports reproduce in the provider-independent test. The four arm
templates and qualified ELM configuration exist. A model-backed arm cannot
produce a run manifest until a researcher supplies its concrete model ID, as
the provider-independent study test now proves. No approved primary comparison
criterion, source-chat configuration, participant-consent record, or pilot
outcome exists. The protocol now contains a deliberately unapproved `TBD`
decision-record template so the research owner can freeze those items without
the SDK silently supplying a study decision. Those decisions and the eventual
pilot outcome remain external to the SDK.

**Exit gate:** study outcome rows reproduce from events without manual repair;
transcript judges remain secondary.

## 16. S12 — Portability proof

**Status:** `DONE`

- [x] Build a tiny fractions content pack with a deterministic derivation and evaluator.
- [x] Reuse core content, evidence, move, event, replay, and renderer contracts.
- [x] Keep causality imports out of the generic runtime.
- [x] Demonstrate that core progression code does not change.
- [x] Add no extension abstraction: the two real domains do not need one yet.

**Exit gate:** generality is demonstrated by two domains rather than predicted by a plugin design.

## 17. S13 — Executable causal world and M1

**Status:** `DONE`

- [x] Define the causal-world module as an extension outside the generic runtime.
- [x] Add a small executable Boolean structural causal world and deterministic oracle.
- [x] Add learner DAG artifact provenance and separate model/reasoning diagnosis.
- [x] Add deterministic intervention, counterfactual, backdoor-adjustment, and adjusted-risk operations.
- [x] Keep M1 dependencies and truth logic outside the generic runtime.

**Exit gate:** M1 adds causal rigor without changing generic learning authority or weakening M0 replay/evaluation.

## 18. S14 — Conversational M0 entry diagnostic and Astryx client

**Status:** `DONE`

The older S10 page proved that the local runtime worked, but it was not a
credible agentic learning experience. S14 adds a low-stakes starting snapshot
before M0 and replaces that page with a local Astryx/React conversation
workspace. It does not change the evaluator, curriculum completion, or pilot
comparison plan.

- [x] Add a frozen Pydantic `DiagnosticPlan` that references released activity IDs rather than duplicating subject matter.
- [x] Add `causality_m0_diagnostic.json` with one M0 practice activity for each of the nine scoped concepts.
- [x] Evaluate every diagnostic response through the ordinary deterministic evaluator and expose only a starting snapshot, never a skip, readiness, or mastery decision.
- [x] Gate the local M0 start endpoint behind the configured diagnostic and preserve normal local reset semantics.
- [x] Accept bounded learner free text, append it before the model runs, and project the trace as a chat conversation.
- [x] Allow the tutor to persist one short validated Socratic question only on a legal question-oriented move; it cannot name an answer, score, or advance.
- [x] Install Astryx, generate its agent guidance, and build a neutral-theme accessible React client with diagnostic, chat, current choice, progress, and guarded-authority views.
- [x] Run the complete provider-independent suite, schema check, production client build, and one fresh real-provider browser smoke after the final S14 code changes.

**Exit gate:** swapping the content pack and diagnostic plan can create a new
entry check without a new evaluator; free learner text produces a persisted,
guarded tutor interaction; and the browser client is a renderer over the same
deterministic runtime authority.

**Current evidence:** 104 provider-independent tests pass on Python 3.13.15;
both generated schemas are current; `npm run web:check`, `npm run web:build`,
and `npx astryx doctor` pass. A fresh Chrome run on the guarded ELM mode
completed the entry diagnostic, entered the M0 chat, appended one learner
message before the model call, reloaded the client, and continued with a
persisted guarded move and validated Socratic question. The final review also
made browser request IDs reload-safe, rejects visible answer labels in model
questions during both append and replay, binds the local server to loopback,
and uses a domain-neutral reflection prompt. A final new guarded ELM session
verified that the variables activity now renders that neutral reflection rather
than the observation/intervention-specific wording. Checkpoint is recorded in
Git.

## 19. S15 — Socratic learning-workspace refinement

**Status:** `DONE`

S15 refines the S14 client without adding a second authority, route engine, or
teaching agent. The route remains a read-only projection of the existing M0
content; response evaluation and progression remain entirely server-owned.

- [x] Replace immediate-answer buttons with an accessible radio selection and
  explicit learner commitment action for diagnostic and M0 choices.
- [x] Present a compact M0 route that shows the active concept and only marks
  concepts complete from replay-derived runtime state.
- [x] Render the active answer action after prior learner evidence and tutor
  feedback, so a revision follows the Socratic sequence rather than history
  order.
- [x] Keep the client Astryx-only, with no parallel CSS system or new UI
  dependency.
- [x] Use an Astryx responsive wide workspace: from 1100px, a 1440px learning
  composition gives the active learning stream a 960px budget and a 440px
  contextual side panel for the large scenario image and read-only route;
  below that breakpoint the image appears directly below the active prompt.
- [x] Render the complete conversation in append-only trace order without a
  default-hidden history; place the current answer commitment or continue
  action after the exchange, and keep the free-text composer pinned below it.
- [x] Identify tutor turns with the supplied EducAgent mascot through the
  accessible Astryx `Avatar` fallback chain.
- [x] Make the free-text composer compact, left-aligned, and driven by the
  composer's submitted value; expose whether the live tutor is ready and show
  a visible thinking state while a guarded turn is pending.
- [x] Run full repository validation and record the checkpoint commit.

**Exit gate:** a learner can see their current concept and evidence-based
progress, make a deliberate answer commitment, receive tutor feedback, then
make a revision without the UI implying that a click alone proves learning.

**Current evidence:** 106 provider-independent Python tests, both generated
schema checks, `pip check`, `npm run web:check`, `npm run web:build`,
`npx astryx doctor`, and `git diff --check` pass. Local Chrome inspection
verified the redesigned entry screen, radio selection enabling the explicit
commit action, M0 route, revision ordering, and a wide active-learning stream
beside the large contextual image. A further Chrome pass verified that the
full transcript is visible in trace order, scrolls independently without an
exposed horizontal scrollbar, and retains a bottom composer while the learner
reviews it. The keyboard order reaches answer controls before the composer;
the submit action remains unavailable until an answer is selected. A fresh
guarded ELM run also appended a free learner message and returned a validated
Socratic tutor turn through the local API. The checkpoint is the commit
containing this roadmap snapshot.

## 20. S16 — Visual scenario context for early M0 prompts

**Status:** `DONE`

S16 makes the first five practice prompts visually approachable without
changing the assessment or creating another teaching authority. The generated
illustrations are owned by their `Activity` records and render in the same
diagnostic and M0 views that project the activities.

- [x] Add the optional strict `ScenarioImage` contract with a local media path
  and accessible alternative text.
- [x] Attach five reviewed neutral images to the first five Causality M0
  practice activities.
- [x] Run full repository validation, including generated-schema freshness.
- [x] Inspect the built local client in Chrome and record the checkpoint.

**Exit gate:** the image is optional content context, not input to the
evaluator, tutor correctness, or runtime progression; media paths cannot point
outside the local static root; the same activity projects the image through
diagnostic and M0; and the visual does not reveal an answer or causal claim.

**Current evidence:** the complete 105-test provider-independent suite,
generated-schema check, `pip check`, Astryx type check and production build,
`npx astryx doctor`, and `git diff --check` pass. Chrome inspection completed
the diagnostic, showed scenario media for its first two prompts, entered M0,
and verified that a wrong response yields feedback before the same prompt and
its visual context reappear for revision. The checkpoint is the commit
containing this roadmap snapshot.

## 21. S17 — Required-tutor workspace redesign

**Status:** `DONE IN WORKTREE`

- [x] Apply the approved editorial Socratic workspace direction through an
  EducAgent Astryx theme, responsive context rail, commitment controls, tutor
  dock, and accepted-evidence continuation state.
- [x] Remove learner-visible offline guidance and the `--agent` opt-in path;
  retain one explicit local `Reset progress` control for the single-user demo.
- [x] Require a guarded Pydantic AI model at the local browser-server boundary;
  retain evaluator and runtime progression authority.
- [x] Pass Astryx type checking, production build, and the then-107-test
  provider-independent suite.

**Checkpoint evidence:** `npm run web:check`, `npm run web:build`, and
`PYTHONPATH=src conda run -n educagent-sdk python -m unittest discover -s tests -v`
pass on 2026-08-25. The production build reports an existing-size advisory for
its then-531 kB JavaScript chunk; no functionality is affected.

## 22. S18 — Targeted-route and dialogue-convergence hardening

**Status:** `DONE IN WORKTREE`

- [x] Make an initially correct scored classification eligible for immediate
  advance while retaining required revision after rejected evidence.
- [x] Remove learner-visible generic question suffixes and add a deterministic
  semantic near-repetition validator for `clarify` questions.
- [x] Keep the current activity's dialogue in the tutor dock without imposing
  a hard free-text turn quota.
- [x] Make diagnostic-targeted sessions stop after their preferred activities,
  including the zero-miss case, rather than falling through to the full pack.
- [x] Render green completed checks, red diagnostic misses, and a yellow current
  question mark; make unfinished route rows navigate through append-only
  interrupted attempts without granting completion.
- [x] Pass the complete provider-independent suite, schema checks, production
  client build, real configured ELM smoke, and Chrome workflow after the final
  code changes.

Two neutral generated scenario images now belong to the focus-mode observation
and help-page/bug-report transfer activities. The Socratic design review used
`socrates-pen` only for explicit asked-question context, deterministic
near-duplicate filtering, and code-enforced budgets; its open-ended unscored
completion model remains outside EducAgent.

**Exit evidence:** the 120-test provider-independent suite, generated-schema
check, `pip check`, `git diff --check`, `npm run web:check`, and the production
Vite build pass on 2026-08-25. A prior real configured ELM Chrome workflow
verified a mixed 7/9 diagnostic, non-fixed answer positions, green/red/yellow
route states, direct route navigation, both generated transfer images,
attempt-scoped dialogue, `clarify`-question repetition blocking, two-turn
convergence, corrected-answer progression, and targeted completion without
cycling back to the first activity. A separate read-only Chrome audit on the
same date verified the current diagnostic and M0 workspace at 1920 by 911 with
no console errors; it intentionally made no learner or ELM call, so it does
not replace the recorded real-provider workflow. The production build retains
the advisory for its single 936 kB JavaScript chunk.

## 23. S19 — Generic dialogue safety and route semantics

**Status:** `DONE IN WORKTREE`

- [x] Keep free-text discussion unscored without imposing a per-activity
  message quota.
- [x] Apply deterministic exact and semantic question-repetition validation to
  every question-capable strategy in both command execution and replay.
- [x] Render diagnostic-only success as `Skipped`, not M0 `Completed`.
- [x] Bring the presentation implementation back within the Astryx
  theme/token conventions in `AGENTS.md`: remove the parallel
  `web/src/educagent.css` layer, use Astryx layout/scroll/bubble primitives,
  and keep the branded visual treatment in the registered Astryx theme.

**Why this is not silently included in S18:** S18 proves the M0 browser
experience is bounded and blocks the observed `clarify` loop. The SDK goal
requires those guarantees at the reusable runtime boundary, and the current
route UI must not equate diagnostic credit with M0 evidence.

**Exit evidence:** on 2026-08-26, the final working tree passed the complete
124-method provider-independent suite, generated-schema check, release
validation of `causality_m0_full.json`, `pip check`, `git diff --check`,
`npm run web:check`, and production Vite build. The build retains its advisory
for one large JavaScript chunk. A Chrome check against a fresh local
`--no-diagnostic` temporary trace confirmed that the active tutor dialogue is
visible by default, its history has an `overflow: auto` scroll region, and one
configured ELM follow-up returned the released variable definition and source
reference without restating the original question. The temporary check did not
alter the user's existing demo trace.

## 24. S20 — Causal-workbench and Socratic-investigation design

**Status:** `DONE IN WORKTREE`

- [x] Draft the first M0 causal scene—rain, umbrella carrying, and wet
  pavement—in [`causal-scene-rain-umbrella.md`](causal-scene-rain-umbrella.md).
- [x] Review and freeze the scene's synthetic-world scope, curriculum position,
  and S23 quality rubric with the product and causal-content owner: use the
  documented defaults for S21 implementation while leaving content release
  subject to its ordinary review gate.
- [x] State its unfamiliar transfer hook, learner self-explanation/prediction,
  tutor routing rule, DAG-edit, `do(umbrella_carried)` comparison, revision, and
  only then necessary formal evidence task in one reviewed design record.
- [x] State the released variables, graph actions, observational view,
  intervention result, visibility/reveal rules, and intended deterministic
  consequence.
- [x] Specify keyboard, screen-reader, narrow-screen, and text alternatives.
- [x] Specify the tutor's four dialogue jobs and its content-owned hint/direct
  explanation escape.
- [x] Define tool, parameter, provenance, and arbitrary-code boundaries before
  an agent or renderer implementation begins.

**Decision boundary:** a causal-workbench scene is allowed because it is one
small authored, deterministic causality extension. It is not permission to
build a generic visualisation platform, generic causal world, arbitrary code
sandbox, or an LLM-generated tool catalogue.

## 25. S21 — M0 causal-scene engine and playable learning object

**Status:** `DONE IN WORKTREE`

- [x] Recreate the Claude-design investigation shell using only current released
  M0 activity content: a primary canvas for the learner's unscored starting
  hypothesis, a permanently visible 520px tutor panel with independent thread
  scrolling, and no early quiz-style checkpoint. The shell deliberately
  contains no rain/umbrella facts and no inactive tool action.
- [x] Implement a pure, typed causal-scene specification, action transition,
  and scene replay core. Keep it content-agnostic and provider-independent.
- [x] Bind declared scene actions to the learning trace without granting
  `Evaluation.accepted` or progression from an interaction.
- [x] Build the accessible records/model/intervention web object around the
  same deterministic scene and released content.
- [x] Pass provider-independent scene/replay/accessibility tests and a
  browser action-prediction-observation-revision workflow.

**Exit evidence:** The causal-scene core validates authored graphs, declared
predictions, intervention identity, revision ordering, stale revisions, and
replay without a provider. Each action is an append-only
`causal_scene_action_recorded` event and cannot set `Evaluation.accepted` or
advance. The accessible Astryx workbench renders released hook, records,
DAG choices, prediction, intervention result, revision, and a text equivalent;
after revision the scene evaluator scores the committed DAG, while the
pre-reveal prediction remains trace context rather than a retrospective score;
this is not a replacement multiple-choice answer. On 2026-08-26, its
Chrome workflow ran records → model → prediction → intervention → revision,
and the default provider-independent checks, generated schema, TypeScript
check, and production build passed. The subsequent S22 work replaced the
generic activity dialogue with a scene-aware Socratic director; its historical
completion record follows.

## 26. S22 — Socratic causal-scene director

**Status:** `DONE IN WORKTREE`

- [x] Replace the current M0 dialogue prompt with the compact investigation
  master instruction and typed dialogue-job/interaction-focus proposal.
- [x] Expose only read-only frozen scene-snapshot lookups to the Pydantic AI
  tutor; reject undeclared tools, focuses, and question repetition in command
  execution and replay.
- [x] Drive every tutor response from the learner's actual prediction, scene
  action, or observed result, with a bounded content-owned hint ladder.
- [x] Prove the protocol with deterministic `FunctionModel` trajectories and
  a separate configured ELM run.

**Exit evidence:** `CausalSceneActionRecorded` is a first-class pending tutor
input. The only exposed tools return frozen scene state, a revealed intervention
identity, or the phase-derived legal focus. The runtime fills the sole valid
`interaction_focus_id` and its `dialogue_job` into every tutor scene event;
both are trace-recorded and replay-checked. The FunctionModel
trajectory covers hook, incorrect graph, prediction, intervention, comparison,
clarification, rejected final model, the released bounded hint, direct teaching
after that budget, revised model, and accepted final evidence. The latest
configured ELM run on 2026-08-26 completed records → graph → prediction →
intervention → revision → rejected evidence → hint → rejected evidence →
direct teaching → corrected revision → accepted evidence, with ten valid
focus/job pairs and zero fallback. Chrome completed the same flow
by keyboard and rendered its action direction, accessible controls, and text
alternative without the legacy final radio choice.

## 27. S23 — Interactive-Socratic quality qualification

**Status:** state/entry and guided-text repairs, targeted real-model probes,
Chrome verification, and local demo restart are `DONE IN WORKTREE`.
The participant comparison remains `BLOCKED` on the S11 pre-pilot decision record
and real follow-up. Simulated traces cannot supply learning-effect evidence.

**Earlier 2026-09-05 state/entry repair verification:** 148 provider-independent SDK tests passed (rerun: 5.543 s),
along with web TypeScript checks/build. The companion Nirvana passed four Python
unit tests and one Node UI-state regression. HTTP checks blocked private source
paths and stale JavaScript with 404 responses. Chrome verified optional diagnostic
skipping, practical-mission entry and final-evidence controls, and Nirvana's
draft/confirmed revisions, synchronised handoff, and manual DG link. The simulated
full scene passed its score and Continue path. Historical traces are preserved;
pack `1.1.0` uses separate progress. These checks do not extend historical guarded
qualification to the then-current vanilla mode or the subsequent guided prompt.

**Earlier authorised vanilla ELM smoke, 2026-09-05:** the shared configuration uses
`gpt-5.6-luna`. Two synthetic Nirvana API requests returned HTTP 200 in 5.86 s and
10.89 s; the observed replies did not carry over the prior case or present unknown
inputs as established facts. They did produce verbose seven-/nine-section
checklists. These are two integration observations, not comparative product or
learning evidence.

The real Portal Chrome scene also completed: an initially incorrect
umbrella-to-pavement model and more-wet prediction led to an unchanged intervention
result, a revision to the two supplied rain arrows with an unscored reflection,
Submit causal model, a passed check, Continue, and `Selected route complete`
for one activity. The temporary trace recorded eight `teaching_move_selected`,
five scene actions, one learner free-text message, one `response_recorded`, one
`attempt_closed`, and one `session_completed`, with no fallback reasons recorded.
Both `completed_concept_ids` and `m1_ready_concept_ids` remained empty as intended:
finishing this single mission does not complete the full concept requirements or
grant mastery/advanced readiness. Historical user traces were not changed.

**Observed vanilla teaching defects before the guidance repair:** live Portal free-text testing revealed the
rain/common-cause explanation early and introduced real-world umbrella-dripping
possibilities outside the supplied synthetic scene. Free-text grounding, reveal
timing, and concise teaching were not controlled by the minimal vanilla policy.
The earlier successful end-to-end path did not resolve those defects.

**Subsequent guided-text repair, 2026-09-05:** `run_open_demo_reply` now sends only
the current activity, phase-visible authored resources, `scene_text_projection`,
the recorded graph/prediction/reflection, legal next focus, and same-attempt
dialogue. It includes the latest learner message once and excludes the full scene
and `TutorDeps` with future results/assessment answers. A bounded length retry
replaces silent 1200-character truncation. Definitions and direct help remain
available. Plain text still cannot grade, mutate scene state, or advance.

The changed SDK suite passed 152 tests in 6.082 s, including exhausted
empty/overlong-response retries; the focused demo module passed 24 tests. The
companion Nirvana guidance has eight provider-independent tests. Its revised
prompt carries explicit user answers forward despite stale worksheet blanks,
asks for one genuinely missing field by default, and expands when detail is
requested; no automatic Brief extraction/editing was added.

Five final Portal probes using the existing ELM `gpt-5.6-luna` configuration
produced 48, 58, 20, 53, and 74 words. They did not name hidden rain before the
intervention, defined confounding neutrally, gave a concrete next action, marked
dripping as not recorded by the scene, and compared the revealed result with the
prediction while distinguishing supplied assumptions from uniquely identified
graphs. Each retained `can_continue=False`. An earlier tuning iteration still
named rain as a hypothesis and was corrected before this final probe set.

Final Nirvana probes produced a 44-word initial reply, a 53-word follow-up that
recognised outcome/population/time and asked for the missing comparator, and a
156-word response to an explicit detail request. Two intermediate tuning probes
re-asked population; the final tested follow-up corrected that behaviour.

Final Chrome verification passed for the guided prompt. In an isolated Portal
session, a real wrong-cause response did not name the hidden rain explanation;
a follow-up defined confounding neutrally without granting advancement or credit.
Nirvana's real Chrome replies were about 69 and 55 words; they acknowledged weekly
journeys, adult city residents, and six months, then asked for the missing comparison
rather than re-asking outcome/population/time. Its visible chat label is now
`Framing guide via ELM`.

The final current-code rerun passed 152 SDK tests in 6.557 s, eight Nirvana Python
tests, one Node UI-state regression, TypeScript checks, and the actual launch
script's web build. The local demo was restarted on port 4173, with Nirvana health
on 8011 returning 200. No `-Reset` was used and historical user traces were unchanged.
These targeted improvements address the observed cases; they do not guarantee
semantic grounding or no leakage on arbitrary inputs. No new frozen quality
qualification, formal guardrail closure, or participant study is claimed.

- [x] Freeze the human-review rubric and failure taxonomy before inspecting
  real-provider dialogue in
  [`causal-scene-quality-rubric.md`](causal-scene-quality-rubric.md).
- [x] Run representative scripted and real-provider trajectories; record
  whether the tutor moves the investigation forward instead of repeating it.
- [x] Run Chrome usability checks for mouse, keyboard, and text-equivalent
  interaction. The 2026-08-26 wide-screen check confirms no legacy radio
  checkpoint, accessible DAG checkboxes, an independent tutor transcript, and
  no intervention-result reveal before the declared action.
- [x] Run a narrow-screen Chrome usability check. At 390×844 on 2026-08-26,
  the hook's two action buttons initially overflowed their non-wrapping row;
  adding the existing Astryx `HStack` wrapping fixed the defect. A fresh
  mobile run proved a 390px document width, visible wrapped `Open the records`
  control, keyboard Space selection of both DAG arrows, enabled model commit,
  visible text alternative, and an ordinary scroll path to the tutor transcript.
- [x] Repair the free-text tutor regression found on 2026-08-28: ordinary
  learner messages are no longer forced into a `clarify` proposal. The strict
  proposal now carries a bounded, persisted natural-language `tutor_reply`
  grounded by the candidate's runtime-derived released resources/claims, while
  correctness and progression remain outside the model. The client now projects
  the learner message and `thinking` state before awaiting the local
  guarded-tutor response, then replaces that projection with the append-only
  server state. A configured ELM run produced a normal variable explanation
  with no fallback.
- [ ] Compare the existing immediate/delayed transfer evidence under the S11
  protocol before extending the workbench.

## 28. S24 — Learner depth and content adaptation

**Status:** `LATER`

- [ ] Define explicit, editable `overview`, `applied`, and `technical` user
  choices—not inferred learner labels.
- [ ] Author and review corresponding language, concept, notation, and scene
  variants.
- [ ] Record the chosen variant in the trace and keep the evaluation standard
  explicit.
- [ ] Qualify every variant separately before using it in a study claim.

## 29. Milestones

| Milestone | Required steps | Outcome |
| --- | --- | --- |
| Documented restart | S0 | one trustworthy empty implementation checkpoint |
| Stable agentic SDK core | S1–S5 | content, evidence, moves, replay, and one guarded Pydantic AI tutor |
| Headless agentic Causality M0 | S6–S8 | complete reviewed curriculum, transfer, and explainable learner state |
| Qualified tutor | S9 | measured grounding, quality, failure recovery, and observability |
| Demonstrable product | S10 | accessible renderer over the stable runtime |
| Interactive causal workbench | S20–S23 | deterministic scene and configuration-scoped technical qualification; participant comparison remains separate |
| Learner-adaptive workbench | S24 | explicit reviewed depth variants |
| Research-ready M0 | S11 | reproducible comparison and delayed-transfer export |
| Earned generic SDK | S12 | second domain proves portability |
| Causality M1 | S13 | executable causal-world extensions |

## 30. Decision log

| Date | Decision | Reason | Revisit when |
| --- | --- | --- | --- |
| 2026-08-22 | Restart from a documentation-only baseline instead of restoring the legacy bootstrap | implementation should follow the new contracts step by step without carrying old structure forward | only if lost behavior is later shown to be a required contract |
| 2026-08-22 | Keep hint and explanation text inline only in schema v1 | S1 needs a readable seed but not the source, claim, release, or resource registry owned by S2 | S2 migrates the seed to released `TeachingResource` records |
| 2026-08-22 | Pydantic models are authoritative; JSON remains authored data; JSON Schema is generated | one structural source of truth with readable distributable content | a non-Python implementation needs a different canonical source |
| 2026-08-22 | Replace schema v1 in one direction instead of supporting dual inline/resource forms | the repository has one seed and no released compatibility obligation; one representation prevents duplicate truth | an external released pack creates a real migration obligation |
| 2026-08-22 | Limit S2 resources to question, hint, explanation, and consequence | these are the only kinds used by the current seed | a real activity first needs another kind |
| 2026-08-22 | Treat review, release, locator, and rights fields as auditable declarations | the validator can check internal consistency but cannot prove reviewer identity, method existence, or legal permission | a second external release workflow requires a manifest/context |
| 2026-08-22 | Keep expert concept graphs and compact M0 indexes retrieval-only authoring artifacts | they reduce source-reading context, while released claims and located source references remain the teaching authority | a second source or distributed authoring tool needs a tracked generator, schema, and rights review |
| 2026-08-22 | Keep S3 to concrete choice evidence, deterministic evaluation, and a pure canonical move gate | attempts, policy metadata, generic payloads, and renderer conversion have no current implementation owner and would couple S3 to later steps | S4 adds events/attempts or S6 adds a second real evidence type |
| 2026-08-22 | Make one Pydantic AI tutor the primary pedagogical orchestrator in S5 | the product hypothesis is agentic tutoring; the LLM should interpret learner language and choose the next Socratic move | a complete S6 episode shows a smaller mechanism achieves the same learning and dialogue quality |
| 2026-08-22 | Preserve S1–S4 as a provider-independent safety kernel | learner evidence, released facts, replay, and progression must survive invalid output or provider failure | a stronger verified mechanism replaces a specific guardrail without weakening its invariant |
| 2026-08-22 | Keep tutor proposals minimal, hide runtime-only fallbacks, and derive canonical move, grounding, framing, and expected evidence in runtime | prompts or merely valid IDs cannot enforce relevance, selector authority, support budgets, reveal rules, retry, or progression | measured failures require a narrower proposal contract or additional verified guardrail |
| 2026-08-22 | Keep M0 factual teaching in released resources and framing in the fixed headless turn catalog; defer generated prose | claim IDs alone do not prove that generated prose is entailed by those claims | S9 demonstrates a real teaching need and a grounded-paraphrase evaluator meets a frozen threshold |
| 2026-08-22 | Use one named tutor before any multi-agent design | a single agent plus deep runtime contracts is the smallest implementation that tests the product hypothesis | a second agent has a concrete independent responsibility that cannot fit the tutor boundary |
| 2026-08-24 | Replace unreleased in-memory event schema 1.0 with 2.0 for S5 provenance | no persistence adapter or released event files exist, and one required payload shape is safer than optional provenance fields or a speculative migration layer | an external event consumer or durable store creates a compatibility obligation |
| 2026-08-24 | Represent the first complete episode as ordinary activities and evidence, not a separate episode state machine | the existing event reducer already owns ordering, evidence, replay, support, and progression; `ClassificationEvidence` adds only artifact/revision facts | a second episode reveals a shared protocol that cannot remain inside the current event/runtime modules |
| 2026-08-24 | Replace unreleased in-memory event schema 2.0 with 3.0 for typed classification evidence | no durable event store or external event consumer exists, so one clear response payload prevents dual replay rules | an external event consumer or durable store creates a compatibility obligation |
| 2026-08-22 | Build one complete episode before expanding M0 | a vertical learning loop is stronger evidence than more shallow activities | S6 exit gate passes |
| 2026-08-22 | Do not build causal world/tools in M0 | they are causality extensions, not generic SDK prerequisites | M0 evaluation and portability proof are stable |
| 2026-08-24 | Replace unreleased content schema 2.0 with 3.0 for concept-owned completion/M1 requirements | progress must be replay-derived from authored requirements, not a mutable profile field | external content-pack consumers require compatibility support |
| 2026-08-24 | Keep learner profiles as a read-only projection and restrict policy access to a bounded redacted view | failures and hypotheses should stay evidence-scoped rather than becoming opaque learner labels | a second policy needs another explicit field |
| 2026-08-24 | Use a standard-library local HTTP renderer and JSONL store for the first playable demo | it proves the stable headless boundary without a frontend framework or production persistence commitment | a second presentation/store implementation demonstrates a shared need |
| 2026-08-24 | Keep the demo offline by default and make the guarded tutor an explicit mode with one server-owned async runtime | the local control remains reproducible without credentials, while an OpenAI-compatible async client cannot safely move between per-request loops; both modes retain the same evaluator and runtime gate | a multi-user deployment establishes an ASGI/worker boundary or a second production transport has concrete needs |
| 2026-08-24 | Keep Logfire opt-in and content-free; do not run a provider without an explicit model choice | telemetry must not leak learner payloads, and a provider call can incur cost or external data transfer | the user authorizes a concrete provider/model qualification |
| 2026-08-24 | Keep Boolean causal worlds, DAG diagnosis, adjustment, estimation, and counterfactuals in a causality module | M1 truth logic is domain-specific and the fractions proof does not require it | a second domain shares a concrete extension need |
| 2026-08-24 | Permit one persisted bounded Socratic question from the tutor on legal question-oriented moves | a fixed turn catalog alone made free-text dialogue feel non-agentic; one-question validation preserves released factual content, deterministic scoring, replay, and progression authority | a grounded factual paraphrase or a second presentation implementation proves a stronger mechanism is needed |
| 2026-08-24 | Use explicit learner commitment and a compact read-only M0 route in the client | selection should be a deliberate, revisable learner act, and progress should explain the current curriculum location without becoming a second curriculum authority | a second content pack or presentation needs a shared, content-owned client manifest |
| 2026-08-24 | Use the scenario image as a large responsive context panel, rather than a small choice-side thumbnail | images should support noticing the situation without stealing width from the active question or implying an answer; the existing Astryx layout panel supplies this without a second styling system | user research demonstrates that the route and contextual media need independent resizing or another renderer needs a shared layout contract |
| 2026-08-24 | Keep scenario images as optional activity-owned, non-evidentiary local media | images make early prompts approachable without adding a second renderer curriculum, teaching claim, evaluator input, or tutor authority | another content pack needs richer media semantics or a content review workflow |
| 2026-08-25 | Require a guarded Pydantic AI model for the browser demo while retaining the evaluator and runtime as authorities | the approved workspace has no tutor-free learner route, but model output must not award correctness or progression | a future deployment introduces an approved service-level availability policy |
| 2026-08-25 | Use diagnostic success as route credit for targeted review, not as M0 completion | the diagnostic may reduce repetition in the local review route, but it does not create M0 scored evidence or a mastery claim | S19 gives credit and M0 completion visibly distinct labels and moves dialogue safeguards into the generic kernel |
| 2026-08-26 | Make future M0 interactions action-first rather than chat-first | feedback confirms that free conversation alone does not make the relevant causal structure visible; a bounded object gives the tutor something specific to elicit, inspect, and explain | S20 has reviewed and tested one accessible object without widening M0 into a generic tool platform |
| 2026-08-26 | Make a single deterministic causal scene and Socratic investigation director the next product slice | the product should go deeper than NotebookLM's broad feature set: a learner must manipulate a causal model, predict an intervention, and interpret the result with a tutor that can see this state | S20-S23 qualify the rain/umbrella/wet-pavement scene; this supersedes the earlier blanket M0 ban only for this bounded causality extension |
| 2026-08-26 | Treat the rain/umbrella workbench as a synthetic, unreleased causal scene | a familiar story can make association, common cause, DAG, and `do(X)` visible, but its exact world and result are authored teaching data rather than empirical evidence | causal-content review approves the scene record and released resources |
| 2026-09-05 | Repair the current Portal in place and retain the M0 concept backbone while moving toward fixed task-driven missions | review found mismatched scene dialogue, overstated response feedback, a mandatory diagnostic, rights metadata errors, and a broad static root; these are local reliability issues, not grounds for a full rewrite | local regression passes, then a fresh independently assessed mission justifies curriculum expansion |
| 2026-09-05 | Version revised full/delayed packs as 1.1.0 and preserve pre-repair packs and traces privately | changed evidence semantics must not silently reinterpret old learning events or historical qualification | an explicit, tested migration or separately approved study requires one |
| 2026-09-05 | Treat the umbrella vanilla tutor as a separate local experiment, not one of the frozen v1 study arms | a shared provider/model name does not preserve guarded prompt, content, or policy guarantees | a reviewed study amendment freezes and qualifies the exact comparison configuration |
| 2026-09-05 | Replace minimal local text prompts with guided context while retaining plain-text output and the legacy CLI switch | live review exposed early reveal, scene drift, verbose checklists, and re-asking answered fields; existing phase projection, attempt boundaries, and a concise prompt address these without a new runtime | targeted checks fail, a broader evaluation justifies another policy, or a frozen study needs a separately versioned baseline |
| 2026-10-14 | Implement S24a as one authored General/Medical worked lesson with isolated progress and memory-only preview | review the explanation-practice-challenge format and repair reliability before full M1 course or full-course adaptation work | user/expert review approves the sample or changes the next authoring scope |
| 2026-10-14 | Integrate fixed General/Medical contexts across the existing nine-topic Foundations route as S24b | user requested normal onboarding and complete Foundations, explicitly deferring M1; retain original General scoring/history and isolate Medical | expert review changes content or a later user request expands scope |

## 31. Next-action rule

2026-09-09 LAN demo maintenance: the example CLI supports explicit `--lan`
binding; default loopback enforcement remains tested. The umbrella launch adds
the exact LAN origin to Nirvana and documents the shared Portal state. Validation:
153 provider-independent SDK tests passed on Python 3.13.15, TypeScript check,
web build, and `git diff --check` passed. No commit was made; unrelated worktree
changes were preserved. Colleague-device connectivity still requires an actual
network check and this does not add multi-user session isolation.

The current sequence is unambiguous:

```text
S0 restart baseline
  -> S1 authoritative content contract: complete
  -> S2 released claims and teaching resources: complete
  -> S3 typed learner evidence, evaluation, and gated teaching move: complete
  -> S4 agent-ready append-only events and replay: complete
  -> S5 guarded Pydantic AI Socratic tutor: complete
  -> S6 one complete agentic causality episode: deterministic path complete
  -> S7–S8 complete M0 and explainable profile: implemented and tested
  -> S9 real-provider qualification: completed with the recorded ELM run
  -> S10 local playable renderer: implemented and tested
  -> S11 pilot decision: blocked until a real pilot
  -> S12 portability proof and S13 M1 causal-world seed: implemented and tested
  -> S19 generic dialogue and route hardening: done in worktree
  -> S20 causal-workbench design: approved worktree specification
  -> S21 deterministic M0 causal scene: done in worktree; historical evidence above
  -> S22 Socratic causal-scene director: done in worktree; historical evidence above
  -> S23 interaction quality: state/entry and guided-text checks, real-model probes, Chrome, and restart passed; participant comparison blocked
  -> S24a one-concept General/Medical lesson and local reliability: implemented and validated; expert review pending
  -> S24 full learner-depth adaptation: later; no runtime personalised curriculum generation
  -> real pilot: still blocked on S11 research-owner decisions
```

Do not treat provider-independent tests as a real-model qualification or a pilot decision.
