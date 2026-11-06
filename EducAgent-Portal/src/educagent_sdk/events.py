"""Append-only learning events, commands, and pure replay."""

from collections.abc import Iterable
from typing import Annotated, Literal, TypeAlias

from pydantic import Field, StringConstraints

from .contracts import (
    Activity,
    CausalScene,
    Concept,
    ContentPack,
    ContractModel,
    NonEmptyText,
    SemanticVersion,
    StableId,
)
from .causal_scene import (
    CausalSceneAction,
    SceneDialogueJob,
    CausalSceneSnapshot,
    apply_scene_action,
    dialogue_job_for_scene_focus,
    initial_scene_snapshot,
    legal_scene_focus_ids,
)
from .evaluation import (
    EVALUATOR_VERSION,
    CausalSceneEvidence,
    ChoiceEvidence,
    ClassificationEvidence,
    Evaluation,
    LearnerEvidence,
    evaluate_evidence,
)
from .experiments import (
    ExperimentAction, ExperimentSnapshot, apply_experiment_action,
    experiment_ready_for_assessment, initial_experiment_snapshot,
)
from .release import validate_release
from .umbrella_simulation import simulation_ready
from .runtime import (
    SelectorKind,
    SELECTOR_VERSION,
    SupportRequestKind,
    TeachingCandidate,
    TeachingMove,
    TeachingStrategy,
    gate_reused_direct_instruction,
    message_teaching_candidates,
    runtime_hold_candidate,
    scored_teaching_candidates,
    support_teaching_candidates,
    validate_candidate_membership,
    validate_runtime_hold,
)
from .turns import (
    FRAMING_CATALOG_VERSION,
    SocraticQuestion,
    TutorReply,
    expected_evidence_for_move,
    framing_id_for_move,
    grounding_resource_ids_for_move,
    resolve_tutor_turn,
    validate_socratic_question_focus,
)


EVENT_SCHEMA_VERSION = "4.0"
RUNTIME_VERSION = "0.10.0"
REPLAY_RUNTIME_VERSIONS = frozenset({"0.8.0", "0.8.1", "0.9.0", "0.9.1", RUNTIME_VERSION})

SessionPhase = Literal[
    "ready_for_activity",
    "awaiting_response",
    "awaiting_move",
    "complete",
]
SessionStatus = Literal["active", "completed"]
SupportKind = SupportRequestKind
AttemptStatus = Literal["completed", "abandoned", "interrupted"]
RouteScope = Literal["all", "preferred"]
FallbackReason = Literal[
    "unsupported_request",
    "interrupted_after_learner_event",
    "timeout",
    "provider_failure",
    "invalid_output",
]
LearnerMessageText = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=1000),
]


class SupportRequest(ContractModel):
    """One explicit unscored learner request."""

    kind: SupportKind


class LearnerMessage(ContractModel):
    """Bounded low-trust natural-language learner input."""

    text: LearnerMessageText


class SessionStartedPayload(ContractModel):
    """Versions that define the initial runtime contract."""

    content_schema_version: Literal["3.0"]
    runtime_version: SemanticVersion
    concepts: tuple[Concept, ...] = Field(min_length=1)
    preferred_activity_ids: tuple[StableId, ...] = ()
    route_scope: RouteScope = "all"


class AttemptStartedPayload(ContractModel):
    """Frozen activity input and runtime-derived support budget."""

    activity: Activity
    support_budget: int = Field(ge=0)
    causal_scene: CausalScene | None = None


class SupportRequestedPayload(ContractModel):
    """Typed unscored input; it is never an incorrect response."""

    request: SupportRequest


class ResponseRecordedPayload(ContractModel):
    """Complete scored evidence and its deterministic evaluation."""

    evidence: LearnerEvidence
    evaluation: Evaluation
    evaluator_version: SemanticVersion
    curriculum_requirements_met: bool


class LearnerMessageRecordedPayload(ContractModel):
    """Unscored natural-language input stored before the tutor runs."""

    message: LearnerMessage


class CausalSceneActionRecordedPayload(ContractModel):
    """One declared, unscored learner action in a frozen causal scene."""

    scene_id: StableId
    action: CausalSceneAction
    input_revision: int = Field(ge=0)
    output_revision: int = Field(ge=1)


class ExperimentActionRecordedPayload(ContractModel):
    """An unscored artifact edit, reduced without a pending Tutor turn."""

    experiment_id: StableId
    action: ExperimentAction
    input_revision: int = Field(ge=0)
    output_revision: int = Field(ge=1)


class TeachingMoveSelectedPayload(ContractModel):
    """The exact validated move and the input event that licensed it."""

    candidate_id: StableId
    move: TeachingMove
    evidence_event_ids: tuple[StableId, ...] = Field(min_length=1, max_length=1)
    expected_evidence_predicate_ids: tuple[StableId, ...]
    selector_kind: SelectorKind
    selector_version: SemanticVersion
    framing_catalog_version: SemanticVersion
    framing_id: StableId
    grounding_resource_ids: tuple[StableId, ...]
    grounding_claim_ids: tuple[StableId, ...]
    activity_question_text: NonEmptyText | None = None
    misconception_hypothesis_id: StableId | None = None
    supporting_event_ids: tuple[StableId, ...] = ()
    socratic_question: SocraticQuestion | None = None
    tutor_reply: TutorReply | None = None
    interaction_focus_id: StableId | None = None
    dialogue_job: SceneDialogueJob | None = None
    decision_trace_id: StableId | None = None
    fallback_reason: FallbackReason | None = None


class AttemptClosedPayload(ContractModel):
    """Terminal status of one attempt and predicates reached by it."""

    status: AttemptStatus
    evidence_predicate_ids: tuple[StableId, ...] = ()


class SessionCompletedPayload(ContractModel):
    """Runtime-derived curriculum completion predicates."""

    satisfied_predicate_ids: tuple[StableId, ...] = Field(min_length=1)
    completed_concept_ids: tuple[StableId, ...] = ()
    m1_ready_concept_ids: tuple[StableId, ...] = ()


class LearningEventEnvelope(ContractModel):
    """Fields shared by every versioned learning event."""

    event_schema_version: Literal["4.0"] = EVENT_SCHEMA_VERSION
    event_id: StableId
    sequence: int = Field(ge=1)
    session_id: StableId
    pack_id: StableId
    pack_version: SemanticVersion


class SessionStarted(LearningEventEnvelope):
    event_type: Literal["session_started"] = "session_started"
    payload: SessionStartedPayload


class AttemptStarted(LearningEventEnvelope):
    event_type: Literal["attempt_started"] = "attempt_started"
    attempt_id: StableId
    activity_id: StableId
    payload: AttemptStartedPayload


class SupportRequested(LearningEventEnvelope):
    event_type: Literal["support_requested"] = "support_requested"
    attempt_id: StableId
    activity_id: StableId
    request_id: StableId
    payload: SupportRequestedPayload


class ResponseRecorded(LearningEventEnvelope):
    event_type: Literal["response_recorded"] = "response_recorded"
    attempt_id: StableId
    activity_id: StableId
    request_id: StableId
    payload: ResponseRecordedPayload


class LearnerMessageRecorded(LearningEventEnvelope):
    event_type: Literal["learner_message_recorded"] = "learner_message_recorded"
    attempt_id: StableId
    activity_id: StableId
    request_id: StableId
    payload: LearnerMessageRecordedPayload


class CausalSceneActionRecorded(LearningEventEnvelope):
    event_type: Literal["causal_scene_action_recorded"] = "causal_scene_action_recorded"
    attempt_id: StableId
    activity_id: StableId
    request_id: StableId
    payload: CausalSceneActionRecordedPayload


class ExperimentActionRecorded(LearningEventEnvelope):
    event_type: Literal["experiment_action_recorded"] = "experiment_action_recorded"
    attempt_id: StableId
    activity_id: StableId
    request_id: StableId
    payload: ExperimentActionRecordedPayload


class TeachingMoveSelected(LearningEventEnvelope):
    event_type: Literal["teaching_move_selected"] = "teaching_move_selected"
    attempt_id: StableId
    activity_id: StableId
    request_id: StableId
    payload: TeachingMoveSelectedPayload


class AttemptClosed(LearningEventEnvelope):
    event_type: Literal["attempt_closed"] = "attempt_closed"
    attempt_id: StableId
    activity_id: StableId
    request_id: StableId | None = None
    payload: AttemptClosedPayload


class SessionCompleted(LearningEventEnvelope):
    event_type: Literal["session_completed"] = "session_completed"
    request_id: StableId | None = None
    payload: SessionCompletedPayload


LearningEvent: TypeAlias = (
    SessionStarted
    | AttemptStarted
    | SupportRequested
    | ResponseRecorded
    | LearnerMessageRecorded
    | CausalSceneActionRecorded
    | ExperimentActionRecorded
    | TeachingMoveSelected
    | AttemptClosed
    | SessionCompleted
)
LearnerInputEvent: TypeAlias = (
    SupportRequested | ResponseRecorded | LearnerMessageRecorded | CausalSceneActionRecorded
)

