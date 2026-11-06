"""Reviewed wording must not change historical assessments or evidence authority."""

import copy
import json
import unittest
from pathlib import Path

from authoring.foundation_expert_review import apply_review
from educagent_sdk import ContentPack, load_content_pack, validate_release
from educagent_sdk.foundation_profiles import load_foundation_profiles


ROOT = Path(__file__).resolve().parents[1]


class FoundationExpertReviewTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.historical = load_content_pack(ROOT / "content/causality_m0_full.json")
        cls.profiles = load_foundation_profiles(
            cls.historical, ROOT / "content/foundation_profiles.json",
        )

    def reviewed(self, profile_id):
        data = self.profiles[profile_id].model_dump(mode="json")
        before = copy.deepcopy(data)
        apply_review(data, profile_id)
        return before, data

    def test_display_review_preserves_ids_scoring_structure_and_provenance(self):
        for profile_id in self.profiles:
            with self.subTest(profile=profile_id):
                before, data = self.reviewed(profile_id)
                self.assertEqual(data["claims"], before["claims"])
                self.assertEqual(data["sources"], before["sources"])
                self.assertEqual(data["concepts"], before["concepts"])
                self.assertEqual(data["causal_scenes"], before["causal_scenes"])
                self.assertEqual(data["pack_id"], before["pack_id"])
                self.assertEqual(data["version"], before["version"])
                for original, reviewed in zip(before["resources"], data["resources"], strict=True):
                    self.assertEqual({key: value for key, value in original.items() if key != "text"},
                                     {key: value for key, value in reviewed.items() if key != "text"})
                for original, reviewed in zip(before["activities"], data["activities"], strict=True):
                    self.assertEqual({key: value for key, value in original.items()
                                      if key not in {"choices", "scenario_image"}},
                                     {key: value for key, value in reviewed.items()
                                      if key not in {"choices", "scenario_image"}})
                    for old_choice, new_choice in zip(original["choices"], reviewed["choices"], strict=True):
                        self.assertEqual({key: value for key, value in old_choice.items() if key != "text"},
                                         {key: value for key, value in new_choice.items() if key != "text"})
                pack = ContentPack.model_validate_json(json.dumps(data))
                self.assertEqual(validate_release(pack).unused_resource_ids, ())
                self.assertEqual(self.profiles[profile_id].model_dump(mode="json"), before)

    def test_nine_practice_questions_and_options_are_clear_without_overclaiming(self):
        for profile_id in self.profiles:
            with self.subTest(profile=profile_id):
                _, data = self.reviewed(profile_id)
                resources = {item["resource_id"]: item["text"] for item in data["resources"]}
                choices = {choice["option_id"]: choice["text"]
                           for activity in data["activities"] for choice in activity["choices"]}
                self.assertIn("Could resting heart rate", resources["variables.question.practice"])
                self.assertIn("based on these observations", resources["association.question.practice"])
                self.assertIn("alone establish", resources["not-causation.question.practice"])
                self.assertIn("different drug dose", resources["treatment.question.practice"])
                self.assertIn("changing the drug dose", choices["treatment.practice.yes"])
                self.assertNotIn("hence", choices["treatment.practice.yes"])
                self.assertIn("without assigning", resources["intervention.question.practice"])
                self.assertIn("diagram data or a model", resources["world-data-model.question.practice"])
                self.assertIn("these records", resources["assumptions.question.practice"])
                self.assertIn("proposed causal diagram", resources["dag.question.practice"])
                self.assertEqual(choices["dag.practice.arrow"], "A proposed causal relationship")
                self.assertTrue(resources["probability.question.practice"].startswith("Suppose"))
                self.assertEqual(choices["probability.practice.probabilistic"], "Probabilistic")
                self.assertEqual(choices["probability.practice.deterministic"], "Deterministic")

    def test_probability_is_hypothetical_and_museum_does_not_assert_identification(self):
        for profile_id in self.profiles:
            with self.subTest(profile=profile_id):
                _, data = self.reviewed(profile_id)
                resources = {item["resource_id"]: item["text"] for item in data["resources"]}
                lessons = {item["concept_id"]: item for item in data["lessons"]}
                probability = lessons["probabilistic-effects"]
                self.assertTrue(resources[probability["hook_resource_id"]].startswith("Suppose"))
                self.assertIn("not a clinical finding", resources[probability["example_label_resource_id"]])
                self.assertTrue(all("simulator" not in resources[step["resource_id"]]
                                    for step in probability["worked_steps"]))
                self.assertIn("not establish a real treatment benefit", resources[probability["pitfall_resource_id"]])
                self.assertEqual(probability["review_status"], "author_draft")
                if profile_id == "general":
                    assumptions = lessons["data-vs-assumptions"]
                    self.assertIn("donations", resources[assumptions["hook_resource_id"]])
                    self.assertIn("visitor numbers cause both", resources[assumptions["hook_resource_id"]])
                    self.assertIn("pattern alone does not establish", resources[assumptions["worked_steps"][2]["resource_id"]])
                    self.assertIn("tutorial", resources["probability.question.transfer"])
                    self.assertNotIn("onboarding", probability["challenge_title"])

    def test_fictional_cleanup_is_limited_to_visible_copy(self):
        _, data = self.reviewed("medical")
        data["claims"][0]["proposition"] += " Fictional provenance retained."
        data["sources"][0]["citation"] += " Fictional source citation retained."
        resource = next(item for item in data["resources"] if item["resource_id"] == "variables.explanation")
        resource["text"] = "Fictional patients visit a fictional clinic."
        activity = next(item for item in data["activities"] if item["activity_id"] == "variables-and-values.transfer")
        activity["choices"][0]["text"] = "A fictional case"
        data["activities"][0]["scenario_image"] = {
            "path": "media/example.png", "alt_text": "Fictional patients in a clinic.",
        }
        provenance = copy.deepcopy((data["claims"], data["sources"]))
        apply_review(data, "medical")
        self.assertEqual((data["claims"], data["sources"]), provenance)
        self.assertEqual(resource["text"], "Patients visit a clinic.")
        self.assertEqual(activity["choices"][0]["text"], "A case")
        for resource in data["resources"]:
            self.assertNotIn("fictional", resource["text"].lower())
        for item in [*data["activities"], *data["lessons"]]:
            if item.get("scenario_image") is not None:
                self.assertNotIn("fictional", item["scenario_image"]["alt_text"].lower())
        self.assertEqual(data["activities"][0]["scenario_image"]["path"], "media/example.png")

    def test_unknown_profile_is_rejected_before_mutation(self):
        data = self.profiles["general"].model_dump(mode="json")
        before = copy.deepcopy(data)
        with self.assertRaisesRegex(ValueError, "general or medical"):
            apply_review(data, "unknown")
        self.assertEqual(data, before)


if __name__ == "__main__":
    unittest.main()
