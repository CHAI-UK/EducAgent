"""Compile fixed context variants while preserving the selected M0 assessment contract."""

import json
from pathlib import Path
from typing import Self

from pydantic import Field, model_validator

from .contracts import (
    CausalSceneEdge, Claim, ContentPack, ContractModel, DeterministicDerivation,
    LessonWorkedGraph, LessonWorkedStep, NonEmptyText, ResourceKind, ScenarioImage,
    SemanticVersion, SourceRef, StableId, TeachingLesson, TeachingResource,
    _reject_duplicate_object_keys,
)
from .lesson_samples import ProfileId, SampleWorkedGraph, SampleWorkedStep
from .release import validate_release


CONCEPT_CLAIM_IDS = {
    "variables-and-values": ("variables-take-values",),
    "observed-association": ("records-show-association",),
    "association-is-not-causation": (
        "association-does-not-establish-cause", "records-show-association",
        "intervention-deliberately-sets", "causal-direction-is-assumption",
    ),
    "treatment-and-outcome": ("treatment-changes-outcome-question",),
    "observation-vs-intervention": ("intervention-deliberately-sets",),
    "world-data-model": ("world-data-model-distinct",),
    "data-vs-assumptions": ("causal-direction-is-assumption", "records-show-association"),
    "basic-dag-language": ("dag-terms", "causal-direction-is-assumption"),
    "probabilistic-effects": ("causes-can-change-probability",),
}


class FoundationLecture(ContractModel):
    """One independently authored page; no assessment answers or scene outcomes."""

    concept_id: StableId
    title: NonEmptyText
    hook: NonEmptyText
    worked_steps: tuple[SampleWorkedStep, ...] = Field(min_length=1)
    definition: NonEmptyText
    pitfall: NonEmptyText
    takeaway: NonEmptyText
    example_label: NonEmptyText = "Synthetic teaching example; not a real-world finding."
    scenario_image: ScenarioImage | None = None
    worked_graph: SampleWorkedGraph | None = None
    source_refs: tuple[SourceRef, ...] = ()
    challenge_title: NonEmptyText = "Try a new case"


class FoundationProfile(ContractModel):
    """Medical overrides name existing questions/options, never grading semantics."""

    lectures: tuple[FoundationLecture, ...] = Field(min_length=9, max_length=9)
    resources: dict[StableId, NonEmptyText] = Field(default_factory=dict)
    choice_text: dict[StableId, NonEmptyText] = Field(default_factory=dict)
    activity_images: dict[StableId, ScenarioImage | None] = Field(default_factory=dict)


class FoundationProfileSource(ContractModel):
    """Strict source: version plus General/Medical profiles with nine ordered lectures."""

    version: SemanticVersion
    profiles: dict[ProfileId, FoundationProfile]

    @model_validator(mode="after")
    def require_pair(self) -> Self:
        if set(self.profiles) != {"general", "medical"}:
            raise ValueError("Foundations source requires general and medical profiles")
        general = self.profiles["general"]
        if general.resources or general.choice_text or general.activity_images:
            raise ValueError("General teaching companion cannot override original assessments")
        return self


def load_foundation_profiles(
    base_pack: ContentPack, path: str | Path,
) -> dict[ProfileId, ContentPack]:
    """Return a General teaching companion and a separately versioned Medical pack.

    The normal General controller must continue scoring with ``base_pack`` and its
    existing trace. The General return value is only its read-only teaching source.
    """

    validate_release(base_pack)
    if tuple(item.concept_id for item in base_pack.concepts) != tuple(CONCEPT_CLAIM_IDS):
        raise ValueError("Foundations profiles require the selected nine-concept M0 backbone")
    raw = Path(path).read_text(encoding="utf-8")
    json.loads(raw, object_pairs_hook=_reject_duplicate_object_keys)
    source = FoundationProfileSource.model_validate_json(raw)
    claim_ids = {item.claim_id for item in base_pack.claims}
    if any(claim_id not in claim_ids for ids in CONCEPT_CLAIM_IDS.values() for claim_id in ids):
        raise ValueError("Foundations profiles require the existing released M0 scientific claims")
    known_sources = {item.source_id for item in base_pack.sources}
    for profile in source.profiles.values():
        if tuple(item.concept_id for item in profile.lectures) != tuple(CONCEPT_CLAIM_IDS):
            raise ValueError("Foundations lectures must preserve all nine concept IDs and their order")
        if any(ref.source_id not in known_sources for lecture in profile.lectures for ref in lecture.source_refs):
            raise ValueError("Foundations lecture references an unknown base source")
    medical = source.profiles["medical"]
    ordinary_questions = {
        activity.question_resource_id for activity in base_pack.activities
        if activity.activity_type != "causal_scene"
    }
    if set(medical.resources) != ordinary_questions:
        raise ValueError("Medical resources must override exactly the non-scene activity questions")
    known_options = {choice.option_id for activity in base_pack.activities for choice in activity.choices}
    if set(medical.choice_text) - known_options:
        raise ValueError("Medical choice text references an unknown option ID")
    ordinary_activities = {
        activity.activity_id for activity in base_pack.activities
        if activity.activity_type != "causal_scene"
    }
    if set(medical.activity_images) - ordinary_activities:
        raise ValueError("Medical images must name existing non-scene activities")
    return {
        profile_id: _compile_foundation(base_pack, source.version, profile_id, profile)
        for profile_id, profile in source.profiles.items()
    }