_EVENT_TYPES = (
    SessionStarted,
    AttemptStarted,
    SupportRequested,
    ResponseRecorded,
    LearnerMessageRecorded,
    CausalSceneActionRecorded,
    ExperimentActionRecorded,
    TeachingMoveSelected,
    AttemptClosed,
    SessionCompleted,
)


class SessionState(ContractModel):
    """Minimal state projection derived entirely from learning events."""

    session_id: StableId
    pack_id: StableId
    pack_version: SemanticVersion
    runtime_version: SemanticVersion
    concepts: tuple[Concept, ...]
    preferred_activity_ids: tuple[StableId, ...] = ()
    route_scope: RouteScope = "all"
    phase: SessionPhase
    status: SessionStatus
    current_activity_id: StableId | None = None
    open_attempt_id: StableId | None = None
    response_ordinal: int = Field(ge=0)
    last_evaluation: Evaluation | None = None
    support_level: int = Field(ge=0)
    support_budget: int = Field(ge=0)
    classification_artifact_id: StableId | None = None
    explicit_support_request: SupportRequest | None = None
    pending_learner_message: LearnerMessage | None = None
    causal_scene_snapshot: CausalSceneSnapshot | None = None
    experiment_snapshot: ExperimentSnapshot | None = None
    learner_message_count: int = Field(default=0, ge=0)
    requires_new_learner_action: bool = False
    advance_allowed_for_event_id: StableId | None = None
    completion_evidence_event_id: StableId | None = None
    pending_request_id: StableId | None = None
    pending_input_event_id: StableId | None = None
    last_strategy: TeachingStrategy | None = None
    completed_activity_ids: tuple[StableId, ...] = ()
    independent_transfer_activity_ids: tuple[StableId, ...] = ()
    completed_concept_ids: tuple[StableId, ...] = ()
    m1_ready_concept_ids: tuple[StableId, ...] = ()
    last_sequence: int = Field(ge=1)


class PendingTurn(ContractModel):
    """Read-only bounded context for the current pending learner input."""

    state: SessionState
    activity: Activity
    learner_input: LearnerInputEvent
    candidates: tuple[TeachingCandidate, ...]


def is_unanswered_final_support(
    activity: Activity,
    state: SessionState,
    request: SupportRequest | None,
) -> bool:
    """Only opening/explanation support before a final's first scored response."""

    return bool(
        activity.workbench is not None
        and activity.workbench.stage == "capstone"
        and state.response_ordinal == 0
        and request is not None
        and request.kind in {"orientation", "explanation"}
    )


def can_complete_attempt(state: SessionState) -> bool:
    """Only a validated scored advance, with no pending turn, permits closure."""

    return (
        state.open_attempt_id is not None
        and state.completion_evidence_event_id is not None
        and state.pending_request_id is None
    )


