"""Complementary facets have visible teaching and versioned deterministic answers."""

import copy
import unittest

from authoring.build_foundation_course import ROOT, build, course_path
from authoring.foundation_complementary_challenges import apply_complementary_challenges
from educagent_sdk import ClassificationEvidence, evaluate_classification, load_content_pack, validate_release
from educagent_sdk.lesson_samples import lesson_projection


REVISED = {
    "variables-and-values": ("variables.transfer.value", "recorded-value"),
    "observed-association": ("association.transfer.linked-records", "same-case"),
    "treatment-and-outcome": ("treatment.transfer.roles", "action-and-result"),
    "observation-vs-intervention": ("intervention.transfer.set-value", "actively-set"),
    "data-vs-assumptions": ("assumptions.transfer.observation", "recorded-statement"),
    "probabilistic-effects": ("probability.transfer.mechanism", "not-determined"),
}


class FoundationComplementaryChallengesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.packs = {profile: build(profile) for profile in ("general", "medical")}
        cls.previous = {profile: load_content_pack(ROOT / f"content/foundation_{profile}_course_1_7_0.json")
                        for profile in cls.packs}

    def test_every_new_option_is_evaluated_with_new_ids_and_the_old_display_position(self):
        for profile, pack in self.packs.items():
            with self.subTest(profile=profile):
                self.assertEqual(pack.version, "1.8.0")
                self.assertEqual(pack, load_content_pack(course_path(profile)))
                self.assertEqual((len(pack.concepts), len(pack.activities), len(pack.lessons)), (9, 28, 9))
                old_activities = {item.activity_id: item for item in self.previous[profile].activities}
                resources = {item.resource_id: item.text for item in pack.resources}
                for concept, (prefix, accepted_suffix) in REVISED.items():
                    activity_id = concept + ".transfer"
                    activity = next(item for item in pack.activities if item.activity_id == activity_id)
                    old = old_activities[activity_id]
                    self.assertEqual(len(activity.choices), len(old.choices))
                    self.assertEqual(next(i for i, choice in enumerate(activity.choices) if choice.correct),
                                     next(i for i, choice in enumerate(old.choices) if choice.correct))
                    self.assertFalse({choice.option_id for choice in activity.choices}
                                     & {choice.option_id for choice in old.choices})
                    self.assertEqual(activity.explanation_resource_id, prefix + ".explanation")
                    for choice in activity.choices:
                        verdict = evaluate_classification(pack, ClassificationEvidence(
                            activity_id=activity_id, classification_id=choice.option_id,
                            artifact_id=f"facets.{profile}.{choice.option_id}"))
                        expected = choice.option_id == prefix + "." + accepted_suffix
                        self.assertEqual(verdict.accepted, expected)
                        self.assertEqual(choice.correct, expected)
                        self.assertEqual(verdict.consequence_resource_id,
                                         prefix + (".accepted" if expected else ".rejected"))
                        if not expected:
                            self.assertEqual(choice.hint_resource_ids, (prefix + ".hint",))
                            feedback = resources[choice.consequence_resource_id]
                            right = next(item.text for item in activity.choices if item.correct)
                            self.assertTrue(feedback.startswith("Not yet."))
                            self.assertNotIn(right, feedback)
                            self.assertNotIn(resources[activity.explanation_resource_id], feedback)
                    old_answer = next(choice.option_id for choice in old.choices if choice.correct)
                    with self.assertRaises(ValueError):
                        evaluate_classification(pack, ClassificationEvidence(activity_id=activity_id,
                            classification_id=old_answer, artifact_id=f"old-facet.{profile}.{concept}"))
                self.assertEqual(validate_release(pack).unused_resource_ids, ())

    def test_default_visible_core_teaches_the_facets_without_copying_challenge_examples(self):
        for profile, pack in self.packs.items():
            lessons = {concept.concept_id: lesson_projection(pack, concept.concept_id) for concept in pack.concepts}
            self.assertIn("A value is one entry", lessons["variables-and-values"].definition)
            association = lessons["observed-association"]
            self.assertIn("For this comparison", association.definition)
            self.assertIn("count combinations of values", association.definition)
            self.assertIn("Separate unlinked totals", association.definition)
            self.assertIn("record pairs", association.hook)
            self.assertIn("treatment is the change", lessons["treatment-and-outcome"].definition)
            self.assertIn("outcome is the result", lessons["treatment-and-outcome"].definition)
            self.assertIn("Selecting records with a value is not the same as setting", lessons["observation-vs-intervention"].definition)
            self.assertIn("Data describe recorded values", lessons["data-vs-assumptions"].definition)
            probability = lessons["probabilistic-effects"]
            self.assertIn("starting conditions differ", probability.definition)
            self.assertIn("deterministic or random", probability.definition)
            self.assertIn("teaching model may use a fixed rule", probability.hook)
            self.assertIn("starting conditions" if profile == "medical" else "prior knowledge", probability.hook)
            self.assertNotIn("readmission", probability.hook)
            self.assertNotIn("continued use", probability.hook)
            for lesson in lessons.values():
                self.assertLessEqual(len((lesson.definition + " " + lesson.hook).split()), 150)

    def test_revised_answers_match_values_roles_actions_and_the_actual_observational_records(self):
        for profile, pack in self.packs.items():
            activities = {item.activity_id: item for item in pack.activities}
            right = {concept: next(choice.text for choice in activities[concept + ".transfer"].choices if choice.correct)
                     for concept in REVISED}
            self.assertEqual(right["variables-and-values"],
                "One recorded value of systolic blood pressure." if profile == "medical" else "One recorded value of waiting time.")
            self.assertIn("Each patient's" if profile == "medical" else "Each user's", right["observed-association"])
            self.assertIn("Outcome: mobility" if profile == "medical" else "Outcome: continued use", right["treatment-and-outcome"])
            self.assertTrue(right["observation-vs-intervention"].startswith(
                "In a supervised study session" if profile == "medical" else "Set "))
            self.assertIn("fixed rules or includes randomness", right["probabilistic-effects"])
            records = activities["data-vs-assumptions.transfer"].workbench.tables[0].rows
            if profile == "medical":
                self.assertIn(("Yes", "1"), records)
                self.assertEqual(right["data-vs-assumptions"],
                                 "One patient used the tracker and had one nurse contact in the recorded week.")
            else:
                self.assertIn(("4", "1"), records)
                self.assertEqual(right["data-vs-assumptions"],
                                 "One user had four help-page visits and one bug report in the recorded week.")

    def test_only_six_transfers_their_support_and_four_visible_resources_change_from_1_7(self):
        for profile, pack in self.packs.items():
            with self.subTest(profile=profile):
                expected = self.previous[profile].model_dump(mode="json")
                actual = pack.model_dump(mode="json")
                actual["version"] = expected["version"]
                next(item for item in actual["claims"] if item["claim_id"] == "foundation.final-case")["deterministic_derivation"]["method_version"] = expected["version"]
                old_activities = {item["activity_id"]: item for item in expected["activities"]}
                old_resources = {item["resource_id"]: item for item in expected["resources"]}
                old_lessons = {item["concept_id"]: item for item in expected["lessons"]}
                editable_resources = set()
                added_ids = []
                for concept, (prefix, _) in REVISED.items():
                    before = old_activities[concept + ".transfer"]
                    after = next(item for item in actual["activities"] if item["activity_id"] == before["activity_id"])
                    after["choices"] = before["choices"]
                    after["explanation_resource_id"] = before["explanation_resource_id"]
                    if before["workbench"] is not None:
                        after["workbench"]["prompt"] = before["workbench"]["prompt"]
                        if concept == "observed-association":
                            after["workbench"]["introduction"] = before["workbench"]["introduction"]
                    editable_resources.add(before["question_resource_id"])
                    next(item for item in actual["lessons"] if item["concept_id"] == concept)["challenge_title"] = old_lessons[concept]["challenge_title"]
                    right = next(item for item in before["choices"] if item["correct"])
                    wrong = next(item for item in before["choices"] if not item["correct"])
                    templates = {"explanation": before["explanation_resource_id"],
                                 "hint": wrong["hint_resource_ids"][0],
                                 "accepted": right["consequence_resource_id"],
                                 "rejected": wrong["consequence_resource_id"]}
                    for suffix, template in templates.items():
                        resource_id = prefix + "." + suffix
                        added_ids.append(resource_id)
                        added = next(item for item in actual["resources"] if item["resource_id"] == resource_id)
                        self.assertEqual({**added, "resource_id": template, "text": old_resources[template]["text"]},
                                         old_resources[template])
                for concept in ("observed-association", "probabilistic-effects"):
                    for field in ("definition_resource_id", "hook_resource_id"):
                        editable_resources.add(old_lessons[concept][field])
                self.assertEqual([item["resource_id"] for item in actual["resources"][len(expected["resources"]):]], added_ids)
                actual["resources"] = actual["resources"][:len(expected["resources"])]
                for resource in actual["resources"]:
                    if resource["resource_id"] in editable_resources:
                        resource["text"] = old_resources[resource["resource_id"]]["text"]
                self.assertEqual(actual, expected)

    def test_unknown_profile_cannot_partially_change_a_frozen_pack(self):
        data = self.previous["general"].model_dump(mode="json")
        before = copy.deepcopy(data)
        with self.assertRaisesRegex(ValueError, "Unknown Foundations profile"):
            apply_complementary_challenges(data, "unknown")
        self.assertEqual(data, before)
