# EducAgent Nirvana

For a fresh installation and deployment of all three experiences, use the
[repository deployment guide](../README.md). This document retains prototype
design and historical development context; local `output/` evidence and private
deployment records are intentionally excluded from the public repository.

**Status:** prototypes with S47 deployed for technical review on GCP HTTPS; full Medical Effect/Shift remote technical acceptance passed; no learning-effect evidence

**Internal codename:** Nirvana

**Last consolidated:** 2026-10-27

EducAgent has two independent entry routes and a specialist layer. **Portal** introduces causal reasoning to the public and beginners. **Nirvana** is designed to help researchers who know their problem but are new to causal methods prepare an understandable, reviewable **Causal Research Brief**. Specialist tools such as the Domain Generalization Copilot retain responsibility for their own causal frameworks and downstream reasoning.

## Current conclusion

Portal now contains six normal course packs: General and Medical versions of
Foundations, Effect of an intervention, and Robust prediction or generation.
Foundations `1.8.0` has nine concepts, nine explanation pages and 28 activities
per context, including nine objective-specific final questions. Effect `1.4.0`
and Shift `1.4.0` each have four concepts, four explanations
and 16 activities per context: eight topic quiz/challenge items,
four operational experiment stages and four
final questions. All courses share Quiz -> Explanation -> Challenge and profile
switching. Default open module access is browsing permission, not learning
credit. Historical M0 `1.1.0` packs and traces remain unchanged and are not
migrated into the new packs. Foundations `1.2.0` through `1.5.0` outputs and evidence
also remain frozen. Earlier M1 `1.0.0` and `1.1.0` packs/traces remain separate
without migration into `1.2.0`; the original `0.1.0` M1 seed files remain available.

S47 is the current GCP release. It repairs guided-practice Tutor openings that
used the scored interpretation before any test had run, reusing the released
prediction guide before the check and restoring the scored prompt after the
recorded comparison. Content versions, mathematics and unlimited dialogue are
unchanged. Local Medical Effect Chrome verified a fresh corrected opening;
VM build, manifest/preflight and localhost/public checks passed. The actual
S46 image and a new stopped-state Portal backup remain available for rollback,
with Caddy/TLS and the original volume preserved. Actual GCP Chrome completed
all 16 activities in each Medical M1 course, including four practices, four
finals and the separate final trace in each course. Saved practice/reload, completed-final review,
mobile scrolling and fictional Tutor dialogue passed. General received targeted
profile isolation, saved-practice restoration and a fresh opening check; it was
not rewalked end to end in S47. See the
[S47 acceptance record](../output/gcp-s47-20261027/verification.md).
This technical acceptance does not renew causal-expert approval.

The 1.7.0 revision keeps the model-identification Quiz and changes the
World/data/model Challenge to distinguish recorded measurements from the actual
device and its processes. General and Medical use separate versioned progress;
1.6.0 packs and records are retained without credit migration. This assessment
revision is included in S46 RC1; it was not present in S44.

The S46 revision reviews each Quiz/Challenge pair for a different facet
of the same objective and makes the required teaching visible in the default
definition/hook. Foundations 1.8.0 and M1 1.4.0 preserve quizzes, final questions,
interactive practices and the curriculum. Previous 1.7.0/1.3.0 packs remain frozen,
with separate progress and no migrated credit. S46 RC1 was deployed on
27 October at `https://learn.chai.ac.uk/`, retaining Caddy, private configuration,
Secure session cookies, the named Portal data volume and the actual S44 image
for rollback. Targeted Chrome checks cover Learning, Portal and Nirvana;
the [remote acceptance record](../output/gcp-s46-20261027/verification.md)
separates exact browser/live-model scope from API and health checks. This is
not a repeat of every course walkthrough or renewed expert approval.