def replay(events: Iterable[LearningEvent]) -> SessionState:
    """Purely validate and reduce an event history without writing to it."""

    history = tuple(events)
    if not history:
        raise ValueError("cannot replay an empty event history")

    state: SessionState | None = None
    learner_inputs: dict[StableId, LearnerInputEvent] = {}
    selected_moves: set[StableId] = set()
    transition_request_ids: set[StableId] = set()
    event_ids: set[StableId] = set()
    attempt_ids: set[StableId] = set()
    attempt_event_ids: set[StableId] = set()
    responses_by_event_id: dict[StableId, ResponseRecorded] = {}
    current_activity: Activity | None = None
    current_scene: CausalScene | None = None
    used_direct_instruction_resource_ids: set[StableId] = set()
    attempt_socratic_questions: list[SocraticQuestion] = []

    for expected_sequence, event in enumerate(history, start=1):
        if not isinstance(event, _EVENT_TYPES):
            raise TypeError("events must be validated LearningEvent instances")
        if event.sequence != expected_sequence:
            raise ValueError(
                f"expected event sequence {expected_sequence}, got {event.sequence}"
            )
        expected_event_id = f"{event.session_id}.event.{event.sequence}"
        if event.event_id != expected_event_id:
            raise ValueError(f"expected event_id {expected_event_id}")
        if event.event_id in event_ids:
            raise ValueError(f"duplicate event_id: {event.event_id}")
        event_ids.add(event.event_id)

        if state is None:
            if not isinstance(event, SessionStarted):
                raise ValueError("the first event must be session_started")
            state = SessionState(
                session_id=event.session_id,
                pack_id=event.pack_id,
                pack_version=event.pack_version,
                runtime_version=event.payload.runtime_version,
                concepts=event.payload.concepts,
                preferred_activity_ids=event.payload.preferred_activity_ids,
                route_scope=event.payload.route_scope,
                phase="ready_for_activity",
                status="active",
                response_ordinal=0,
                support_level=0,
                support_budget=0,
                last_sequence=event.sequence,
            )
            if event.payload.runtime_version not in REPLAY_RUNTIME_VERSIONS:
                raise ValueError(
                    f"unsupported runtime_version: {event.payload.runtime_version}"
                )
            continue

        _require_matching_session(state, event)
        if isinstance(event, SessionStarted):
            raise ValueError("session_started may appear only once")
        if state.status != "active":
            raise ValueError("no event may follow session completion")

        if isinstance(event, AttemptStarted):
            _require_phase(state, "ready_for_activity", event.event_type)
            if event.activity_id != event.payload.activity.activity_id:
                raise ValueError("attempt activity_id does not match its frozen activity")
            if event.attempt_id in attempt_ids:
                raise ValueError(f"duplicate attempt_id: {event.attempt_id}")
            if event.activity_id in state.completed_activity_ids:
                raise ValueError("a completed activity cannot be attempted again")
            derived_support_budget = _support_budget(
                event.payload.activity, event.payload.causal_scene
            )
            if event.payload.support_budget != derived_support_budget:
                raise ValueError("support_budget does not match the frozen activity")
            if event.payload.activity.causal_scene_id is None:
                if event.payload.causal_scene is not None:
                    raise ValueError("ordinary activity cannot freeze a causal scene")
            elif (
                event.payload.causal_scene is None
                or event.payload.causal_scene.scene_id
                != event.payload.activity.causal_scene_id
            ):
                raise ValueError("scene activity must freeze its declared causal scene")
            attempt_ids.add(event.attempt_id)
            attempt_event_ids = {event.event_id}
            current_activity = event.payload.activity
            current_scene = event.payload.causal_scene
            used_direct_instruction_resource_ids = set()
            attempt_socratic_questions = []
            state = state.model_copy(
                update={
                    "phase": "awaiting_response",
                    "current_activity_id": event.activity_id,
                    "open_attempt_id": event.attempt_id,
                    "response_ordinal": 0,
                    "last_evaluation": None,
                    "support_level": 0,
                    "support_budget": event.payload.support_budget,
                    "classification_artifact_id": None,
                    "explicit_support_request": None,
                    "pending_learner_message": None,
                    "causal_scene_snapshot": (
                        None
                        if current_scene is None
                        else initial_scene_snapshot(current_scene)
                    ),
                    "experiment_snapshot": (
                        None if current_activity.experiment is None
                        else initial_experiment_snapshot(current_activity.experiment)
                    ),
                    "learner_message_count": 0,
                    "requires_new_learner_action": False,
                    "advance_allowed_for_event_id": None,
                    "completion_evidence_event_id": None,
                    "pending_request_id": None,
                    "pending_input_event_id": None,
                    "last_strategy": None,
                    "last_sequence": event.sequence,
                }
            )
            continue

        if isinstance(event, ExperimentActionRecorded):
            _require_open_attempt(state, event)
            _require_phase(state, "awaiting_response", event.event_type)
            if event.request_id in learner_inputs or event.request_id in transition_request_ids:
                raise ValueError(f"request_id has another command: {event.request_id}")
            if current_activity is None or current_activity.experiment is None or state.experiment_snapshot is None:
                raise ValueError("experiment action has no active frozen experiment")
            if state.last_evaluation is not None and state.last_evaluation.accepted:
                raise ValueError("the experiment is frozen after an accepted scored response")
            spec = current_activity.experiment
            if event.payload.experiment_id != spec.experiment_id:
                raise ValueError("experiment action references another experiment")
            snapshot = apply_experiment_action(
                spec, state.experiment_snapshot, event.payload.action,
                input_revision=event.payload.input_revision,
            )
            if event.payload.output_revision != snapshot.revision:
                raise ValueError("experiment action output revision is not canonical")
            transition_request_ids.add(event.request_id)
            attempt_event_ids.add(event.event_id)
            state = state.model_copy(update={
                "experiment_snapshot": snapshot,
                "last_evaluation": None,
                "requires_new_learner_action": False,
                "advance_allowed_for_event_id": None,
                "completion_evidence_event_id": None,
                "last_sequence": event.sequence,
            })
            continue

        if isinstance(event, CausalSceneActionRecorded):
            _require_open_attempt(state, event)
            _require_phase(state, "awaiting_response", event.event_type)
            if event.request_id in learner_inputs or event.request_id in transition_request_ids:
                raise ValueError(f"request_id has another command: {event.request_id}")
            if current_scene is None or state.causal_scene_snapshot is None:
                raise ValueError("causal-scene action has no active frozen scene")
            if event.payload.scene_id != current_scene.scene_id:
                raise ValueError("causal-scene action references another scene")
            if current_scene.simulation is not None and state.last_evaluation is not None and state.last_evaluation.accepted:
                raise ValueError("the dynamic scene is frozen after an accepted scored response")
            snapshot = apply_scene_action(
                current_scene,
                state.causal_scene_snapshot,
                event.payload.action,
                input_revision=event.payload.input_revision,
            )
            if snapshot.revision != event.payload.output_revision:
                raise ValueError("causal-scene action output revision is not canonical")
            learner_inputs[event.request_id] = event
            attempt_event_ids.add(event.event_id)
            state = state.model_copy(
                update={
                    "causal_scene_snapshot": snapshot,
                    "last_evaluation": None,
                    "advance_allowed_for_event_id": None,
                    "completion_evidence_event_id": None,
                    "phase": "awaiting_move",
                    "pending_request_id": event.request_id,
                    "pending_input_event_id": event.event_id,
                    "last_strategy": None,
                    "last_sequence": event.sequence,
                }
            )
            continue

        if isinstance(
            event,
            (SupportRequested, ResponseRecorded, LearnerMessageRecorded),
        ):
            _require_open_attempt(state, event)
            _require_phase(state, "awaiting_response", event.event_type)
            if event.request_id in learner_inputs:
                raise ValueError(f"duplicate learner request_id: {event.request_id}")
            if event.request_id in transition_request_ids:
                raise ValueError(f"request_id has another command: {event.request_id}")
            learner_inputs[event.request_id] = event
            attempt_event_ids.add(event.event_id)

            if isinstance(event, SupportRequested):
                state = state.model_copy(
                    update={
                        "phase": "awaiting_move",
                        "explicit_support_request": event.payload.request,
                        "pending_learner_message": None,
                        "advance_allowed_for_event_id": None,
                        "pending_request_id": event.request_id,
                        "pending_input_event_id": event.event_id,
                        "last_strategy": None,
                        "last_sequence": event.sequence,
                    }
                )
            elif isinstance(event, ResponseRecorded):
                evidence = event.payload.evidence
                if evidence.activity_id != event.activity_id:
                    raise ValueError("response evidence activity_id does not match event")
                if event.payload.evaluator_version != EVALUATOR_VERSION:
                    raise ValueError(
                        "unsupported evaluator_version: "
                        f"{event.payload.evaluator_version}"
                    )
                if current_activity is None:
                    raise ValueError("response has no frozen activity")
                _require_experiment_assessment(current_activity, state.experiment_snapshot)
                expected_evaluation = _evaluate_frozen_evidence(
                    current_activity, evidence, scene=current_scene
                )
                if event.payload.evaluation != expected_evaluation:
                    raise ValueError("evaluation does not match the frozen activity")
                classification_artifact_id = state.classification_artifact_id
                if isinstance(evidence, ClassificationEvidence):
                    _validate_classification_evidence(
                        evidence,
                        event,
                        current_activity,
                        state,
                        responses_by_event_id,
                    )
                    classification_artifact_id = evidence.artifact_id
                elif isinstance(evidence, CausalSceneEvidence):
                    _validate_causal_scene_evidence(
                        evidence,
                        current_activity,
                        current_scene,
                        state,
                    )
                may_advance = (
                    event.payload.evaluation.accepted
                    and event.payload.curriculum_requirements_met
                    and (
                        not current_activity.requires_revision
                        or state.response_ordinal == 0
                        or (
                            isinstance(evidence, ClassificationEvidence)
                            and evidence.revises_evidence_event_id is not None
                        )
                    )
                )
                state = state.model_copy(
                    update={
                        "phase": "awaiting_move",
                        "response_ordinal": state.response_ordinal + 1,
                        "last_evaluation": event.payload.evaluation,
                        "classification_artifact_id": classification_artifact_id,
                        "explicit_support_request": None,
                        "pending_learner_message": None,
                        "requires_new_learner_action": False,
                        "advance_allowed_for_event_id": (
                            event.event_id if may_advance else None
                        ),
                        "completion_evidence_event_id": None,
                        "pending_request_id": event.request_id,
                        "pending_input_event_id": event.event_id,
                        "last_strategy": None,
                        "last_sequence": event.sequence,
                    }
                )
                responses_by_event_id[event.event_id] = event
            else:
                if current_activity is None:
                    raise ValueError("learner message has no frozen activity")
                state = state.model_copy(
                    update={
                        "phase": "awaiting_move",
                        "explicit_support_request": None,
                        "pending_learner_message": event.payload.message,
                        "learner_message_count": state.learner_message_count + 1,
                        "requires_new_learner_action": False,
                        "advance_allowed_for_event_id": None,
                        "pending_request_id": event.request_id,
                        "pending_input_event_id": event.event_id,
                        "last_strategy": None,
                        "last_sequence": event.sequence,
                    }
                )
            continue

        if isinstance(event, TeachingMoveSelected):
            _require_open_attempt(state, event)
            _require_phase(state, "awaiting_move", event.event_type)
            if event.request_id != state.pending_request_id:
                raise ValueError("move request_id is not the current pending request")
            if event.request_id in selected_moves:
                raise ValueError(f"request already has a selected move: {event.request_id}")
            if event.request_id not in learner_inputs:
                raise ValueError("move has no matching learner input")
            if event.payload.evidence_event_ids != (state.pending_input_event_id,):
                raise ValueError("move must cite the exact current learner input event")
            learner_event = learner_inputs[event.request_id]
            if event.payload.selector_version != SELECTOR_VERSION:
                raise ValueError(
                    f"unsupported selector_version: {event.payload.selector_version}"
                )
            if current_activity is None:
                raise ValueError("move has no frozen activity")
            _validate_replayed_move(
                event,
                learner_event,
                current_activity,
                current_scene,
                state,
                attempt_event_ids,
                frozenset(used_direct_instruction_resource_ids),
                tuple(attempt_socratic_questions),
            )
            selected_moves.add(event.request_id)
            attempt_event_ids.add(event.event_id)
            if event.payload.socratic_question is not None:
                attempt_socratic_questions.append(event.payload.socratic_question)
            strategy = event.payload.move.strategy
            if strategy == "direct_instruction":
                assert event.payload.move.resource_id is not None
                used_direct_instruction_resource_ids.add(
                    event.payload.move.resource_id
                )

            if strategy == "advance":
                if state.advance_allowed_for_event_id != state.pending_input_event_id:
                    raise ValueError("advance is not licensed by the current response")
                state = state.model_copy(
                    update={
                        "phase": "awaiting_response",
                        "completion_evidence_event_id": state.pending_input_event_id,
                        "advance_allowed_for_event_id": None,
                        "explicit_support_request": None,
                        "pending_learner_message": None,
                        "pending_request_id": None,
                        "pending_input_event_id": None,
                        "last_strategy": strategy,
                        "last_sequence": event.sequence,
                    }
                )
            else:
                support_level = state.support_level
                if strategy == "socratic_hint" and state.completion_evidence_event_id is None:
                    support_level = min(state.support_budget, support_level + 1)
                elif strategy == "direct_instruction" and state.completion_evidence_event_id is None:
                    support_level = state.support_budget
                state = state.model_copy(
                    update={
                        "phase": "awaiting_response",
                        "support_level": support_level,
                        "explicit_support_request": None,
                        "pending_learner_message": None,
                        "requires_new_learner_action": (
                            True
                            if strategy == "direct_instruction"
                            and state.completion_evidence_event_id is None
                            else state.requires_new_learner_action
                        ),
                        "advance_allowed_for_event_id": None,
                        "pending_request_id": None,
                        "pending_input_event_id": None,
                        "last_strategy": strategy,
                        "last_sequence": event.sequence,
                    }
                )
            continue

        if isinstance(event, AttemptClosed):
            _require_open_attempt(state, event)
            _record_transition_request(
                event.request_id,
                learner_inputs,
                transition_request_ids,
            )
            if event.payload.status == "completed":
                if not can_complete_attempt(state):
                    raise ValueError("only a validated advance may complete an attempt")
                if current_activity is None:
                    raise ValueError("completed attempt has no frozen activity")
                independent_transfer = (
                    current_activity.is_transfer
                    and state.support_level == 0
                    and state.response_ordinal == 1
                )
                expected_predicates = (
                    "response.accepted",
                    "curriculum.requirements-met",
                ) + (("transfer.independent",) if independent_transfer else ())
                if event.payload.evidence_predicate_ids != expected_predicates:
                    raise ValueError("completed attempt predicates are not canonical")
                completed_activity_ids = (
                    *state.completed_activity_ids,
                    event.activity_id,
                )
                independent_transfer_activity_ids = (
                    (*state.independent_transfer_activity_ids, event.activity_id)
                    if independent_transfer
                    else state.independent_transfer_activity_ids
                )
            else:
                if event.payload.evidence_predicate_ids:
                    raise ValueError("incomplete attempts cannot claim evidence predicates")
                completed_activity_ids = state.completed_activity_ids
                independent_transfer_activity_ids = (
                    state.independent_transfer_activity_ids
                )
            completed_concept_ids, m1_ready_concept_ids = _derive_concept_statuses(
                state.concepts,
                completed_activity_ids,
                independent_transfer_activity_ids,
            )
            state = state.model_copy(
                update={
                    "phase": "ready_for_activity",
                    "current_activity_id": None,
                    "open_attempt_id": None,
                    "explicit_support_request": None,
                    "pending_learner_message": None,
                    "causal_scene_snapshot": None,
                    "learner_message_count": 0,
                    "requires_new_learner_action": False,
                    "classification_artifact_id": None,
                    "advance_allowed_for_event_id": None,
                    "completion_evidence_event_id": None,
                    "pending_request_id": None,
                    "pending_input_event_id": None,
                    "last_strategy": None,
                    "completed_activity_ids": completed_activity_ids,
                    "independent_transfer_activity_ids": independent_transfer_activity_ids,
                    "completed_concept_ids": completed_concept_ids,
                    "m1_ready_concept_ids": m1_ready_concept_ids,
                    "last_sequence": event.sequence,
                }
            )
            current_activity = None
            current_scene = None
            used_direct_instruction_resource_ids = set()
            attempt_socratic_questions = []
            continue

        if isinstance(event, SessionCompleted):
            _require_phase(state, "ready_for_activity", event.event_type)
            if state.open_attempt_id is not None:
                raise ValueError("cannot complete a session with an open attempt")
            _record_transition_request(
                event.request_id,
                learner_inputs,
                transition_request_ids,
            )
            if event.payload.satisfied_predicate_ids != ("curriculum.completed",):
                raise ValueError("session completion predicates are not canonical")
            if event.payload.completed_concept_ids != state.completed_concept_ids:
                raise ValueError("completed concepts do not match replay")
            if event.payload.m1_ready_concept_ids != state.m1_ready_concept_ids:
                raise ValueError("m1-ready concepts do not match replay")
            state = state.model_copy(
                update={
                    "phase": "complete",
                    "status": "completed",
                    "last_sequence": event.sequence,
                }
            )
            continue

        raise TypeError(f"unsupported event type: {type(event).__name__}")

    assert state is not None
    return state


