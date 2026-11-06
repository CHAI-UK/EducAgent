"""Compile authored profile examples into ordinary, independently scoped packs."""

import json
from pathlib import Path
from typing import Literal, Self

from pydantic import Field, model_validator

from .contracts import (
    Activity, CausalSceneEdge, Choice, Claim, Concept, ContentPack, ContractModel,
    DeterministicDerivation, LessonGraphNode, LessonWorkedGraph, LessonWorkedStep,
    NonEmptyText, ResourceKind, ScenarioImage, SemanticVersion, SourceRef, StableId,
    TeachingLesson, TeachingResource, _reject_duplicate_object_keys,
)
from .release import validate_release


ProfileId = Literal["general", "medical"]


class SampleChoice(ContractModel):
    option_id: StableId
    text: NonEmptyText
    correct: bool
    feedback: NonEmptyText


class SampleActivity(ContractModel):
    activity_id: StableId
    question: NonEmptyText
    choices: tuple[SampleChoice, ...] = Field(min_length=2)
    title: NonEmptyText | None = None


class SampleWorkedStep(ContractModel):
    title: NonEmptyText
    text: NonEmptyText


class SampleGraphEdge(ContractModel):
    parent_id: StableId = Field(alias="from")
    child_id: StableId = Field(alias="to")


class SampleWorkedGraph(ContractModel):
    label: NonEmptyText
    nodes: tuple[LessonGraphNode, ...] = Field(min_length=2)
    edges: tuple[SampleGraphEdge, ...] = Field(min_length=1)
    note: NonEmptyText


class SampleProfile(ContractModel):
    title: NonEmptyText
    hook: NonEmptyText
    example_label: NonEmptyText
    scenario_image: ScenarioImage
    worked_steps: tuple[SampleWorkedStep, ...] = Field(min_length=1)
    worked_graph: SampleWorkedGraph
    definition: NonEmptyText
    pitfall: NonEmptyText
    takeaway: NonEmptyText
    practice: SampleActivity
    transfer: SampleActivity


class LessonSampleSource(ContractModel):
    version: SemanticVersion
    concept_id: StableId
    objective: NonEmptyText
    source_refs: tuple[SourceRef, ...] = Field(min_length=1)
    profiles: dict[ProfileId, SampleProfile]

    @model_validator(mode="after")
    def require_profile_pair(self) -> Self:
        if set(self.profiles) != {"general", "medical"}:
            raise ValueError("lesson samples require general and medical profiles")
        return self


def load_lesson_samples(base_pack: ContentPack, path: str | Path) -> dict[ProfileId, ContentPack]:
    """Compile two fixed authored variants; never change the base curriculum."""

    raw = Path(path).read_text(encoding="utf-8")
    json.loads(raw, object_pairs_hook=_reject_duplicate_object_keys)
    source = LessonSampleSource.model_validate_json(raw)
    concept = next((item for item in base_pack.concepts if item.concept_id == source.concept_id), None)
    if concept is None or concept.objective != source.objective:
        raise ValueError("lesson sample objective must exactly match the base concept")
    known_sources = {item.source_id: item for item in base_pack.sources}
    if any(ref.source_id not in known_sources for ref in source.source_refs):
        raise ValueError("lesson sample references an unknown base source")
    return {
        profile_id: _compile_profile(base_pack, source, profile_id, profile)
        for profile_id, profile in source.profiles.items()
    }