S43 applies the same guided presentation to both Effect profiles, with one
control per practice and computed starting-group counts alongside relevant
differences. Stable App-owned drafts retain settings and text across responsive
layout changes and introduction exit/resume; reload restores saved artifacts
only. Historical Effect 1.2.0 packs/progress remain separate. The curriculum,
calculation and scoring contracts and unlimited Tutor dialogue are unchanged.
The SDK roadmap records complete local Effect acceptance and targeted authorised
GCP HTTPS acceptance separately, including live fictional Tutor checks in both
profiles. S43 was deployed with the earlier image and learner-data backup retained.

S44 (23 October) changes only the Learning entry's CHAI colour alignment and
EducAgent-first resource/navigation order, retaining light/dark preferences.
It was deployed on the same GCP HTTPS service; Portal/Nirvana code and course
content are byte-identical to S43. See the
[Learning acceptance record](../output/learning-s44-20261023/verification.md).

S42 revised the local General/Medical Shift route: topics 1-3 Quiz/Challenge,
prediction practices 1-3, topic 4 Quiz/Challenge, generation practice 4, then
four final items. Concrete stories and one relevant control guide each practice.
The four-concept curriculum, objectives, activity/answer IDs, deterministic
model and evaluator truth are preserved; presentation order changes. Optional
authored guide metadata and phase-visible browser/Tutor projection are new,
without a Tutor dialogue quota. S43 selects introduction and illustration
catalogs `1.3.0` and `1.4.0`. Historical Shift 1.2.0 packs/progress remain unchanged,
without migration to 1.3.0. S42 was accepted locally without a standalone archive;
the authorised S43 release combines both guided M1 revisions. Installed-target
acceptance is recorded separately in the SDK roadmap. Technical changes are not
renewed expert approval or evidence of learning effectiveness.

S33 revises all four M1 context packs in new `*_1_2_0.json` files, using short
definitions/examples, optional detail, plausible question-matching choices and
separate authored rejection prompts. Course concepts, objectives, 16-activity
structure, evaluator contracts and experiment mathematics are unchanged. The
introduction catalog is separately versioned `1.1.0`. This applies the clarity
standards from the Foundations review; it does not claim Kurt/Damian reviewed
the new M1 revision or implement Damian's proposed curriculum reorganisation.

S26 supersedes S25's fixed-table M1 practice. Learners commit typed parameters
and an unscored prediction, run a server-owned deterministic model, change
settings and rerun, then record a comparison after two distinct configurations
before attempting the existing scored check.
Historical Effect 1.2.0 retains `Save my prediction`, `Run experiment` and
`Record my comparison`; both current M1 routes use `Start practice`, `Save my prediction`,
`Run this test`, `Change one setting and test again` and `Record my comparison`,
then opens the scored interpretation check. Saved configurations and results
can be compared together. Exit/resume does not reset progress or award credit.
These unscored artifacts do not award completion by themselves. Effect
experiments distinguish source assignment, target weights and analysis. Robustness experiments vary
cue, measurement and missing context, and compare prediction rules with actual
template-generated reports and withholding/coverage tradeoffs. Source-faithful
reporting is distinct from agreement with the teaching model's preset reference.
That reference is not a real clinical review. This adds no LLM report
generation, arbitrary code execution or real clinical data. Free Tutor dialogue
has no turn quota. The later Kurt/Damian Foundations revision retains its
curriculum while clarifying questions, compact explanations and inline feedback.
Current S39 guided policy `1.9.0` (Tutor `1.15.0`, prompt `1.16.0`, runtime `0.10.0`) retains
different-case conceptual help before a final
answer, withholds learner-copied current final wording from the model, and recorded-feedback discussion after submission; it does not grade or
advance and is not a guarantee against every semantic answer leak.
The S33 follow-up supplies public Shift quantity definitions so the Tutor can
distinguish a reference target from its noisy measurement and correct conflicting
earlier chat. Unsubmitted final-assessment openings and `Explain this concept`
now use the same concept-only context instead of the current item's accepted
explanation. The support button/events remain, and the repair does not establish
complete semantic non-leakage. It changes neither experiment mathematics nor
the schema, scoring or unlimited-dialogue contract; it adds no conversation gate.

