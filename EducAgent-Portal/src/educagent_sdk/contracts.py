"""Strict public contracts for authored EducAgent content packs."""

import json
from collections.abc import Iterable
from pathlib import Path
from typing import Annotated, Literal, Self, TypeAlias

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator


StableId = Annotated[
    str,
    StringConstraints(
        min_length=1,
        pattern=r"^[a-z0-9]+(?:[._-][a-z0-9]+)*$",
    ),
]
NonEmptyText = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1),
]
SemanticVersion = Annotated[
    str,
    StringConstraints(pattern=r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$"),
]
ReviewStatus = Literal["draft", "reviewed"]
ReleaseStatus = Literal["draft", "released"]
ResourceKind = Literal["question", "hint", "explanation", "consequence"]
ActivityType = Literal["choice", "classification", "causal_scene"]
BinarySceneValue = Literal["yes", "no"]
ScenarioImagePath = Annotated[
    str,
    StringConstraints(
        pattern=r"^media(?:/[a-z0-9]+(?:[._-][a-z0-9]+)*)+\.png$",
    ),
]


class ContractModel(BaseModel):
    """Base settings shared by every serialized public contract."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)


class SourceRef(ContractModel):
    """An author-declared stable location within a cited source."""

    source_id: StableId
    locator: NonEmptyText


class Source(ContractModel):
    """Author-declared citation, rights, and internal review metadata."""

    source_id: StableId
    citation: NonEmptyText
    rights: NonEmptyText
    review_status: ReviewStatus


class DeterministicDerivation(ContractModel):
    """Declared versioned method identifier for a deterministic claim."""

    method_id: StableId
    method_version: SemanticVersion


class Claim(ContractModel):
    """One canonical proposition with exactly one provenance route."""

    claim_id: StableId
    proposition: NonEmptyText
    source_refs: tuple[SourceRef, ...] = ()
    deterministic_derivation: DeterministicDerivation | None = None
    release_status: ReleaseStatus

    @model_validator(mode="after")
    def validate_provenance(self) -> Self:
        has_sources = bool(self.source_refs)
        has_derivation = self.deterministic_derivation is not None
        if has_sources == has_derivation:
            raise ValueError(
                "a claim requires exactly one provenance route: source_refs or "
                "deterministic_derivation"
            )
        _require_unique(
            "source_ref",
            (f"{ref.source_id}@{ref.locator}" for ref in self.source_refs),
        )
        return self


class TeachingResource(ContractModel):
    """Learner-facing wording licensed by canonical claims."""

    resource_id: StableId
    kind: ResourceKind
    text: NonEmptyText
    claim_ids: tuple[StableId, ...] = Field(min_length=1)
    release_status: ReleaseStatus

    @model_validator(mode="after")
    def validate_claim_ids(self) -> Self:
        _require_unique("claim_id reference", self.claim_ids)
        return self


class Choice(ContractModel):
    """One stable answer option and its resource references."""

    option_id: StableId
    text: NonEmptyText
    correct: bool
    misconception_id: StableId | None = None
    hint_resource_ids: tuple[StableId, ...] = ()
    consequence_resource_id: StableId

    @model_validator(mode="after")
    def validate_feedback(self) -> Self:
        _require_unique("hint_resource_id reference", self.hint_resource_ids)
        if self.correct and (
            self.misconception_id is not None or self.hint_resource_ids
        ):
            raise ValueError(
                "a correct choice cannot contain misconception or hint references"
            )
        if not self.correct and (
            self.misconception_id is None or not self.hint_resource_ids
        ):
            raise ValueError(
                "an incorrect choice requires misconception_id and hint_resource_ids"
            )
        return self


class ScenarioImage(ContractModel):
    """Optional, non-evidentiary visual context owned by an activity."""

    path: ScenarioImagePath
    alt_text: NonEmptyText


class CausalSceneEdge(ContractModel):
    """One permitted proposed arrow in the first causal workbench."""

    parent_id: StableId
    child_id: StableId

    @model_validator(mode="after")
    def validate_distinct_nodes(self) -> Self:
        if self.parent_id == self.child_id:
            raise ValueError("a causal-scene edge cannot connect a node to itself")
        return self


class CausalSceneNode(ContractModel):
    """One variable made available to the learner's small DAG editor."""

    node_id: StableId
    label: NonEmptyText
    initially_visible: bool


class CausalSceneRecord(ContractModel):
    """One aggregate row in the M0 observational or intervention table."""

    umbrella_carried: BinarySceneValue
    pavement_wet: BinarySceneValue
    arrivals: int = Field(ge=0)


class CausalSceneIntervention(ContractModel):
    """The one declared assignment and its deterministic aggregate result."""

    action_id: StableId
    variable_id: StableId
    value: BinarySceneValue
    result_records: tuple[CausalSceneRecord, ...] = Field(min_length=1)


class CausalScenePrediction(ContractModel):
    """One content-authored prediction a learner may commit before a reveal."""

    prediction_id: StableId
    label: NonEmptyText


class CausalSceneAssessment(ContractModel):
    """The hidden, deterministic rubric for a scene's final submitted model."""

    accepted_edges: tuple[CausalSceneEdge, ...] = Field(min_length=1)
    hint_resource_ids: tuple[StableId, ...] = Field(min_length=1, max_length=2)
    accepted_consequence_resource_id: StableId
    rejected_consequence_resource_id: StableId
    rejected_misconception_id: StableId


UmbrellaHypothesisId = Literal[
    "rain-common-cause", "umbrella-causes-wet", "wet-causes-umbrella",
]


class SceneHypothesis(ContractModel):
    """One named, executable mechanism in the finite umbrella model catalog."""

    hypothesis_id: UmbrellaHypothesisId
    label: NonEmptyText
    mechanism: NonEmptyText


class CausalSceneSimulation(ContractModel):
    """Versioned finite SCMs, not equations inferred from a learner's arrows."""

    kind: Literal["umbrella_scm"] = "umbrella_scm"
    model_version: Literal["1.0.0"] = "1.0.0"
    population_size: int = Field(ge=1, le=100000)
    root_yes_count: int = Field(ge=0)
    hypotheses: tuple[SceneHypothesis, ...] = Field(min_length=2, max_length=3)
    reference_hypothesis_id: UmbrellaHypothesisId
    minimum_hypotheses: int = Field(default=2, ge=2, le=3)

    @model_validator(mode="after")
    def validate_simulation_shape(self) -> Self:
        ids = tuple(item.hypothesis_id for item in self.hypotheses)
        if len(ids) != len(set(ids)):
            raise ValueError("scene hypothesis IDs must be unique")
        if self.reference_hypothesis_id not in ids:
            raise ValueError("reference world must use a declared hypothesis")
        if self.root_yes_count > self.population_size:
            raise ValueError("scene root count cannot exceed its population")
        if self.minimum_hypotheses > len(ids):
            raise ValueError("scene comparison requires more hypotheses than declared")
        return self


class CausalScene(ContractModel):
    """Released, authored data for one deterministic M0 causal investigation."""

    scene_id: StableId
    title: NonEmptyText
    claim_ids: tuple[StableId, ...] = Field(min_length=1)
    hook_resource_id: StableId
    records_resource_id: StableId
    model_resource_id: StableId
    prediction_resource_id: StableId
    intervention_resource_id: StableId
    result_resource_id: StableId
    reflection_resource_id: StableId
    direct_explanation_resource_id: StableId
    nodes: tuple[CausalSceneNode, ...] = Field(min_length=2)
    permitted_edges: tuple[CausalSceneEdge, ...] = Field(min_length=1)
    observed_records: tuple[CausalSceneRecord, ...] = Field(min_length=1)
    intervention: CausalSceneIntervention
    predictions: tuple[CausalScenePrediction, ...] = Field(min_length=2)
    assessment: CausalSceneAssessment
    simulation: CausalSceneSimulation | None = None

    @model_validator(mode="after")
    def validate_scene_shape(self) -> Self:
        _require_unique("causal_scene claim_id", self.claim_ids)
        _require_unique("causal_scene node_id", (node.node_id for node in self.nodes))
        _require_unique("causal_scene permitted edge", (
            f"{edge.parent_id}->{edge.child_id}" for edge in self.permitted_edges
        ))
        _require_unique(
            "causal_scene prediction_id",
            (prediction.prediction_id for prediction in self.predictions),
        )
        node_ids = {node.node_id for node in self.nodes}
        unknown_nodes = {
            node_id
            for edge in self.permitted_edges
            for node_id in (edge.parent_id, edge.child_id)
        } - node_ids
        if unknown_nodes:
            raise ValueError(
                "causal-scene edges reference unknown nodes: "
                + ", ".join(sorted(unknown_nodes))
            )
        if self.intervention.variable_id not in node_ids:
            raise ValueError("causal-scene intervention references an unknown node")
        assessment_edges = {
            (edge.parent_id, edge.child_id) for edge in self.assessment.accepted_edges
        }
        permitted_edges = {
            (edge.parent_id, edge.child_id) for edge in self.permitted_edges
        }
        if not assessment_edges.issubset(permitted_edges):
            raise ValueError("causal-scene assessment contains an undeclared edge")
        if len(assessment_edges) != len(self.assessment.accepted_edges):
            raise ValueError("causal-scene assessment contains duplicate edges")
        _require_unique(
            "causal_scene assessment hint_resource_id",
            self.assessment.hint_resource_ids,
        )
        if sum(row.arrivals for row in self.observed_records) != sum(
            row.arrivals for row in self.intervention.result_records
        ):
            raise ValueError(
                "causal-scene intervention must preserve the declared arrival total"
            )
        if not any(row.arrivals for row in self.observed_records):
            raise ValueError("causal-scene records must contain at least one arrival")
        if self.simulation is not None:
            # The narrow adapter owns the equations and checks their authored
            # records. Import after contract construction to avoid a type cycle.
            from .umbrella_simulation import validate_scene_simulation
            validate_scene_simulation(self)
        return self

    @property
    def prediction_ids(self) -> tuple[StableId, ...]:
        """Keep transition validation independent of learner-visible labels."""

        return tuple(prediction.prediction_id for prediction in self.predictions)


class ComparisonTable(ContractModel):
    """One currently visible authored comparison, never a hidden result table."""

    table_id: StableId
    label: NonEmptyText
    columns: tuple[NonEmptyText, ...] = Field(min_length=1)
    rows: tuple[tuple[NonEmptyText, ...], ...] = Field(min_length=1)
    note: NonEmptyText | None = None

    @model_validator(mode="after")
    def validate_rows(self) -> Self:
        if any(len(row) != len(self.columns) for row in self.rows):
            raise ValueError("comparison table rows must match the column count")
        return self


class ComparisonWorkbench(ContractModel):
    """Released current-activity observations shared by the renderer and Tutor."""

    title: NonEmptyText
    introduction: NonEmptyText
    scenario_id: StableId
    stage: Literal["investigate", "capstone"]
    prompt: NonEmptyText | None = None
    tables: tuple[ComparisonTable, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_tables(self) -> Self:
        _require_unique("comparison table_id", (table.table_id for table in self.tables))
        return self


class EffectExperimentConfig(ContractModel):
    """Learner settings for the two-stratum intervention teaching model."""

    kind: Literal["effect"] = "effect"
    assignment: Literal["self_selected", "randomized"] = "self_selected"
    target_high_pct: int = Field(default=50, ge=0, le=100, multiple_of=10)
    analysis: Literal["pooled", "standardized"] = "pooled"


class ShiftExperimentConfig(ContractModel):
    """Learner settings for prediction and source-faithful generation."""

    kind: Literal["shift"] = "shift"
    predictor: Literal["cue", "content"] = "cue"
    cue_accuracy_pct: int = Field(default=90, ge=0, le=100, multiple_of=10)
    measurement_error_pct: int = Field(default=10, ge=0, le=100, multiple_of=10)
    metadata_available_pct: int = Field(default=100, ge=0, le=100, multiple_of=10)
    flip_cue: bool = False
    generator: Literal["fluent", "grounded"] = "fluent"


ExperimentConfig: TypeAlias = Annotated[
    EffectExperimentConfig | ShiftExperimentConfig, Field(discriminator="kind"),
]


class EffectExperimentModel(ContractModel):
    """Frozen authored rates and labels; never sent as Tutor or browser state."""

    kind: Literal["effect"] = "effect"
    a_low: float = Field(default=0.9, ge=0, le=1)
    a_high: float = Field(default=0.6, ge=0, le=1)
    b_low: float = Field(default=0.8, ge=0, le=1)
    b_high: float = Field(default=0.4, ge=0, le=1)
    selected_high_a_pct: int = Field(default=80, ge=1, le=99)
    selected_high_b_pct: int = Field(default=20, ge=1, le=99)
    low_label: NonEmptyText
    high_label: NonEmptyText
    outcome_label: NonEmptyText
    treatment_a_label: NonEmptyText
    treatment_b_label: NonEmptyText

    @model_validator(mode="after")
    def validate_source_population(self) -> Self:
        if self.selected_high_a_pct + self.selected_high_b_pct != 100:
            raise ValueError("selected programme mixtures must preserve the fixed equal-baseline source population")
        return self


class ShiftExperimentModel(ContractModel):
    """Frozen source assertions for the small deterministic shift simulator."""

    kind: Literal["shift"] = "shift"
    source_positive: NonEmptyText
    source_negative: NonEmptyText
    qualifier: NonEmptyText
    unsupported_detail: NonEmptyText


ExperimentModel: TypeAlias = Annotated[
    EffectExperimentModel | ShiftExperimentModel, Field(discriminator="kind"),
]


class ExperimentGuideMetric(ContractModel):
    """A short authored label for one existing computed experiment metric."""

    metric_label: NonEmptyText
    label: NonEmptyText


class ExperimentGuide(ContractModel):
    """Story-first presentation metadata, never simulation or scoring authority."""

    section: Literal["intervention", "prediction", "generation"]
    story: NonEmptyText
    goal: NonEmptyText
    parameter_id: Literal[
        "assignment", "target_high_pct", "analysis",
        "cue_accuracy_pct", "flip_cue", "measurement_error_pct", "generator",
    ]
    parameter_label: NonEmptyText
    parameter_description: NonEmptyText
    prediction_prompt: NonEmptyText
    comparison_prompt: NonEmptyText
    metrics: tuple[ExperimentGuideMetric, ...] = Field(min_length=1, max_length=3)

    @model_validator(mode="after")
    def validate_focus(self) -> Self:
        if (self.section == "generation") != (self.parameter_id == "generator"):
            raise ValueError("the generation guide must focus on the report generator")
        effect_controls = {"assignment", "target_high_pct", "analysis"}
        if (self.section == "intervention") != (self.parameter_id in effect_controls):
            raise ValueError("intervention guides must use an effect experiment control")
        _require_unique("guide metric", (metric.metric_label for metric in self.metrics))
        effect_metrics = {
            "Source pooled A minus B", "Target-standardized A minus B", "Selected analysis contrast",
        }
        shift_metrics = {
            "Reference prediction accuracy", "Complete source-supported reports / all cases",
            "Full-report coverage", "Source-supported / emitted reports",
            "Reports with unsupported additions / all cases",
            "Reports contradicting source flag / all cases",
        }
        allowed_metrics = effect_metrics if self.section == "intervention" else shift_metrics
        if any(metric.metric_label not in allowed_metrics for metric in self.metrics):
            raise ValueError("guide metrics must name existing result metrics for their section")
        if self.section == "prediction" and any(
                metric.metric_label != "Reference prediction accuracy" for metric in self.metrics):
            raise ValueError("prediction guides must not introduce report-generation metrics")
        return self


class ExperimentWorkbench(ContractModel):
    """One released model with learner operations before its scored check."""

    experiment_id: StableId
    title: NonEmptyText
    instructions_resource_id: StableId
    model_version: Literal["1.0.0"] = "1.0.0"
    model: ExperimentModel
    initial_config: ExperimentConfig
    min_distinct_runs: int = Field(default=2, ge=2, le=4)
    guide: ExperimentGuide | None = None

    @model_validator(mode="after")
    def validate_model_config(self) -> Self:
        if self.model.kind != self.initial_config.kind:
            raise ValueError("experiment model and initial configuration kinds must match")
        if self.guide is not None and (
                (self.guide.section == "intervention") != (self.model.kind == "effect")):
            raise ValueError("the story-first guide section must match the experiment model")
        return self


class Activity(ContractModel):
    """One deterministic activity with a declared structured response type."""

    activity_id: StableId
    concept_id: StableId
    activity_type: ActivityType = "choice"
    question_resource_id: StableId
    choices: tuple[Choice, ...] = ()
    explanation_resource_id: StableId
    scenario_image: ScenarioImage | None = None
    workbench: ComparisonWorkbench | None = None
    experiment: ExperimentWorkbench | None = None
    causal_scene_id: StableId | None = None
    requires_revision: bool = False
    is_transfer: bool = False
    covered_concept_ids: tuple[StableId, ...] = ()

    @model_validator(mode="after")
    def validate_response_contract(self) -> Self:
        _require_unique("option_id", (choice.option_id for choice in self.choices))
        if self.activity_type == "causal_scene":
            if self.causal_scene_id is None:
                raise ValueError("a causal_scene activity requires a causal_scene_id")
            if self.choices:
                raise ValueError("a causal_scene activity must not declare choices")
        elif len(self.choices) < 2 or sum(choice.correct for choice in self.choices) != 1:
            raise ValueError("an activity requires exactly one correct choice")
        if self.requires_revision and self.activity_type != "classification":
            raise ValueError("only a classification activity may require revision")
        if self.experiment is not None and self.activity_type == "causal_scene":
            raise ValueError("an experiment must use a choice or classification scored check")
        _require_unique("covered_concept_id", self.covered_concept_ids)
        if self.concept_id in self.covered_concept_ids:
            raise ValueError("covered_concept_ids must not repeat the primary concept")
        return self


class Concept(ContractModel):
    """One content-owned objective and its completion evidence requirements."""

    concept_id: StableId
    objective: NonEmptyText
    completion_activity_ids: tuple[StableId, ...] = Field(min_length=1)
    m1_ready_activity_ids: tuple[StableId, ...] = ()

    @model_validator(mode="after")
    def validate_activity_ids(self) -> Self:
        _require_unique("completion_activity_id", self.completion_activity_ids)
        _require_unique("m1_ready_activity_id", self.m1_ready_activity_ids)
        if not set(self.m1_ready_activity_ids).issubset(self.completion_activity_ids):
            raise ValueError("m1_ready activities must also be completion activities")
        return self


class LessonWorkedStep(ContractModel):
    """One authored explanatory step, separate from scored activity evidence."""

    title: NonEmptyText
    resource_id: StableId


class LessonGraphNode(ContractModel):
    """A labelled variable in the lesson's explicitly hypothetical graph."""

    node_id: StableId
    label: NonEmptyText


class LessonWorkedGraph(ContractModel):
    """A hypothetical common-cause fork supported by the current lesson renderer."""

    label: NonEmptyText
    nodes: tuple[LessonGraphNode, ...] = Field(min_length=3, max_length=3)
    edges: tuple[CausalSceneEdge, ...] = Field(min_length=2, max_length=2)
    note_resource_id: StableId

    @model_validator(mode="after")
    def validate_graph(self) -> Self:
        _require_unique("lesson graph node", (node.node_id for node in self.nodes))
        _require_unique("lesson graph edge", (
            f"{edge.parent_id}->{edge.child_id}" for edge in self.edges
        ))
        node_ids = {node.node_id for node in self.nodes}
        if any(edge.parent_id not in node_ids or edge.child_id not in node_ids for edge in self.edges):
            raise ValueError("lesson graph edges reference unknown nodes")
        common_cause = self.edges[0].parent_id
        if (
            any(edge.parent_id != common_cause for edge in self.edges)
            or {edge.child_id for edge in self.edges} != node_ids - {common_cause}
        ):
            raise ValueError("lesson worked graph must be a three-node common-cause fork")
        return self


class TeachingLesson(ContractModel):
    """An authored one-screen lesson with two linked deterministic activities."""

    profile_id: Literal["general", "medical"]
    concept_id: StableId
    title: NonEmptyText
    review_status: Literal["author_draft"] = "author_draft"
    hook_resource_id: StableId
    example_label_resource_id: StableId
    worked_steps: tuple[LessonWorkedStep, ...] = Field(min_length=1)
    worked_graph: LessonWorkedGraph | None = None
    definition_resource_id: StableId
    pitfall_resource_id: StableId
    takeaway_resource_id: StableId
    practice_activity_id: StableId
    challenge_activity_id: StableId
    challenge_title: NonEmptyText
    scenario_image: ScenarioImage | None = None

    def resource_references(self) -> tuple[tuple[str, StableId, ResourceKind], ...]:
        """Keep release checks and lecture projection tied to one reference list."""

        graph_refs = (
            (("worked_graph/note_resource_id", self.worked_graph.note_resource_id, "explanation"),)
            if self.worked_graph is not None else ()
        )
        return (
            ("hook_resource_id", self.hook_resource_id, "question"),
            ("example_label_resource_id", self.example_label_resource_id, "explanation"),
            *((f"worked_steps/{index}/resource_id", step.resource_id, "explanation")
              for index, step in enumerate(self.worked_steps)),
            *graph_refs,
            ("definition_resource_id", self.definition_resource_id, "explanation"),
            ("pitfall_resource_id", self.pitfall_resource_id, "explanation"),
            ("takeaway_resource_id", self.takeaway_resource_id, "explanation"),
        )


class ContentPack(ContractModel):
    """A versioned authored content pack with strict structural validation."""

    schema_version: Literal["3.0"]
    pack_id: StableId
    version: SemanticVersion
    title: NonEmptyText
    concepts: tuple[Concept, ...] = Field(min_length=1)
    sources: tuple[Source, ...]
    claims: tuple[Claim, ...] = Field(min_length=1)
    resources: tuple[TeachingResource, ...] = Field(min_length=1)
    activities: tuple[Activity, ...] = Field(min_length=1)
    causal_scenes: tuple[CausalScene, ...] = ()
    lesson: TeachingLesson | None = None
    lessons: tuple[TeachingLesson, ...] = ()

    @model_validator(mode="after")
    def validate_pack(self) -> Self:
        _require_unique("concept_id", (concept.concept_id for concept in self.concepts))
        _require_unique("source_id", (source.source_id for source in self.sources))
        _require_unique("claim_id", (claim.claim_id for claim in self.claims))
        _require_unique(
            "resource_id", (resource.resource_id for resource in self.resources)
        )
        _require_unique(
            "activity_id", (activity.activity_id for activity in self.activities)
        )
        _require_unique("causal_scene_id", (scene.scene_id for scene in self.causal_scenes))
        _require_unique(
            "option_id",
            (
                choice.option_id
                for activity in self.activities
                for choice in activity.choices
            ),
        )

        concepts = {concept.concept_id: concept for concept in self.concepts}
        activities = {activity.activity_id: activity for activity in self.activities}
        scene_ids = {scene.scene_id for scene in self.causal_scenes}
        activity_scene_ids = [
            activity.causal_scene_id
            for activity in self.activities
            if activity.causal_scene_id is not None
        ]
        _require_unique("activity causal_scene_id", activity_scene_ids)
        unknown_scenes = sorted(set(activity_scene_ids) - scene_ids)
        if unknown_scenes:
            raise ValueError(
                "activities reference unknown causal_scene_ids: "
                + ", ".join(unknown_scenes)
            )
        unowned_scenes = sorted(scene_ids - set(activity_scene_ids))
        if unowned_scenes:
            raise ValueError(
                "causal scenes must be owned by one activity: "
                + ", ".join(unowned_scenes)
            )
        declared_activity_concepts = {
            concept_id
            for activity in self.activities
            for concept_id in (activity.concept_id, *activity.covered_concept_ids)
        }
        unknown_concepts = sorted(declared_activity_concepts - set(concepts))
        if unknown_concepts:
            raise ValueError(
                f"activities reference unknown concept_ids: {', '.join(unknown_concepts)}"
            )
        for concept in self.concepts:
            required_ids = set(concept.completion_activity_ids)
            unknown_activities = sorted(required_ids - set(activities))
            if unknown_activities:
                raise ValueError(
                    "concept references unknown completion activities: "
                    + ", ".join(unknown_activities)
                )
            wrong_concepts = sorted(
                activity_id
                for activity_id in required_ids
                if concept.concept_id
                not in (
                    activities[activity_id].concept_id,
                    *activities[activity_id].covered_concept_ids,
                )
            )
            if wrong_concepts:
                raise ValueError(
                    "concept completion activities must teach that concept: "
                    + ", ".join(wrong_concepts)
                )
            non_transfer_ready = sorted(
                activity_id
                for activity_id in concept.m1_ready_activity_ids
                if not activities[activity_id].is_transfer
            )
            if non_transfer_ready:
                raise ValueError(
                    "m1_ready activities must be declared transfers: "
                    + ", ".join(non_transfer_ready)
                )
            authored_ids = {
                activity.activity_id
                for activity in self.activities
                if concept.concept_id
                in (activity.concept_id, *activity.covered_concept_ids)
            }
            if required_ids != authored_ids:
                raise ValueError(
                    "concept completion activities must cover every authored activity: "
                    + concept.concept_id
                )
        lessons = (*((self.lesson,) if self.lesson is not None else ()), *self.lessons)
        _require_unique("lesson concept_id", (lesson.concept_id for lesson in lessons))
        if len({lesson.profile_id for lesson in lessons}) > 1:
            raise ValueError("lessons in one content pack must use the same profile")
        for lesson in lessons:
            if lesson.concept_id not in concepts:
                raise ValueError("lesson references an unknown concept")
            if lesson.practice_activity_id == lesson.challenge_activity_id:
                raise ValueError("lesson practice and challenge must be different activities")
            for activity_id in (lesson.practice_activity_id, lesson.challenge_activity_id):
                if activity_id not in activities:
                    raise ValueError("lesson references an unknown activity: " + activity_id)
                if activities[activity_id].concept_id != lesson.concept_id:
                    raise ValueError("lesson activities must teach its unchanged concept")
                activity = activities[activity_id]
                if activity.activity_type not in ("choice", "classification") and not (
                    activity_id == lesson.challenge_activity_id
                    and lesson.concept_id == "association-is-not-causation"
                    and activity.activity_type == "causal_scene"
                    and activity.causal_scene_id in scene_ids
                ):
                    raise ValueError("lesson activities must use deterministic choices or the declared association scene challenge")
            if activities[lesson.practice_activity_id].is_transfer:
                raise ValueError("lesson practice must not be a transfer activity")
            if not activities[lesson.challenge_activity_id].is_transfer:
                raise ValueError("lesson challenge must be a declared transfer activity")
        return self


def load_content_pack(path: str | Path) -> ContentPack:
    """Load UTF-8 JSON through duplicate-key and structural validation.

    File and encoding errors retain their standard Python exception types. Invalid JSON
    or duplicate object keys raise ``ValueError``; contract failures raise Pydantic's
    ``ValidationError``. Call ``validate_release`` before using learner-facing content.
    """

    raw_json = Path(path).read_text(encoding="utf-8")
    json.loads(raw_json, object_pairs_hook=_reject_duplicate_object_keys)
    return ContentPack.model_validate_json(raw_json)


def _require_unique(label: str, values: Iterable[str]) -> None:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    if duplicates:
        raise ValueError(f"duplicate {label}: {', '.join(sorted(duplicates))}")


def _reject_duplicate_object_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON object key: {key}")
        result[key] = value
    return result
