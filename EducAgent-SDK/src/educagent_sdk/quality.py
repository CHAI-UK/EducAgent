"""Deterministic audits for a guarded tutor decision trace."""

from collections.abc import Iterable
from typing import Literal

from pydantic import Field

from .contracts import ContentPack, ContractModel, SemanticVersion, StableId
from .events import AttemptStarted, LearningEvent, TeachingMoveSelected, pending_turn, replay
from .runtime import TeachingCandidate
from .turns import resolve_tutor_turn


QUALITY_PROTOCOL_VERSION: SemanticVersion = "1.0.0"
QualityRisk = Literal[
    "grounding",
    "premature_reveal",
    "illegal_advance",
    "irrelevant_question",
    "repeated_question",
    "fallback_rate",
]


class TutorQualityCase(ContractModel):
    """A named risk case that a provider qualification must exercise."""

    case_id: StableId
    risk: QualityRisk
    description: str = Field(min_length=1, max_length=280)


FROZEN_TUTOR_QUALITY_CASES: tuple[TutorQualityCase, ...] = (
    TutorQualityCase(
        case_id="quality.grounding",
        risk="grounding",
        description="The selected turn must resolve exactly to released framing, resources, and claims.",
    ),
    TutorQualityCase(
        case_id="quality.premature-reveal",
        risk="premature_reveal",
        description="Direct instruction is accepted only when it is a current runtime candidate.",
    ),
    TutorQualityCase(
        case_id="quality.illegal-advance",
        risk="illegal_advance",
        description="Advance is accepted only when the reconstructed runtime candidates permit it.",
    ),
    TutorQualityCase(
        case_id="quality.irrelevant-question",
        risk="irrelevant_question",
        description="Question moves must use the current activity's released question resource.",
    ),
    TutorQualityCase(
        case_id="quality.repeated-question",
        risk="repeated_question",
        description="A question resource must not be repeated in an attempt without a separately reviewed policy change.",
    ),
    TutorQualityCase(
        case_id="quality.fallback-rate",
        risk="fallback_rate",
        description="Fallback use is measured separately from subject correctness and progression.",
    ),
)


class TutorQualityThresholds(ContractModel):
    """Frozen automatic acceptance thresholds for one candidate configuration."""

    max_grounding_violations: int = Field(ge=0)
    max_premature_reveals: int = Field(ge=0)
    max_illegal_advances: int = Field(ge=0)
    max_irrelevant_questions: int = Field(ge=0)
    max_repeated_questions: int = Field(ge=0)
    max_fallback_rate: float = Field(ge=0, le=1)


FROZEN_TUTOR_QUALITY_THRESHOLDS = TutorQualityThresholds(
    max_grounding_violations=0,
    max_premature_reveals=0,
    max_illegal_advances=0,
    max_irrelevant_questions=0,
    max_repeated_questions=0,
    max_fallback_rate=0.25,
)


class TutorQualityReport(ContractModel):
    """Replay-audited counts; this report never judges subject correctness."""

    protocol_version: SemanticVersion
    decision_count: int = Field(ge=0)
    fallback_count: int = Field(ge=0)
    fallback_rate: float = Field(ge=0, le=1)
    grounding_violation_count: int = Field(ge=0)
    premature_reveal_count: int = Field(ge=0)
    illegal_advance_count: int = Field(ge=0)
    irrelevant_question_count: int = Field(ge=0)
    repeated_question_count: int = Field(ge=0)


class TutorQualityAssessment(ContractModel):
    """A threshold decision over one deterministic quality report."""

    report: TutorQualityReport
    thresholds: TutorQualityThresholds
    qualified: bool
    failed_risks: tuple[QualityRisk, ...] = ()