S34 adds an internal typed `AdjustmentExampleReply` for generated adjustment
analogies. Its role header and explanation clauses reuse one assignment of
treatment, outcome, pre-treatment common cause and target; grouping therefore
does not silently substitute another role label. A safe replay-derived active
example anchor survives beyond the twelve-message recent context. Chat and
unanswered-final Explanation share the history filter; intentional new examples
are announced explicitly, and ordinary text answers remain available.
Instructions separate the hypothetical example from names and numerical results
on the active experiment page. This is not a semantic guarantee for arbitrary
prose or scientific approval. No curriculum, evaluator, profile, dialogue-quota
or Nirvana research-state change is introduced by S34. S35 additionally repairs
repeated explanation, guided-request deadlines, explicit one-question preference,
long-label rendering and mobile/input recovery. First/new example roles are
readable details rather than repeated machine headers. Historical S35 runtime
`0.9.1` retained old replay, with no scoring or conversation-quota change. Its acceptance evidence is
in `../output/portal-s35-20261019/review.md`; it is not scientific qualification.

The Tutor remains visible at completion and supports temporary topic review;
normal progress remains separate by module/context/version. Developer preview
also uses temporary state. S39 makes the shared General/Medical umbrella mission
a bounded dynamic practice: select one of three declared Boolean hypotheses,
commit an unscored prediction, run the existing umbrella-setting intervention,
and compare the computed hypothesis outcome with an independently fixed reference
world. At least two distinct hypotheses must be tested before the final revision.
Only the final graph representation of the disclosed reference assumptions is
evaluated; predictions and reflections do not earn correctness. Matching an
intervention result does not identify a unique DAG. The nine concepts, 28
activities and other scored questions are unchanged. Historical 1.5.0 packs and
prewritten scene replay remain frozen; their progress is not migrated to 1.6.0.
The later DAG lesson reuses this example, and trace review has a fixed-size scrolling chat pane. Source links
and rights metadata remain in place. Course material retains `author_draft`
metadata and requires scientific review, although lesson pages no longer repeat
that status caption. S26 passes all 246 provider-independent Python tests
(39.624 s), six Node editor tests, schema/M1 generator freshness and web
type/build checks. Targeted Chrome operations passed in all four M1
course/context variants: assignment and target-weight changes, cue reversal,
report withholding and measurement error. Medical robustness received three
consecutive live Tutor replies and passed incorrect-answer recovery with the
checked artifact frozen. This does not claim a Chrome walkthrough of every
activity or scientific/learning-effect approval. See the
[S26 acceptance record](../EducAgent-SDK/output/portal-s26-20261015/verification.md).
Scientific review and learner evaluation remain pending. Historical S25 local technical checks passed:
230 Python tests, six Node editor tests and web/schema/build checks passed,
followed by 24 focused tests and a schema recheck after final refinements.
Targeted Chrome checks covered the question-first flow, three live novice Tutor
turns, M1 context/practical/final samples, an ordinary Medical umbrella mission,
completion-page Tutor and bounded trace scrolling. Not every activity was
walked through in Chrome; these checks are not scientific approval, full
curriculum qualification or learning-effect evidence. See the
[S25 acceptance record](../EducAgent-SDK/output/portal-s25-20261015/verification.md)
and [Portal conclusion](docs/portal-conclusion.md). Nirvana state and its
research-framing boundary are unchanged.

An empty chat shows a local welcome message with the Nirvana avatar, introducing
research-question clarification, causal concepts and Brief preparation. It
reappears after chat reset, without an ELM request or added model history.

Nirvana uses its own transparent seated mascot in the chat launcher, panel and
beside its name in each assistant reply,
stored at `demo/assets/nirvana-mascot.png`. The Portal tutor retains its original
avatar. The normal demo staging copies this asset with the Nirvana source.

