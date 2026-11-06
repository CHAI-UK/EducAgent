"""The new scene interaction changes assumptions, not the M0 curriculum."""

import copy
import json
from pathlib import Path
import unittest

from authoring.foundation_dynamic_umbrella import apply_dynamic_umbrella


ROOT = Path(__file__).resolve().parents[1]


class DynamicUmbrellaContentTest(unittest.TestCase):
    def historical(self, profile):
        return json.loads((ROOT / f"content/foundation_{profile}_course_1_5_0.json")
                          .read_text(encoding="utf-8"))

    def test_revision_only_adds_simulation_and_updates_existing_scene_copy(self):
        for profile in ("general", "medical"):
            with self.subTest(profile=profile):
                original = self.historical(profile)
                updated = copy.deepcopy(original)
                apply_dynamic_umbrella(updated)
                self.assertEqual(updated["concepts"], original["concepts"])
                self.assertEqual(updated["activities"], original["activities"])
                self.assertEqual(updated["lessons"], original["lessons"])
                self.assertEqual(updated["claims"], original["claims"])
                self.assertEqual(updated["sources"], original["sources"])
                self.assertEqual(len(updated["activities"]), 28)
                self.assertEqual(len(updated["concepts"]), 9)
                for before, after in zip(original["resources"], updated["resources"], strict=True):
                    if before["resource_id"].startswith("scene.rain-umbrella."):
                        self.assertEqual({**after, "text": before["text"]}, before)
                    else:
                        self.assertEqual(after, before)
                simulation = updated["causal_scenes"][0].pop("simulation")
                self.assertEqual(updated["causal_scenes"], original["causal_scenes"])
                self.assertEqual(simulation["minimum_hypotheses"], 2)
                self.assertEqual(simulation["reference_hypothesis_id"], "rain-common-cause")
                self.assertEqual([item["hypothesis_id"] for item in simulation["hypotheses"]],
                                 ["rain-common-cause", "umbrella-causes-wet", "wet-causes-umbrella"])

    def test_general_and_medical_share_explicit_rules_and_scientific_boundaries(self):
        revised = []
        for profile in ("general", "medical"):
            updated = self.historical(profile)
            apply_dynamic_umbrella(updated)
            revised.append(updated)
            resources = {item["resource_id"]: item["text"] for item in updated["resources"]}
            self.assertIn("Arrows alone do not specify numerical predictions", resources["scene.rain-umbrella.model"])
            self.assertIn("does not establish a unique graph", resources["scene.rain-umbrella.reflection"])
            self.assertIn("unscored", resources["scene.rain-umbrella.prediction"])
            self.assertIn("unscored", resources["scene.rain-umbrella.consequence.accepted"])
            self.assertNotIn("reference", " ".join(item["label"] + item["mechanism"]
                                                    for item in updated["causal_scenes"][0]["simulation"]["hypotheses"]))
            frozen = copy.deepcopy(updated)
            apply_dynamic_umbrella(updated)
            self.assertEqual(updated, frozen)
        self.assertEqual(revised[0]["causal_scenes"], revised[1]["causal_scenes"])


if __name__ == "__main__":
    unittest.main()
