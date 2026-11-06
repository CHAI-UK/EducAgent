"""Explicit neutral artwork never rewrites curriculum, grading or saved evidence."""

import json
from pathlib import Path
import tempfile
import unittest

from pydantic import ValidationError
from pydantic_ai.models.test import TestModel

from educagent_sdk import load_content_pack
from educagent_sdk.course_illustrations import CourseIllustrationCatalog, load_course_illustrations
from educagent_sdk.demo import DemoController
from educagent_sdk.lesson_samples import lesson_view
from educagent_sdk.web_demo import _state
from examples.playable_demo import _build_module, _load_registry


ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "content/course_illustrations.json"


def without_images(pack):
    value = pack.model_dump(mode="json")
    for item in value["activities"] + value["lessons"]:
        item.pop("scenario_image", None)
    if value["lesson"] is not None:
        value["lesson"].pop("scenario_image", None)
    return value


class CourseIllustrationTest(unittest.TestCase):
    def setUp(self):
        self.catalog = load_course_illustrations(CATALOG)
        self.entries = _load_registry(ROOT / "content/modules.json")

    def test_all_six_profiles_only_change_images_and_preserve_original_packs(self):
        self.assertEqual(len(self.catalog.packs), 20)
        for entry in self.entries:
            for profile, path in entry["profile_pack_paths"].items():
                with self.subTest(module=entry["module_id"], profile=profile):
                    pack = load_content_pack(ROOT / path)
                    original = pack.model_dump_json()
                    illustrated = self.catalog.for_pack(pack)
                    self.assertEqual(without_images(illustrated), without_images(pack))
                    self.assertEqual(pack.model_dump_json(), original)
                    controller = DemoController(pack, teaching_pack=illustrated, profile_id=profile)
                    self.assertIs(controller.pack, pack)
                    self.assertIs(controller.teaching_pack, illustrated)

    def test_every_catalog_image_exists_and_has_accessible_context_not_a_remote_url(self):
        for image in self.catalog.images.values():
            self.assertTrue((ROOT / "web/public" / image.path).is_file(), image.path)
            self.assertGreater(len(image.alt_text), 35)
            self.assertTrue(image.path.startswith("media/"))

    def test_current_question_projection_uses_explicit_image_and_no_lesson_fallback(self):
        for module_id, profile, expected in (
            ("causality_m0", "general", "foundation-general-it-v1.png"),
            ("causality_m0", "medical", "variables-and-values-clinic.png"),
            ("m1_effect", "general", "effect-general-library-v1.png"),
            ("m1_effect", "medical", "treatment-and-outcome-consultation.png"),
            ("m1_shift", "general", "shift-general-parcels-v1.png"),
            ("m1_shift", "medical", "shift-medical-imaging-v1.png"),
        ):
            entry = next(item for item in self.entries if item["module_id"] == module_id)
            pack = load_content_pack(ROOT / entry["profile_pack_paths"][profile])
            controller = DemoController(pack, teaching_pack=self.catalog.for_pack(pack), profile_id=profile)
            view = controller.start()
            self.assertTrue(view["scenario_image"]["path"].endswith(expected))
        # An independent transfer case uses its own explicit picture, not a fallback.
        effect = next(item for item in self.entries if item["module_id"] == "m1_effect")
        pack = self.catalog.for_pack(load_content_pack(ROOT / effect["profile_pack_paths"]["general"]))
        challenge = next(item for item in pack.activities
                         if item.activity_id == "defining-an-intervention.challenge")
        self.assertTrue(challenge.scenario_image.path.endswith("campus-travel-v1.png"))
        self.assertNotEqual(challenge.scenario_image, pack.lessons[0].scenario_image)

    def test_revised_lessons_do_not_reuse_unrelated_old_building_or_robot_art(self):
        for entry in self.entries[1:]:
            for profile, path in entry["profile_pack_paths"].items():
                pack = self.catalog.for_pack(load_content_pack(ROOT / path))
                for lesson in pack.lessons:
                    image = lesson_view(pack, lesson.concept_id)["scenario_image"]
                    self.assertIn("question-context/", image["path"])
        medical = load_content_pack(ROOT / self.entries[0]["profile_pack_paths"]["medical"])
        medical = self.catalog.for_pack(medical)
        self.assertTrue(lesson_view(medical, "world-data-model")["scenario_image"]["path"]
                        .endswith("laboratory-records-v1.png"))
        self.assertTrue(lesson_view(medical, "observation-vs-intervention")["scenario_image"]["path"]
                        .endswith("observation-sleep-recording.png"))
        self.assertTrue(next(item for item in medical.activities
                             if item.activity_id == "world-data-model.practice").scenario_image.path
                        .endswith("laboratory-records-v1.png"))

    def test_unknown_version_keeps_its_original_presentation(self):
        pack = load_content_pack(ROOT / self.entries[0]["profile_pack_paths"]["general"])
        older = pack.model_copy(update={"version": "1.3.0"})
        self.assertIs(self.catalog.for_pack(older), older)

    def test_bad_ids_and_staged_scene_images_are_rejected(self):
        pack = load_content_pack(ROOT / self.entries[0]["profile_pack_paths"]["general"])
        for activity_id in ("not-a-question", "m0-final-quiz.01", "association-is-not-causation.transfer"):
            value = self.catalog.model_dump(mode="json")
            binding = next(item for item in value["packs"]
                           if (item["pack_id"], item["pack_version"]) == (pack.pack_id, pack.version))
            binding["activities"][activity_id] = "service-records"
            with self.subTest(activity=activity_id), self.assertRaises(ValueError):
                CourseIllustrationCatalog.model_validate_json(json.dumps(value)).for_pack(pack)
        value = self.catalog.model_dump(mode="json")
        binding = next(item for item in value["packs"]
                       if (item["pack_id"], item["pack_version"]) == (pack.pack_id, pack.version))
        binding["lessons"]["unknown-concept"] = "service-records"
        with self.assertRaisesRegex(ValueError, "unknown lesson"):
            CourseIllustrationCatalog.model_validate_json(json.dumps(value)).for_pack(pack)

    def test_catalog_rejects_unknown_images_duplicate_packs_keys_and_unsafe_paths(self):
        value = self.catalog.model_dump(mode="json")
        value["packs"][0]["activities"]["variables-and-values.practice"] = "unknown-image"
        with self.assertRaisesRegex(ValidationError, "unknown image"):
            CourseIllustrationCatalog.model_validate_json(json.dumps(value))
        value = self.catalog.model_dump(mode="json")
        value["packs"].append(value["packs"][0])
        with self.assertRaisesRegex(ValidationError, "must be unique"):
            CourseIllustrationCatalog.model_validate_json(json.dumps(value))
        value = self.catalog.model_dump(mode="json")
        value["images"]["service-records"]["path"] = "../private.png"
        with self.assertRaises(ValidationError):
            CourseIllustrationCatalog.model_validate_json(json.dumps(value))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.json"
            path.write_text('{"catalog_version":"0.0.0",' + CATALOG.read_text(encoding="utf-8").lstrip()[1:],
                            encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "duplicate"):
                load_course_illustrations(path)

    def test_normal_factory_binds_all_profiles_without_creating_progress(self):
        with tempfile.TemporaryDirectory() as directory:
            for entry in self.entries:
                module = _build_module(entry, events_root=Path(directory), reset=False,
                                       illustration_catalog=self.catalog)
                for runtime in module.profiles.values():
                    controller = runtime.controller
                    self.assertEqual(controller.events, [])
                    self.assertIsNot(controller.pack, controller.teaching_pack)
                    self.assertEqual(without_images(controller.pack), without_images(controller.teaching_pack))
            self.assertEqual(list(Path(directory).iterdir()), [])

    def test_every_ordinary_quiz_and_challenge_has_explicit_art_including_integrated_transfer(self):
        checked = 0
        for entry in self.entries:
            for profile, path in entry["profile_pack_paths"].items():
                original = load_content_pack(ROOT / path)
                pack = self.catalog.for_pack(original)
                for before, activity in zip(original.activities, pack.activities, strict=True):
                    if (activity.causal_scene_id is not None or activity.experiment is not None
                        or (activity.workbench is not None and activity.workbench.stage == "capstone")):
                        self.assertEqual(activity.scenario_image, before.scenario_image)
                        continue
                    with self.subTest(module=entry["module_id"], profile=profile, activity=activity.activity_id):
                        self.assertIsNotNone(activity.scenario_image)
                        self.assertTrue((ROOT / "web/public" / activity.scenario_image.path).is_file())
                        checked += 1
                if entry["module_id"] == "causality_m0":
                    integrated = next(item for item in pack.activities
                                      if item.activity_id == "m0-integrated-transfer.01")
                    self.assertTrue(integrated.scenario_image.path.endswith("observation-sleep-recording.png"))
        self.assertEqual(checked, 68)

    def test_actual_experiments_scenes_and_capstone_items_still_reject_image_bindings(self):
        rejected = 0
        for entry in self.entries:
            pack = load_content_pack(ROOT / entry["profile_pack_paths"]["general"])
            for activity in pack.activities:
                if (activity.causal_scene_id is None and activity.experiment is None
                    and (activity.workbench is None or activity.workbench.stage != "capstone")):
                    continue
                value = self.catalog.model_dump(mode="json")
                binding = next(item for item in value["packs"]
                               if item["pack_id"] == pack.pack_id and item["pack_version"] == pack.version)
                binding["activities"][activity.activity_id] = "service-records"
                with self.subTest(module=entry["module_id"], activity=activity.activity_id):
                    with self.assertRaisesRegex(ValueError, "staged scenes, experiments or final"):
                        CourseIllustrationCatalog.model_validate_json(json.dumps(value)).for_pack(pack)
                    rejected += 1
        self.assertEqual(rejected, 26)

    def test_new_m1_versions_retain_every_historical_image_binding(self):
        for task, profile in ((task, profile) for task in ("effect", "shift") for profile in ("general", "medical")):
            entries = [item for item in self.catalog.packs
                       if item.pack_id == f"causality.m1.{task}.{profile}"]
            historical = next(item for item in entries if item.pack_version == "1.2.0")
            current = next(item for item in entries if item.pack_version == "1.3.0")
            self.assertEqual(historical.activities, current.activities)
            self.assertEqual(historical.lessons, current.lessons)

    def test_current_foundation_bindings_retain_the_historical_overlay(self):
        self.assertEqual(self.catalog.catalog_version, "1.6.0")
        for profile in ("general", "medical"):
            entries = [item for item in self.catalog.packs
                       if item.pack_id == f"causality.m0.{profile}.course"]
            historical = next(item for item in entries if item.pack_version == "1.6.0")
            current = next(item for item in entries if item.pack_version == "1.7.0")
            for activity_id, image_id in historical.activities.items():
                self.assertEqual(current.activities[activity_id], image_id)
            self.assertEqual(historical.lessons, current.lessons)
            if profile == "general":
                self.assertNotIn("world-data-model.transfer", historical.activities)
                self.assertEqual(current.activities["world-data-model.transfer"], "laboratory-records")
            pack = load_content_pack(ROOT / f"content/foundation_{profile}_course_1_7_0.json")
            challenge = next(item for item in self.catalog.for_pack(pack).activities
                             if item.activity_id == "world-data-model.transfer")
            self.assertTrue(challenge.scenario_image.path.endswith("laboratory-records-v1.png"))
            old_pack = load_content_pack(ROOT / f"content/foundation_{profile}_course_1_6_0.json")
            illustrated = self.catalog.for_pack(old_pack)
            self.assertEqual(without_images(illustrated), without_images(old_pack))
            self.assertEqual(illustrated.version, "1.6.0")

    def test_complementary_courses_retain_every_prior_exact_version_image_binding(self):
        for module in self.entries:
            previous_version = "1.7.0" if module["module_id"] == "causality_m0" else "1.3.0"
            for profile, path in module["profile_pack_paths"].items():
                with self.subTest(module=module["module_id"], profile=profile):
                    pack = load_content_pack(ROOT / path)
                    previous = next(item for item in self.catalog.packs
                                    if (item.pack_id, item.pack_version) == (pack.pack_id, previous_version))
                    current = next(item for item in self.catalog.packs
                                   if (item.pack_id, item.pack_version) == (pack.pack_id, pack.version))
                    self.assertEqual(current.activities, previous.activities)
                    self.assertEqual(current.lessons, previous.lessons)

    def test_optional_entry_check_uses_same_question_picture_without_changing_diagnostic_pack(self):
        with tempfile.TemporaryDirectory() as directory:
            module = _build_module(self.entries[0], events_root=Path(directory), reset=False,
                                   illustration_catalog=self.catalog)
            general = module.profiles["general"]
            original = general.diagnostic.pack.model_dump_json()
            self.assertIsNone(_state(general.controller, general.diagnostic, TestModel())["diagnostic"]["scenario_image"])
            general.diagnostic.start()
            view = _state(general.controller, general.diagnostic, TestModel())
            self.assertTrue(view["diagnostic"]["scenario_image"]["path"].endswith("foundation-general-it-v1.png"))
            self.assertEqual(general.diagnostic.pack.model_dump_json(), original)
            self.assertEqual(general.diagnostic.responses, [])
            self.assertEqual(general.controller.events, [])


if __name__ == "__main__":
    unittest.main()