Task-first generation: `/api/classify` returns only task and reason. Task Next
unlocks immediately; `/api/frame` prepares the selected task's Brief and concepts
in the background without moving the user back. Pending/ready/error state and
draft-only retry are visible. Manual edits/reset/task changes discard obsolete
responses. The `other` exit skips drafting and offers referral. The local API
handles simultaneous requests so obsolete work does not serialize new requests.
This improves time-to-classification, not necessarily total generation time or
cost: the normal path now has two model calls. See docs/task-latency-profile.md.

11 September workflow repair: Problem → Task confirmation → Framing (extracted
mapping, question-specific AI concepts and an unscored reasoning/application
note with an explicit ELM discussion button) → Brief → Route. Every Brief spec has hover/focus help. Chat
suggestions are editable before Accept; Reject keeps the original. A finite
item-by-item review supports confirm, defer and pause/resume, without unattended
ELM calls or a claim of scientific validity. Route includes a source-linked tool
directory for all eight tasks, a rule-based recommendation with reasons, input-preparation guidance and a manual
methodologist/ChatGPT/Claude fallback. No downstream tool is embedded or executed.
These statements supersede the older interaction descriptions below; see
[task specs](docs/task-specs.md) for the graph, limits and source mappings.

Examples 1–8 now use medical and health-study scenarios: Medicaid effects, MRI
domain shift, pain-treatment mediation, obesity trends, Alzheimer's biomarker
discovery, sequential depression treatment, brain MRI counterfactuals and EHR
readmission prediction. Each loads a paper-anchored teaching question and provenance.
After AI categorisation, a matching task receives the authored worked specs;
editing the question restores ordinary AI drafting. Paper facts, teaching choices
and unresolved decisions are explicitly distinguished. Earlier question-only and
synthetic preset descriptions are superseded.
Example 9 remains unchanged. See docs/task-specs.md for source-to-task mappings.

Accept/Reject decisions appear as compact, centered muted-gray notices beneath
the assistant response, not user bubbles. Exact JSON-quoted decisions remain in
model history but are not displayed. After resolving all proposals, a local hint
points to the next empty spec (excluding rejected specs), with permission to leave
it unknown. This does not trigger an automatic ELM request. The agent prioritises
one meaningful missing spec when the conversation continues, without re-asking
answered questions or turning every conceptual answer into an intake question.

The compact chat composer places Send to the right of the Message textarea, with shortcut guidance and request status below. Keyboard shortcuts and proposal/processing send locks are unchanged.

Example 9 contains the user-provided CTPA contrast-to-non-contrast synthesis question verbatim. It loads only the question, clears prior fields/chat, and waits for Next to call AI categorisation. It is labelled user-provided rather than synthetic; no training coverage or metadata availability is invented as a preset.

Problem supports Markdown source editing with an Edit/Preview switch. Preview uses the same safe CommonMark renderer as chat; ELM still receives the original Markdown text. Toggling preview does not alter the question, Brief, or conversation. Start again returns to editing mode.

Chat resizing: drag the top-left corner handle to adjust width and height, or focus it and use arrow keys. Dimensions are constrained to the viewport. Closing preserves the size. The separate expand/restore button has been removed. No resize library is required.

Assistant replies render CommonMark (paragraphs, lists, emphasis, links, blockquotes and fenced code); user text and proposed diffs stay plain text. Raw HTML and unsafe link protocols are disabled; Markdown images do not load. The prompt encourages short paragraphs separated by blank lines. `chat-markdown.mjs` reuses Portal's installed micromark parser and is bundled locally (no CDN or new dependency):

```powershell
rtk node ../EducAgent-SDK/node_modules/esbuild/bin/esbuild chat-markdown.mjs --bundle --platform=neutral --main-fields=module,main --format=iife --global-name=NirvanaMarkdown --minify --outfile=demo/markdown.js
rtk node --test tests/test_chat_markdown.cjs tests/test_demo_ui.cjs tests/test_learning_theme.cjs
```