def audit_tutor_trace(
    events: Iterable[LearningEvent],
    pack: ContentPack,
) -> TutorQualityReport:
    """Audit candidate legality and grounding from the immutable event trace."""

    history = tuple(events)
    replay(history)
    attempts: dict[StableId, AttemptStarted] = {}
    fallback_count = 0
    grounding_violations = 0
    premature_reveals = 0
    illegal_advances = 0
    irrelevant_questions = 0
    repeated_questions = 0
    question_resources_seen: set[tuple[StableId, StableId]] = set()
    decision_count = 0

    for index, event in enumerate(history):
        if isinstance(event, AttemptStarted):
            attempts[event.attempt_id] = event
            continue
        if not isinstance(event, TeachingMoveSelected):
            continue

        decision_count += 1
        payload = event.payload
        if payload.fallback_reason is not None:
            fallback_count += 1

        activity = attempts[event.attempt_id].payload.activity
        resolved = resolve_tutor_turn(pack, activity.activity_id, payload_to_candidate(event))
        if (
            payload.framing_catalog_version != resolved.framing_catalog_version
            or payload.framing_id != resolved.framing_id
            or payload.grounding_resource_ids != resolved.grounding_resource_ids
            or payload.grounding_claim_ids != resolved.grounding_claim_ids
            or payload.expected_evidence_predicate_ids
            != resolved.expected_evidence_predicate_ids
        ):
            grounding_violations += 1

        prefix = history[:index]
        try:
            pending = pending_turn(prefix, pack, request_id=event.request_id)
            is_current_candidate = any(
                candidate == payload_to_candidate(event)
                for candidate in pending.candidates
            )
        except ValueError:
            is_current_candidate = False
        if not is_current_candidate:
            if payload.move.strategy == "advance":
                illegal_advances += 1
            else:
                grounding_violations += 1

        if payload.move.strategy == "direct_instruction" and not is_current_candidate:
            premature_reveals += 1
        if payload.move.strategy in {"elicit", "clarify"}:
            if payload.move.resource_id != activity.question_resource_id:
                irrelevant_questions += 1
            elif payload.move.resource_id is not None:
                key = (event.attempt_id, payload.move.resource_id)
                if key in question_resources_seen:
                    repeated_questions += 1
                question_resources_seen.add(key)

    return TutorQualityReport(
        protocol_version=QUALITY_PROTOCOL_VERSION,
        decision_count=decision_count,
        fallback_count=fallback_count,
        fallback_rate=(fallback_count / decision_count) if decision_count else 0.0,
        grounding_violation_count=grounding_violations,
        premature_reveal_count=premature_reveals,
        illegal_advance_count=illegal_advances,
        irrelevant_question_count=irrelevant_questions,
        repeated_question_count=repeated_questions,
    )


def assess_tutor_quality(
    report: TutorQualityReport,
    *,
    thresholds: TutorQualityThresholds = FROZEN_TUTOR_QUALITY_THRESHOLDS,
) -> TutorQualityAssessment:
    """Apply the frozen automatic thresholds; human review remains separate."""

    failures: list[QualityRisk] = []
    if report.grounding_violation_count > thresholds.max_grounding_violations:
        failures.append("grounding")
    if report.premature_reveal_count > thresholds.max_premature_reveals:
        failures.append("premature_reveal")
    if report.illegal_advance_count > thresholds.max_illegal_advances:
        failures.append("illegal_advance")
    if report.irrelevant_question_count > thresholds.max_irrelevant_questions:
        failures.append("irrelevant_question")
    if report.repeated_question_count > thresholds.max_repeated_questions:
        failures.append("repeated_question")
    if report.fallback_rate > thresholds.max_fallback_rate:
        failures.append("fallback_rate")
    return TutorQualityAssessment(
        report=report,
        thresholds=thresholds,
        qualified=not failures,
        failed_risks=tuple(failures),
    )


def payload_to_candidate(event: TeachingMoveSelected) -> TeachingCandidate:
    """Recover a candidate-shaped value solely for deterministic validation."""

    return TeachingCandidate(
        candidate_id=event.payload.candidate_id,
        move=event.payload.move,
        selection_scope=(
            "runtime_only"
            if event.payload.move.strategy == "hold"
            else "tutor_selectable"
        ),
    )
