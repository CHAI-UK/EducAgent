"""Versioned, de-identified exports for reproducible EducAgent studies."""

import hmac
import platform
from hashlib import sha256
from importlib.metadata import version
from typing import Iterable, Literal, Self

from pydantic import Field, model_validator

from .contracts import ContentPack, ContractModel, SemanticVersion, StableId
from .evaluation import EVALUATOR_VERSION
from .events import LearningEvent, ResponseRecorded, TeachingMoveSelected, replay
from .profiles import LearnerProfile, project_learner_profile
from .quality import TutorQualityReport, audit_tutor_trace
from .runtime import FIXED_POLICY_VERSION


STUDY_EXPORT_VERSION: SemanticVersion = "1.0.0"
StudyArmKind = Literal[
    "reading",
    "source_grounded_chat",
    "fixed_policy_control",
    "guarded_pydantic_ai",
]


class StudyArmManifest(ContractModel):
    """A predeclared experimental condition, not a runtime authority."""

    arm_id: StableId
    kind: StudyArmKind
    policy_id: StableId
    policy_version: SemanticVersion
    model_id: str | None = Field(default=None, max_length=240)
    prompt_version: SemanticVersion | None = None


class DependencyVersion(ContractModel):
    """One recorded installed dependency version."""

    package: StableId
    installed_version: str = Field(min_length=1, max_length=120)