Chat keyboard shortcut: Ctrl+Enter sends; Enter and Shift+Enter insert new lines. Sending remains disabled while a request or unresolved edit proposals are pending. IME composition does not trigger the shortcut.

Brief fields, including their mirrored and proposal editors, have a visible
2,000-character limit. Oversized imported/programmatic drafts remain intact;
the interface explains any field, 16,000-character context or 32 KB UTF-8 request
overflow before sending. It never truncates the Brief to fit. Requests include
up to twelve recent discussion messages, omitting older messages from that
request if needed for its byte limit; the interface reports this and keeps the
full on-screen discussion. Failed requests restore the message for retry without
also placing that failed message in completed conversation history. These are
browser-memory safeguards, not persistence or provider-side exactly-once calls.

Current chat contract: initial Problem classification drafts the worksheet; subsequent chat only proposes field-level changes. Each proposal displays Before/Proposed text with Accept/Reject. Only accepted edits enter the Brief or handoff; resolve proposals before sending the next message. Manual worksheet edits invalidate pending proposals. Route now includes a task-specific “Where Causality can be applied” summary. Copy works for unreviewed drafts too, retaining their explicit draft status; confirmation is optional, not a copy gate. No text is automatically sent to DG Copilot.

Task switching preserves each task's working fields for the current question, so returning to the recommended task restores its generated Brief. Starting again, loading another example, or regenerating a question clears cached task drafts. The CTPA contrast-to-non-contrast synthesis question was checked with live ELM in Chrome through Problem → Task → Brief; the recommended shift Brief was populated and retained after Next. This targeted check does not establish the cause of every empty-brief report.

Problem → Next opens Task with a categorising indicator. Nirvana highlights its recommended task first; the user confirms with Next before entering Brief. Classification failures offer retry or manual task selection. The framing guide opens only through the bottom-right **Chat with Nirvana** mascot button, never automatically. It uses left/right chat bubbles and an expand/restore control; closing or Escape preserves conversation and in-flight requests. Manual Brief edits still clear chat. Internal edit counters protect against stale responses but are not displayed or included in handoff prompts. The popup uses existing components with no new dependency.

- Portal and Nirvana belong to one learning offer; neither is a prerequisite for the other.
- Portal retains the SDK's nine-concept M0 backbone and offers authored General/Medical Foundations and two M1 routes, with comparison investigations and objective-specific final questions. These fixed courses do not generate a curriculum at runtime or establish validated learning transfer.
- Nirvana accepts new natural-language questions through **Generate Brief with AI**. Shared ELM classifies the task and returns structured editable fields. Follow-up answers update the draft; unknowns remain blank. A diagnostic teaching loop, teach-back assessment, and item-level provenance are not implemented.
- The proposed first causal-method branch is an intervention-effect question. Prediction under data/domain shift has a preparatory route to DG Copilot; this is not a specialist integration or a claim that Nirvana performs DG reasoning.
- The main flow uses a small structured ELM framing agent, not a final tutor policy. It updates provisional Brief fields but cannot establish the truth of assumptions. The previous text-only `/api/chat` remains available for compatibility.
- The repaired worksheet starts blank, separates synthetic examples from user-entered content, and requires explicit confirmation before copying a handoff. Editing invalidates confirmation and clears the old chat context; refresh still loses this browser-session worksheet.
- Technical checks, polished outputs, and a runnable demo do not establish usability, learning, comparative value, CHAI acceptance, or funding eligibility.

Earlier 2026-09-05 checks passed the repaired worksheet and scene flow, but exposed verbose Nirvana checklists and Portal answer leakage/synthetic-world drift. The guided-context repair keeps plain text while supplying Portal only phase-visible scene material and same-attempt history; Nirvana's `Framing guide via ELM` focuses on the next genuinely missing field and carries forward explicit user answers. Targeted live probes and final Chrome checks passed, with concise ordinary replies and more detail on request. The final suite passed 152 SDK tests, eight Nirvana Python tests, and one Node UI-state regression; TypeScript/build checks passed. The local demo is restarted on 4173 with health on 8011, without resetting user progress. These are targeted observations, not a semantic guarantee, learning evidence, or new qualification.

