# Task specs and chat review QA — 9 September 2026

## Workflow repair verification — 11 September 2026

### Follow-up: concepts, worked examples and recommendations

- Four Node tests and twelve Python tests pass. The UI regression iterates all
  eight worked examples, validates every authored spec, provenance and route,
  exercises reasoning submission, and accepts one edited proposal while rejecting
  another without changing its original value. These are mocked provider tests.
- Explicitly authorised live ELM calls in a separate Chrome test tab: Oregon
  classified as effect; all seven worked fields populated. A reasoning question
  confusing lottery assignment with Medicaid enrollment received a relevant
  explanation, four problem-specific H3 concepts, and no Brief changes.
- The first live response omitted optional concepts. Concepts are now required
  (2–4 validated entries). A subsequent fresh prostate-MRI generation returned
  four specific concepts: single-source DG, shortcuts/invariance, label-preserving
  augmentation and environment-separated evaluation. Eight worked specs rendered.
- Chrome verified the fixed-position help overlay and Escape dismissal without
  disclosure reflow, and DG Copilot recommendation, reasoning and handoff on Route.
- Limitation: the MRI task was correctly classified as shift, but the model added
  a debatable `generation` context tag for augmentation. Tags remain provisional;
  they neither select specs nor drive destination recommendations. This small
  smoke test is not a classifier benchmark or evidence verification.

| Requirement | Evidence |
| --- | --- |
| Bridge between Task and Brief | All eight example routes in Node tests pass through Framing; direct Route navigation is gated until Continue. Chrome showed the MRI target, training/deployment mapping, concept explanation and application question. |
| Specific help for every spec | Tests assert authored help for each task field; Chrome showed question-mark disclosures alongside input labels. Training-environment help explicitly distinguishes data acquisition from GPU/Python. |
| Edit/Accept/Reject and continuing review | All eight tasks test edited exact values and a two-proposal batch; Accept writes only the edited value and Reject preserves original. Resolving the batch advances past handled items. Tests cover pause/resume, defer and finite pass completion. |
| Tool navigation | All eight tasks have source-linked destinations; tests verify contributing field IDs and rendered URLs, and every route has the human/ChatGPT/Claude fallback. Chrome showed DG Copilot, DomainBed and preparation guidance. |

Final provider-independent checks: 4 Node tests and 12 Python tests passed.
Node tests include existing stale-response, confirmation/copy and Markdown safety
coverage as well as the additions above. JavaScript syntax check passed.

With explicit user permission, a separate Chrome tab used the real configured ELM
for the fictional prostate MRI example. Observations:

1. Generation stayed on Task, recommended shift, populated the Brief and did not
   open chat automatically. Task Next opened Framing before Brief.
2. Chat requested two changes. Both stayed pending without modifying the Brief.
3. The target suggestion was edited to "Prostate segmentation for research-only
   volume measurement; not clinical diagnosis." before Accept. Both worksheet
   views displayed that exact value. Reject kept candidate predictors blank.
4. A conceptual follow-up about hospital/scanner versus GPU/Python returned a
   correct data-generating-environment explanation, no new proposals, and retained
   both reviewed values. Copy reported success; its preview contained the edited
   target and excluded the rejected predictor.
5. That live run exposed immediate re-questioning of a rejected field. The finite
   review now records handled field IDs and skips them within the pass, regardless
   of proposal order. The final all-task regression verifies this correction.
6. A fresh Chrome load verified the final larger default chat with a collapsed
   detail explanation, visible review controls, conversation area and composer.
   Prior Chrome checks verified pause/resume/defer and reasoning-note handoff.

The live test is one targeted integration probe, not proof of universal model
correctness, clinical suitability or learning outcomes. The final handled-item
correction was regression-tested with deterministic replies; no claim is made
that every task was live-tested. No Portal state, credentials or patient data
were changed or shared. Canonical demo assets were staged to both local outputs.

## Provider-independent checks

- 12 Python unit tests passed, including field-ID/UI consistency for every task,
  wrong-route field rejection, structured agent output and existing LAN behavior.
- 4 Node tests passed, including all four literature examples through Task,
  dedicated Brief and copyable Route; existing Accept/Reject, stale-response,
  Markdown and worksheet-isolation checks remain passing.

## Chrome with the configured live ELM

The final opt-in live classification smoke suite passed 10/10 cases: discovery,
policy, counterfactual, ordinary prediction, population effect, effect transport,
mediation, descriptive disparity, generation under shift, and an unclear request.
Expected transport/generation tags were present. The suite does not establish
generalisation accuracy; it checks a small set of explicit goals and boundaries.

Tested in separate QA tabs, without changing the user's existing worksheet.

1. CTPA Example 5 was classified as shift with generation context. It populated
   the synthesis target and proposed environment concerns while leaving the
   unspecified training environment blank.
2. A follow-up supplied training demographics and vendor imbalance. Proposals
   did not modify fields until a choice was made. Accept wrote training context;
   Reject retained the original values in the other specs. Copy excluded pending
   changes.
3. The initial follow-up revealed punctuation-only proposals: unchanged fields
   acquired an extra trailing period. Decision-history values are now JSON
   quoted, and chat receives an exact field-ID/value snapshot rather than
   ambiguous prose to copy from.
4. Retested the updated implementation with Example 7. ELM classified it as policy,
   generated its dedicated specs and left missing uncertainty blank.
5. Asked chat to propose exactly two edits: capacity of 100 places/year and mean
   earnings over 12 months. Both remained proposals until reviewed.
6. Accepted capacity; rejected the earnings specification. The capacity field
   changed to the accepted string; the objective retained its original string.
7. Asked a conceptual follow-up about policy choice versus prediction. There
   were zero new proposals; both fields retained their exact reviewed values.
8. Clicked Copy on Route. The UI reported success. The handoff included the
   accepted capacity and excluded the rejected earnings specification.

These are observed smoke-test outcomes, not guarantees that future model replies
will always be well classified, concise or free of unnecessary proposed edits.
The UI's review gate is deterministic; proposal quality remains model-dependent.
# Review and Route regression — 2026-09-11

Live Chrome/ELM test with a new fictional SMS appointment-reminder study:

- Generated an effect Brief; eligibility and follow-up remained unspecified.
- Proposed population and follow-up changes without applying them. Edited population to `Adults aged 18–75 (fictional eligibility)` before accepting; exact text reached both Brief editors.
- Rejected the 12-week follow-up: the original blank remained. Decisions appeared as centered muted notices below the reply.
- After resolving both proposals, the guided review focused on Assumptions & uncertainty with the model's assignment question, rather than an unrelated sequential field.
- A Ctrl+Enter follow-up about fictional patient-level randomization produced only an assumptions proposal. It preserved the accepted age range and did not resurrect the rejected follow-up.
- Accepting that proposal returned to the earliest unreviewed field, rather than declaring the pass complete merely because the model had jumped to the last field. Pause/resume also worked.
- Inspected the visible chat in Chrome: fixed header/input, one scrollable conversation/proposal/review body. Fixed a real-browser HTMLCollection `.at()` error that the lightweight DOM seam had missed; added a regression assertion.

Provider-independent checks cover all eight worked task/spec families, out-of-order review focus, exact Accept/Reject, finite review completion, task changes and obsolete responses, draft retry, Markdown safety, and task-scoped Route handoffs. Route candidates are not automatically selected merely because all fields are filled. Descriptive and ordinary prediction summaries ask whether causality is needed; specialist/tool fit remains conditional. `other` keeps its domain-expert/general-purpose-LLM referral.

This is a functional prototype test, not evidence of clinical validity, exhaustive model reliability, or downstream-tool compatibility.
