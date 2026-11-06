"""Final navigation is separate from concept identity and temporary review credit."""

import json
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from pydantic_ai.models.test import TestModel

from educagent_sdk import load_content_pack
from educagent_sdk.demo import DemoController, JsonlEventStore
from educagent_sdk.web_demo import ModuleRuntime, ProfileRuntime, create_module_hub_server


ROOT = Path(__file__).resolve().parents[1]


class FinalCheckNavigationTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.modules = []
        for entry in json.loads((ROOT / "content/modules.json").read_text(encoding="utf-8"))["modules"]:
            profiles = {profile: ProfileRuntime(DemoController(
                load_content_pack(ROOT / path), profile_id=profile,
                store=JsonlEventStore(self.directory / f"{entry['module_id']}-{profile}.jsonl"),
            )) for profile, path in entry["profile_pack_paths"].items()}
            self.modules.append(ModuleRuntime(entry["module_id"], entry["title"], entry["optional"],
                tuple(entry["prerequisite_module_ids"]), entry["nirvana_task"],
                profiles["general"].controller, profiles=profiles))
        self.model = TestModel()
        self.server = create_module_hub_server(self.modules, port=0, model=self.model)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.stop_server)
        self.base = f"http://127.0.0.1:{self.server.server_port}"

    def stop_server(self):
        self.server.shutdown()
        self.thread.join(timeout=5)
        self.server.server_close()

    def command(self, path, **body):
        request = Request(self.base + path, data=json.dumps(body).encode(),
                          headers={"Content-Type": "application/json"})
        with urlopen(request, timeout=10) as response:
            return json.load(response)

    def select(self, module, profile):
        self.command("/api/select-module", module_id=module.module_id)
        return self.command("/api/select-profile", profile_id=profile)

    def answer(self, controller, request_id, *, correct=True):
        activity = next(item for item in controller.pack.activities if item.activity_id == controller.view()["activity_id"])
        option = next(item.option_id for item in activity.choices if item.correct == correct)
        return controller.respond(request_id=request_id, option_id=option)

    def test_six_routes_expose_unstarted_finals_and_pending_navigation_awards_no_credit(self):
        for module in self.modules:
            for profile in ("general", "medical"):
                with self.subTest(module=module.module_id, profile=profile):
                    controller = module.profiles[profile].controller
                    selected = self.select(module, profile)
                    finals = controller.final_activity_ids()
                    self.assertTrue(finals)
                    self.assertEqual(selected["final_check_activity_ids"], list(finals))
                    self.assertEqual(selected["final_check"], {"status": "not_started", "is_current": False,
                        "completed_count": 0, "total_count": len(finals)})
                    with self.assertRaises(HTTPError):
                        self.command("/api/final-check", request_id="final.unstarted")
                    self.assertFalse(controller.events)
                    controller.start(session_id=f"final.nav.{module.module_id}.{profile}")
                    previous_bytes = controller.store.path.read_bytes()
                    opened = self.command("/api/final-check", request_id="final.open")
                    self.assertFalse(opened["review_mode"])
                    self.assertEqual(opened["activity_id"], finals[0])
                    self.assertEqual(opened["final_check"], {"status": "in_progress", "is_current": True,
                        "completed_count": 0, "total_count": len(finals)})
                    self.assertEqual(opened["completed_activity_ids"], [])
                    self.assertEqual(opened["topic_practice_completed_concept_ids"], [])
                    self.assertFalse(opened["assessment_accepted"])
                    self.assertTrue(controller.store.path.read_bytes().startswith(previous_bytes))
                    saved = controller.store.path.read_bytes()
                    repeated = self.command("/api/final-check", request_id="final.open")
                    self.assertEqual(repeated["attempt_id"], opened["attempt_id"])
                    self.assertEqual(controller.store.path.read_bytes(), saved)
        self.assertIsNone(self.model.last_model_request_parameters)

    def test_six_routes_resume_the_exact_saved_final_after_completed_topic_review(self):
        for module in self.modules:
            for profile in ("general", "medical"):
                with self.subTest(module=module.module_id, profile=profile):
                    controller = module.profiles[profile].controller
                    self.select(module, profile)
                    controller.start(session_id=f"final.resume.{module.module_id}.{profile}")
                    concept_id = controller.pack.concepts[0].concept_id
                    topic_ids = controller.topic_activity_ids(concept_id)
                    for index, activity_id in enumerate(topic_ids):
                        self.assertEqual(controller.view()["activity_id"], activity_id)
                        self.answer(controller, f"topic.answer.{index}")
                        controller.continue_activity(request_id=f"topic.continue.{index}")
                    self.command("/api/final-check", request_id="final.jump")
                    self.answer(controller, "final.saved.answer")
                    original = controller.view()
                    saved = controller.store.path.read_bytes()
                    reviewed = self.command("/api/review-topic", concept_id=concept_id)
                    self.assertFalse(reviewed["final_check"]["is_current"])
                    self.assertEqual(reviewed["final_check"]["completed_count"], 1)
                    self.assertEqual(reviewed["final_check"]["status"], "in_progress")
                    resumed = self.command("/api/final-check", request_id="final.resume")
                    self.assertFalse(resumed["review_mode"])
                    self.assertTrue(resumed["final_check"]["is_current"])
                    self.assertEqual(resumed["attempt_id"], original["attempt_id"])
                    self.assertEqual(resumed["activity_id"], original["activity_id"])
                    self.assertTrue(resumed["assessment_accepted"])
                    self.assertTrue(resumed["can_continue"])
                    self.assertEqual(controller.view(), original)
                    self.assertEqual(controller.store.path.read_bytes(), saved)
        self.assertIsNone(self.model.last_model_request_parameters)

    def test_six_routes_count_accepted_finals_and_completed_review_never_changes_saved_credit(self):
        for module in self.modules:
            for profile in ("general", "medical"):
                with self.subTest(module=module.module_id, profile=profile):
                    controller = module.profiles[profile].controller
                    self.select(module, profile)
                    finals = controller.final_activity_ids()
                    controller.start(session_id=f"final.complete.{module.module_id}.{profile}",
                                     preferred_activity_ids=finals, route_scope="preferred")
                    wrong = self.answer(controller, "final.wrong", correct=False)
                    self.assertEqual(wrong["final_check"]["completed_count"], 0)
                    for index, activity_id in enumerate(finals):
                        self.assertEqual(controller.view()["activity_id"], activity_id)
                        accepted = self.answer(controller, f"final.answer.{index}")
                        self.assertEqual(accepted["final_check"]["completed_count"], index + 1)
                        self.assertEqual(len(accepted["completed_activity_ids"]), index)
                        if index == len(finals) - 1:
                            self.assertEqual(accepted["final_check"]["status"], "completed")
                            self.assertEqual(accepted["status"], "active")
                            self.assertTrue(accepted["can_continue"])
                        controller.continue_activity(request_id=f"final.continue.{index}")
                    original = controller.view()
                    saved = controller.store.path.read_bytes()
                    self.assertEqual(original["status"], "completed")
                    self.assertEqual(original["final_check_activity_ids"], list(finals))
                    self.assertFalse(original["final_check"]["is_current"])
                    review = self.command("/api/final-check", request_id="final.review")
                    self.assertTrue(review["review_mode"])
                    self.assertEqual(review["final_check_activity_ids"], list(finals))
                    self.assertEqual(review["activity_id"], finals[0])
                    self.assertTrue(review["final_check"]["is_current"])
                    self.assertEqual(review["final_check"]["completed_count"], len(finals))
                    self.assertEqual(review["final_check"]["status"], "completed")
                    first = next(item for item in controller.pack.activities if item.activity_id == finals[0])
                    scored = self.command("/api/respond", request_id="final.review.answer",
                        option_id=next(item.option_id for item in first.choices if item.correct))
                    self.assertEqual(scored["final_check"]["completed_count"], len(finals))
                    repeated = self.command("/api/final-check", request_id="final.review.again")
                    self.assertEqual(repeated["attempt_id"], review["attempt_id"])
                    self.assertTrue(repeated["assessment_accepted"])
                    self.assertEqual(controller.store.path.read_bytes(), saved)
                    self.assertEqual(controller.view(), original)
                    restored = self.command("/api/end-review")
                    self.assertFalse(restored["review_mode"])
                    self.assertEqual(restored["final_check"], original["final_check"])
                    self.assertEqual(controller.store.path.read_bytes(), saved)

    def test_partial_route_final_review_does_not_count_temporary_answers_as_real_progress(self):
        module = self.modules[0]
        controller = module.profiles["general"].controller
        self.select(module, "general")
        first = controller.pack.activities[0]
        controller.start(session_id="final.partial", preferred_activity_ids=(first.activity_id,), route_scope="preferred")
        self.answer(controller, "partial.answer")
        controller.continue_activity(request_id="partial.continue")
        original = controller.view()
        saved = controller.store.path.read_bytes()
        self.assertEqual(original["final_check"]["status"], "not_started")
        review = self.command("/api/final-check", request_id="partial.review")
        self.assertTrue(review["review_mode"])
        first_final = next(item for item in controller.pack.activities if item.activity_id == controller.final_activity_ids()[0])
        accepted = self.command("/api/respond", request_id="partial.review.answer",
            option_id=next(item.option_id for item in first_final.choices if item.correct))
        self.assertTrue(accepted["assessment_accepted"])
        self.assertEqual(accepted["final_check"], {**original["final_check"], "is_current": True})
        self.assertEqual(controller.store.path.read_bytes(), saved)
        self.assertEqual(controller.view(), original)

    def test_preview_and_missing_request_id_cannot_change_the_saved_final(self):
        module = self.modules[0]
        controller = module.profiles["general"].controller
        self.select(module, "general")
        controller.start(session_id="final.boundaries")
        original = controller.view()
        saved = controller.store.path.read_bytes()
        with self.assertRaises(HTTPError):
            self.command("/api/final-check")
        self.command("/api/preview", enabled=True)
        with self.assertRaises(HTTPError):
            self.command("/api/final-check", request_id="final.preview")
        self.command("/api/preview", enabled=False)
        self.assertEqual(controller.view(), original)
        self.assertEqual(controller.store.path.read_bytes(), saved)

    def test_packs_without_capstone_activities_have_no_virtual_final(self):
        controller = DemoController(load_content_pack(ROOT / "content/causality_m0_full.json"))
        self.assertEqual(controller.final_activity_ids(), ())
        self.assertIsNone(controller.view()["final_check"])
        self.assertEqual(controller.view()["final_check_activity_ids"], [])
        controller.start(session_id="final.legacy")
        with self.assertRaisesRegex(ValueError, "no final check"):
            controller.navigate_to_final_check(request_id="final.absent")

    def test_six_trace_projections_identify_finals_by_activity_without_rewriting_history(self):
        for module in self.modules:
            for profile in ("general", "medical"):
                with self.subTest(module=module.module_id, profile=profile):
                    controller = module.profiles[profile].controller
                    self.select(module, profile)
                    controller.start(session_id=f"trace.final.{module.module_id}.{profile}")
                    concept_id = controller.pack.concepts[0].concept_id
                    for index, activity_id in enumerate(controller.topic_activity_ids(concept_id)):
                        self.assertEqual(controller.view()["activity_id"], activity_id)
                        self.answer(controller, f"trace.topic.answer.{index}")
                        controller.continue_activity(request_id=f"trace.topic.continue.{index}")
                    self.command("/api/final-check", request_id="trace.final.open")
                    self.answer(controller, "trace.final.answer")
                    saved = controller.store.path.read_bytes()
                    trace = controller.developer_trace()
                    original = controller.view()
                    finals = set(original["final_check_activity_ids"])
                    final_messages = [item for item in original["conversation"] if item["activity_id"] in finals]
                    topic_messages = [item for item in original["conversation"] if item["activity_id"] not in finals]
                    self.assertTrue(final_messages)
                    self.assertTrue(topic_messages)
                    self.assertTrue(any(item["concept_id"] == concept_id for item in final_messages))
                    self.assertTrue(any(item["concept_id"] == concept_id for item in topic_messages))
                    self.assertEqual(len(final_messages) + len(topic_messages), len(original["conversation"]))
                    review = self.command("/api/review-topic", concept_id=concept_id)
                    self.assertEqual(review["final_check_activity_ids"], original["final_check_activity_ids"])
                    restored = self.command("/api/end-review")
                    self.assertEqual(restored["final_check_activity_ids"], original["final_check_activity_ids"])
                    replayed = DemoController(controller.pack, profile_id=profile, store=controller.store)
                    self.assertEqual(replayed.view(), original)
                    self.assertEqual(controller.developer_trace(), trace)
                    self.assertEqual(controller.store.path.read_bytes(), saved)
                    disposable = controller.view()
                    disposable["final_check_activity_ids"].clear()
                    self.assertEqual(controller.view()["final_check_activity_ids"], original["final_check_activity_ids"])

    def test_frozen_1_7_pack_projects_final_ids_for_its_existing_trace(self):
        for profile in ("general", "medical"):
            with self.subTest(profile=profile):
                pack = load_content_pack(ROOT / f"content/foundation_{profile}_course_1_7_0.json")
                store = JsonlEventStore(self.directory / f"historical-{profile}.jsonl")
                controller = DemoController(pack, profile_id=profile, store=store)
                finals = controller.final_activity_ids()
                controller.start(session_id=f"historical.final.{profile}",
                                 preferred_activity_ids=finals, route_scope="preferred")
                self.answer(controller, "historical.final.answer")
                saved = store.path.read_bytes()
                restored = DemoController(pack, profile_id=profile, store=store)
                self.assertEqual(restored.view()["final_check_activity_ids"], list(finals))
                self.assertTrue(all(item["activity_id"] in finals for item in restored.view()["conversation"]))
                self.assertEqual(store.path.read_bytes(), saved)