class StudyRunManifest(ContractModel):
    """All behavior versions required to interpret a participant run."""

    study_id: StableId
    run_id: StableId
    arm: StudyArmManifest
    pack_id: StableId
    pack_version: SemanticVersion
    evaluator_version: SemanticVersion
    runtime_version: SemanticVersion
    renderer_version: SemanticVersion
    python_version: str = Field(min_length=1, max_length=120)
    dependencies: tuple[DependencyVersion, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_model_provenance(self) -> Self:
        if self.arm.kind in {"source_grounded_chat", "guarded_pydantic_ai"}:
            if self.arm.model_id is None:
                raise ValueError("a model-backed arm requires a concrete model_id")
        if self.arm.kind == "guarded_pydantic_ai" and self.arm.prompt_version is None:
            raise ValueError("the guarded tutor arm requires prompt_version")
        return self


class DeidentifiedEventRow(ContractModel):
    """An exportable event projection with no raw identifiers or learner text."""

    participant_id: StableId
    sequence: int = Field(ge=1)
    event_type: StableId
    activity_id: StableId | None = None
    accepted: bool | None = None
    misconception_id: StableId | None = None
    strategy: str | None = Field(default=None, max_length=80)
    selector_kind: str | None = Field(default=None, max_length=80)
    fallback_reason: str | None = Field(default=None, max_length=120)


class SubjectCorrectnessReport(ContractModel):
    accepted_response_count: int = Field(ge=0)
    rejected_response_count: int = Field(ge=0)


class PedagogyProtocolReport(ContractModel):
    quality: TutorQualityReport


class LearningOutcomeReport(ContractModel):
    completed_concept_count: int = Field(ge=0)
    m1_ready_concept_count: int = Field(ge=0)
    independent_transfer_concept_count: int = Field(ge=0)
    supported_transfer_concept_count: int = Field(ge=0)
    rejected_transfer_concept_count: int = Field(ge=0)


class DeidentifiedConceptState(ContractModel):
    """Counts and authored IDs only; trace event IDs stay out of exports."""

    concept_id: StableId
    attempt_count: int = Field(ge=0)
    accepted_count: int = Field(ge=0)
    rejected_count: int = Field(ge=0)
    revision_count: int = Field(ge=0)
    hint_dependent_success_count: int = Field(ge=0)
    transfer_status: str = Field(min_length=1, max_length=40)
    hypothesis_ids: tuple[StableId, ...]
    expected_evidence_count: int = Field(ge=0)
    expected_evidence_match_count: int = Field(ge=0)


class DeidentifiedLearnerState(ContractModel):
    """A de-identified replay projection suitable for outcome analysis."""

    participant_id: StableId
    completed_concept_ids: tuple[StableId, ...]
    m1_ready_concept_ids: tuple[StableId, ...]
    concepts: tuple[DeidentifiedConceptState, ...]


class StudyExport(ContractModel):
    """One de-identified participant export and separate outcome reports."""

    export_version: SemanticVersion
    manifest: StudyRunManifest
    participant_id: StableId
    events: tuple[DeidentifiedEventRow, ...]
    learner_state: DeidentifiedLearnerState
    subject_correctness: SubjectCorrectnessReport
    pedagogy_protocol: PedagogyProtocolReport
    learning_outcomes: LearningOutcomeReport


def frozen_m0_arm_manifests() -> tuple[StudyArmManifest, ...]:
    """Return the four predeclared M0 comparison conditions."""

    return (
        StudyArmManifest(
            arm_id="m0.reading",
            kind="reading",
            policy_id="reading-only",
            policy_version="1.0.0",
        ),
        StudyArmManifest(
            arm_id="m0.source-grounded-chat",
            kind="source_grounded_chat",
            policy_id="source-grounded-chat",
            policy_version="1.0.0",
        ),
        StudyArmManifest(
            arm_id="m0.fixed-policy-control",
            kind="fixed_policy_control",
            policy_id="fixed-policy",
            policy_version=FIXED_POLICY_VERSION,
        ),
        StudyArmManifest(
            arm_id="m0.guarded-pydantic-ai",
            kind="guarded_pydantic_ai",
            policy_id="guarded-pydantic-ai",
            policy_version="1.0.0",
            prompt_version="1.1.0",
        ),
    )


def build_study_run_manifest(
    pack: ContentPack,
    *,
    study_id: StableId,
    run_id: StableId,
    arm: StudyArmManifest,
    renderer_version: SemanticVersion,
) -> StudyRunManifest:
    """Construct a complete manifest from installed, non-secret version facts."""

    from .events import RUNTIME_VERSION

    return StudyRunManifest(
        study_id=study_id,
        run_id=run_id,
        arm=arm,
        pack_id=pack.pack_id,
        pack_version=pack.version,
        evaluator_version=EVALUATOR_VERSION,
        runtime_version=RUNTIME_VERSION,
        renderer_version=renderer_version,
        python_version=platform.python_version(),
        dependencies=tuple(
            DependencyVersion(package=package, installed_version=version(distribution))
            for package, distribution in (
                ("pydantic", "pydantic"),
                ("pydantic-ai", "pydantic-ai-slim"),
                ("logfire", "logfire"),
            )
        ),
    )


def export_study_run(
    events: Iterable[LearningEvent],
    pack: ContentPack,
    *,
    manifest: StudyRunManifest,
    pseudonym_secret: str,
) -> StudyExport:
    """Produce a reproducible de-identified export from the append-only trace."""

    if not pseudonym_secret:
        raise ValueError("pseudonym_secret must not be empty")
    history = tuple(events)
    state = replay(history)
    if manifest.pack_id != pack.pack_id or manifest.pack_version != pack.version:
        raise ValueError("study manifest does not match the content pack")
    participant_id = _participant_id(state.session_id, pseudonym_secret)
    profile = project_learner_profile(history)
    rows = tuple(_event_row(event, participant_id) for event in history)
    accepted = sum(
        row.accepted is True for row in rows if row.event_type == "response_recorded"
    )
    rejected = sum(
        row.accepted is False for row in rows if row.event_type == "response_recorded"
    )
    statuses = [concept.transfer_status for concept in profile.concepts]
    return StudyExport(
        export_version=STUDY_EXPORT_VERSION,
        manifest=manifest,
        participant_id=participant_id,
        events=rows,
        learner_state=_deidentified_state(profile, participant_id),
        subject_correctness=SubjectCorrectnessReport(
            accepted_response_count=accepted,
            rejected_response_count=rejected,
        ),
        pedagogy_protocol=PedagogyProtocolReport(
            quality=audit_tutor_trace(history, pack)
        ),
        learning_outcomes=LearningOutcomeReport(
            completed_concept_count=len(profile.completed_concept_ids),
            m1_ready_concept_count=len(profile.m1_ready_concept_ids),
            independent_transfer_concept_count=statuses.count("independent"),
            supported_transfer_concept_count=statuses.count("supported"),
            rejected_transfer_concept_count=statuses.count("rejected"),
        ),
    )


def _participant_id(session_id: StableId, secret: str) -> StableId:
    digest = hmac.new(
        secret.encode("utf-8"), session_id.encode("utf-8"), sha256
    ).hexdigest()
    return f"participant-{digest[:24]}"


def _event_row(
    event: LearningEvent,
    participant_id: StableId,
) -> DeidentifiedEventRow:
    values: dict[str, object] = {
        "participant_id": participant_id,
        "sequence": event.sequence,
        "event_type": event.event_type,
        "activity_id": getattr(event, "activity_id", None),
    }
    if isinstance(event, ResponseRecorded):
        values.update(
            accepted=event.payload.evaluation.accepted,
            misconception_id=event.payload.evaluation.misconception_id,
        )
    if isinstance(event, TeachingMoveSelected):
        values.update(
            strategy=event.payload.move.strategy,
            selector_kind=event.payload.selector_kind,
            fallback_reason=event.payload.fallback_reason,
        )
    return DeidentifiedEventRow(**values)


def _deidentified_state(
    profile: LearnerProfile,
    participant_id: StableId,
) -> DeidentifiedLearnerState:
    return DeidentifiedLearnerState(
        participant_id=participant_id,
        completed_concept_ids=profile.completed_concept_ids,
        m1_ready_concept_ids=profile.m1_ready_concept_ids,
        concepts=tuple(
            DeidentifiedConceptState(
                concept_id=concept.concept_id,
                attempt_count=concept.attempt_count,
                accepted_count=len(concept.accepted_event_ids),
                rejected_count=len(concept.rejected_event_ids),
                revision_count=len(concept.revision_event_ids),
                hint_dependent_success_count=len(
                    concept.hint_dependent_success_event_ids
                ),
                transfer_status=concept.transfer_status,
                hypothesis_ids=tuple(
                    dict.fromkeys(item.hypothesis_id for item in concept.hypotheses)
                ),
                expected_evidence_count=len(concept.expected_evidence),
                expected_evidence_match_count=sum(
                    item.matched for item in concept.expected_evidence
                ),
            )
            for concept in profile.concepts
        ),
    )
