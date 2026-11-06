"""Read-only, replay-derived learner-profile projections."""

from dataclasses import dataclass, field
from typing import Literal

from pydantic import Field

from .contracts import Activity, ContractModel, StableId
from .evaluation import ClassificationEvidence
from .events import (
    AttemptClosed,
    AttemptStarted,
    LearnerMessageRecorded,
    LearningEvent,
    ResponseRecorded,
    SupportRequested,
    TeachingMoveSelected,
    replay,
)


TransferStatus = Literal["not_attempted", "rejected", "supported", "independent"]


class HypothesisObservation(ContractModel):
    """One tentative tutor hypothesis with its event-scoped evidence."""

    concept_id: StableId
    hypothesis_id: StableId
    move_event_id: StableId
    supporting_event_ids: tuple[StableId, ...]


class ExpectedEvidenceOutcome(ContractModel):
    """Whether the next attempt event matched one move's expected evidence."""

    move_event_id: StableId
    expected_predicate_ids: tuple[StableId, ...]
    next_event_id: StableId | None = None
    matched: bool = False


class ConceptProfile(ContractModel):
    """Explainable evidence summary for one authored concept."""

    concept_id: StableId
    attempt_count: int = Field(ge=0)
    accepted_event_ids: tuple[StableId, ...] = ()
    rejected_event_ids: tuple[StableId, ...] = ()
    revision_event_ids: tuple[StableId, ...] = ()
    hint_dependent_success_event_ids: tuple[StableId, ...] = ()
    transfer_status: TransferStatus = "not_attempted"
    hypotheses: tuple[HypothesisObservation, ...] = ()
    expected_evidence: tuple[ExpectedEvidenceOutcome, ...] = ()


class LearnerProfile(ContractModel):
    """The complete profile derived from one validated event trace."""

    session_id: StableId
    completed_concept_ids: tuple[StableId, ...]
    m1_ready_concept_ids: tuple[StableId, ...]
    concepts: tuple[ConceptProfile, ...]


class PolicyConceptView(ContractModel):
    """Bounded, redacted concept summary sufficient for future routing."""

    concept_id: StableId
    attempt_count: int = Field(ge=0)
    accepted_count: int = Field(ge=0)
    rejected_count: int = Field(ge=0)
    transfer_status: TransferStatus


class PolicyLearnerView(ContractModel):
    """A bounded view with no learner text, event IDs, or explanations."""

    session_id: StableId
    completed_concept_ids: tuple[StableId, ...]
    m1_ready_concept_ids: tuple[StableId, ...]
    concepts: tuple[PolicyConceptView, ...]


@dataclass
class _AttemptProjection:
    activity: Activity
    support_used: bool = False
    closed: AttemptClosed | None = None


def project_learner_profile(events: list[LearningEvent] | tuple[LearningEvent, ...]) -> LearnerProfile:
    """Project explainable learner evidence from a validated immutable trace."""

    history = tuple(events)
    state = replay(history)
    attempts: dict[StableId, _AttemptProjection] = {}
    concepts = {concept.concept_id: _ConceptAccumulator() for concept in state.concepts}

    for event in history:
        if isinstance(event, AttemptStarted):
            attempts[event.attempt_id] = _AttemptProjection(event.payload.activity)
            for concept_id in _activity_concept_ids(event.payload.activity):
                concepts[concept_id].attempt_count += 1
        elif isinstance(event, ResponseRecorded):
            attempt = attempts[event.attempt_id]
            for concept_id in _activity_concept_ids(attempt.activity):
                accumulator = concepts[concept_id]
                target = (
                    accumulator.accepted_event_ids
                    if event.payload.evaluation.accepted
                    else accumulator.rejected_event_ids
                )
                target.append(event.event_id)
                if event.payload.evaluation.accepted and attempt.support_used:
                    accumulator.hint_dependent_success_event_ids.append(event.event_id)
                if (
                    isinstance(event.payload.evidence, ClassificationEvidence)
                    and event.payload.evidence.revises_evidence_event_id is not None
                ):
                    accumulator.revision_event_ids.append(event.event_id)
        elif isinstance(event, TeachingMoveSelected):
            attempt = attempts[event.attempt_id]
            if event.payload.move.strategy in {"socratic_hint", "direct_instruction"}:
                attempt.support_used = True
            if event.payload.misconception_hypothesis_id is not None:
                for concept_id in _activity_concept_ids(attempt.activity):
                    concepts[concept_id].hypotheses.append(
                        HypothesisObservation(
                            concept_id=concept_id,
                            hypothesis_id=event.payload.misconception_hypothesis_id,
                            move_event_id=event.event_id,
                            supporting_event_ids=event.payload.supporting_event_ids,
                        )
                    )
        elif isinstance(event, AttemptClosed):
            attempts[event.attempt_id].closed = event

    for attempt in attempts.values():
        concept_ids = _activity_concept_ids(attempt.activity)
        if attempt.activity.is_transfer:
            status = _transfer_status(attempt)
            for concept_id in concept_ids:
                concepts[concept_id].transfer_status = _merge_transfer_status(
                    concepts[concept_id].transfer_status,
                    status,
                )

    for outcome in _expected_evidence_outcomes(history):
        move = next(
            event
            for event in history
            if isinstance(event, TeachingMoveSelected)
            and event.event_id == outcome.move_event_id
        )
        activity = attempts[move.attempt_id].activity
        for concept_id in _activity_concept_ids(activity):
            concepts[concept_id].expected_evidence.append(outcome)

    return LearnerProfile(
        session_id=state.session_id,
        completed_concept_ids=state.completed_concept_ids,
        m1_ready_concept_ids=state.m1_ready_concept_ids,
        concepts=tuple(
            accumulator.build(concept_id)
            for concept_id, accumulator in concepts.items()
        ),
    )


