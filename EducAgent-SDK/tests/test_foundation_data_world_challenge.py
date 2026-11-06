"""The new transfer distinguishes data/world while the old model quiz stays frozen."""

import copy
import unittest

from authoring.build_foundation_course import ROOT
from authoring.foundation_assessment_revision import apply_data_world_challenge
from educagent_sdk import ClassificationEvidence, evaluate_classification, load_content_pack, validate_release


PREFIX = "world-data-model.transfer.data-world"


class FoundationDataWorldChallengeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.packs = {profile: load_content_pack(ROOT / f"content/foundation_{profile}_course_1_7_0.json")
                     for profile in ("general", "medical")}
        cls.historical = {profile: load_content_pack(ROOT / f"content/foundation_{profile}_course_1_6_0.json")
                          for profile in cls.packs}

    def test_each_new_pair_has_its_declared_verdict_and_the_old_answer_still_belongs_to_1_6(self):
        expected = {f"{PREFIX}.recorded-and-physical": True,
                    f"{PREFIX}.swapped": False, f"{PREFIX}.model-as-data": False}
        for profile, pack in self.packs.items():
            with self.subTest(profile=profile):
                activity = next(item for item in pack.activities if item.activity_id == "world-data-model.transfer")
                old = next(item for item in self.historical[profile].activities if item.activity_id == activity.activity_id)
                self.assertEqual(pack.version, "1.7.0")
                self.assertEqual({choice.option_id for choice in activity.choices}, set(expected))
                self.assertFalse({choice.option_id for choice in activity.choices}
                                 & {choice.option_id for choice in old.choices})
                self.assertEqual(next(i for i, choice in enumerate(activity.choices) if choice.correct),
                                 next(i for i, choice in enumerate(old.choices) if choice.correct))
                system = "laboratory device"
                readings = "laboratory readings" if profile == "medical" else "sensor readings"
                right = next(choice for choice in activity.choices if choice.correct)
                self.assertEqual(right.text,
                    f"Data: the {readings} saved in the log. World: the physical {system} and the processes that produce its readings.")
                for choice in activity.choices:
                    evidence = ClassificationEvidence(activity_id=activity.activity_id,
                        classification_id=choice.option_id, artifact_id=f"data-world.{profile}.{choice.option_id}")
                    verdict = evaluate_classification(pack, evidence)
                    self.assertEqual(verdict.accepted, expected[choice.option_id])
                    self.assertEqual(choice.correct, expected[choice.option_id])
                    self.assertEqual(verdict.consequence_resource_id,
                                     f"{PREFIX}.accepted" if verdict.accepted else f"{PREFIX}.rejected")
                    if not verdict.accepted:
                        self.assertEqual(choice.hint_resource_ids, (f"{PREFIX}.hint",))
                old_answer = ClassificationEvidence(activity_id=old.activity_id,
                    classification_id="world-data-model.transfer.model", artifact_id=f"old-model.{profile}")
                self.assertTrue(evaluate_classification(self.historical[profile], old_answer).accepted)
                with self.assertRaises(ValueError):
                    evaluate_classification(pack, old_answer)

    def test_support_explains_data_and_world_independently_without_rewriting_the_model_quiz(self):
        for profile, pack in self.packs.items():
            with self.subTest(profile=profile):
                resources = {item.resource_id: item for item in pack.resources}
                old_resources = {item.resource_id: item for item in self.historical[profile].resources}
                quiz = next(item for item in pack.activities if item.activity_id == "world-data-model.practice")
                old_quiz = next(item for item in self.historical[profile].activities if item.activity_id == quiz.activity_id)
                self.assertEqual(quiz, old_quiz)
                self.assertEqual(next(choice.option_id for choice in quiz.choices if choice.correct),
                                 "world-data-model.practice.model")
                activity = next(item for item in pack.activities if item.activity_id == "world-data-model.transfer")
                question = resources[activity.question_resource_id].text
                self.assertIn("logs", question)
                self.assertIn("sketches how it works", question)
                self.assertIn("A hospital engineer" if profile == "medical" else "a university laboratory", question)
                self.assertTrue(question.endswith("Which option correctly identifies the data and the world?"))
                self.assertEqual(activity.explanation_resource_id, f"{PREFIX}.explanation")
                explanation = resources[activity.explanation_resource_id].text
                system = "laboratory device"
                self.assertIn("Data are the measurement values saved in the log.", explanation)
                self.assertIn(f"The world is the physical {system} and the processes that produce its readings.", explanation)
                self.assertIn("The engineer's sketch is a model", explanation)
                for suffix, template in (
                    ("explanation", "world-data-model.explanation"),
                    ("hint", "world-data-model.hint"),
                    ("accepted", "world-data-model.consequence.accepted"),
                    ("rejected", "world-data-model.consequence.rejected"),
                ):
                    added, before = resources[f"{PREFIX}.{suffix}"], old_resources[template]
                    self.assertEqual(added.model_copy(update={"resource_id": before.resource_id, "text": before.text}), before)
                    self.assertEqual(resources[template], before)
                rejected = resources[f"{PREFIX}.rejected"].text
                self.assertTrue(rejected.startswith("Not yet."))
                self.assertNotIn(explanation, rejected)
                self.assertEqual(validate_release(pack).unused_resource_ids, ())

    def test_all_content_outside_the_declared_assessment_revisions_matches_the_frozen_course(self):
        for profile, pack in self.packs.items():
            with self.subTest(profile=profile):
                actual = pack.model_dump(mode="json")
                expected = self.historical[profile].model_dump(mode="json")
                actual["version"] = expected["version"]
                claim = next(item for item in actual["claims"] if item["claim_id"] == "foundation.final-case")
                claim["deterministic_derivation"]["method_version"] = expected["version"]
                before_activity = next(item for item in expected["activities"] if item["activity_id"] == "world-data-model.transfer")
                activity = next(item for item in actual["activities"] if item["activity_id"] == before_activity["activity_id"])
                activity["choices"] = before_activity["choices"]
                activity["explanation_resource_id"] = before_activity["explanation_resource_id"]
                before_question = next(item for item in expected["resources"] if item["resource_id"] == before_activity["question_resource_id"])
                next(item for item in actual["resources"] if item["resource_id"] == before_question["resource_id"])["text"] = before_question["text"]
                self.assertEqual([item["resource_id"] for item in actual["resources"][-4:]],
                                 [f"{PREFIX}.{suffix}" for suffix in ("explanation", "hint", "accepted", "rejected")])
                actual["resources"] = actual["resources"][:-4]
                # The separate assumptions-table presentation keeps all choices
                # and permits only these two workbenches and four text records.
                for activity_id in ("data-vs-assumptions.practice", "data-vs-assumptions.transfer"):
                    before = next(item for item in expected["activities"] if item["activity_id"] == activity_id)
                    next(item for item in actual["activities"] if item["activity_id"] == activity_id)["workbench"] = before["workbench"]
                for resource_id in ("assumptions.question.practice", "assumptions.question.transfer",
                                    "assumptions.explanation", "assumptions.consequence.rejected"):
                    before = next(item for item in expected["resources"] if item["resource_id"] == resource_id)
                    next(item for item in actual["resources"] if item["resource_id"] == resource_id)["text"] = before["text"]
                before_lesson = next(item for item in expected["lessons"] if item["concept_id"] == "world-data-model")
                next(item for item in actual["lessons"] if item["concept_id"] == "world-data-model")["challenge_title"] = before_lesson["challenge_title"]
                self.assertEqual(actual, expected)

    def test_unknown_profile_cannot_partly_rewrite_a_course(self):
        data = self.historical["general"].model_dump(mode="json")
        before = copy.deepcopy(data)
        with self.assertRaisesRegex(ValueError, "Unknown Foundations profile"):
            apply_data_world_challenge(data, "unknown")
        self.assertEqual(data, before)
