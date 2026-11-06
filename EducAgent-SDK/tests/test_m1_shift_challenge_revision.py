"""Visible Shift teaching keeps the complementary assessments and old releases."""

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import unittest

from authoring.m1_shift_challenge_revision import apply_shift_challenge_revision
from authoring.m1_shift_revision import CONCEPT_IDS
from educagent_sdk import ClassificationEvidence, evaluate_classification, validate_release
from educagent_sdk.contracts import ContentPack
from educagent_sdk.lesson_samples import lesson_view


ROOT = Path(__file__).resolve().parents[1]
CHANGED_HOOK_IDS = {
    "m1.shift.distribution-shift.lecture.hook",
    "m1.shift.invariance-across-environments.lecture.hook",
    "m1.shift.when-predictions-can-still-fail.lecture.hook",
}
FROZEN_HASHES = {
    "m1_shift_course_general.json": "bf80dbd7ee01fe297ccc7e280cebf7e9b6ca2670fe4a9fe895affbbb20e7bcef",
    "m1_shift_course_medical.json": "b915a5100c31859592749c3a6414563dbeb21bbe849b0a1c95cb99d4cda47bc6",
    "m1_shift_course_general_1_2_0.json": "dc112f6c81b43225dd310b2ad0e186cb0bf897796962b1042446ac8458a980d3",
    "m1_shift_course_medical_1_2_0.json": "3be89e2d0ffa9f83c8674a997e4050f74f1e3c735dd3fdc4133f066f5025bd7c",
    "m1_shift_course_general_1_3_0.json": "7b74ab6e58ffc1938d2934350cdffb07b95ee134212bbf0aa7eb9696408e5f49",
    "m1_shift_course_medical_1_3_0.json": "9872b4b60d3cd50fffd6d62e870faacd9e34975030b5e7bfb78b8e5ecac9e89d",
}


def frozen_pack(profile):
    return json.loads((ROOT / f"content/m1_shift_course_{profile}_1_3_0.json").read_text(encoding="utf-8"))


def changed_paths(before, after, path=()):
    """Identify every changed leaf, rejecting structural changes separately."""
    assert type(before) is type(after), (path, "type changed")
    if isinstance(before, dict):
        assert before.keys() == after.keys(), (path, "keys changed")
        return [p for key in before for p in changed_paths(before[key], after[key], (*path, key))]
    if isinstance(before, list):
        assert len(before) == len(after), (path, "length changed")
        return [p for index, (old, new) in enumerate(zip(before, after, strict=True))
                for p in changed_paths(old, new, (*path, index))]
    return [] if before == after else [path]


class ShiftChallengeRevisionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.originals = {profile: frozen_pack(profile) for profile in ("general", "medical")}
        cls.revisions = {}
        for profile, original in cls.originals.items():
            revised = deepcopy(original)
            apply_shift_challenge_revision(revised, profile)
            revised["version"] = "1.4.0"
            cls.revisions[profile] = revised

    def test_historical_releases_remain_byte_identical(self):
        for filename, digest in FROZEN_HASHES.items():
            with self.subTest(filename=filename):
                self.assertEqual(hashlib.sha256((ROOT / "content" / filename).read_bytes()).hexdigest(), digest)

    def test_mutates_only_three_named_hooks_and_one_title_with_caller_owned_version(self):
        for profile, original in self.originals.items():
            with self.subTest(profile=profile):
                revised = deepcopy(original)
                self.assertIsNone(apply_shift_challenge_revision(revised, profile))
                self.assertEqual(revised["version"], "1.3.0")
                expected = {
                    ("resources", index, "text")
                    for index, resource in enumerate(original["resources"])
                    if resource["resource_id"] in CHANGED_HOOK_IDS
                }
                self.assertEqual(len(expected), 3)
                expected.add(("lessons", 2, "title"))
                self.assertEqual(set(changed_paths(original, revised)), expected)
                revised["version"] = "1.4.0"
                self.assertEqual(set(changed_paths(original, revised)), expected | {("version",)})
                once = deepcopy(revised)
                self.assertIsNone(apply_shift_challenge_revision(revised, profile))
                self.assertEqual(revised, once)
                self.assertEqual(original, frozen_pack(profile))

    def test_invalid_profiles_and_curricula_do_not_rewrite_another_course(self):
        original = self.originals["general"]
        for profile, pattern in (("other", "general or medical"), ("medical", "matching shift profile")):
            candidate = deepcopy(original)
            with self.assertRaisesRegex(ValueError, pattern):
                apply_shift_challenge_revision(candidate, profile)
            self.assertEqual(candidate, original)
        changed = deepcopy(original)
        changed["concepts"].reverse()
        with self.assertRaisesRegex(ValueError, "four-concept"):
            apply_shift_challenge_revision(changed, "general")
        changed = deepcopy(original)
        changed["activities"].pop()
        with self.assertRaisesRegex(ValueError, "sixteen activities"):
            apply_shift_challenge_revision(changed, "general")

    def test_new_version_releases_and_every_quiz_challenge_option_keeps_its_verdict(self):
        for profile, original in self.originals.items():
            before = ContentPack.model_validate_json(json.dumps(original))
            after = ContentPack.model_validate_json(json.dumps(self.revisions[profile]))
            with self.subTest(profile=profile):
                self.assertEqual(after.version, "1.4.0")
                self.assertEqual(validate_release(after).unused_resource_ids, ())
                self.assertEqual(len(after.activities), 16)
                self.assertEqual(len(after.lessons), 4)
                self.assertEqual(before.activities, after.activities,
                                 "all quizzes, challenges, guides, models and finals remain identical")
                for activity in after.activities:
                    if activity.activity_id not in {
                        concept + suffix for concept in CONCEPT_IDS for suffix in (".quiz", ".challenge")
                    }:
                        continue
                    for choice in activity.choices:
                        evidence = ClassificationEvidence(activity_id=activity.activity_id,
                            classification_id=choice.option_id, artifact_id="shift.facet.verdict")
                        with self.subTest(activity=activity.activity_id, option=choice.option_id):
                            self.assertEqual(evaluate_classification(before, evidence).accepted,
                                             evaluate_classification(after, evidence).accepted)
                            self.assertEqual(evaluate_classification(after, evidence).accepted, choice.correct)

    def test_visible_definition_and_worked_example_teach_all_four_distinct_facets(self):
        for profile, revised in self.revisions.items():
            pack = ContentPack.model_validate_json(json.dumps(revised))
            visible = {}
            for concept in CONCEPT_IDS:
                view = lesson_view(pack, concept)
                self.assertIsNotNone(view)
                visible[concept] = view["definition"] + " " + view["hook"]
                if concept != CONCEPT_IDS[1]:
                    with self.subTest(profile=profile, concept=concept):
                        self.assertLessEqual(len(visible[concept].split()), 150)
                        self.assertNotIn("?", view["hook"], "the example explains its reasoning")
            with self.subTest(profile=profile, facet="new-use evidence versus cause of a score gap"):
                self.assertIn("A separate test there checks the proposed use", visible[CONCEPT_IDS[0]])
                self.assertIn("scores alone cannot separate the effects", visible[CONCEPT_IDS[0]])
                self.assertIn("marker is applied differently" if profile == "medical" else "uses its labels differently",
                              visible[CONCEPT_IDS[0]])
                self.assertIn("recorded less reliably" if profile == "medical" else "records photograph findings less reliably",
                              visible[CONCEPT_IDS[0]])
            with self.subTest(profile=profile, facet="input dependence versus causal feature measurement"):
                self.assertIn("underlying outcome", visible[CONCEPT_IDS[1]])
                self.assertIn("causal feature also needs reliable measurement", visible[CONCEPT_IDS[1]])
            with self.subTest(profile=profile, facet="tested relationship versus pooled group errors"):
                self.assertEqual(lesson_view(pack, CONCEPT_IDS[2])["title"],
                                 "Check stability across settings")
                self.assertIn("range of cases", visible[CONCEPT_IDS[2]])
                self.assertIn("same overall accuracy", visible[CONCEPT_IDS[2]])
                self.assertIn("Compare errors for similar", visible[CONCEPT_IDS[2]])
                self.assertIn("Different group sizes", visible[CONCEPT_IDS[2]])
                self.assertIn("does not by itself establish", visible[CONCEPT_IDS[2]])
                self.assertIn("untested kinds", visible[CONCEPT_IDS[2]])
            with self.subTest(profile=profile, facet="source contradiction versus missing-evidence response"):
                self.assertIn("Source fidelity", visible[CONCEPT_IDS[3]])
                self.assertIn("no date", visible[CONCEPT_IDS[3]])
                self.assertIn("leave the incomplete report for review", visible[CONCEPT_IDS[3]])
                self.assertIn("does not verify the missing information", visible[CONCEPT_IDS[3]])
                self.assertIn("new recording setup still needs its own evaluation", visible[CONCEPT_IDS[3]])
            for activity in pack.activities:
                if activity.activity_id.endswith((".quiz", ".challenge")):
                    correct = next(choice.text for choice in activity.choices if choice.correct)
                    self.assertNotIn(correct, visible[activity.concept_id],
                                     "worked examples do not paste an assessment's exact correct option")

    def test_worked_examples_keep_profiles_and_prediction_generation_sections_separate(self):
        for profile, revised in self.revisions.items():
            pack = ContentPack.model_validate_json(json.dumps(revised))
            for concept in CONCEPT_IDS[:3]:
                hook = lesson_view(pack, concept)["hook"]
                with self.subTest(profile=profile, concept=concept):
                    self.assertNotIn("generation", hook.lower())
                    self.assertNotIn("write a report", hook.lower())
                    self.assertNotIn("generated draft", hook.lower())
                    self.assertNotIn("source fidelity", hook.lower())
            first = lesson_view(pack, CONCEPT_IDS[0])["hook"]
            grouped = lesson_view(pack, CONCEPT_IDS[2])["hook"]
            report = lesson_view(pack, CONCEPT_IDS[3])["hook"]
            if profile == "medical":
                self.assertIn("not a diagnosis by itself", first)
                self.assertIn("younger adults", grouped)
                self.assertIn("scan date", report)
                self.assertNotIn("warehouse", first + grouped + report)
                self.assertNotIn("parcel", first + grouped + report)
            else:
                self.assertIn("photograph", first)
                self.assertIn("small parcels", grouped)
                self.assertIn("inspection date", report)
                self.assertNotIn("hospital", first + grouped + report)
                self.assertNotIn("opacity", first + grouped + report)


if __name__ == "__main__":
    unittest.main()
