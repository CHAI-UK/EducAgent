"""Open course access, current observations and independent profile runtimes."""

import asyncio
import copy
import json
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.request import Request, urlopen

from pydantic import ValidationError
from pydantic_ai.messages import ModelResponse, TextPart, UserPromptPart
from pydantic_ai.models import override_allow_model_requests
from pydantic_ai.models.function import FunctionModel
from pydantic_ai.models.test import TestModel

from educagent_sdk import (
    ContentPack, LearnerMessage, ReleaseValidationError, build_tutor_deps,
    load_content_pack, record_learner_message, validate_release,
)
from educagent_sdk.contracts import ComparisonWorkbench
from educagent_sdk.demo import DemoController
from educagent_sdk.web_demo import ModuleRuntime, create_module_hub_server
from tests.experiment_helpers import finish_current_experiment


ROOT = Path(__file__).resolve().parents[1]


def comparison() -> dict:
    return {
        "title": "Compare the observations", "introduction": "Inspect the recorded groups.",
        "scenario_id": "test.comparison", "stage": "investigate",
        "tables": [{
            "table_id": "observed.groups", "label": "Recorded groups",
            "columns": ["Group", "Recovered"],
            "rows": [["A", "12/20"], ["B", "9/20"]],
            "note": "No assignment was imposed.",
        }],
    }


def comparison_pack() -> ContentPack:
    data = load_content_pack(ROOT / "content/causality_m0_episode.json").model_dump(mode="json")
    data["activities"][0]["workbench"] = comparison()
    question_id = data["activities"][0]["question_resource_id"]
    question = next(item for item in data["resources"] if item["resource_id"] == question_id)
    question["text"] += " Group A: Recovered 12/20; Group B: Recovered 9/20. No assignment was imposed."
    return ContentPack.model_validate_json(json.dumps(data))


class ComparisonWorkbenchTest(unittest.TestCase):
    def test_activity_concept_projection_does_not_depend_on_activity_id_prefix(self) -> None:
        original = comparison_pack()
        data = original.model_dump(mode="json")
        old_id = data["activities"][0]["activity_id"]
        new_id = "investigation.current.01"
        data["activities"][0]["activity_id"] = new_id
        for concept in data["concepts"]:
            for field in ("completion_activity_ids", "m1_ready_activity_ids"):
                concept[field] = [new_id if item == old_id else item for item in concept.get(field, [])]
        pack = ContentPack.model_validate_json(json.dumps(data))
        controller = DemoController(pack)
        state = controller.start()
        self.assertEqual(state["activity_id"], new_id)
        self.assertEqual(state["activity_concept_id"], pack.activities[0].concept_id)
        self.assertFalse(new_id.startswith(state["activity_concept_id"]))

    def test_strict_table_contract_and_release_grounding(self) -> None:
        workbench = ComparisonWorkbench.model_validate_json(json.dumps(comparison()))
        self.assertEqual(workbench.tables[0].rows[0], ("A", "12/20"))
        for mutate in (
            lambda item: item["tables"].append(copy.deepcopy(item["tables"][0])),
            lambda item: item["tables"][0]["rows"][0].append("extra"),
            lambda item: item["tables"][0].update(rows=[]),
            lambda item: item["tables"][0]["rows"][0].__setitem__(0, " "),
            lambda item: item["tables"][0].update(answer="A"),
        ):
            data = comparison()
            mutate(data)
            with self.subTest(data=data), self.assertRaises(ValidationError):
                ComparisonWorkbench.model_validate_json(json.dumps(data))
        pack = comparison_pack()
        self.assertTrue(validate_release(pack).releasable)
        data = pack.model_dump(mode="json")
        data["activities"][0]["workbench"]["tables"][0]["rows"][0][1] = "UNRELEASED_RESULT"
        with self.assertRaises(ReleaseValidationError) as error:
            validate_release(ContentPack.model_validate_json(json.dumps(data)))
        self.assertIn("ungrounded-workbench", [issue.code for issue in error.exception.report.issues])

    def test_clean_prompt_must_be_nonempty_and_grounded_in_current_question(self) -> None:
        pack = comparison_pack()
        data = pack.model_dump(mode="json")
        question_id = data["activities"][0]["question_resource_id"]
        question = next(item for item in data["resources"] if item["resource_id"] == question_id)
        prompt = "What do these observations alone show?"
        question["text"] += " " + prompt
        data["activities"][0]["workbench"]["prompt"] = prompt
        grounded = ContentPack.model_validate_json(json.dumps(data))
        self.assertTrue(validate_release(grounded).releasable)
        controller = DemoController(grounded)
        self.assertEqual(controller.start()["workbench"]["prompt"], prompt)
        data["activities"][0]["workbench"]["prompt"] = "An unprovided question."
        with self.assertRaises(ReleaseValidationError) as error:
            validate_release(ContentPack.model_validate_json(json.dumps(data)))
        self.assertTrue(any(issue.path.endswith("/workbench/prompt") for issue in error.exception.report.issues))
        data["activities"][0]["workbench"]["prompt"] = " "
        with self.assertRaises(ValidationError):
            ContentPack.model_validate_json(json.dumps(data))

    def test_only_current_workbench_reaches_view_and_guided_tutor(self) -> None:
        pack = comparison_pack()
        controller = DemoController(pack)
        started = controller.start()
        self.assertEqual(started["workbench"], {**comparison(), "prompt": None})
        self.assertFalse(started["assessment_submitted"])
        self.assertNotIn("correct", json.dumps(started["workbench"]))
        captured = []

        def reply(messages, _info):
            for message in messages:
                for part in message.parts:
                    if isinstance(part, UserPromptPart) and isinstance(part.content, str):
                        captured.append(json.loads(part.content))
            return ModelResponse(parts=[TextPart("Compare the recorded groups before deciding what the pattern means.")])

        with override_allow_model_requests(False):
            asyncio.run(controller.send_message_with_tutor(
                request_id="comparison.chat", text="What should I compare?",
                model=FunctionModel(reply), unguarded=True,
            ))
        self.assertEqual(captured[-1]["visible_workbench"], {**comparison(), "prompt": None})
        self.assertNotIn("correct", json.dumps(captured[-1]["visible_workbench"]))

    def test_assessment_projection_tracks_rejected_and_accepted_current_attempt(self) -> None:
        controller = DemoController(comparison_pack())
        started = controller.start()
        activity = controller.pack.activities[0]
        rejected = controller.respond(
            request_id="comparison.wrong", option_id=next(choice.option_id for choice in activity.choices if not choice.correct),
        )
        self.assertTrue(rejected["assessment_submitted"])
        self.assertFalse(rejected["assessment_accepted"])
        self.assertFalse(rejected["can_continue"])
        accepted = controller.respond(
            request_id="comparison.correct", option_id=next(choice.option_id for choice in activity.choices if choice.correct),
        )
        self.assertTrue(accepted["assessment_submitted"])
        self.assertTrue(accepted["assessment_accepted"])
        next_view = controller.continue_activity(request_id="comparison.continue")
        self.assertNotEqual(next_view["attempt_id"], started["attempt_id"])
        self.assertFalse(next_view["assessment_submitted"])
        self.assertFalse(next_view["assessment_accepted"])
        self.assertIsNone(next_view["workbench"])