def start_session(
    events: list[LearningEvent],
    pack: ContentPack,
    *,
    session_id: StableId,
    preferred_activity_ids: tuple[StableId, ...] = (),
    route_scope: RouteScope = "all",
) -> SessionStarted:
    """Start one session, or return its identical first event."""

    validate_release(pack)
    if events:
        state = replay(events)
        first = events[0]
        if (
            isinstance(first, SessionStarted)
            and state.session_id == session_id
            and state.pack_id == pack.pack_id
            and state.pack_version == pack.version
            and first.payload.preferred_activity_ids == preferred_activity_ids
            and first.payload.route_scope == route_scope
        ):
            return first
        raise ValueError("event history already belongs to another session or pack")

    known_activity_ids = {activity.activity_id for activity in pack.activities}
    if len(preferred_activity_ids) != len(set(preferred_activity_ids)):
        raise ValueError("preferred activity IDs must be unique")
    if not set(preferred_activity_ids).issubset(known_activity_ids):
        raise ValueError("preferred activity IDs must exist in the content pack")
    event = SessionStarted(
        **_envelope(events, session_id, pack),
        payload=SessionStartedPayload(
            content_schema_version=pack.schema_version,
            runtime_version=RUNTIME_VERSION,
            concepts=pack.concepts,
            preferred_activity_ids=preferred_activity_ids,
            route_scope=route_scope,
        ),
    )
    return _append(events, event)


def start_attempt(
    events: list[LearningEvent],
    pack: ContentPack,
    *,
    attempt_id: StableId,
    activity_id: StableId | None = None,
) -> AttemptStarted:
    """Open the requested or next incomplete authored activity."""

    state = replay(events)
    _require_pack(state, pack)
    prior = next(
        (
            event
            for event in events
            if isinstance(event, AttemptStarted) and event.attempt_id == attempt_id
        ),
        None,
    )
    if prior is not None:
        if activity_id is not None and prior.activity_id != activity_id:
            raise ValueError("attempt_id was reused for another activity")
        return prior
    if state.phase != "ready_for_activity":
        raise ValueError("an attempt may start only when the session is ready")

    if activity_id is None:
        activity = next_required_activity(pack, state)
    else:
        activity = next(
            (item for item in pack.activities if item.activity_id == activity_id),
            None,
        )
        if activity is None:
            raise ValueError("requested activity does not exist in the content pack")
        if activity.activity_id in state.completed_activity_ids:
            raise ValueError("a completed activity cannot be attempted again")
    if activity is None:
        raise ValueError("all activities are complete")
    scene = (
        None
        if activity.causal_scene_id is None
        else next(
            item
            for item in pack.causal_scenes
            if item.scene_id == activity.causal_scene_id
        )
    )
    event = AttemptStarted(
        **_envelope(events, state.session_id, pack),
        attempt_id=attempt_id,
        activity_id=activity.activity_id,
        payload=AttemptStartedPayload(
            activity=activity,
            support_budget=_support_budget(activity, scene),
            causal_scene=scene,
        ),
    )
    return _append(events, event)


def record_choice_response(
    events: list[LearningEvent],
    pack: ContentPack,
    *,
    attempt_id: StableId,
    request_id: StableId,
    evidence: ChoiceEvidence,
    curriculum_requirements_met: bool,
) -> ResponseRecorded:
    """Evaluate and append scored evidence before any teaching decision."""

    return _record_scored_response(
        events,
        pack,
        attempt_id=attempt_id,
        request_id=request_id,
        evidence=evidence,
        curriculum_requirements_met=curriculum_requirements_met,
        operation="record_choice_response",
    )


def record_classification_response(
    events: list[LearningEvent],
    pack: ContentPack,
    *,
    attempt_id: StableId,
    request_id: StableId,
    evidence: ClassificationEvidence,
    curriculum_requirements_met: bool,
) -> ResponseRecorded:
    """Append one deterministic committed classification or revision."""

    return _record_scored_response(
        events,
        pack,
        attempt_id=attempt_id,
        request_id=request_id,
        evidence=evidence,
        curriculum_requirements_met=curriculum_requirements_met,
        operation="record_classification_response",
    )


def _record_scored_response(
    events: list[LearningEvent],
    pack: ContentPack,
    *,
    attempt_id: StableId,
    request_id: StableId,
    evidence: LearnerEvidence,
    curriculum_requirements_met: bool,
    operation: str,
) -> ResponseRecorded:
    if type(curriculum_requirements_met) is not bool:
        raise TypeError("curriculum_requirements_met must be a boolean")
    state = replay(events)
    _require_pack(state, pack)
    activity = next((item for item in pack.activities if item.activity_id == evidence.activity_id), None)
    if activity is not None:
        _require_experiment_assessment(activity, state.experiment_snapshot)
    evaluation = evaluate_evidence(pack, evidence)
    existing = _learner_input_for_request(events, request_id)
    if existing is not None:
        if (
            isinstance(existing, ResponseRecorded)
            and existing.attempt_id == attempt_id
            and existing.activity_id == evidence.activity_id
            and existing.payload.evidence == evidence
            and existing.payload.evaluation == evaluation
            and existing.payload.curriculum_requirements_met
            == curriculum_requirements_met
        ):
            return existing
        raise ValueError(f"request_id was reused with different content: {request_id}")

    _require_command_attempt(state, attempt_id, evidence.activity_id)
    _require_phase(state, "awaiting_response", operation)
    if (
        state.causal_scene_snapshot is not None
        and state.causal_scene_snapshot.phase != "revision"
    ):
        raise ValueError("complete the causal-scene revision before formal evidence")
    event = ResponseRecorded(
        **_envelope(events, state.session_id, pack),
        attempt_id=attempt_id,
        activity_id=evidence.activity_id,
        request_id=request_id,
        payload=ResponseRecordedPayload(
            evidence=evidence,
            evaluation=evaluation,
            evaluator_version=EVALUATOR_VERSION,
            curriculum_requirements_met=curriculum_requirements_met,
        ),
    )
    return _append(events, event)


def record_experiment_action(
    events: list[LearningEvent],
    pack: ContentPack,
    *,
    attempt_id: StableId,
    request_id: StableId,
    experiment_id: StableId,
    input_revision: int,
    action: ExperimentAction,
) -> ExperimentActionRecorded:
    """Append a typed artifact operation without scoring or invoking the Tutor."""

    state = replay(events)
    _require_pack(state, pack)
    existing = next((event for event in events if getattr(event, "request_id", None) == request_id), None)
    if existing is not None:
        if (
            isinstance(existing, ExperimentActionRecorded)
            and existing.attempt_id == attempt_id
            and existing.payload.experiment_id == experiment_id
            and existing.payload.input_revision == input_revision
            and existing.payload.action == action
        ):
            return existing
        raise ValueError(f"request_id was reused with different content: {request_id}")
    if state.current_activity_id is None or state.experiment_snapshot is None:
        raise ValueError("the current activity has no experiment")
    _require_command_attempt(state, attempt_id, state.current_activity_id)
    _require_phase(state, "awaiting_response", "record_experiment_action")
    if state.last_evaluation is not None and state.last_evaluation.accepted:
        raise ValueError("the experiment is frozen after an accepted scored response")
    activity = next(item for item in pack.activities if item.activity_id == state.current_activity_id)
    spec = activity.experiment
    if spec is None or spec.experiment_id != experiment_id:
        raise ValueError("experiment action references another experiment")
    snapshot = apply_experiment_action(spec, state.experiment_snapshot, action, input_revision=input_revision)
    event = ExperimentActionRecorded(
        **_envelope(events, state.session_id, pack),
        attempt_id=attempt_id, activity_id=activity.activity_id, request_id=request_id,
        payload=ExperimentActionRecordedPayload(
            experiment_id=experiment_id, action=action,
            input_revision=input_revision, output_revision=snapshot.revision,
        ),
    )
    return _append(events, event)