def _compile_profile(
    base_pack: ContentPack, source: LessonSampleSource,
    profile_id: ProfileId, profile: SampleProfile,
) -> ContentPack:
    prefix = f"foundation.lesson.{profile_id}"
    base_claims = {item.claim_id: item for item in base_pack.claims}
    scientific_ids = (
        "association-does-not-establish-cause", "records-show-association",
        "intervention-deliberately-sets", "causal-direction-is-assumption", "dag-terms",
    )
    if any(claim_id not in base_claims for claim_id in scientific_ids):
        raise ValueError("foundation lesson samples need the released M0 causal claims")
    common_cause_id = "foundation.lesson.common-cause"
    synthetic_id = prefix + ".synthetic"
    claims = [base_claims[claim_id] for claim_id in scientific_ids]
    claims.extend((
        Claim(
            claim_id=common_cause_id,
            proposition="A common cause can produce an observed association; the observed pattern alone does not establish a causal direction or prove that proposed explanation.",
            source_refs=source.source_refs, release_status="released",
        ),
        Claim(
            claim_id=synthetic_id,
            proposition="The situations, possible common-cause explanations and graph in this lesson are authored synthetic teaching examples, not verified findings about real people or treatments.",
            deterministic_derivation=DeterministicDerivation(
                method_id="foundation.lesson-sample", method_version=source.version,
            ),
            release_status="released",
        ),
    ))
    association_id = scientific_ids[0]
    scenario_claims = (association_id, common_cause_id, synthetic_id)
    resources: list[TeachingResource] = []

    def resource(
        suffix: str, kind: ResourceKind, text: str,
        claim_ids: tuple[str, ...] = scenario_claims,
    ) -> str:
        resource_id = prefix + "." + suffix
        resources.append(TeachingResource(
            resource_id=resource_id, kind=kind, text=text,
            claim_ids=claim_ids, release_status="released",
        ))
        return resource_id

    hook_id = resource("hook", "question", profile.hook)
    example_id = resource("example-label", "explanation", profile.example_label, (synthetic_id,))
    worked_steps = tuple(LessonWorkedStep(
        title=step.title,
        resource_id=resource(
            f"worked-step.{index + 1}", "explanation", step.text,
            (*scientific_ids[:4], common_cause_id, synthetic_id),
        ),
    ) for index, step in enumerate(profile.worked_steps))
    definition_id = resource("definition", "explanation", profile.definition, scientific_ids[:3])
    pitfall_id = resource("pitfall", "explanation", profile.pitfall)
    takeaway_id = resource("takeaway", "explanation", profile.takeaway, (association_id, scientific_ids[3]))
    graph_note_id = resource(
        "graph-note", "explanation", profile.worked_graph.note,
        (association_id, scientific_ids[3], scientific_ids[4], synthetic_id),
    )
    activities: list[Activity] = []
    for activity_kind, authored in (("practice", profile.practice), ("transfer", profile.transfer)):
        question_id = resource(activity_kind + ".question", "question", authored.question)
        hint_id = resource(
            activity_kind + ".hint", "hint",
            "Separate the recorded association from what would happen if a variable were deliberately changed. Consider whether more than one explanation fits the records.",
            (*scenario_claims, "intervention-deliberately-sets"),
        )
        choices = tuple(Choice(
            option_id=f"{authored.activity_id}.{choice.option_id}",
            text=choice.text, correct=choice.correct,
            consequence_resource_id=resource(
                f"{activity_kind}.feedback.{choice.option_id}", "consequence", choice.feedback,
            ),
            hint_resource_ids=() if choice.correct else (hint_id,),
            misconception_id=None if choice.correct else f"{prefix}.{choice.option_id}",
        ) for choice in authored.choices)
        activities.append(Activity(
            activity_id=authored.activity_id, concept_id=source.concept_id,
            activity_type="choice", question_resource_id=question_id,
            explanation_resource_id=definition_id, choices=choices,
            is_transfer=activity_kind == "transfer",
            scenario_image=profile.scenario_image if activity_kind == "practice" else None,
        ))
    lesson = TeachingLesson(
        profile_id=profile_id, concept_id=source.concept_id, title=profile.title,
        hook_resource_id=hook_id, example_label_resource_id=example_id,
        worked_steps=worked_steps,
        worked_graph=LessonWorkedGraph(
            label=profile.worked_graph.label, nodes=profile.worked_graph.nodes,
            edges=tuple(CausalSceneEdge(parent_id=edge.parent_id, child_id=edge.child_id)
                        for edge in profile.worked_graph.edges),
            note_resource_id=graph_note_id,
        ),
        definition_resource_id=definition_id, pitfall_resource_id=pitfall_id,
        takeaway_resource_id=takeaway_id,
        practice_activity_id=profile.practice.activity_id,
        challenge_activity_id=profile.transfer.activity_id,
        challenge_title=profile.transfer.title or "Fresh challenge",
        scenario_image=profile.scenario_image,
    )
    used_claim_ids = {claim_id for item in resources for claim_id in item.claim_ids}
    claims = [item for item in claims if item.claim_id in used_claim_ids]
    used_source_ids = {ref.source_id for claim in claims for ref in claim.source_refs}
    pack = ContentPack(
        schema_version="3.0", pack_id=f"causality.foundation-sample.{profile_id}",
        version=source.version, title=profile.title,
        concepts=(Concept(
            concept_id=source.concept_id, objective=source.objective,
            completion_activity_ids=tuple(item.activity_id for item in activities),
        ),),
        sources=tuple(item for item in base_pack.sources if item.source_id in used_source_ids),
        claims=tuple(claims), resources=tuple(resources), activities=tuple(activities), lesson=lesson,
    )
    validate_release(pack)
    return pack


class LessonStepView(ContractModel):
    title: NonEmptyText
    text: NonEmptyText