class OpenCourseAccessTest(unittest.TestCase):
    def test_default_access_does_not_create_completion_credit(self) -> None:
        pack = load_content_pack(ROOT / "content/causality_m0_episode.json")
        modules = [
            ModuleRuntime("foundation", "Foundation", False, (), None, DemoController(pack)),
            ModuleRuntime("followup", "Follow-up", True, ("foundation",), None, DemoController(pack)),
        ]
        server = create_module_hub_server(modules, port=0, model=TestModel())
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            request = Request(
                f"http://127.0.0.1:{server.server_port}/api/select-module",
                data=json.dumps({"module_id": "followup"}).encode(),
                headers={"Content-Type": "application/json"},
            )
            with urlopen(request, timeout=5) as response:
                state = json.load(response)
            self.assertEqual(state["active_module_id"], "followup")
            self.assertEqual([item["status"] for item in state["modules"]], ["available", "available"])
            self.assertEqual(state["status"], "not_started")
            self.assertFalse(modules[0].controller.events)
            self.assertFalse(modules[1].controller.events)
            self.assertNotIn("completed_concept_ids", state)
        finally:
            server.shutdown()
            thread.join(timeout=5)
            server.server_close()


class DirectProfileCourseTest(unittest.TestCase):
    def test_new_profile_packs_load_complete_and_keep_independent_stores(self) -> None:
        from examples.playable_demo import _build_module

        entries = json.loads((ROOT / "content/modules.json").read_text(encoding="utf-8"))["modules"]
        with tempfile.TemporaryDirectory() as directory:
            for entry in entries:
                if entry["module_id"] == "causality_m0":
                    continue
                with self.subTest(module=entry["module_id"]):
                    self.assertIn("profile_pack_paths", entry)
                    module = _build_module(entry, events_root=Path(directory), reset=False)
                    self.assertEqual(set(module.profiles), {"general", "medical"})
                    self.assertEqual(module.profiles["general"].controller.pack.concepts, module.profiles["medical"].controller.pack.concepts)
                    for profile_id, runtime in module.profiles.items():
                        controller = runtime.controller
                        self.assertEqual(controller.profile_id, profile_id)
                        self.assertEqual(len(controller.pack.lessons), len(controller.pack.concepts))
                        self.assertTrue(any(item.workbench and item.workbench.stage == "capstone" for item in controller.pack.activities))
                        controller.start(session_id=f"complete.{entry['module_id']}.{profile_id}")
                        ordinal = 0
                        while controller.view()["status"] != "completed":
                            ordinal += 1
                            self.assertLessEqual(ordinal, len(controller.pack.activities))
                            activity_id = controller.view()["activity_id"]
                            activity = next(item for item in controller.pack.activities if item.activity_id == activity_id)
                            self.assertIn(activity.activity_type, {"choice", "classification"})
                            finish_current_experiment(controller)
                            controller.respond(
                                request_id=f"route.answer.{ordinal}", option_id=next(item.option_id for item in activity.choices if item.correct),
                            )
                            controller.continue_activity(request_id=f"route.continue.{ordinal}")
                        self.assertEqual(set(controller.view()["completed_concept_ids"]), {item.concept_id for item in controller.pack.concepts})
                    self.assertNotEqual(module.profiles["general"].controller.store.path, module.profiles["medical"].controller.store.path)

    def test_profile_preference_follows_module_switches_and_resumes_each_context(self) -> None:
        from examples.playable_demo import _build_module

        entries = json.loads((ROOT / "content/modules.json").read_text(encoding="utf-8"))["modules"]
        with tempfile.TemporaryDirectory() as directory:
            modules = [_build_module(entry, events_root=Path(directory), reset=False) for entry in entries]
            server = create_module_hub_server(modules, port=0, model=TestModel())
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                def command(path: str, **body: object) -> dict:
                    request = Request(
                        f"http://127.0.0.1:{server.server_port}" + path,
                        data=json.dumps(body).encode(), headers={"Content-Type": "application/json"},
                    )
                    with urlopen(request, timeout=5) as response:
                        return json.load(response)

                command("/api/select-profile", profile_id="medical")
                selected = command("/api/select-module", module_id="m1_effect")
                self.assertEqual(selected["profile_id"], "medical")
                medical = command("/api/start")
                self.assertEqual(medical["activity_concept_id"], modules[1].profiles["medical"].controller.pack.activities[0].concept_id)
                general = command("/api/select-profile", profile_id="general")
                self.assertEqual(general["status"], "not_started")
                general = command("/api/start")
                self.assertNotEqual(medical["attempt_id"], general["attempt_id"])
                command("/api/select-module", module_id="m1_shift")
                selected = command("/api/select-profile", profile_id="medical")
                self.assertEqual(selected["status"], "not_started")
                restored = command("/api/select-module", module_id="m1_effect")
                self.assertEqual(restored["profile_id"], "medical")
                self.assertEqual(restored["attempt_id"], medical["attempt_id"])
                self.assertEqual(command("/api/select-module", module_id="causality_m0")["profile_id"], "medical")
            finally:
                server.shutdown()
                thread.join(timeout=5)
                server.server_close()