def _require_experiment_assessment(activity: Activity, snapshot: ExperimentSnapshot | None) -> None:
    if activity.experiment is not None and (
        snapshot is None or not experiment_ready_for_assessment(activity.experiment, snapshot)
    ):
        raise ValueError("the experiment is not ready; complete and reflect on the required runs before submitting the scored check")


def record_causal_scene_action(
    events: list[LearningEvent],
    pack: ContentPack,
    *,
    attempt_id: StableId,
    request_id: StableId,
    action: CausalSceneAction,
    input_revision: int,
) -> CausalSceneActionRecorded:
    """Append one idempotent causal-scene action without evaluating it."""

    state = replay(events)
    _require_pack(state, pack)
    existing = next(
        (
            event
            for event in events
            if isinstance(event, CausalSceneActionRecorded)
            and event.request_id == request_id
        ),
        None,
    )
    if existing is not None:
        if (
            existing.attempt_id == attempt_id
            and existing.payload.action == action
            and existing.payload.input_revision == input_revision
        ):
            return existing
        raise ValueError(f"request_id was reused with different content: {request_id}")
    if state.current_activity_id is None or state.causal_scene_snapshot is None:
        raise ValueError("the current activity has no causal scene")
    _require_command_attempt(state, attempt_id, state.current_activity_id)
    _require_phase(state, "awaiting_response", "record_causal_scene_action")
    scene = _scene_for_current_activity(pack, state.current_activity_id)
    if scene.simulation is not None and state.last_evaluation is not None and state.last_evaluation.accepted:
        raise ValueError("the dynamic scene is frozen after an accepted scored response")
    snapshot = apply_scene_action(
        scene, state.causal_scene_snapshot, action, input_revision=input_revision
    )
    event = CausalSceneActionRecorded(
        **_envelope(events, state.session_id, pack),
        attempt_id=attempt_id,
        activity_id=state.current_activity_id,
        request_id=request_id,
        payload=CausalSceneActionRecordedPayload(
            scene_id=scene.scene_id,
            action=action,
            input_revision=input_revision,
            output_revision=snapshot.revision,
        ),
    )
    return _append(events, event)


def record_causal_scene_evidence(
    events: list[LearningEvent],
    pack: ContentPack,
    *,
    attempt_id: StableId,
    request_id: StableId,
) -> ResponseRecorded:
    """Evaluate the revision artifact, never an intermediate scene action."""

    state = replay(events)
    _require_pack(state, pack)
    if state.current_activity_id is None or state.causal_scene_snapshot is None:
        raise ValueError("the current activity has no causal scene")
    _require_command_attempt(state, attempt_id, state.current_activity_id)
    _require_phase(state, "awaiting_response", "record_causal_scene_evidence")
    snapshot = state.causal_scene_snapshot
    if snapshot.phase != "revision":
        raise ValueError("complete the causal-scene revision before final evidence")
    if (
        snapshot.prediction_id is None
        or snapshot.intervention_action_id is None
    ):
        raise ValueError("causal-scene evidence requires a prediction and intervention")
    return _record_scored_response(
        events,
        pack,
        attempt_id=attempt_id,
        request_id=request_id,
        evidence=CausalSceneEvidence(
            activity_id=state.current_activity_id,
            scene_id=snapshot.scene_id,
            scene_revision=snapshot.revision,
            edges=snapshot.graph_edges,
            prediction_id=snapshot.prediction_id,
            intervention_action_id=snapshot.intervention_action_id,
        ),
        curriculum_requirements_met=True,
        operation="record_causal_scene_evidence",
    )


def record_support_request(
    events: list[LearningEvent],
    pack: ContentPack,
    *,
    attempt_id: StableId,
    request_id: StableId,
    request: SupportRequest,
) -> SupportRequested:
    """Append an explicit unscored support request."""

    state = replay(events)
    _require_pack(state, pack)
    existing = _learner_input_for_request(events, request_id)
    if existing is not None:
        if (
            isinstance(existing, SupportRequested)
            and existing.attempt_id == attempt_id
            and existing.payload.request == request
        ):
            return existing
        raise ValueError(f"request_id was reused with different content: {request_id}")

    if state.current_activity_id is None:
        raise ValueError("there is no current activity")
    _require_command_attempt(state, attempt_id, state.current_activity_id)
    _require_phase(state, "awaiting_response", "record_support_request")
    event = SupportRequested(
        **_envelope(events, state.session_id, pack),
        attempt_id=attempt_id,
        activity_id=state.current_activity_id,
        request_id=request_id,
        payload=SupportRequestedPayload(request=request),
    )
    return _append(events, event)


def record_learner_message(
    events: list[LearningEvent],
    pack: ContentPack,
    *,
    attempt_id: StableId,
    request_id: StableId,
    message: LearnerMessage,
) -> LearnerMessageRecorded:
    """Append bounded unscored learner text before any tutor decision."""

    state = replay(events)
    _require_pack(state, pack)
    existing = _learner_input_for_request(events, request_id)
    if existing is not None:
        if (
            isinstance(existing, LearnerMessageRecorded)
            and existing.attempt_id == attempt_id
            and existing.payload.message == message
        ):
            return existing
        raise ValueError(f"request_id was reused with different content: {request_id}")

    if state.current_activity_id is None:
        raise ValueError("there is no current activity")
    _require_command_attempt(state, attempt_id, state.current_activity_id)
    _require_phase(state, "awaiting_response", "record_learner_message")
    event = LearnerMessageRecorded(
        **_envelope(events, state.session_id, pack),
        attempt_id=attempt_id,
        activity_id=state.current_activity_id,
        request_id=request_id,
        payload=LearnerMessageRecordedPayload(message=message),
    )
    return _append(events, event)


def select_s4_move(
    events: list[LearningEvent],
    pack: ContentPack,
    *,
    request_id: StableId,
) -> TeachingMoveSelected:
    """Select S4's sole normal candidate or unsupported-request hold."""

    state = replay(events)
    _require_pack(state, pack)
    existing = _move_for_request(events, request_id)
    if existing is not None:
        return existing
    learner_event = _pending_input(events, state, request_id)

    if isinstance(learner_event, ResponseRecorded):
        if state.current_activity_id is None:
            raise ValueError("there is no current activity")
        activity = next(
            item
            for item in pack.activities
            if item.activity_id == state.current_activity_id
        )
        current_candidates = _candidates_for_input(
            activity,
            learner_event,
            state,
            scene=_scene_for_current_activity(pack, activity.activity_id)
            if activity.causal_scene_id is not None
            else None,
            used_direct_instruction_resource_ids=(
                _used_direct_instruction_resource_ids(events, state.open_attempt_id)
            ),
        )
        selectable = tuple(
            candidate
            for candidate in current_candidates
            if candidate.selection_scope == "tutor_selectable"
        )
        if len(selectable) != 1:
            raise ValueError("S4 baseline requires exactly one tutor-selectable candidate")
        candidate = validate_candidate_membership(
            current_candidates,
            selectable[0],
            selector_kind="baseline",
        )
        selector_kind: SelectorKind = "baseline"
        fallback_reason: FallbackReason | None = None
    else:
        candidate = validate_runtime_hold(
            runtime_hold_candidate(),
            selector_kind="unsupported_request",
        )
        selector_kind = "unsupported_request"
        fallback_reason = "unsupported_request"

    return append_teaching_move(
        events,
        pack,
        request_id=request_id,
        candidate=candidate,
        selector_kind=selector_kind,
        fallback_reason=fallback_reason,
    )


def select_fixed_policy_move(
    events: list[LearningEvent],
    pack: ContentPack,
    *,
    request_id: StableId,
) -> TeachingMoveSelected:
    """Run the versioned deterministic control over the ordinary candidate gate.

    This is deliberately an alias of the existing S4 baseline, not a second
    policy state machine.  Its selected event retains ``selector_kind="baseline"``
    and the same ``SELECTOR_VERSION`` used for replay.
    """

    return select_s4_move(events, pack, request_id=request_id)


def pending_turn(
    events: Iterable[LearningEvent],
    pack: ContentPack,
    *,
    request_id: StableId,
) -> PendingTurn:
    """Return replay-derived input and candidates for one pending request."""

    history = tuple(events)
    state = replay(history)
    _require_pack(state, pack)
    learner_event = _pending_input(history, state, request_id)
    if state.current_activity_id is None:
        raise ValueError("there is no current activity")
    activity = next(
        item for item in pack.activities if item.activity_id == state.current_activity_id
    )
    return PendingTurn(
        state=state,
        activity=activity,
        learner_input=learner_event,
        candidates=_candidates_for_input(
            activity,
            learner_event,
            state,
            scene=(
                _scene_for_current_activity(pack, activity.activity_id)
                if activity.causal_scene_id is not None
                else None
            ),
            used_direct_instruction_resource_ids=(
                _used_direct_instruction_resource_ids(history, state.open_attempt_id)
            ),
        ),
    )