## Read only these five documents

2026-09-09 implementation checks: 10 provider-independent Python tests and the Node UI-state regression cover structured generation/refinement, unknown fields, example isolation, stale responses, failure retention, and confirmation/copy state. Live ELM and Chrome checks used a user-authorised CTPA synthesis/domain-shift question: task selection, field population, follow-up preservation of unknown training/reference availability, and the current DG preparation preview worked. This is a targeted integration check, not a guarantee of scientific correctness or DG suitability for image synthesis. No Portal progress was reset.

| Order | Document | Purpose |
| --- | --- | --- |
| 1 | [README.md](README.md) | Two-minute conclusion and current capability boundary |
| 2 | [Portfolio conclusion](docs/portfolio-conclusion.md) | Parallel routes, gains/losses, ownership, and external decisions |
| 3 | [Nirvana conclusion](docs/nirvana-conclusion.md) | Intended user, Brief, handoff, and smallest product test |
| 4 | [Portal conclusion](docs/portal-conclusion.md) | Public zero-to-one learning, task-driven direction, and evidence |
| 5 | [Roadmap](ROADMAP.md) | Current repairs, next bounded deliverables, and validation gates |

Read the first two for a direction discussion; use the relevant track conclusion for its review. Do not create another parallel planning document.

## Current state and next decision

| Area | Current implementation or decision | Still needed |
| --- | --- | --- |
| Portfolio | Two entry routes and specialist ownership are the working direction | Supervisor/CHAI review, named owners, and capacity decision before public commitment |
| Portal | Six versioned General/Medical course packs, shared question-first learning flow, parameter-driven M1 experiments, final questions and completion-page Tutor review; S26 targeted Chrome acceptance passed in worktree | Obtain scientific review, then freeze the mode/build and assessment design before a study |
| Nirvana | Manual worksheet, task-specific Brief views, and separate guided framing chat | Review the framing boundary and DG handoff with Damian/Kurt; test user understanding separately from artifact quality |
| Release | Local prototype only | A reviewed public asset set, rights/privacy/accessibility/security checks, and an authorised participant or deployment route |

The authorised local implementation can proceed without waiting for a public-product decision. It does not authorise participant recruitment, processing real unpublished research questions, or external deployment. Portal's S26 acceptance and outstanding scientific course review remain separate from Nirvana's draft, confirmation, and handoff workflow.

## Local prototype

### Private Linux shared-server package

The authorised shared-server review package uses Docker Compose and a single
loopback-published entrance on port 9090 for Learning, Portal and Nirvana.
The S39 release identifier is `educagent-server-20261021-s39`; its current
Foundations packs are 1.6.0. Keep the S38 release and matching state for rollback;
older Foundations completion is retained but not migrated to the new version.
See [the deployment guide](deploy/README.md) for packaging, private ELM
configuration, SSH/IT-proxy access, health checks, backups and updates.
The optional explicitly requested private archive includes the existing ELM
configuration; the shareable archive does not. Neither includes local learner
history or textbook PDFs. Nirvana's deployment configuration selects a
same-origin API while ordinary Windows startup retains port 8011.
Portal now isolates runtime state and preferences by anonymous browser session;
same-browser tabs share a record, while other browsers have separate progress
and resets. This is not account authentication, cross-device sync, scientific
approval, or a completed target-server deployment. Keep one process per data
directory and place the service behind the approved access boundary.

