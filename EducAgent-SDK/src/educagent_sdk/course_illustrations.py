"""Presentation-only illustrations bound to exact authored course versions."""

import json
from pathlib import Path
from typing import Self

from pydantic import Field, model_validator

from .contracts import (
    ContentPack, ContractModel, ScenarioImage, SemanticVersion, StableId,
    _reject_duplicate_object_keys,
)


class PackIllustrations(ContractModel):
    pack_id: StableId
    pack_version: SemanticVersion
    activities: dict[StableId, StableId | None] = Field(default_factory=dict)
    lessons: dict[StableId, StableId | None] = Field(default_factory=dict)


class CourseIllustrationCatalog(ContractModel):
    catalog_version: SemanticVersion
    images: dict[StableId, ScenarioImage]
    packs: tuple[PackIllustrations, ...]

    @model_validator(mode="after")
    def validate_references(self) -> Self:
        identities = [(pack.pack_id, pack.pack_version) for pack in self.packs]
        if len(identities) != len(set(identities)):
            raise ValueError("illustration pack identities must be unique")
        for pack in self.packs:
            for image_id in (*pack.activities.values(), *pack.lessons.values()):
                if image_id is not None and image_id not in self.images:
                    raise ValueError("illustration references an unknown image")
        return self

    def for_pack(self, pack: ContentPack) -> ContentPack:
        """Return an image-only teaching overlay, never mutate a scored pack.

        Explicit activity bindings prevent a lesson's picture from silently
        illustrating a different transfer case or revealing a scene's answer.
        Older course versions retain their original presentation and evidence.
        """

        binding = next((item for item in self.packs
                        if (item.pack_id, item.pack_version) == (pack.pack_id, pack.version)), None)
        if binding is None:
            return pack
        lessons = pack.lessons + (() if pack.lesson is None else (pack.lesson,))
        activities = {item.activity_id: item for item in pack.activities}
        if not set(binding.activities).issubset(activities):
            raise ValueError("illustration references an unknown activity")
        # Integrated transfer is also rendered as a Challenge, even though it
        # is not one lesson's declared pair. Keep all staged/final surfaces out.
        if any(activities[key].causal_scene_id is not None or activities[key].experiment is not None
               or (activities[key].workbench is not None and activities[key].workbench.stage == "capstone")
               for key in binding.activities):
            raise ValueError("illustrations cannot decorate staged scenes, experiments or final assessments")
        if not set(binding.lessons).issubset({lesson.concept_id for lesson in lessons}):
            raise ValueError("illustration references an unknown lesson")

        def image(image_id: str | None) -> ScenarioImage | None:
            return None if image_id is None else self.images[image_id]

        def illustrated_lesson(lesson):
            return lesson.model_copy(update={"scenario_image": image(binding.lessons[lesson.concept_id])}) \
                if lesson.concept_id in binding.lessons else lesson

        return pack.model_copy(update={
            "activities": tuple(
                item.model_copy(update={"scenario_image": image(binding.activities[item.activity_id])})
                if item.activity_id in binding.activities else item
                for item in pack.activities
            ),
            "lessons": tuple(illustrated_lesson(lesson) for lesson in pack.lessons),
            "lesson": None if pack.lesson is None else illustrated_lesson(pack.lesson),
        })


def load_course_illustrations(path: str | Path) -> CourseIllustrationCatalog:
    raw = Path(path).read_text(encoding="utf-8")
    json.loads(raw, object_pairs_hook=_reject_duplicate_object_keys)
    return CourseIllustrationCatalog.model_validate_json(raw)