class LessonGraphView(ContractModel):
    label: NonEmptyText
    nodes: tuple[LessonGraphNode, ...]
    edges: tuple[SampleGraphEdge, ...]
    note: NonEmptyText


class LessonSourceView(ContractModel):
    source_id: StableId
    citation: NonEmptyText
    locator: NonEmptyText


class LessonView(ContractModel):
    """Released lecture copy only; never include scoring keys or feedback."""

    profile_id: ProfileId
    version: SemanticVersion
    concept_id: StableId
    objective: NonEmptyText
    title: NonEmptyText
    review_status: Literal["author_draft"]
    hook: NonEmptyText
    example_label: NonEmptyText
    worked_steps: tuple[LessonStepView, ...]
    worked_graph: LessonGraphView | None
    definition: NonEmptyText
    pitfall: NonEmptyText
    takeaway: NonEmptyText
    practice_activity_id: StableId
    challenge_activity_id: StableId
    challenge_title: NonEmptyText
    scenario_image: ScenarioImage | None
    sources: tuple[LessonSourceView, ...]


def lesson_projection(pack: ContentPack, concept_id: str | None = None) -> LessonView | None:
    """Project frozen released lesson resources, without activity answer data."""

    lesson = next((item for item in pack.lessons if item.concept_id == concept_id), None)
    if lesson is None and pack.lesson is not None and (
        concept_id is None or pack.lesson.concept_id == concept_id
    ):
        lesson = pack.lesson
    if lesson is None and concept_id is None and pack.lessons:
        lesson = pack.lessons[0]
    if lesson is None:
        return None
    validate_release(pack)
    resources = {resource.resource_id: resource for resource in pack.resources}
    claims = {claim.claim_id: claim for claim in pack.claims}
    sources = {source.source_id: source for source in pack.sources}
    refs = {
        (ref.source_id, ref.locator)
        for _, resource_id, _ in lesson.resource_references()
        for claim_id in resources[resource_id].claim_ids
        for ref in claims[claim_id].source_refs
    }
    return LessonView(
        profile_id=lesson.profile_id, version=pack.version, concept_id=lesson.concept_id,
        objective=next(item.objective for item in pack.concepts if item.concept_id == lesson.concept_id),
        title=lesson.title, review_status=lesson.review_status,
        hook=resources[lesson.hook_resource_id].text,
        example_label=resources[lesson.example_label_resource_id].text,
        worked_steps=tuple(LessonStepView(title=step.title, text=resources[step.resource_id].text)
                           for step in lesson.worked_steps),
        worked_graph=LessonGraphView(
            label=lesson.worked_graph.label, nodes=lesson.worked_graph.nodes,
            edges=tuple(SampleGraphEdge(**{"from": edge.parent_id, "to": edge.child_id})
                        for edge in lesson.worked_graph.edges),
            note=resources[lesson.worked_graph.note_resource_id].text,
        ) if lesson.worked_graph is not None else None,
        definition=resources[lesson.definition_resource_id].text,
        pitfall=resources[lesson.pitfall_resource_id].text,
        takeaway=resources[lesson.takeaway_resource_id].text,
        practice_activity_id=lesson.practice_activity_id,
        challenge_activity_id=lesson.challenge_activity_id, challenge_title=lesson.challenge_title,
        scenario_image=lesson.scenario_image,
        sources=tuple(LessonSourceView(
            source_id=source_id, citation=sources[source_id].citation, locator=locator,
        ) for source_id, locator in sorted(refs)),
    )


def lesson_view(pack: ContentPack, concept_id: str | None = None) -> dict[str, object] | None:
    """A JSON-ready value snapshot for browser and guided tutor context."""

    view = lesson_projection(pack, concept_id)
    return None if view is None else view.model_dump(mode="json", by_alias=True)


def lesson_lecture_context(pack: ContentPack, concept_id: str | None = None) -> tuple[str, ...]:
    """Read-only tutor context: the lecture, not unseen challenge answers."""

    view = lesson_projection(pack, concept_id)
    if view is None:
        return ()
    graph_context: tuple[str, ...] = ()
    if view.worked_graph is not None:
        labels = {node.node_id: node.label for node in view.worked_graph.nodes}
        graph_context = (
            view.worked_graph.label,
            *(f"Proposed arrow: {labels[edge.parent_id]} -> {labels[edge.child_id]}"
              for edge in view.worked_graph.edges),
            view.worked_graph.note,
        )
    return (
        view.title, view.example_label, view.hook,
        *(f"{step.title}: {step.text}" for step in view.worked_steps),
        *graph_context, view.definition, view.pitfall, view.takeaway,
    )
