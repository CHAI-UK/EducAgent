"""Module-specific entry and non-sensitive HTTP diagnostics."""

import json
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from pydantic_ai.models.test import TestModel

from educagent_sdk import LearnerMessage, load_content_pack, record_learner_message
from educagent_sdk.demo import DemoController
from educagent_sdk.lesson_samples import load_lesson_samples
from educagent_sdk.web_demo import ModuleRuntime, create_module_hub_server


ROOT = Path(__file__).resolve().parents[1]


class ModuleHubTest(unittest.TestCase):
    def setUp(self) -> None:
        legacy_paths = {
            "causality_m0": "content/causality_m0_full.json",
            "m1_effect": "content/m1_effect_of_an_intervention.json",
            "m1_shift": "content/m1_robust_prediction_or_generation.json",
        }
        self.modules = [
            ModuleRuntime(entry["module_id"], entry["title"], entry["optional"],
                          tuple(entry["prerequisite_module_ids"]), entry["nirvana_task"],
                          DemoController(load_content_pack(ROOT / legacy_paths[entry["module_id"]])))
            for entry in json.loads((ROOT / "content/modules.json").read_text(encoding="utf-8"))["modules"]
        ]
        self.server = create_module_hub_server(self.modules, port=0, model=TestModel(), open_modules=False)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self) -> None:
        self.server.shutdown()
        self.thread.join(timeout=5)
        self.server.server_close()

    def command(self, path: str, **body: object) -> dict:
        request = Request(self.base + path, data=json.dumps(body).encode(),
                          headers={"Content-Type": "application/json"})
        with urlopen(request, timeout=5) as response:
            return json.load(response)

    def test_each_module_exposes_only_its_own_mission_and_resumes(self) -> None:
        with urlopen(self.base + "/api/state", timeout=5) as response:
            foundation = json.load(response)
        self.assertEqual(foundation["practical_mission"]["activity_id"], "association-is-not-causation.transfer")
        for module_id in ("m1_effect", "m1_shift"):
            with self.subTest(module=module_id):
                selected = self.command("/api/select-module", module_id=module_id, test_only_force_unlock=True)
                self.assertIsNone(selected["practical_mission"])
                started = self.command("/api/start")
                self.assertEqual(started["active_module_id"], module_id)
                self.assertEqual(started["status"], "active")
                self.assertNotEqual(started["activity_id"], "association-is-not-causation.transfer")
                self.command("/api/select-module", module_id="causality_m0")
                resumed = self.command("/api/select-module", module_id=module_id, test_only_force_unlock=True)
                self.assertEqual(resumed["attempt_id"], started["attempt_id"])

    def test_invalid_state_and_missing_mission_are_not_provider_disconnects(self) -> None:
        for path, body, status, code in (
            ("/api/select-module", {"module_id": "m1_effect", "request_id": "hub.locked"}, 409, "invalid_state"),
            ("/api/start-scene", {"request_id": "hub.no-mission"}, 400, "invalid_request"),
        ):
            if path == "/api/start-scene":
                self.command("/api/select-module", module_id="m1_effect", test_only_force_unlock=True)
            with self.subTest(path=path), self.assertRaises(HTTPError) as error:
                self.command(path, **body)
            self.assertEqual(error.exception.code, status)
            failure = json.load(error.exception)
            self.assertEqual(failure["code"], code)
            self.assertEqual(failure["request_id"], body["request_id"])
            self.assertFalse(failure["retryable"])
            self.assertIn("recovery", failure)
            self.assertNotEqual(failure["error"], "tutor unavailable")

    def test_finishing_a_targeted_route_does_not_unlock_all_foundations(self) -> None:
        controller = self.modules[0].controller
        activity = next(item for item in controller.pack.activities if item.activity_id == "variables-and-values.practice")
        controller.start(preferred_activity_ids=(activity.activity_id,), route_scope="preferred")
        controller.respond(request_id="hub.targeted.answer", option_id=next(item.option_id for item in activity.choices if item.correct))
        controller.continue_activity(request_id="hub.targeted.continue")
        self.assertEqual(controller.view()["status"], "completed")
        with urlopen(self.base + "/api/state", timeout=5) as response:
            state = json.load(response)
        self.assertEqual(next(item for item in state["modules"] if item["module_id"] == "m1_effect")["status"], "locked")

    def test_premature_continue_and_response_during_pending_chat_are_state_conflicts(self) -> None:
        controller = self.modules[0].controller
        started = controller.start()
        with self.assertRaises(HTTPError) as premature:
            self.command("/api/continue", request_id="hub.premature-continue")
        self.assertEqual(premature.exception.code, 409)
        failure = json.load(premature.exception)
        self.assertEqual(failure["code"], "invalid_state")
        self.assertIn("cannot advance", failure["detail"])

        record_learner_message(
            controller.events, controller.pack, attempt_id=started["attempt_id"],
            request_id="hub.pending-chat", message=LearnerMessage(text="What is a variable?"),
        )
        with self.assertRaises(HTTPError) as pending:
            self.command(
                "/api/respond", request_id="hub.pending-answer",
                option_id=started["choices"][0]["option_id"],
            )
        self.assertEqual(pending.exception.code, 409)
        failure = json.load(pending.exception)
        self.assertEqual(failure["code"], "invalid_state")
        self.assertIn("not ready", failure["detail"])
        self.assertEqual(failure["request_id"], "hub.pending-answer")

    def test_preview_can_reopen_any_activity_without_changing_learning_events(self) -> None:
        foundation = self.modules[0].controller
        foundation.start()
        original_events = tuple(foundation.events)
        entered = self.command("/api/preview", enabled=True)
        self.assertTrue(entered["preview_mode"])
        self.assertTrue(all(item["status"] == "available" for item in entered["modules"]))
        activity_id = "data-vs-assumptions.practice"
        first = self.command("/api/preview/navigate", activity_id=activity_id)
        choice = next(choice.option_id for activity in foundation.pack.activities
                      if activity.activity_id == activity_id for choice in activity.choices if choice.correct)
        self.command("/api/respond", request_id="preview.answer", option_id=choice)
        reopened = self.command("/api/preview/navigate", activity_id=activity_id)
        self.assertNotEqual(reopened["attempt_id"], first["attempt_id"])
        self.assertFalse(reopened["can_continue"])
        self.assertEqual(reopened["completed_concept_ids"], [])
        self.command("/api/select-module", module_id="m1_effect")
        self.command("/api/start")
        self.assertFalse(self.modules[1].controller.events)
        self.command("/api/select-module", module_id="causality_m0")
        restored = self.command("/api/preview", enabled=False)
        self.assertEqual(restored["attempt_id"], foundation.view()["attempt_id"])
        self.assertEqual(tuple(foundation.events), original_events)

    def test_editor_exports_are_validated_by_sdk_not_only_browser_rules(self) -> None:
        pack = self.modules[0].controller.pack.model_dump(mode="json")
        result = self.command("/api/validate-content-pack", pack=pack)
        self.assertTrue(result["valid"])
        self.assertTrue(result["releasable"])
        pack["activities"][0]["choices"][0]["correct"] = True
        pack["activities"][0]["choices"][1]["correct"] = True
        rejected = self.command("/api/validate-content-pack", pack=pack)
        self.assertFalse(rejected["valid"])
        self.assertTrue(rejected["issues"])
        with urlopen(self.base + "/authoring/content-pack-editor.html", timeout=5) as response:
            self.assertIn("Validate with SDK", response.read().decode())

    def test_exit_preview_restores_normal_course_after_visiting_a_locked_module(self) -> None:
        foundation = self.modules[0].controller
        original = foundation.start()
        original_events = tuple(foundation.events)
        self.command("/api/preview", enabled=True)
        self.command("/api/select-module", module_id="m1_shift")
        self.command("/api/start")
        self.command("/api/preview", enabled=True)
        restored = self.command("/api/preview", enabled=False)
        self.assertFalse(restored["preview_mode"])
        self.assertEqual(restored["active_module_id"], "causality_m0")
        self.assertEqual(restored["activity_id"], original["activity_id"])
        self.assertEqual(restored["attempt_id"], original["attempt_id"])
        self.assertEqual(tuple(foundation.events), original_events)
        self.assertFalse(self.modules[2].controller.events)
        self.assertEqual(next(item for item in restored["modules"] if item["module_id"] == "m1_shift")["status"], "locked")
        with self.assertRaises(HTTPError) as locked:
            self.command("/api/select-module", module_id="m1_shift")
        self.assertEqual(locked.exception.code, 409)

    def test_exit_preview_restores_normal_medical_lesson_and_checked_answer(self) -> None:
        foundation = self.modules[0].controller
        foundation.start()
        base_events = tuple(foundation.events)
        self.modules[0].lesson_samples.update({
            profile: DemoController(pack, mode="guarded_tutor")
            for profile, pack in load_lesson_samples(foundation.pack, ROOT / "content/foundation_lesson_samples.json").items()
        })
        original = self.command("/api/start-lesson", profile_id="medical")
        medical = self.modules[0].lesson_samples["medical"]
        activity = next(item for item in medical.pack.activities if item.activity_id == original["activity_id"])
        checked = self.command(
            "/api/respond", request_id="hub.medical.before-preview",
            option_id=next(item.option_id for item in activity.choices if item.correct),
        )
        medical_events = tuple(medical.events)
        self.command("/api/preview", enabled=True)
        self.command("/api/start-lesson", profile_id="general")
        self.command("/api/select-module", module_id="m1_shift")
        self.command("/api/preview", enabled=True)
        restored = self.command("/api/preview", enabled=False)
        self.assertEqual(restored["active_module_id"], "causality_m0")
        self.assertEqual(restored["profile_id"], "medical")
        self.assertEqual(restored["lesson"]["profile_id"], "medical")
        self.assertEqual(restored["activity_id"], checked["activity_id"])
        self.assertEqual(restored["attempt_id"], checked["attempt_id"])
        self.assertTrue(restored["can_continue"])
        self.assertEqual(tuple(medical.events), medical_events)
        self.assertEqual(tuple(foundation.events), base_events)
        self.assertFalse(self.modules[0].lesson_samples["general"].events)

    def test_profile_samples_have_separate_sessions_and_do_not_replace_foundation_progress(self) -> None:
        foundation = self.modules[0].controller
        foundation.start()
        original_events = tuple(foundation.events)
        self.modules[0].lesson_samples.update({
            profile: DemoController(pack, mode="guarded_tutor")
            for profile, pack in load_lesson_samples(foundation.pack, ROOT / "content/foundation_lesson_samples.json").items()
        })
        general = self.command("/api/start-lesson", profile_id="general")
        self.assertEqual(general["lesson"]["profile_id"], "general")
        self.assertEqual(general["profile_id"], "general")
        self.assertIn("ice-cream", general["lesson"]["hook"])
        medical = self.command("/api/start-lesson", profile_id="medical")
        self.assertIn("Treatment A", medical["lesson"]["hook"])
        self.assertNotEqual(general["attempt_id"], medical["attempt_id"])
        resumed = self.command("/api/start-lesson", profile_id="general")
        self.assertEqual(resumed["attempt_id"], general["attempt_id"])
        restored = self.command("/api/select-module", module_id="causality_m0")
        self.assertIsNone(restored["lesson"])
        self.assertEqual(restored["attempt_id"], foundation.view()["attempt_id"])
        self.assertEqual(tuple(foundation.events), original_events)

    def test_valid_drafts_return_release_issues_without_exposing_input_values(self) -> None:
        pack = self.modules[0].controller.pack.model_dump(mode="json")
        question_id = pack["activities"][0]["question_resource_id"]
        question = next(item for item in pack["resources"] if item["resource_id"] == question_id)
        question["release_status"] = "draft"
        question["text"] = "AUTHORING_DRAFT_SENTINEL_DO_NOT_ECHO"
        draft = self.command("/api/validate-content-pack", pack=pack)
        self.assertTrue(draft["valid"])
        self.assertFalse(draft["releasable"])
        self.assertIn("draft-resource", [item["code"] for item in draft["issues"]])
        self.assertNotIn("error", draft)
        self.assertNotIn("diagnostic", draft)
        self.assertNotIn(question["text"], json.dumps(draft))

        pack["activities"][0]["choices"][0]["correct"] = "INVALID_BOOL_SENTINEL_DO_NOT_ECHO"
        invalid = self.command("/api/validate-content-pack", pack=pack)
        self.assertFalse(invalid["valid"])
        self.assertFalse(invalid["releasable"])
        self.assertTrue(invalid["issues"])
        self.assertNotIn("INVALID_BOOL_SENTINEL_DO_NOT_ECHO", json.dumps(invalid))
        self.assertNotIn(question["text"], json.dumps(invalid))


if __name__ == "__main__":
    unittest.main()