def _compile_foundation(
    base_pack: ContentPack, version: str, profile_id: ProfileId, profile: FoundationProfile,
) -> ContentPack:
    resources = [
        resource.model_copy(update={"text": profile.resources[resource.resource_id]})
        if resource.resource_id in profile.resources else resource
        for resource in base_pack.resources
    ]
    activities = tuple(activity.model_copy(update={
        "choices": tuple(
            choice.model_copy(update={"text": profile.choice_text[choice.option_id]})
            if choice.option_id in profile.choice_text else choice
            for choice in activity.choices
        ),
        "scenario_image": profile.activity_images.get(activity.activity_id, activity.scenario_image),
    }) for activity in base_pack.activities)
    claims = list(base_pack.claims)
    base_claims = {item.claim_id: item for item in base_pack.claims}
    concepts = {item.concept_id: item for item in base_pack.concepts}
    synthetic_id = f"foundation.{profile_id}.synthetic"
    claims.append(Claim(
        claim_id=synthetic_id,
        proposition="The independently authored profile lectures and adapted questions are synthetic teaching examples, not verified clinical or real-world findings. The shared rain simulator keeps its own declared rules and assessment.",
        deterministic_derivation=DeterministicDerivation(
            method_id="foundation.profile-context", method_version=version,
        ),
        release_status="released",
    ))
    if profile_id == "medical":
        resources = [
            resource.model_copy(update={"claim_ids": (*resource.claim_ids, synthetic_id)})
            if resource.resource_id in profile.resources else resource
            for resource in resources
        ]
    lessons: list[TeachingLesson] = []
    for lecture in profile.lectures:
        prefix = f"foundation.{profile_id}.{lecture.concept_id}"
        scientific_ids = CONCEPT_CLAIM_IDS[lecture.concept_id]
        if lecture.source_refs:
            reference_id = prefix + ".reference"
            claims.append(base_claims[scientific_ids[0]].model_copy(update={
                "claim_id": reference_id, "source_refs": lecture.source_refs,
            }))
            scientific_ids = (reference_id, *scientific_ids[1:])
        lecture_claims = (*scientific_ids, synthetic_id)

        def resource(suffix: str, kind: ResourceKind, text: str) -> str:
            resource_id = prefix + "." + suffix
            resources.append(TeachingResource(
                resource_id=resource_id, kind=kind, text=text,
                claim_ids=lecture_claims, release_status="released",
            ))
            return resource_id

        hook_id = resource("hook", "question", lecture.hook)
        example_id = resource("example-label", "explanation", lecture.example_label)
        steps = tuple(LessonWorkedStep(
            title=step.title,
            resource_id=resource(f"worked-step.{index + 1}", "explanation", step.text),
        ) for index, step in enumerate(lecture.worked_steps))
        graph = None
        if lecture.worked_graph is not None:
            graph = LessonWorkedGraph(
                label=lecture.worked_graph.label, nodes=lecture.worked_graph.nodes,
                edges=tuple(CausalSceneEdge(parent_id=edge.parent_id, child_id=edge.child_id)
                            for edge in lecture.worked_graph.edges),
                note_resource_id=resource("graph-note", "explanation", lecture.worked_graph.note),
            )
        concept = concepts[lecture.concept_id]
        practice_id, challenge_id = concept.completion_activity_ids[:2]
        lessons.append(TeachingLesson(
            profile_id=profile_id, concept_id=lecture.concept_id, title=lecture.title,
            hook_resource_id=hook_id, example_label_resource_id=example_id,
            worked_steps=steps, worked_graph=graph,
            definition_resource_id=resource("definition", "explanation", lecture.definition),
            pitfall_resource_id=resource("pitfall", "explanation", lecture.pitfall),
            takeaway_resource_id=resource("takeaway", "explanation", lecture.takeaway),
            practice_activity_id=practice_id, challenge_activity_id=challenge_id,
            challenge_title=lecture.challenge_title, scenario_image=lecture.scenario_image,
        ))
    pack = ContentPack(
        schema_version=base_pack.schema_version,
        pack_id="causality.m0.general.teaching" if profile_id == "general" else "causality.m0.medical",
        version=version,
        title="Causality M0 Foundations: General teaching" if profile_id == "general" else "Causality M0 Foundations: Medical context",
        concepts=base_pack.concepts, sources=base_pack.sources,
        claims=tuple(claims), resources=tuple(resources), activities=activities,
        causal_scenes=base_pack.causal_scenes, lessons=tuple(lessons),
    )
    validate_release(pack)
    return pack