def policy_learner_view(profile: LearnerProfile, *, max_concepts: int = 12) -> PolicyLearnerView:
    """Return a bounded redacted view; learner text and trace IDs stay private."""

    if type(max_concepts) is not int or max_concepts < 1:
        raise ValueError("max_concepts must be a positive integer")
    return PolicyLearnerView(
        session_id=profile.session_id,
        completed_concept_ids=profile.completed_concept_ids[:max_concepts],
        m1_ready_concept_ids=profile.m1_ready_concept_ids[:max_concepts],
        concepts=tuple(
            PolicyConceptView(
                concept_id=concept.concept_id,
                attempt_count=concept.attempt_count,
                accepted_count=len(concept.accepted_event_ids),
                rejected_count=len(concept.rejected_event_ids),
                transfer_status=concept.transfer_status,
            )
            for concept in profile.concepts[:max_concepts]
        ),
    )


@dataclass
class _ConceptAccumulator:
    attempt_count: int = 0
    accepted_event_ids: list[StableId] = field(default_factory=list)
    rejected_event_ids: list[StableId] = field(default_factory=list)
    revision_event_ids: list[StableId] = field(default_factory=list)
    hint_dependent_success_event_ids: list[StableId] = field(default_factory=list)
    transfer_status: TransferStatus = "not_attempted"
    hypotheses: list[HypothesisObservation] = field(default_factory=list)
    expected_evidence: list[ExpectedEvidenceOutcome] = field(default_factory=list)

    def build(self, concept_id: StableId) -> ConceptProfile:
        return ConceptProfile(
            concept_id=concept_id,
            attempt_count=self.attempt_count,
            accepted_event_ids=tuple(self.accepted_event_ids),
            rejected_event_ids=tuple(self.rejected_event_ids),
            revision_event_ids=tuple(self.revision_event_ids),
            hint_dependent_success_event_ids=tuple(
                self.hint_dependent_success_event_ids
            ),
            transfer_status=self.transfer_status,
            hypotheses=tuple(self.hypotheses),
            expected_evidence=tuple(self.expected_evidence),
        )


def _activity_concept_ids(activity: Activity) -> tuple[StableId, ...]:
    return (activity.concept_id, *activity.covered_concept_ids)


def _transfer_status(attempt: _AttemptProjection) -> TransferStatus:
    if attempt.closed is None or attempt.closed.payload.status != "completed":
        return "rejected"
    if "transfer.independent" in attempt.closed.payload.evidence_predicate_ids:
        return "independent"
    return "supported"


def _merge_transfer_status(
    current: TransferStatus,
    new: TransferStatus,
) -> TransferStatus:
    rank = {"not_attempted": 0, "rejected": 1, "supported": 2, "independent": 3}
    return new if rank[new] > rank[current] else current


def _expected_evidence_outcomes(
    history: tuple[LearningEvent, ...],
) -> tuple[ExpectedEvidenceOutcome, ...]:
    outcomes: list[ExpectedEvidenceOutcome] = []
    for index, event in enumerate(history):
        if not isinstance(event, TeachingMoveSelected):
            continue
        next_event = next(
            (
                candidate
                for candidate in history[index + 1 :]
                if getattr(candidate, "attempt_id", None) == event.attempt_id
                and isinstance(
                    candidate,
                    (ResponseRecorded, SupportRequested, LearnerMessageRecorded, AttemptClosed),
                )
            ),
            None,
        )
        outcomes.append(
            ExpectedEvidenceOutcome(
                move_event_id=event.event_id,
                expected_predicate_ids=event.payload.expected_evidence_predicate_ids,
                next_event_id=None if next_event is None else next_event.event_id,
                matched=_matches_expected_evidence(event, next_event),
            )
        )
    return tuple(outcomes)


def _matches_expected_evidence(
    move: TeachingMoveSelected,
    next_event: LearningEvent | None,
) -> bool:
    predicates = set(move.payload.expected_evidence_predicate_ids)
    if "attempt.completed" in predicates:
        return isinstance(next_event, AttemptClosed) and next_event.payload.status == "completed"
    if "learner.revision" in predicates:
        return (
            isinstance(next_event, ResponseRecorded)
            and isinstance(next_event.payload.evidence, ClassificationEvidence)
            and next_event.payload.evidence.revises_evidence_event_id is not None
        )
    if "learner.new-action" in predicates:
        return isinstance(next_event, (ResponseRecorded, SupportRequested, LearnerMessageRecorded))
    return False
