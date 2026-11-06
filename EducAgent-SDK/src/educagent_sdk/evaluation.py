"""Deterministic evaluation of typed learner evidence."""

from typing import Self, TypeAlias

from pydantic import Field, model_validator

from .contracts import (
    Activity,
    CausalSceneEdge,
    ContentPack,
    ContractModel,
    StableId,
)
from .release import validate_release


EVALUATOR_VERSION = "2.0.0"


class ChoiceEvidence(ContractModel):
    """One single-choice response using stable authored IDs."""

    activity_id: StableId
    option_id: StableId


class ClassificationEvidence(ContractModel):
    """One committed classification, optionally revising a prior artifact."""

    activity_id: StableId
    classification_id: StableId
    artifact_id: StableId
    revises_evidence_event_id: StableId | None = None


class CausalSceneEvidence(ContractModel):
    """A final causal model with its immutable pre-reveal prediction snapshot."""

    activity_id: StableId
    scene_id: StableId
    scene_revision: int = Field(ge=0)
    edges: tuple[CausalSceneEdge, ...]
    prediction_id: StableId
    intervention_action_id: StableId


LearnerEvidence: TypeAlias = ChoiceEvidence | ClassificationEvidence | CausalSceneEvidence


class Evaluation(ContractModel):
    """A deterministic verdict containing semantic IDs, never teaching prose."""

    accepted: bool
    misconception_id: StableId | None
    consequence_resource_id: StableId

    @model_validator(mode="after")
    def validate_verdict(self) -> Self:
        if self.accepted and self.misconception_id is not None:
            raise ValueError("accepted evidence cannot have a misconception_id")
        if not self.accepted and self.misconception_id is None:
            raise ValueError("rejected evidence requires a misconception_id")
        return self


def evaluate_choice(pack: ContentPack, evidence: ChoiceEvidence) -> Evaluation:
    """Evaluate one released choice by stable activity and option IDs."""

    activity = _activity(pack, evidence.activity_id, "choice")
    return _evaluate_option(activity, evidence.option_id, "option_id")


def evaluate_classification(
    pack: ContentPack,
    evidence: ClassificationEvidence,
) -> Evaluation:
    """Evaluate one released classification by stable activity and label IDs."""

    activity = _activity(pack, evidence.activity_id, "classification")
    return _evaluate_option(activity, evidence.classification_id, "classification_id")


def evaluate_causal_scene(
    pack: ContentPack,
    evidence: CausalSceneEvidence,
) -> Evaluation:
    """Evaluate the revised model after the declared intervention was observed."""

    activity = _activity(pack, evidence.activity_id, "causal_scene")
    if activity.causal_scene_id != evidence.scene_id:
        raise ValueError("causal-scene evidence references another scene")
    scene = next(
        item for item in pack.causal_scenes if item.scene_id == evidence.scene_id
    )
    expected_edges = {
        (edge.parent_id, edge.child_id) for edge in scene.assessment.accepted_edges
    }
    submitted_edges = {(edge.parent_id, edge.child_id) for edge in evidence.edges}
    accepted = (
        evidence.scene_revision >= 5
        and evidence.intervention_action_id == scene.intervention.action_id
        and submitted_edges == expected_edges
    )
    if accepted:
        return Evaluation(
            accepted=True,
            misconception_id=None,
            consequence_resource_id=scene.assessment.accepted_consequence_resource_id,
        )
    return Evaluation(
        accepted=False,
        misconception_id=scene.assessment.rejected_misconception_id,
        consequence_resource_id=scene.assessment.rejected_consequence_resource_id,
    )


def evaluate_evidence(pack: ContentPack, evidence: LearnerEvidence) -> Evaluation:
    """Evaluate the exact structured response type declared by its activity."""

    if isinstance(evidence, ChoiceEvidence):
        return evaluate_choice(pack, evidence)
    if isinstance(evidence, ClassificationEvidence):
        return evaluate_classification(pack, evidence)
    return evaluate_causal_scene(pack, evidence)


def _activity(
    pack: ContentPack,
    activity_id: StableId,
    activity_type: str,
) -> Activity:
    validate_release(pack)
    activity = next(
        (item for item in pack.activities if item.activity_id == activity_id),
        None,
    )
    if activity is None:
        raise ValueError(f"unknown activity_id: {activity_id}")
    if activity.activity_type != activity_type:
        raise ValueError(f"activity {activity_id} does not accept {activity_type} evidence")
    return activity


def _evaluate_option(
    activity: Activity,
    option_id: StableId,
    field_name: str,
) -> Evaluation:
    choice = next(
        (item for item in activity.choices if item.option_id == option_id),
        None,
    )
    if choice is None:
        raise ValueError(f"unknown {field_name} for {activity.activity_id}: {option_id}")
    return Evaluation(
        accepted=choice.correct,
        misconception_id=choice.misconception_id,
        consequence_resource_id=choice.consequence_resource_id,
    )
