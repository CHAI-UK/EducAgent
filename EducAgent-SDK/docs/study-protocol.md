# Causality M0 study protocol v1 — historical specification; current build not enrolled

This document freezes the pilot comparison structure and outcome definitions.
It is a study protocol, not a learner-facing lesson or a runtime authority.
It does not authorize recruitment or analysis: the outstanding pre-pilot
decisions below must be approved by the research owner first.

## Current-build boundary — 2026-09-05

The four conditions below remain the v1 protocol specification, not a description of the current umbrella demo. The legacy `--unguarded-tutor` switch now selects guided local free-text replies with phase-visible context and same-attempt history; it is no longer the earlier minimal vanilla baseline. Neither local variant is one of these four arms. Supplying authored context does not automatically make this `m0.source-grounded-chat`, and a plain-text reply path does not inherit guarded-tutor qualification.

The full and delayed content packs are now version `1.1.0`. Earlier `1.0.0` qualification and assessment records remain historical evidence for their recorded configuration only. Pre-repair pack snapshots are retained under `.educagent-demo/packs/`; the original `.educagent-demo/causality-m0-full.jsonl` trace is preserved. Default traces for revised content are pack/version-specific, not an automatic migration of old scores.

The revised integrated/delayed binary items support only the declared association-versus-causation decision, not nine-concept transfer credit. Other full-pack concepts retain their own practice/transfer completion requirements, and these revised packs configure no M1-readiness requirements. The rain mission's written reflection is unscored; matching its supplied model is not evidence of identifying a unique causal graph. The optional diagnostic reuses practice items, so it must not be treated as an independent held-out outcome.

Before enrolling anyone on the revised Portal, approve a new study version or explicit reviewed amendment naming its exact content hashes/versions, tutor mode and prompt, provider/model, UI, assessment exposure rules, comparison, and analysis. Run any required fresh quality qualification. Do not relabel a vanilla or guided-local run as a frozen arm or pool the earlier baseline and changed-prompt results silently. The targeted 2026-09-05 live probes are development checks, not a new study arm or scientific outcome.

## Conditions

The exported arm manifests define four conditions:

- `m0.reading`: released materials without adaptive teaching;
- `m0.source-grounded-chat`: source-grounded chat with no progression authority;
- `m0.fixed-policy-control`: the versioned deterministic selector over the
  ordinary runtime candidate gate;
- `m0.guarded-pydantic-ai`: the constrained Pydantic AI tutor, after its named
  provider/model configuration has passed the frozen quality cases (the ELM
  record is `docs/evidence/elm-qualification.json`).

The selected arm, pack/evaluator/runtime/renderer versions, Python version,
and relevant dependency versions are recorded in every `StudyRunManifest`.
No transcript judge decides correctness, progression, completion, or M1
readiness.

## Frozen transfer tasks and scoring

The immediate task is the released integrated transfer activity
`m0-integrated-transfer.01` in `content/causality_m0_full.json`.

The delayed task is the released, new-surface assessment activity
`m0-delayed-transfer.01` in
`content/causality_m0_delayed_transfer.json`. It is administered after a
predeclared interval of 7 days (allowable window: 6–10 days) and is scored by
its deterministic classification evaluator. The delayed pack is separate from
the learning-session pack so it cannot be silently used as a teaching hint.

Primary outcome: independent correct delayed transfer. A response is
independent only when the assessment attempt closes with the replay-derived
`transfer.independent` predicate. Secondary outcomes are immediate independent
transfer, completed concept count, M1-ready concept count, accepted/rejected
response counts, support-dependent success, and the quality-protocol measures.

These are v1 operational measures, not established measures of comprehensive causal reasoning. Each current transfer probe is one binary classification; its declared concept coverage cannot establish mastery or independent understanding of nine concepts. The revised study must review assessment validity and use fresh tasks with explicit concept-specific rubrics before making broader transfer claims. Preserve the distinction between an independent response to this item and independent competence across the curriculum.

## Exclusions and missing follow-up

- Exclude a run only when its event trace fails replay validation, has a pack or
  manifest mismatch, or lacks an authenticated participant-consent record held
  outside this SDK.
- Do not manually repair event sequences or outcomes.
- Report missing delayed follow-up separately; do not treat it as a wrong
  response and do not impute a score in the primary analysis.

## Open pre-pilot decisions

Before enrolling a participant, the research owner must record a reviewed,
study-specific analysis plan. It must name:

- the primary contrast (guarded tutor versus which declared control arm);
- allocation, target sample, and eligibility/recruitment procedure;
- the statistical test or estimation method, effect/precision threshold, and
  rule for interpreting missing delayed follow-up;
- the concrete source-grounded-chat provider/model and learner-facing delivery
  used for that comparison arm; and
- the consent, data-retention, and any required ethics-review record held
  outside this SDK.

The guarded-tutor arm may use only a provider/model/build configuration with an applicable recorded qualification. The historical record names ELM `gpt-5.6-luna`; that name alone does not qualify a changed prompt, pack, policy, or renderer. A changed configuration needs the appropriate new qualification record before use in a study claim.

## Pre-pilot decision record

**Status:** `DRAFT — NOT APPROVED FOR ENROLMENT OR ANALYSIS`

The research owner completes and reviews this record before enrolling a
participant. It is intentionally blank: the SDK cannot choose a scientific
contrast, recruit participants, obtain consent, or approve a study on the
owner's behalf.

| Required decision | Research-owner record |
| --- | --- |
| Study owner and protocol version | `TBD` |
| Primary contrast | `TBD` — guarded tutor versus one declared control arm |
| Allocation, target sample, eligibility, and recruitment | `TBD` |
| Primary estimator or statistical test | `TBD` |
| Effect or precision criterion for retain / revise / reject | `TBD` |
| Rule for delayed follow-up missingness | `TBD` |
| Source-grounded-chat provider, model, and learner-facing delivery | `TBD` |
| Guarded-tutor provider and qualified model | `ELM gpt-5.6-luna`, or `TBD` with a new qualification record |
| Consent record, data retention, and required ethics review | `TBD` — held outside this SDK |
| Review approval (name, date, and durable record location) | `TBD` |

No participant enrolment, pilot analysis, or `retain` / `revise` / `reject`
decision is authorized until every row is completed and the final approval is
recorded by the research owner.

## Decision rule after the pre-pilot plan is approved

Before reviewing pilot outcomes, retain the guarded-agent design only if its
quality thresholds are met, its fallback and protocol results remain visible,
and the primary delayed-transfer comparison meets the approved, predeclared
analysis criterion. Otherwise record `revise` with the failing guardrail or
`reject` with the reason. The SDK exports evidence for that decision; it does
not infer the decision itself.