def selected_move_for_request(
    events: Iterable[LearningEvent],
    request_id: StableId,
) -> TeachingMoveSelected | None:
    """Return the already-recorded move for an idempotent request, if any."""

    return _move_for_request(events, request_id)


def append_teaching_move(
    events: list[LearningEvent],
    pack: ContentPack,
    *,
    request_id: StableId,
    candidate: TeachingCandidate,
    selector_kind: SelectorKind,
    fallback_reason: FallbackReason | None = None,
    misconception_hypothesis_id: StableId | None = None,
    supporting_event_ids: tuple[StableId, ...] = (),
    socratic_question: SocraticQuestion | None = None,
    tutor_reply: TutorReply | None = None,
    interaction_focus_id: StableId | None = None,
    dialogue_job: SceneDialogueJob | None = None,
    decision_trace_id: StableId | None = None,
) -> TeachingMoveSelected:
    """Rebuild the current gate and append one validated teaching move."""

    existing = _move_for_request(events, request_id)
    if existing is not None:
        return existing
    pending = pending_turn(events, pack, request_id=request_id)
    state = pending.state
    learner_event = pending.learner_input
    activity = pending.activity
    candidate = validate_candidate_membership(
        pending.candidates,
        candidate,
        selector_kind=selector_kind,
    )
    if selector_kind != "tutor" and socratic_question is not None:
        raise ValueError("only a tutor proposal may record a Socratic question")
    if selector_kind != "tutor" and tutor_reply is not None:
        raise ValueError("only a tutor proposal may record a tutor reply")
    if tutor_reply is not None:
        if not (isinstance(learner_event, LearnerMessageRecorded) or (
            isinstance(learner_event, SupportRequested)
            and is_unanswered_final_support(activity, state, learner_event.payload.request)
        )):
            raise ValueError("only a learner message or unanswered final support may carry a tutor reply")
        if candidate.move.strategy in {"advance", "hold"}:
            raise ValueError("advance and hold cannot carry a tutor reply")
    activity_question = _resource_text(pack, activity.question_resource_id)
    validate_socratic_question_focus(
        socratic_question,
        candidate.move.strategy,
        answer_labels=(choice.text for choice in activity.choices),
        activity_question=activity_question,
        previous_questions=_socratic_questions_for_attempt(
            events,
            learner_event.attempt_id,
        ),
    )
    resolved = resolve_tutor_turn(pack, activity.activity_id, candidate)
    event = TeachingMoveSelected(
        **_envelope(events, state.session_id, pack),
        attempt_id=learner_event.attempt_id,
        activity_id=learner_event.activity_id,
        request_id=request_id,
        payload=TeachingMoveSelectedPayload(
            candidate_id=candidate.candidate_id,
            move=candidate.move,
            evidence_event_ids=(learner_event.event_id,),
            expected_evidence_predicate_ids=(
                resolved.expected_evidence_predicate_ids
            ),
            selector_kind=selector_kind,
            selector_version=SELECTOR_VERSION,
            framing_catalog_version=resolved.framing_catalog_version,
            framing_id=resolved.framing_id,
            grounding_resource_ids=resolved.grounding_resource_ids,
            grounding_claim_ids=resolved.grounding_claim_ids,
            activity_question_text=(
                activity_question if socratic_question is not None else None
            ),
            misconception_hypothesis_id=misconception_hypothesis_id,
            supporting_event_ids=supporting_event_ids,
            socratic_question=socratic_question,
            tutor_reply=tutor_reply,
            interaction_focus_id=interaction_focus_id,
            dialogue_job=dialogue_job,
            decision_trace_id=decision_trace_id,
            fallback_reason=fallback_reason,
        ),
    )
    return _append(events, event)


def recover_pending_turn(
    events: list[LearningEvent],
    pack: ContentPack,
    *,
    request_id: StableId,
) -> TeachingMoveSelected | None:
    """Close an interrupted pending turn with one validated runtime hold."""

    state = replay(events)
    _require_pack(state, pack)
    existing = _move_for_request(events, request_id)
    if existing is not None:
        return existing
    if state.pending_request_id != request_id:
        return None
    candidate = validate_runtime_hold(
        runtime_hold_candidate(),
        selector_kind="recovery",
    )
    return append_teaching_move(
        events,
        pack,
        request_id=request_id,
        candidate=candidate,
        selector_kind="recovery",
        fallback_reason="interrupted_after_learner_event",
    )


def close_attempt(
    events: list[LearningEvent],
    pack: ContentPack,
    *,
    attempt_id: StableId,
    status: AttemptStatus,
    request_id: StableId | None = None,
) -> AttemptClosed:
    """Close an open attempt after a legal terminal transition."""

    state = replay(events)
    _require_pack(state, pack)
    existing = next(
        (
            event
            for event in events
            if isinstance(event, AttemptClosed) and event.attempt_id == attempt_id
        ),
        None,
    )
    if existing is not None:
        if existing.payload.status == status and existing.request_id == request_id:
            return existing
        raise ValueError(f"attempt already closed differently: {attempt_id}")
    if state.open_attempt_id != attempt_id or state.current_activity_id is None:
        raise ValueError("attempt_id is not the current open attempt")
    if status == "completed" and not can_complete_attempt(state):
        raise ValueError("only a validated advance may complete an attempt")

    predicate_ids: tuple[StableId, ...] = ()
    if status == "completed":
        activity = next(
            item for item in pack.activities if item.activity_id == state.current_activity_id
        )
        predicate_ids = ("response.accepted", "curriculum.requirements-met") + (
            ("transfer.independent",)
            if activity.is_transfer
            and state.support_level == 0
            and state.response_ordinal == 1
            else ()
        )
    event = AttemptClosed(
        **_envelope(events, state.session_id, pack),
        attempt_id=attempt_id,
        activity_id=state.current_activity_id,
        request_id=request_id,
        payload=AttemptClosedPayload(
            status=status,
            evidence_predicate_ids=predicate_ids,
        ),
    )
    return _append(events, event)


def complete_session(
    events: list[LearningEvent],
    pack: ContentPack,
    *,
    request_id: StableId | None = None,
) -> SessionCompleted:
    """Complete a session only after every activity in its declared route is complete."""

    state = replay(events)
    _require_pack(state, pack)
    existing = next(
        (event for event in events if isinstance(event, SessionCompleted)),
        None,
    )
    if existing is not None:
        if existing.request_id == request_id:
            return existing
        raise ValueError("session was already completed by another request")
    if state.phase != "ready_for_activity" or state.open_attempt_id is not None:
        raise ValueError("session is not ready for completion")
    if next_required_activity(pack, state) is not None:
        raise ValueError("curriculum still has an incomplete activity")

    event = SessionCompleted(
        **_envelope(events, state.session_id, pack),
        request_id=request_id,
        payload=SessionCompletedPayload(
            satisfied_predicate_ids=("curriculum.completed",),
            completed_concept_ids=state.completed_concept_ids,
            m1_ready_concept_ids=state.m1_ready_concept_ids,
        ),
    )
    return _append(events, event)


def next_required_activity(
    pack: ContentPack,
    state: SessionState,
) -> Activity | None:
    """Return the first incomplete activity in authored curriculum order."""

    _require_pack(state, pack)
    completed = set(state.completed_activity_ids)
    activity_ids = (
        state.preferred_activity_ids
        if state.route_scope == "preferred"
        else tuple(activity.activity_id for activity in pack.activities)
    )
    activities = {activity.activity_id: activity for activity in pack.activities}
    return next(
        (activities[activity_id] for activity_id in activity_ids if activity_id not in completed),
        None,
    )


def _derive_concept_statuses(
    concepts: tuple[Concept, ...],
    completed_activity_ids: tuple[StableId, ...],
    independent_transfer_activity_ids: tuple[StableId, ...],
) -> tuple[tuple[StableId, ...], tuple[StableId, ...]]:
    completed = set(completed_activity_ids)
    independent_transfers = set(independent_transfer_activity_ids)
    completed_concepts = tuple(
        concept.concept_id
        for concept in concepts
        if set(concept.completion_activity_ids).issubset(completed)
    )
    m1_ready_concepts = tuple(
        concept.concept_id
        for concept in concepts
        if concept.concept_id in completed_concepts
        and concept.m1_ready_activity_ids
        and set(concept.m1_ready_activity_ids).issubset(independent_transfers)
    )
    return completed_concepts, m1_ready_concepts


def _append(events: list[LearningEvent], event: LearningEvent):
    replay((*events, event))
    events.append(event)
    return event


def _envelope(
    events: list[LearningEvent],
    session_id: StableId,
    pack: ContentPack,
) -> dict[str, object]:
    sequence = len(events) + 1
    return {
        "event_id": f"{session_id}.event.{sequence}",
        "sequence": sequence,
        "session_id": session_id,
        "pack_id": pack.pack_id,
        "pack_version": pack.version,
    }


