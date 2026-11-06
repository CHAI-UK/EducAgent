"""Effect Challenges assess taught facets without changing operational practice."""

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import unittest

from authoring.m1_effect_challenge_revision import apply_effect_challenge_revision
from educagent_sdk import ClassificationEvidence, ContentPack, evaluate_classification, load_content_pack, validate_release
from educagent_sdk.lesson_samples import lesson_projection
from tests.test_m1_courses import comparison_config, run_model


ROOT = Path(__file__).resolve().parents[1]
FROZEN_HASHES = {
    "general": "d33d176a28b966572935faeb15fb3cc319f99174ed3d0221635e65f4ede23e11",
    "medical": "420005acd77586e751868d13e26fbc3587b31245699f81d1a5deb086c9c7337e",
}
CHALLENGE = "average-treatment-effect.challenge"


class EffectChallengeRevisionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.originals = {
            profile: load_content_pack(ROOT / f"content/m1_effect_course_{profile}_1_3_0.json")
            for profile in FROZEN_HASHES
        }
        cls.revisions = {}
        for profile, original in cls.originals.items():
            data = original.model_dump(mode="json")
            apply_effect_challenge_revision(data, profile)
            data["version"] = "1.4.0"
            cls.revisions[profile] = ContentPack.model_validate_json(json.dumps(data))

    def test_frozen_release_curriculum_every_quiz_practice_and_final_remain_exact(self):
        for profile, before in self.originals.items():
            path = ROOT / f"content/m1_effect_course_{profile}_1_3_0.json"
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), FROZEN_HASHES[profile])
            after = self.revisions[profile]
            self.assertEqual(after.version, "1.4.0")
            self.assertEqual(len(after.activities), 16)
            self.assertEqual(len(after.lessons), 4)
            for field in ("schema_version", "pack_id", "title", "concepts", "sources", "claims"):
                self.assertEqual(getattr(before, field), getattr(after, field))
            for old_lesson, new_lesson in zip(before.lessons, after.lessons, strict=True):
                if old_lesson.concept_id == "average-treatment-effect":
                    self.assertEqual(old_lesson.title, "Report the average difference and its units")
                    self.assertEqual(new_lesson.title, "Average effects and individual outcomes")
                    self.assertEqual(old_lesson.model_dump(exclude={"title"}),
                                     new_lesson.model_dump(exclude={"title"}))
                else:
                    self.assertEqual(old_lesson, new_lesson)
            self.assertEqual([a.activity_id for a in before.activities], [a.activity_id for a in after.activities])
            for old, new in zip(before.activities, after.activities, strict=True):
                if old.activity_id != CHALLENGE:
                    self.assertEqual(old, new)
                else:
                    self.assertEqual(old.model_dump(exclude={"choices"}), new.model_dump(exclude={"choices"}))
                    self.assertEqual([c.correct for c in old.choices], [c.correct for c in new.choices])
                    for before_choice, after_choice in zip(old.choices, new.choices, strict=True):
                        self.assertEqual(before_choice.model_dump(exclude={"option_id", "text", "misconception_id"}),
                                         after_choice.model_dump(exclude={"option_id", "text", "misconception_id"}))
            allowed = {
                "m1.effect.defining-an-intervention.lecture.definition",
                "m1.effect.average-treatment-effect.lecture.definition",
                "m1.effect.average-treatment-effect.lecture.hook",
                "m1.effect.confounding-and-adjustment.lecture.hook",
                "m1.effect.identifiability-of-effects.lecture.definition",
                *(f"m1.effect.{CHALLENGE}.{suffix}" for suffix in (
                    "question", "hint", "explanation", "accepted", "rejected")),
            }
            changed = set()
            for old, new in zip(before.resources, after.resources, strict=True):
                self.assertEqual(old.resource_id, new.resource_id)
                self.assertEqual(old.model_dump(exclude={"text"}), new.model_dump(exclude={"text"}))
                if old.text != new.text:
                    changed.add(old.resource_id)
            self.assertEqual(changed, allowed)
            self.assertEqual(validate_release(after).unused_resource_ids, ())

    def test_all_new_answer_ids_are_distinct_and_evaluate_only_the_supported_meaning(self):
        for profile, pack in self.revisions.items():
            before = next(a for a in self.originals[profile].activities if a.activity_id == CHALLENGE)
            activity = next(a for a in pack.activities if a.activity_id == CHALLENGE)
            self.assertTrue({c.option_id for c in before.choices}.isdisjoint(c.option_id for c in activity.choices))
            for choice in activity.choices:
                result = evaluate_classification(pack, ClassificationEvidence(
                    activity_id=CHALLENGE, classification_id=choice.option_id,
                    artifact_id="effect.complementary.challenge",
                ))
                self.assertEqual(result.accepted, choice.correct)
                self.assertEqual(result.consequence_resource_id, choice.consequence_resource_id)
            resources = {r.resource_id: r for r in pack.resources}
            stem = resources[activity.question_resource_id].text
            self.assertIn("54/100", stem)
            self.assertIn("40/100", stem)
            self.assertIn("day 30", stem)
            self.assertIn("any one patient's" if profile == "medical" else "any one student's", stem)
            self.assertNotIn("risk difference", stem)
            self.assertIn("group-average", next(c.text for c in activity.choices if c.correct))
            quiz = next(a for a in pack.activities if a.activity_id == "average-treatment-effect.quiz")
            quiz_refs = {quiz.question_resource_id, quiz.explanation_resource_id,
                         *(c.consequence_resource_id for c in quiz.choices),
                         *(r for c in quiz.choices for r in c.hint_resource_ids)}
            challenge_refs = {activity.question_resource_id, activity.explanation_resource_id,
                              *(c.consequence_resource_id for c in activity.choices),
                              *(r for c in activity.choices for r in c.hint_resource_ids)}
            self.assertTrue(quiz_refs.isdisjoint(challenge_refs))
            self.assertIn("uncertainty", resources[activity.explanation_resource_id].text)

    def test_every_challenge_facet_is_taught_in_the_default_visible_core(self):
        markers = {
            "defining-an-intervention": ("some people may not take up", "Randomization applies to assignment", "comparing actual users"),
            "average-treatment-effect": ("An individual's effect", "Group averages do not reveal", "be harmed"),
            "confounding-and-adjustment": ("Practice time is a mediator", "total effect includes this pathway", "Adjusting for practice time would block it"),
            "identifiability-of-effects": ("Transport asks", "follow-up time", "evidence and assumptions for that new target"),
        }
        for profile, pack in self.revisions.items():
            for concept_id, phrases in markers.items():
                with self.subTest(profile=profile, topic=concept_id):
                    view = lesson_projection(pack, concept_id)
                    # App's default article renders definition and hook;
                    # worked steps are inside the closed explanation sidebar.
                    visible = view.definition + "\n" + view.hook
                    self.assertLessEqual(len(visible.split()), 150)
                    for phrase in phrases:
                        self.assertIn(phrase, visible)
                    activity = next(a for a in pack.activities if a.activity_id == view.challenge_activity_id)
                    self.assertNotIn(next(c.text for c in activity.choices if c.correct), visible)
                    if concept_id == "average-treatment-effect":
                        self.assertIn("two hypothetical people", view.hook)
                        self.assertIn("higher is better", view.hook)
                        self.assertIn("10 points", view.hook)
                        self.assertIn("2 points", view.hook)
                        self.assertIn("+4 points", view.hook)
                        self.assertIn("given for the example", view.hook)

    def test_every_operational_model_config_guide_and_computed_result_is_unchanged(self):
        for profile, pack in self.revisions.items():
            original = self.originals[profile]
            for old, new in zip(original.activities, pack.activities, strict=True):
                if new.experiment is None:
                    continue
                self.assertEqual(old.experiment, new.experiment)
                self.assertEqual(old.workbench, new.workbench)
                for config in (new.experiment.initial_config, comparison_config(new)):
                    self.assertEqual(run_model(old.experiment, config), run_model(new.experiment, config))

    def test_revision_is_idempotent_and_rejects_other_profiles_before_mutating(self):
        for profile, original in self.originals.items():
            data = original.model_dump(mode="json")
            apply_effect_challenge_revision(data, profile)
            revised = deepcopy(data)
            apply_effect_challenge_revision(data, profile)
            self.assertEqual(data, revised)
            self.assertEqual(data["version"], "1.3.0")
        data = self.originals["general"].model_dump(mode="json")
        frozen = deepcopy(data)
        with self.assertRaisesRegex(ValueError, "general or medical"):
            apply_effect_challenge_revision(data, "other")
        with self.assertRaisesRegex(ValueError, "matching Effect profile"):
            apply_effect_challenge_revision(data, "medical")
        self.assertEqual(data, frozen)


if __name__ == "__main__":
    unittest.main()