class LiveCourseTutorContextTest(unittest.IsolatedAsyncioTestCase):
    async def test_every_released_choice_activity_supports_post_answer_tutor_context(self) -> None:
        entries = json.loads((ROOT / "content/modules.json").read_text(encoding="utf-8"))["modules"]
        calls = []

        def reply(messages, _info):
            for message in messages:
                for part in message.parts:
                    if isinstance(part, UserPromptPart) and isinstance(part.content, str):
                        calls.append(json.loads(part.content))
            return ModelResponse(parts=[TextPart("Let's compare the scenario details and the reason behind your choice.")])

        model = FunctionModel(reply)
        checked = 0
        shared_misconceptions = 0
        packs = 0
        for entry in entries:
            for profile_id, path in entry["profile_pack_paths"].items():
                packs += 1
                pack = load_content_pack(ROOT / path)
                for index, activity in enumerate(pack.activities):
                    if not activity.choices:
                        continue
                    with self.subTest(pack=pack.pack_id, activity=activity.activity_id):
                        controller = DemoController(pack, profile_id=profile_id)
                        started = controller.start(
                            session_id=f"context.{packs}.{index}",
                            preferred_activity_ids=(activity.activity_id,), route_scope="preferred",
                        )
                        finish_current_experiment(controller)
                        controller.respond(
                            request_id="context.answer", option_id=next(choice.option_id for choice in activity.choices if choice.correct),
                        )
                        message = LearnerMessage(text="Could you explain the reason behind my choice?")
                        record_learner_message(
                            controller.events, pack, attempt_id=started["attempt_id"],
                            request_id="context.followup", message=message,
                        )
                        deps = build_tutor_deps(controller.events, pack, request_id="context.followup")
                        declared = [choice.misconception_id for choice in activity.choices if choice.misconception_id is not None]
                        self.assertEqual(deps.allowed_misconception_ids, tuple(dict.fromkeys(declared)))
                        shared_misconceptions += len(declared) > len(set(declared))
                        with override_allow_model_requests(False):
                            state = await controller.send_message_with_tutor(
                                request_id="context.followup", text=message.text,
                                model=model, unguarded=True,
                            )
                        checked += 1
                        self.assertEqual(len(calls), checked)
                        self.assertEqual(calls[-1]["profile_id"], profile_id)
                        self.assertEqual(calls[-1]["activity"], deps.current_question.text)
                        self.assertTrue(state["assessment_accepted"])
                        self.assertIsNone(state["pending_tutor_message"])
        self.assertEqual(packs, 6)
        self.assertGreater(shared_misconceptions, 0)
        self.assertGreaterEqual(checked, 118)


if __name__ == "__main__":
    unittest.main()
