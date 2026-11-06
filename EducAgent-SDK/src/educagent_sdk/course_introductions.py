"""Authored, non-scoring course openings kept outside versioned learning packs."""

import json
from pathlib import Path
from typing import Literal, Self

from pydantic import Field, model_validator

from .contracts import (
    ContentPack, ContractModel, NonEmptyText, ScenarioImage, SemanticVersion,
    StableId, _reject_duplicate_object_keys,
)


ProfileId = Literal["general", "medical"]
IntroductionModuleId = Literal["m1_effect", "m1_shift"]


class CourseComparison(ContractModel):
    this_course_question: NonEmptyText
    other_module_id: IntroductionModuleId
    other_title: NonEmptyText
    other_course_question: NonEmptyText
    connection: NonEmptyText


class CourseIntroductionCopy(ContractModel):
    profile_id: ProfileId
    title: NonEmptyText
    question: NonEmptyText
    example: NonEmptyText
    why: NonEmptyText
    actions: tuple[NonEmptyText, ...] = Field(min_length=3, max_length=4)
    comparison: CourseComparison
    scenario_image: ScenarioImage
    image_caption: NonEmptyText


class AuthoredCourseIntroduction(CourseIntroductionCopy):
    grounding_claim_ids: tuple[StableId, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def require_unique_claims(self) -> Self:
        if len(self.grounding_claim_ids) != len(set(self.grounding_claim_ids)):
            raise ValueError("course introduction claim references must be unique")
        return self


class CourseIntroductionView(CourseIntroductionCopy):
    """Explicit browser whitelist; no assessment, private grounding or state."""

    catalog_version: SemanticVersion


class CourseIntroductionCatalog(ContractModel):
    catalog_version: SemanticVersion
    courses: dict[IntroductionModuleId, dict[ProfileId, AuthoredCourseIntroduction]]

    @model_validator(mode="after")
    def require_paired_courses_and_profiles(self) -> Self:
        if set(self.courses) != {"m1_effect", "m1_shift"}:
            raise ValueError("course openings require both authored M1 courses")
        if any(set(profiles) != {"general", "medical"} for profiles in self.courses.values()):
            raise ValueError("course openings require general and medical profiles")
        for module_id, profiles in self.courses.items():
            for profile_id, introduction in profiles.items():
                if introduction.profile_id != profile_id:
                    raise ValueError("course opening profile must match its catalog key")
                comparison = introduction.comparison
                if comparison.other_module_id == module_id:
                    raise ValueError("course opening must compare the other M1 course")
                other = self.courses[comparison.other_module_id][profile_id]
                if comparison.other_title != other.title:
                    raise ValueError("course comparison title must match the other course")
                if other.comparison.other_module_id != module_id:
                    raise ValueError("course comparisons must be reciprocal")
        return self

    def for_module(
        self, module_id: str, title: str, packs: dict[str, ContentPack],
    ) -> dict[str, CourseIntroductionView] | None:
        """Bind non-scoring copy to existing released claims without changing a pack."""

        if module_id not in self.courses:
            return None
        profiles = self.courses[module_id]
        if set(packs) != set(profiles):
            raise ValueError("course opening profiles must match the module's packs")
        views = {}
        for profile_id, introduction in profiles.items():
            if introduction.title != title:
                raise ValueError("course opening title must match the module registry")
            released_claims = {
                claim.claim_id for claim in packs[profile_id].claims
                if claim.release_status == "released"
            }
            if not set(introduction.grounding_claim_ids).issubset(released_claims):
                raise ValueError("course opening references an unknown or unreleased pack claim")
            views[profile_id] = CourseIntroductionView(
                catalog_version=self.catalog_version,
                **introduction.model_dump(exclude={"grounding_claim_ids"}),
            )
        return views


def load_course_introductions(path: str | Path) -> CourseIntroductionCatalog:
    """Load one strict authored catalog; do not load progress or invoke a tutor."""

    raw = Path(path).read_text(encoding="utf-8")
    json.loads(raw, object_pairs_hook=_reject_duplicate_object_keys)
    return CourseIntroductionCatalog.model_validate_json(raw)