For an explicitly authorised colleague demo on the same LAN, run the umbrella
`restart-demo.ps1 -LanAddress <your-current-Wi-Fi-IPv4>`. This preserves Portal
progress, opts both servers into IPv4 LAN listening, and adds only that exact
web origin to Nirvana CORS. Normal startup remains loopback-only. Run the umbrella
`enable-lan-firewall.ps1` from an administrator PowerShell once to allow TCP
4173/8011 from the Wi-Fi local subnet. Remove the `EducAgent-LAN-Demo` firewall
rule to undo that exception. Network client isolation may still prevent access.
Use `http://<your-current-Wi-Fi-IPv4>:4173/`; update the launch address if DHCP
changes it. This remains an unauthenticated demo: Portal progress follows each
anonymous browser cookie, and Nirvana drafts remain in each browser. No accounts
or public hosting are added. A retained session cookie can resume after reload
or restart; clearing it starts a new record.

On Windows, double-click `restart-demo.cmd` in the umbrella EducAgent folder
to restart both local services on ports 4173 and 8011. Keep the server window
open; it displays build output and errors. The restart preserves Portal progress
and refuses to stop a listener belonging to another application.

From the canonical umbrella root:

```powershell
rtk powershell -NoProfile -ExecutionPolicy Bypass -File C:\Workspace\EducAgent\start-demo.ps1 -Port 4173
```

The command builds and serves `Learning Resources`, `/portal/`, and `/nirvana/`. Portal's legacy `--unguarded-tutor` switch now selects guided local free-text, not the old vanilla prompt or a qualified guarded policy. Nirvana's separate chat endpoint listens on `127.0.0.1:8011`. Both read `BASE_URL`, `MODEL`, and `ELM_API_KEY` from the shared SDK configuration; credentials are server-side.

The launch stages public entry files, the Sources & rights notice, and built Portal/Nirvana/media assets in the umbrella `.demo-site/` directory and serves that public-only set. Textbook authoring files, development configuration, and progress traces are not copied there. The HTTP handler also restricts public paths and asset types; this technical boundary is not public-release or copyright clearance.

Nirvana sends the question on Generate, or the current Brief, new message and up to 12 prior dialogue messages on Send. `/api/frame` returns structured task/fields/reply output and updates the provisional worksheet. Handoff prompts use current fields and require review before copying. There are no external action tools or conversation persistence. Use only content approved for transmission to ELM. Do not pass `-Reset` unless intentionally clearing Portal progress.

API POST requests require `application/json`. Before invoking a model, the
server rejects a present Origin unless it is an allowed local/explicit LAN
origin or matches the request's public Host for same-origin hosting. The TLS
reverse proxy must preserve that Host, including a non-default port. Requests
without Origin remain available to local command-line checks. This boundary
does not add authentication or replace the restricted deployment/access policy.
The Learning entry's theme switch still works when browser storage is blocked;
only remembering the preference is then unavailable.

## Documentation consolidation

The earlier 24 process documents were replaced by this README and the three conclusions. The pre-consolidation snapshot at `work/pre-consolidation-2026-09-03.zip` is recovery material, not an active source of project status. The original presentation is retained as source material; Markdown conclusions own the current product direction.

## Boundaries that remain

1. Researchers and domain experts retain epistemic ownership. Suggestions and confirmation are not causal evidence.
2. The Brief is the intended scientific artifact; handoffs derive from one reviewed revision. Browser-session state is not durable storage.
3. A complete-looking artifact and a user's understanding must be evaluated separately.
4. Portal evidence cannot substitute for Nirvana evidence, or vice versa.
5. Unobserved value is not a product capability; a planned study is not permission to run it.
6. Colleague projects may overlap in explanation, but specialist causal policy has an explicit owner. Nirvana does not copy DG deployment logic.
# Current task/specification update — 9 September 2026

The demo now supports eight task-specific Briefs plus an unclear/other route:
effect, mediation, shift, discovery, policy, counterfactual, prediction and
description. Each has dedicated specs and a tailored handoff. ELM returns a
classification reason and optional context tags. Examples 5–8 include source
links to published research; their prompts are explicitly hypothetical adaptations.
See [Task specifications and classification rules](docs/task-specs.md) for the
field matrix, literature basis, review behavior and opt-in live smoke tests.
