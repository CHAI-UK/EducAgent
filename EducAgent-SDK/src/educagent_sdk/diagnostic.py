"""Reusable deterministic entry diagnostics built from released activities."""

import json
from collections.abc import Iterable
from pathlib import Path
from typing import Literal, Self

from pydantic import Field, model_validator

from .contracts import Activity, ContentPack, ContractModel, NonEmptyText, SemanticVersion, StableId
from .evaluation import ClassificationEvidence, ChoiceEvidence, Evaluation, evaluate_evidence
from .release import validate_release


DiagnosticStatus = Literal["not_started", "in_progress", "completed"]
StartingPoint = Literal["new_to_m0", "emerging_foundations", "ready_to_begin"]


class DiagnosticPlan(ContractModel):
    """An authored selection of released activities for a low-stakes entry check."""

    schema_version: Literal["1.0"]
    diagnostic_id: StableId
    version: SemanticVersion
    title: NonEmptyText
    introduction: NonEmptyText
    activity_ids: tuple[StableId, ...] = Field(min_length=1, max_length=24)

    @model_validator(mode="after")
    def validate_activity_ids(self) -> Self:
        _require_unique("diagnostic activity_id", self.activity_ids)
        return self


class DiagnosticResponse(ContractModel):
    """One append-only deterministic diagnostic response."""

    request_id: StableId
    activity_id: StableId
    option_id: StableId
    evaluation: Evaluation


class DiagnosticSession:
    """Run a low-stakes check; the host owns optional review routing."""

    def __init__(self, pack: ContentPack, plan: DiagnosticPlan) -> None:
        validate_release(pack)
        self.pack = pack
        self.plan = plan
        self.activities = _resolve_activities(pack, plan.activity_ids)
        self.responses: list[DiagnosticResponse] = []
        self._started = False

    def start(self) -> dict[str, object]:
        """Mark the diagnostic ready without creating an answer record."""

        self._started = True
        return self.view()

    def respond(self, *, request_id: StableId, option_id: StableId) -> dict[str, object]:
        """Evaluate and append the answer to the current diagnostic activity."""

        if not self._started:
            raise ValueError("start the diagnostic before answering")
        existing = next(
            (item for item in self.responses if item.request_id == request_id), None
        )
        if existing is not None:
            if existing.option_id != option_id:
                raise ValueError("request_id was reused with different content")
            return self.view()
        if len(self.responses) == len(self.activities):
            raise ValueError("the diagnostic is already complete")

        activity = self.activities[len(self.responses)]
        evidence = _evidence_for(activity, option_id, self.plan.diagnostic_id, len(self.responses))
        self.responses.append(
            DiagnosticResponse(
                request_id=request_id,
                activity_id=activity.activity_id,
                option_id=option_id,
                evaluation=evaluate_evidence(self.pack, evidence),
            )
        )
        return self.view()

    def reset(self) -> dict[str, object]:
        """Clear local diagnostic responses; the M0 event trace is unaffected."""

        self.responses.clear()
        self._started = False
        return self.view()

    def view(self) -> dict[str, object]:
        """Return a presentation-safe, deterministic snapshot."""

        answered_count = len(self.responses)
        completed = answered_count == len(self.activities)
        status: DiagnosticStatus
        if not self._started:
            status = "not_started"
        elif completed:
            status = "completed"
        else:
            status = "in_progress"
        activity = None if completed or not self._started else self.activities[answered_count]
        result = None if not completed else self._result()
        displayed_choices = (
            ()
            if activity is None
            else activity.choices
            if answered_count % 2 == 0
            else tuple(reversed(activity.choices))
        )
        return {
            "status": status,
            "diagnostic_id": self.plan.diagnostic_id,
            "title": self.plan.title,
            "introduction": self.plan.introduction,
            "answered_count": answered_count,
            "total": len(self.activities),
            "question": None if activity is None else _resource_text(self.pack, activity.question_resource_id),
            "scenario_image": (
                None if activity is None or activity.scenario_image is None else activity.scenario_image.model_dump()
            ),
            "workbench": (
                None if activity is None or activity.workbench is None
                else activity.workbench.model_dump(mode="json")
            ),
            "choices": []
            if activity is None
            else [
                {"option_id": choice.option_id, "text": choice.text}
                for choice in displayed_choices
            ],
            "concept_results": self._concept_results(),
            "result": result,
        }

    def _concept_results(self) -> list[dict[str, object]]:
        """Project answered diagnostic concepts without treating them as M0 completion."""

        responses = {response.activity_id: response for response in self.responses}
        return [
            {
                "concept_id": activity.concept_id,
                "status": (
                    "correct"
                    if response is not None and response.evaluation.accepted
                    else "incorrect"
                    if response is not None
                    else "current"
                    if index == len(self.responses) and self._started
                    else "later"
                ),
            }
            for index, activity in enumerate(self.activities)
            for response in (responses.get(activity.activity_id),)
        ]

    def _result(self) -> dict[str, object]:
        accepted_count = sum(item.evaluation.accepted for item in self.responses)
        return {
            "accepted_count": accepted_count,
            "total": len(self.activities),
            "starting_point": _starting_point(accepted_count, len(self.activities)),
            "concept_results": [
                {
                    "concept_id": activity.concept_id,
                    "accepted": response.evaluation.accepted,
                }
                for activity, response in zip(self.activities, self.responses, strict=True)
            ],
            "next_step": "Choose a review route or the complete M0 route. This starting snapshot does not replace activity-completion evidence.",
        }


def load_diagnostic_plan(path: str | Path) -> DiagnosticPlan:
    """Load one authored diagnostic plan with duplicate-key protection."""

    raw_json = Path(path).read_text(encoding="utf-8")
    json.loads(raw_json, object_pairs_hook=_reject_duplicate_object_keys)
    return DiagnosticPlan.model_validate_json(raw_json)


def _resolve_activities(
    pack: ContentPack, activity_ids: tuple[StableId, ...]
) -> tuple[Activity, ...]:
    by_id = {activity.activity_id: activity for activity in pack.activities}
    unknown_ids = sorted(set(activity_ids) - set(by_id))
    if unknown_ids:
        raise ValueError(
            "diagnostic references unknown activities: " + ", ".join(unknown_ids)
        )
    return tuple(by_id[activity_id] for activity_id in activity_ids)


def _evidence_for(
    activity: Activity,
    option_id: StableId,
    diagnostic_id: StableId,
    index: int,
) -> ChoiceEvidence | ClassificationEvidence:
    if activity.activity_type == "choice":
        return ChoiceEvidence(activity_id=activity.activity_id, option_id=option_id)
    return ClassificationEvidence(
        activity_id=activity.activity_id,
        classification_id=option_id,
        artifact_id=f"diagnostic.{diagnostic_id}.artifact.{index + 1}",
    )


def _resource_text(pack: ContentPack, resource_id: StableId) -> str:
    return next(
        resource.text for resource in pack.resources if resource.resource_id == resource_id
    )


def _starting_point(accepted_count: int, total: int) -> StartingPoint:
    if accepted_count * 3 < total:
        return "new_to_m0"
    if accepted_count * 3 < total * 2:
        return "emerging_foundations"
    return "ready_to_begin"


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
