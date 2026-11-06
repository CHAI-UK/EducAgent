"""Topic teaching-route completion and non-mutating review navigation."""

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
from educagent_sdk.events import replay
from educagent_sdk.web_demo import ModuleRuntime, ProfileRuntime, create_module_hub_server


ROOT = Path(__file__).resolve().parents[1]


class TopicNavigationTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        entries = json.loads((ROOT / "content/modules.json").read_text())["modules"]
        self.modules = []
        for entry in entries:
            profiles = {
                profile: ProfileRuntime(DemoController(
                    load_content_pack(ROOT / path), profile_id=profile,
                    store=JsonlEventStore(self.directory / f"{entry['module_id']}-{profile}.jsonl"),
                ))
                for profile, path in entry["profile_pack_paths"].items()
            }
            self.modules.append(ModuleRuntime(
                entry["module_id"], entry["title"], entry["optional"],
                tuple(entry["prerequisite_module_ids"]), entry["nirvana_task"],
                profiles["general"].controller, profiles=profiles,
            ))
        self.server = create_module_hub_server(self.modules, port=0, model=TestModel())
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
        with urlopen(request, timeout=5) as response:
            return json.load(response)

    def state(self):
        with urlopen(self.base + "/api/state", timeout=5) as response:
            return json.load(response)

    def select_and_finish_topic(self, module, profile):
        controller = module.profiles[profile].controller
        self.command("/api/select-module", module_id=module.module_id)
        self.command("/api/select-profile", profile_id=profile)
        controller.start(session_id=f"topics.{module.module_id}.{profile}")
        concept_id = controller.pack.concepts[0].concept_id
        activities = controller.topic_activity_ids(concept_id)
        self.assertEqual(len(activities), 2)
        for index, activity_id in enumerate(activities):
            self.assertEqual(controller.view()["activity_id"], activity_id)
            activity = next(item for item in controller.pack.activities if item.activity_id == activity_id)
            controller.respond(request_id=f"topic.answer.{index}",
                               option_id=next(item.option_id for item in activity.choices if item.correct))
            controller.continue_activity(request_id=f"topic.next.{index}")
        return controller, concept_id, activities

    def test_six_profiles_separate_topic_completion_from_full_concept_credit_and_replay(self):
        for module in self.modules:
            for profile in ("general", "medical"):
                with self.subTest(module=module.module_id, profile=profile):
                    controller, concept_id, activities = self.select_and_finish_topic(module, profile)
                    saved = controller.store.path.read_bytes()
                    state = self.state()
                    self.assertEqual(state["status"], "active")
                    self.assertEqual(state["topic_practice_completed_concept_ids"], [concept_id])
                    self.assertNotIn(concept_id, state["completed_concept_ids"])
                    self.assertEqual(state["completed_activity_ids"], list(activities))
                    self.assertEqual(next(item for item in state["modules"]
                                          if item["module_id"] == module.module_id)["status"], "available")
                    restored = DemoController(controller.pack, profile_id=profile, store=controller.store)
                    self.assertEqual(restored.view(), controller.view())
                    historical = list(controller.events)
                    historical[0] = historical[0].model_copy(update={
                        "payload": historical[0].payload.model_copy(update={"runtime_version": "0.9.0"}),
                    })
                    self.assertEqual(replay(historical).completed_activity_ids, activities)
                    restored.events = historical
                    self.assertEqual(restored.view()["topic_practice_completed_concept_ids"], (concept_id,))
                    self.assertEqual(controller.store.path.read_bytes(), saved)

    def test_completed_topic_navigation_opens_review_before_course_end_without_changing_credit(self):
        for module in self.modules:
            for profile in ("general", "medical"):
                with self.subTest(module=module.module_id, profile=profile):
                    controller, concept_id, activities = self.select_and_finish_topic(module, profile)
                    original = controller.view()
                    saved = controller.store.path.read_bytes()
                    body = {"request_id": "topics.review", "concept_id": concept_id}
                    review = self.command("/api/navigate", **body)
                    self.assertTrue(review["review_mode"])
                    self.assertEqual(review["activity_id"], activities[0])
                    self.assertNotEqual(review["attempt_id"], original["attempt_id"])
                    self.assertEqual(review["topic_practice_completed_concept_ids"], [concept_id])
                    self.assertEqual(self.state()["topic_practice_completed_concept_ids"], [concept_id])
                    activity = next(item for item in controller.pack.activities if item.activity_id == activities[0])
                    self.command("/api/respond", request_id="topics.review.answer",
                                 option_id=next(item.option_id for item in activity.choices if item.correct))
                    repeated = self.command("/api/navigate", **body)
                    self.assertEqual(repeated["attempt_id"], review["attempt_id"])
                    self.assertTrue(repeated["assessment_accepted"])
                    self.assertEqual(controller.store.path.read_bytes(), saved)
                    restored = self.command("/api/end-review")
                    self.assertFalse(restored["review_mode"])
                    self.assertEqual(restored["attempt_id"], original["attempt_id"])
                    self.assertEqual(restored["completed_activity_ids"], list(activities))
                    self.assertEqual(controller.view(), original)
                    self.assertEqual(controller.store.path.read_bytes(), saved)

    def test_navigation_from_review_resumes_saved_route_and_switches_to_unfinished_topic(self):
        module = self.modules[1]
        controller, concept_id, completed = self.select_and_finish_topic(module, "general")
        other = module.profiles["medical"].controller
        self.command("/api/navigate", request_id="topics.review", concept_id=concept_id)
        target = controller.pack.concepts[2].concept_id
        selected = self.command("/api/navigate", request_id="topics.unfinished", concept_id=target)
        self.assertFalse(selected["review_mode"])
        self.assertEqual(selected["activity_id"], controller.topic_activity_ids(target)[0])
        self.assertEqual(selected["lesson"]["concept_id"], target)
        self.assertEqual(selected["completed_activity_ids"], list(completed))
        self.assertEqual(selected["topic_practice_completed_concept_ids"], [concept_id])
        self.assertFalse(other.events)
        restored = DemoController(controller.pack, profile_id="general", store=controller.store)
        self.assertEqual(restored.view(), controller.view())

    def test_unfinished_topic_cannot_gain_credit_through_review_or_preview(self):
        module = self.modules[0]
        controller, concept_id, completed = self.select_and_finish_topic(module, "general")
        saved = controller.store.path.read_bytes()
        with self.assertRaises(HTTPError):
            self.command("/api/review-topic", concept_id=controller.pack.concepts[1].concept_id)
        preview = self.command("/api/preview", enabled=True)
        self.assertEqual(preview["topic_practice_completed_concept_ids"], [])
        self.assertEqual(preview["completed_activity_ids"], [])
        restored = self.command("/api/preview", enabled=False)
        self.assertEqual(restored["topic_practice_completed_concept_ids"], [concept_id])
        self.assertEqual(restored["completed_activity_ids"], list(completed))
        self.assertEqual(controller.store.path.read_bytes(), saved)

    def test_accepted_challenge_marks_topic_practice_without_closing_or_crediting_attempt(self):
        module = self.modules[1]
        controller = module.profiles["general"].controller
        self.command("/api/select-module", module_id=module.module_id)
        self.command("/api/select-profile", profile_id="general")
        controller.start(session_id="topics.accepted")
        concept_id = controller.pack.concepts[0].concept_id
        activities = controller.topic_activity_ids(concept_id)
        for index, activity_id in enumerate(activities):
            activity = next(item for item in controller.pack.activities if item.activity_id == activity_id)
            controller.respond(request_id=f"accepted.answer.{index}",
                               option_id=next(item.option_id for item in activity.choices if item.correct))
            if index == 0:
                controller.continue_activity(request_id="accepted.quiz.next")
        state = self.state()
        self.assertEqual(state["topic_practice_completed_concept_ids"], [concept_id])
        self.assertEqual(state["completed_activity_ids"], [activities[0]])
        self.assertNotIn(concept_id, state["completed_concept_ids"])
        self.assertTrue(state["can_continue"])
        saved = controller.store.path.read_bytes()
        review = self.command("/api/navigate", request_id="accepted.review", concept_id=concept_id)
        self.assertTrue(review["review_mode"])
        restored = self.command("/api/end-review")
        self.assertEqual(restored["attempt_id"], state["attempt_id"])
        self.assertTrue(restored["can_continue"])
        self.assertEqual(restored["completed_activity_ids"], [activities[0]])
        self.assertEqual(controller.store.path.read_bytes(), saved)


if __name__ == "__main__":
    unittest.main()