def _require_matching_session(
    state: SessionState,
    event: LearningEventEnvelope,
) -> None:
    if event.session_id != state.session_id:
        raise ValueError("event session_id changed within one history")
    if event.pack_id != state.pack_id or event.pack_version != state.pack_version:
        raise ValueError("event pack identity changed within one history")


def _require_pack(state: SessionState, pack: ContentPack) -> None:
    if state.pack_id != pack.pack_id or state.pack_version != pack.version:
        raise ValueError("content pack does not match the event history")


def _require_phase(
    state: SessionState,
    expected: SessionPhase,
    operation: str,
) -> None:
    if state.phase != expected:
        raise ValueError(f"{operation} requires phase {expected}, got {state.phase}")


def _require_open_attempt(
    state: SessionState,
    event: AttemptStarted | LearnerInputEvent | ExperimentActionRecorded | TeachingMoveSelected | AttemptClosed,
) -> None:
    if (
        event.attempt_id != state.open_attempt_id
        or event.activity_id != state.current_activity_id
    ):
        raise ValueError("event does not match the current open attempt")


def _require_command_attempt(
    state: SessionState,
    attempt_id: StableId,
    activity_id: StableId,
) -> None:
    if (
        attempt_id != state.open_attempt_id
        or activity_id != state.current_activity_id
    ):
        raise ValueError("command does not match the current open attempt")


def _validate_replayed_move(
    event: TeachingMoveSelected,
    learner_event: LearnerInputEvent,
    activity: Activity,
    scene: CausalScene | None,
    state: SessionState,
    attempt_event_ids: set[StableId],
    used_direct_instruction_resource_ids: frozenset[StableId],
    prior_socratic_questions: tuple[SocraticQuestion, ...],
) -> None:
    selector_kind = event.payload.selector_kind
    strategy = event.payload.move.strategy
    scope = "runtime_only" if strategy == "hold" else "tutor_selectable"
    candidate = validate_candidate_membership(
        _candidates_for_input(
            activity,
            learner_event,
            state,
            scene=scene,
            used_direct_instruction_resource_ids=(
                used_direct_instruction_resource_ids
            ),
        ),
        TeachingCandidate(
            candidate_id=event.payload.candidate_id,
            move=event.payload.move,
            selection_scope=scope,
        ),
        selector_kind=selector_kind,
    )

    expected_reason = {
        "baseline": None,
        "tutor": None,
        "unsupported_request": "unsupported_request",
        "recovery": "interrupted_after_learner_event",
        "timeout": "timeout",
        "provider_failure": "provider_failure",
        "invalid_output": "invalid_output",
    }[selector_kind]
    if event.payload.fallback_reason != expected_reason:
        raise ValueError("fallback reason does not match selector_kind")
    if selector_kind == "baseline" and not isinstance(
        learner_event, ResponseRecorded
    ):
        raise ValueError("baseline requires scored learner evidence")
    if selector_kind == "unsupported_request" and isinstance(
        learner_event, ResponseRecorded
    ):
        raise ValueError("unsupported_request cannot consume scored evidence")

    if event.payload.framing_catalog_version != FRAMING_CATALOG_VERSION:
        raise ValueError("unsupported framing catalog version")
    if event.payload.framing_id != framing_id_for_move(candidate.move):
        raise ValueError("framing_id does not match the selected move")
    if event.payload.grounding_resource_ids != grounding_resource_ids_for_move(
        activity,
        candidate.move,
    ):
        raise ValueError("grounding resources do not match the selected move")
    if event.payload.expected_evidence_predicate_ids != expected_evidence_for_move(
        candidate.move
    ):
        raise ValueError("expected evidence does not match the selected move")
    if len(set(event.payload.grounding_claim_ids)) != len(
        event.payload.grounding_claim_ids
    ):
        raise ValueError("grounding claim IDs must be unique")

    hypothesis_id = event.payload.misconception_hypothesis_id
    supporting_ids = event.payload.supporting_event_ids
    if selector_kind != "tutor" and (hypothesis_id is not None or supporting_ids):
        raise ValueError("only a tutor proposal may record a hypothesis")
    if selector_kind != "tutor" and event.payload.socratic_question is not None:
        raise ValueError("only a tutor proposal may record a Socratic question")
    if selector_kind != "tutor" and event.payload.tutor_reply is not None:
        raise ValueError("only a tutor proposal may record a tutor reply")
    if event.payload.tutor_reply is not None:
        if not (isinstance(learner_event, LearnerMessageRecorded) or (
            isinstance(learner_event, SupportRequested)
            and is_unanswered_final_support(activity, state, learner_event.payload.request)
        )):
            raise ValueError("only a learner message or unanswered final support may carry a tutor reply")
        if strategy in {"advance", "hold"}:
            raise ValueError("advance and hold cannot carry a tutor reply")
    if selector_kind == "tutor" and state.causal_scene_snapshot is not None and (
        event.payload.interaction_focus_id is None
    ):
        raise ValueError("a scene tutor proposal requires an interaction focus")
    if event.payload.interaction_focus_id is not None:
        if selector_kind != "tutor" or state.causal_scene_snapshot is None:
            raise ValueError("only a scene tutor proposal may record an interaction focus")
        if event.payload.interaction_focus_id not in legal_scene_focus_ids(
            state.causal_scene_snapshot
        ):
            raise ValueError("interaction focus is not legal for the current scene phase")
        if event.payload.dialogue_job != dialogue_job_for_scene_focus(
            event.payload.interaction_focus_id
        ):
            raise ValueError("dialogue job does not match the interaction focus")
    elif event.payload.dialogue_job is not None:
        raise ValueError("dialogue job requires an interaction focus")
    activity_question = event.payload.activity_question_text
    if event.payload.socratic_question is None and activity_question is not None:
        raise ValueError("an activity focus requires a Socratic question")
    validate_socratic_question_focus(
        event.payload.socratic_question,
        strategy,
        answer_labels=(choice.text for choice in activity.choices),
        activity_question=activity_question or "",
        previous_questions=prior_socratic_questions,
        allow_legacy_clarify=True,
    )
    if hypothesis_id is None:
        if supporting_ids:
            raise ValueError("supporting events require a misconception hypothesis")
    else:
        allowed_hypotheses = {
            choice.misconception_id
            for choice in activity.choices
            if choice.misconception_id is not None
        }
        if hypothesis_id not in allowed_hypotheses:
            raise ValueError("misconception hypothesis is not valid for the activity")
        if not supporting_ids:
            raise ValueError("a misconception hypothesis requires supporting events")
        if len(set(supporting_ids)) != len(supporting_ids):
            raise ValueError("supporting event IDs must be unique")
        if not set(supporting_ids).issubset(attempt_event_ids):
            raise ValueError("hypothesis support must be prior events in this attempt")


def _candidates_for_input(
    activity: Activity,
    learner_event: LearnerInputEvent,
    state: SessionState,
    *,
    scene: CausalScene | None,
    used_direct_instruction_resource_ids: frozenset[StableId] = frozenset(),
) -> tuple[TeachingCandidate, ...]:
    if isinstance(learner_event, ResponseRecorded):
        evidence = learner_event.payload.evidence
        evaluation = learner_event.payload.evaluation
        if isinstance(evidence, CausalSceneEvidence):
            if scene is None:
                raise ValueError("causal-scene evidence has no declared scene")
            if evaluation.accepted:
                move = TeachingMove(strategy="advance")
            elif state.support_level < len(scene.assessment.hint_resource_ids):
                move = TeachingMove(
                    strategy="socratic_hint",
                    resource_id=scene.assessment.hint_resource_ids[state.support_level],
                )
            else:
                move = TeachingMove(
                    strategy="direct_instruction",
                    resource_id=activity.explanation_resource_id,
                )
            candidates = (_tutor_candidate(move), runtime_hold_candidate())
        else:
            candidates = scored_teaching_candidates(
                activity,
                evidence,
                evaluation,
                curriculum_requirements_met=(
                    learner_event.payload.curriculum_requirements_met
                ),
                support_level=state.support_level,
                support_budget=state.support_budget,
                requires_reflection=(
                    activity.requires_revision
                    and not evaluation.accepted
                    and isinstance(evidence, ClassificationEvidence)
                    and evidence.revises_evidence_event_id is None
                ),
            )
    elif isinstance(learner_event, CausalSceneActionRecorded):
        if scene is None:
            raise ValueError("causal-scene action has no declared scene")
        resource_id = {
            "open_records": scene.model_resource_id,
            "submit_graph": scene.prediction_resource_id,
            "select_hypothesis": scene.prediction_resource_id,
            "submit_prediction": scene.intervention_resource_id,
            "run_intervention": scene.result_resource_id,
            "submit_revision": scene.direct_explanation_resource_id,
        }[learner_event.payload.action.kind]
        strategy: TeachingStrategy = (
            "reflect"
            if learner_event.payload.action.kind in {"run_intervention", "submit_revision"}
            else "elicit"
        )
        candidates = (
            TeachingCandidate(
                candidate_id=f"tutor.{strategy}.{resource_id}",
                move=TeachingMove(strategy=strategy, resource_id=resource_id),
                selection_scope="tutor_selectable",
            ),
            runtime_hold_candidate(),
        )
    elif isinstance(learner_event, SupportRequested):
        candidates = support_teaching_candidates(
            activity, learner_event.payload.request.kind
        )
    else:
        candidates = message_teaching_candidates(
            activity,
            support_level=state.support_level,
            support_budget=state.support_budget,
        )
    if scene is not None and scene.simulation is not None and state.causal_scene_snapshot is not None and not simulation_ready(scene, state.causal_scene_snapshot):
        # The candidate owner, not just the renderer/chat prompt, must withhold
        # the reference explanation on explicit support and guarded chat too.
        phase = state.causal_scene_snapshot.phase
        safe_resource = (scene.model_resource_id if phase in {"hook", "records"}
                         else scene.intervention_resource_id if phase in {"model", "prediction"}
                         else scene.result_resource_id)
        private_resources = {activity.explanation_resource_id, scene.direct_explanation_resource_id,
                             scene.reflection_resource_id}
        candidates = tuple(
            _tutor_candidate(candidate.move.model_copy(update={"resource_id": safe_resource}))
            if candidate.move.resource_id in private_resources else candidate
            for candidate in candidates
        )
    gated = gate_reused_direct_instruction(
        candidates,
        used_resource_ids=used_direct_instruction_resource_ids,
        clarify_resource_id=activity.question_resource_id,
    )
    if isinstance(learner_event, SupportRequested) and learner_event.payload.request.kind == "explanation":
        direct = next(item for item in candidates if item.move.strategy == "direct_instruction")
        if direct not in gated:
            # An explicit explanation remains available. Retain the old clarify
            # candidate too, so existing traces still replay under the same schema.
            return (direct, *gated)
    return gated


