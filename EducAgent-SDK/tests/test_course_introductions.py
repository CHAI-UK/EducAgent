"""Non-scoring M1 openings preserve pack identity and existing learner traces."""

import copy
import json
import tempfile
import threading
import unittest
from dataclasses import replace
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from pydantic import ValidationError
from pydantic_ai.models import override_allow_model_requests
from pydantic_ai.models.test import TestModel

from educagent_sdk import load_content_pack
from educagent_sdk.course_introductions import CourseIntroductionCatalog, load_course_introductions
from educagent_sdk.web_demo import create_module_hub_server
from examples.playable_demo import _build_module, _load_registry
from tests.experiment_helpers import finish_current_experiment


ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "content/course_introductions.json"


class CourseIntroductionTest(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog = load_course_introductions(CATALOG)
        self.entries = _load_registry(ROOT / "content/modules.json")

    def validate(self, value: dict) -> CourseIntroductionCatalog:
        return CourseIntroductionCatalog.model_validate_json(json.dumps(value))

    def test_all_four_openings_are_whitelisted_and_grounded_without_changing_packs(self) -> None:
        for entry in self.entries:
            packs = {
                profile: load_content_pack(ROOT / path)
                for profile, path in entry["profile_pack_paths"].items()
            }
            originals = {profile: pack.model_dump_json() for profile, pack in packs.items()}
            views = self.catalog.for_module(entry["module_id"], entry["title"], packs)
            if entry["module_id"] == "causality_m0":
                self.assertIsNone(views)
                continue
            self.assertEqual(set(views), {"general", "medical"})
            self.assertNotEqual(views["general"].example, views["medical"].example)
            for profile, view in views.items():
                value = view.model_dump(mode="json")
                self.assertEqual(set(value), {
                    "catalog_version", "profile_id", "title", "question", "example", "why",
                    "actions", "comparison", "scenario_image", "image_caption",
                })
                self.assertEqual(value["catalog_version"], "1.3.0")
                self.assertEqual(value["profile_id"], profile)
                self.assertEqual(view.title, entry["title"])
                self.assertTrue((ROOT / "web/public" / view.scenario_image.path).is_file())
                self.assertEqual(packs[profile].version, "1.4.0")
                self.assertEqual(packs[profile].model_dump_json(), originals[profile])

    def test_openings_are_compact_and_distinguish_the_two_output_tasks(self) -> None:
        for module_id, profiles in self.catalog.courses.items():
            for profile, introduction in profiles.items():
                with self.subTest(module=module_id, profile=profile):
                    self.assertLessEqual(len(introduction.example.split()), 75)
                    self.assertLessEqual(len(introduction.why.split()), 75)
                    self.assertTrue(all(len(action.split()) <= 22 for action in introduction.actions))
                    self.assertNotEqual(introduction.comparison.this_course_question,
                                        introduction.comparison.other_course_question)
                    if module_id == "m1_shift":
                        self.assertIn("rule-based drafts", introduction.why)
                        self.assertIn("Prediction", introduction.why)
                        self.assertIn("generation", introduction.why)

    def test_missing_profile_and_wrong_profile_identity_are_rejected(self) -> None:
        value = self.catalog.model_dump(mode="json")
        del value["courses"]["m1_shift"]["medical"]
        with self.assertRaisesRegex(ValidationError, "general and medical"):
            self.validate(value)
        value = self.catalog.model_dump(mode="json")
        value["courses"]["m1_effect"]["medical"]["profile_id"] = "general"
        with self.assertRaisesRegex(ValidationError, "profile must match"):
            self.validate(value)

    def test_comparison_requires_both_reciprocal_courses_and_matching_titles(self) -> None:
        value = self.catalog.model_dump(mode="json")
        del value["courses"]["m1_shift"]
        with self.assertRaisesRegex(ValidationError, "both authored M1"):
            self.validate(value)
        for field, invalid in (("other_module_id", "unknown"), ("other_module_id", "m1_effect"), ("other_title", "Wrong course")):
            with self.subTest(field=field, invalid=invalid):
                value = self.catalog.model_dump(mode="json")
                value["courses"]["m1_effect"]["general"]["comparison"][field] = invalid
                with self.assertRaises(ValidationError):
                    self.validate(value)

    def test_unsafe_images_unknown_fields_and_duplicate_json_keys_are_rejected(self) -> None:
        for path in ("https://example.com/opening.png", "../private.png", "media/../private.png", "media\\opening.png"):
            with self.subTest(path=path):
                value = self.catalog.model_dump(mode="json")
                value["courses"]["m1_effect"]["general"]["scenario_image"]["path"] = path
                with self.assertRaises(ValidationError):
                    self.validate(value)
        value = self.catalog.model_dump(mode="json")
        value["courses"]["m1_effect"]["general"]["correct_answer"] = "not public"
        with self.assertRaises(ValidationError):
            self.validate(value)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "duplicate.json"
            path.write_text('{"catalog_version":"1.0.0",' + CATALOG.read_text(encoding="utf-8").lstrip()[1:], encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "duplicate"):
                load_course_introductions(path)

    def test_unknown_unreleased_and_duplicate_grounding_claims_are_rejected(self) -> None:
        entry = next(item for item in self.entries if item["module_id"] == "m1_effect")
        packs = {profile: load_content_pack(ROOT / path) for profile, path in entry["profile_pack_paths"].items()}
        value = self.catalog.model_dump(mode="json")
        value["courses"]["m1_effect"]["medical"]["grounding_claim_ids"] = ["unknown.claim"]
        with self.assertRaisesRegex(ValueError, "unknown or unreleased"):
            self.validate(value).for_module(entry["module_id"], entry["title"], packs)
        claim_id = self.catalog.courses["m1_effect"]["medical"].grounding_claim_ids[0]
        packs["medical"] = packs["medical"].model_copy(update={"claims": tuple(
            claim.model_copy(update={"release_status": "draft"}) if claim.claim_id == claim_id else claim
            for claim in packs["medical"].claims
        )})
        with self.assertRaisesRegex(ValueError, "unknown or unreleased"):
            self.catalog.for_module(entry["module_id"], entry["title"], packs)
        value = self.catalog.model_dump(mode="json")
        value["courses"]["m1_effect"]["medical"]["grounding_claim_ids"] = [claim_id, claim_id]
        with self.assertRaisesRegex(ValidationError, "must be unique"):
            self.validate(value)
        with self.assertRaisesRegex(ValueError, "module registry"):
            self.catalog.for_module(entry["module_id"], "Unexpected title", packs)
        with self.assertRaisesRegex(ValueError, "module's packs"):
            self.catalog.for_module(entry["module_id"], entry["title"], {"general": packs["general"]})

    def test_hub_projection_follows_context_and_reading_does_not_start_learning(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            modules = [_build_module(entry, events_root=Path(directory), reset=False, introduction_catalog=self.catalog)
                       for entry in self.entries]
            with override_allow_model_requests(False):
                server = create_module_hub_server(modules, port=0, model=TestModel())
                thread = threading.Thread(target=server.serve_forever, daemon=True)
                thread.start()
                try:
                    def command(path: str, **body: object) -> dict:
                        request = Request(f"http://127.0.0.1:{server.server_port}" + path,
                                          data=json.dumps(body).encode() if body else None,
                                          headers={"Content-Type": "application/json"})
                        with urlopen(request, timeout=5) as response:
                            return json.load(response)

                    self.assertIsNone(command("/api/state")["course_introduction"])
                    before_choice = command("/api/select-module", module_id="m1_effect")
                    self.assertTrue(before_choice["profile_required"])
                    self.assertEqual(before_choice["course_introduction"]["profile_id"], "general")
                    for module_id in ("m1_effect", "m1_shift"):
                        for profile_id in ("general", "medical"):
                            command("/api/select-module", module_id=module_id)
                            state = command("/api/select-profile", profile_id=profile_id)
                            intro = state["course_introduction"]
                            self.assertEqual(intro["profile_id"], profile_id)
                            self.assertEqual(intro["title"], state["course_title"])
                            self.assertNotIn("grounding_claim_ids", intro)
                            self.assertEqual(state["status"], "not_started")
                            for item in state["modules"]:
                                if item["module_id"] == "causality_m0":
                                    self.assertNotIn("intent", item)
                                else:
                                    expected = self.catalog.courses[item["module_id"]][profile_id]
                                    self.assertEqual(item["intent"], expected.comparison.this_course_question)
                            command("/api/state")
                            command("/api/modules")
                    self.assertFalse(list(Path(directory).glob("*.jsonl")))
                    self.assertTrue(all(not runtime.controller.events for module in modules for runtime in module.profiles.values()))
                finally:
                    server.shutdown()
                    thread.join(timeout=5)
                    server.server_close()

    def test_changed_opening_resumes_existing_experiment_and_preserves_trace_bytes(self) -> None:
        changed = self.catalog.model_dump(mode="json")
        changed["catalog_version"] = "1.3.1"
        for profiles in changed["courses"].values():
            for introduction in profiles.values():
                introduction["why"] = "Revised opening copy, without a different learning contract."
        new_catalog = self.validate(changed)
        with tempfile.TemporaryDirectory() as directory, override_allow_model_requests(False):
            for entry in self.entries:
                if entry["module_id"] == "causality_m0":
                    continue
                module = _build_module(entry, events_root=Path(directory), reset=False, introduction_catalog=self.catalog)
                old_views = {}
                old_bytes = {}
                for profile_id, runtime in module.profiles.items():
                    controller = runtime.controller
                    practical = next(activity for activity in controller.pack.activities if activity.experiment)
                    controller.start(session_id=f"intro.{entry['module_id']}.{profile_id}",
                                     preferred_activity_ids=(practical.activity_id,), route_scope="preferred")
                    finish_current_experiment(controller)
                    old_views[profile_id] = copy.deepcopy(controller.view())
                    old_bytes[profile_id] = controller.store.path.read_bytes()
                resumed = _build_module(entry, events_root=Path(directory), reset=False, introduction_catalog=new_catalog)
                for profile_id, runtime in resumed.profiles.items():
                    self.assertEqual(runtime.controller.view(), old_views[profile_id])
                    self.assertEqual(runtime.controller.store.path.read_bytes(), old_bytes[profile_id])
                    self.assertEqual(resumed.introductions[profile_id].catalog_version, "1.3.1")
                    self.assertEqual(runtime.controller.pack.version, "1.4.0")

    def test_preview_start_without_profile_uses_resolved_audience_and_keeps_normal_trace(self) -> None:
        cases = [
            (module_id, path) for module_id in ("m1_effect", "m1_shift")
            for path in ("/api/start", "/api/diagnostic/skip")
        ] + [("causality_m0", "/api/start-scene")]
        for module_id, path in cases:
            with self.subTest(module=module_id, path=path), tempfile.TemporaryDirectory() as directory:
                modules = [_build_module(entry, events_root=Path(directory), reset=False, introduction_catalog=self.catalog)
                           for entry in self.entries]
                normal = next(module for module in modules if module.module_id == module_id).profiles["general"].controller
                normal.start(session_id=f"saved.{module_id}.general")
                saved_view = copy.deepcopy(normal.view())
                saved_bytes = normal.store.path.read_bytes()
                with override_allow_model_requests(False):
                    server = create_module_hub_server(modules, port=0, model=TestModel())
                    thread = threading.Thread(target=server.serve_forever, daemon=True)
                    thread.start()
                    try:
                        def command(command_path: str, **body: object) -> dict:
                            request = Request(f"http://127.0.0.1:{server.server_port}" + command_path,
                                              data=json.dumps(body).encode(),
                                              headers={"Content-Type": "application/json"})
                            with urlopen(request, timeout=10) as response:
                                return json.load(response)

                        command("/api/select-module", module_id=module_id)
                        with self.assertRaises(HTTPError) as blocked:
                            command(path)
                        self.assertEqual(blocked.exception.code, 409)
                        self.assertIn("profile selection is not ready", json.load(blocked.exception)["detail"])
                        command("/api/preview", enabled=True)
                        selected = command("/api/select-module", module_id=module_id)
                        self.assertIsNone(selected["profile_id"])
                        started = command(path)
                        self.assertEqual(started["status"], "active")
                        self.assertTrue(started["preview_mode"])
                        self.assertTrue(started["attempt_id"].startswith(f"course.{module_id}.general."))
                        self.assertIsNotNone(started["question"])
                        restored = command("/api/preview", enabled=False)
                        self.assertFalse(restored["preview_mode"])
                        self.assertEqual(restored["attempt_id"], saved_view["attempt_id"])
                        self.assertEqual(normal.view(), saved_view)
                        self.assertEqual(normal.store.path.read_bytes(), saved_bytes)
                        self.assertEqual(list(Path(directory).glob("*.jsonl")), [normal.store.path])
                    finally:
                        server.shutdown()
                        thread.join(timeout=5)
                        server.server_close()

    def test_hub_rejects_openings_for_legacy_or_missing_peer_modules(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            modules = [_build_module(entry, events_root=Path(directory), reset=False, introduction_catalog=self.catalog)
                       for entry in self.entries]
            with self.assertRaisesRegex(ValueError, "another registered course"):
                create_module_hub_server(modules[:2], port=0, model=TestModel())
            invalid = replace(modules[1], module_id="legacy")
            with self.assertRaisesRegex(ValueError, "only to the authored M1"):
                create_module_hub_server([modules[0], invalid, modules[2]], port=0, model=TestModel())


if __name__ == "__main__":
    unittest.main()