def _tutor_candidate(move: TeachingMove) -> TeachingCandidate:
    candidate_id = f"tutor.{move.strategy}"
    if move.resource_id is not None:
        candidate_id = f"{candidate_id}.{move.resource_id}"
    return TeachingCandidate(
        candidate_id=candidate_id,
        move=move,
        selection_scope="tutor_selectable",
    )


def _used_direct_instruction_resource_ids(
    events: Iterable[LearningEvent],
    attempt_id: StableId | None,
) -> frozenset[StableId]:
    if attempt_id is None:
        return frozenset()
    return frozenset(
        event.payload.move.resource_id
        for event in events
        if isinstance(event, TeachingMoveSelected)
        and event.attempt_id == attempt_id
        and event.payload.move.strategy == "direct_instruction"
        and event.payload.move.resource_id is not None
    )


def _socratic_questions_for_attempt(
    events: Iterable[LearningEvent],
    attempt_id: StableId,
) -> tuple[SocraticQuestion, ...]:
    return tuple(
        event.payload.socratic_question
        for event in events
        if isinstance(event, TeachingMoveSelected)
        and event.attempt_id == attempt_id
        and event.payload.socratic_question is not None
    )


def _resource_text(pack: ContentPack, resource_id: StableId) -> str:
    return next(
        resource.text
        for resource in pack.resources
        if resource.resource_id == resource_id
    )


def _scene_for_current_activity(pack: ContentPack, activity_id: StableId) -> CausalScene:
    activity = next(
        item for item in pack.activities if item.activity_id == activity_id
    )
    if activity.causal_scene_id is None:
        raise ValueError("the current activity does not declare a causal scene")
    return next(
        scene for scene in pack.causal_scenes if scene.scene_id == activity.causal_scene_id
    )


def _support_budget(activity: Activity, scene: CausalScene | None = None) -> int:
    if scene is not None:
        return len(scene.assessment.hint_resource_ids)
    return max(
        (len(choice.hint_resource_ids) for choice in activity.choices),
        default=0,
    )


def _evaluate_frozen_evidence(
    activity: Activity,
    evidence: LearnerEvidence,
    *,
    scene: CausalScene | None,
) -> Evaluation:
    if isinstance(evidence, ChoiceEvidence) and activity.activity_type != "choice":
        raise ValueError("choice evidence does not match the frozen activity")
    if (
        isinstance(evidence, ClassificationEvidence)
        and activity.activity_type != "classification"
    ):
        raise ValueError("classification evidence does not match the frozen activity")
    if isinstance(evidence, CausalSceneEvidence):
        if activity.activity_type != "causal_scene" or scene is None:
            raise ValueError("causal-scene evidence does not match the frozen activity")
        if evidence.scene_id != scene.scene_id:
            raise ValueError("causal-scene evidence references another frozen scene")
        expected_edges = {
            (edge.parent_id, edge.child_id) for edge in scene.assessment.accepted_edges
        }
        submitted_edges = {(edge.parent_id, edge.child_id) for edge in evidence.edges}
        accepted = (
            evidence.scene_revision >= 5
            and evidence.intervention_action_id == scene.intervention.action_id
            and submitted_edges == expected_edges
        )
        return Evaluation(
            accepted=accepted,
            misconception_id=(None if accepted else scene.assessment.rejected_misconception_id),
            consequence_resource_id=(
                scene.assessment.accepted_consequence_resource_id
                if accepted
                else scene.assessment.rejected_consequence_resource_id
            ),
        )
    option_id = evidence.option_id if isinstance(evidence, ChoiceEvidence) else evidence.classification_id
    choice = next(
        (item for item in activity.choices if item.option_id == option_id),
        None,
    )
    if choice is None:
        raise ValueError(f"unknown response ID in frozen activity: {option_id}")
    return Evaluation(
        accepted=choice.correct,
        misconception_id=choice.misconception_id,
        consequence_resource_id=choice.consequence_resource_id,
    )


def _validate_causal_scene_evidence(
    evidence: CausalSceneEvidence,
    activity: Activity,
    scene: CausalScene | None,
    state: SessionState,
) -> None:
    if activity.activity_type != "causal_scene" or scene is None:
        raise ValueError("causal-scene evidence does not match the frozen activity")
    snapshot = state.causal_scene_snapshot
    if snapshot is None or snapshot.phase != "revision":
        raise ValueError("causal-scene evidence requires a completed revision")
    if (
        evidence.scene_id != scene.scene_id
        or evidence.scene_revision != snapshot.revision
        or evidence.edges != snapshot.graph_edges
        or evidence.prediction_id != snapshot.prediction_id
        or evidence.intervention_action_id != snapshot.intervention_action_id
    ):
        raise ValueError("causal-scene evidence must equal the current revision artifact")


def _validate_classification_evidence(
    evidence: ClassificationEvidence,
    event: ResponseRecorded,
    activity: Activity,
    state: SessionState,
    responses_by_event_id: dict[StableId, ResponseRecorded],
) -> None:
    if activity.activity_type != "classification":
        raise ValueError("classification evidence does not match the frozen activity")
    if state.classification_artifact_id is None:
        if evidence.revises_evidence_event_id is not None:
            raise ValueError("the original classification cannot revise an earlier event")
        return
    if evidence.artifact_id != state.classification_artifact_id:
        raise ValueError("classification evidence must use the current artifact_id")
    revised_event_id = evidence.revises_evidence_event_id
    if revised_event_id is None:
        raise ValueError("a later classification must name the revised evidence event")
    revised = responses_by_event_id.get(revised_event_id)
    if revised is None:
        raise ValueError("revised evidence event must be earlier in this session")
    if revised.attempt_id != event.attempt_id or revised.activity_id != event.activity_id:
        raise ValueError("revised evidence event must belong to this activity attempt")
    prior_evidence = revised.payload.evidence
    if not isinstance(prior_evidence, ClassificationEvidence):
        raise ValueError("revised evidence event is not a classification")
    if prior_evidence.artifact_id != evidence.artifact_id:
        raise ValueError("revised evidence event must use the same artifact_id")


def _learner_input_for_request(
    events: Iterable[LearningEvent],
    request_id: StableId,
) -> LearnerInputEvent | None:
    return next(
        (
            event
            for event in events
            if isinstance(
                event,
                (
                    SupportRequested,
                    ResponseRecorded,
                    LearnerMessageRecorded,
                    CausalSceneActionRecorded,
                ),
            )
            and event.request_id == request_id
        ),
        None,
    )


def _move_for_request(
    events: Iterable[LearningEvent],
    request_id: StableId,
) -> TeachingMoveSelected | None:
    return next(
        (
            event
            for event in events
            if isinstance(event, TeachingMoveSelected)
            and event.request_id == request_id
        ),
        None,
    )


def _record_transition_request(
    request_id: StableId | None,
    learner_inputs: dict[StableId, LearnerInputEvent],
    transition_request_ids: set[StableId],
) -> None:
    if request_id is None:
        return
    if request_id in learner_inputs or request_id in transition_request_ids:
        raise ValueError(f"request_id has another command: {request_id}")
    transition_request_ids.add(request_id)


def _pending_input(
    events: Iterable[LearningEvent],
    state: SessionState,
    request_id: StableId,
) -> LearnerInputEvent:
    if state.pending_request_id != request_id:
        raise ValueError("request_id is not the current pending learner input")
    event = _learner_input_for_request(events, request_id)
    if event is None or event.event_id != state.pending_input_event_id:
        raise ValueError("pending learner input is missing from event history")
    return event
