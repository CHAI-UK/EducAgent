"""Normal full-course profile selection, scoped resets and fixed context."""

import asyncio
import json
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from pydantic_ai.messages import ModelResponse, TextPart, UserPromptPart
from pydantic_ai.models import override_allow_model_requests
from pydantic_ai.models.function import FunctionModel
from pydantic_ai.models.test import TestModel

from educagent_sdk import load_content_pack
from educagent_sdk.demo import DemoController, JsonlEventStore
from educagent_sdk.diagnostic import DiagnosticSession, load_diagnostic_plan
from educagent_sdk.foundation_profiles import load_foundation_profiles
from educagent_sdk.web_demo import ModuleRuntime, ProfileRuntime, create_module_hub_server
from tests.experiment_helpers import finish_current_experiment


ROOT = Path(__file__).resolve().parents[1]


class NormalProfilesTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        directory = Path(self.temporary.name)
        self.base_pack = load_content_pack(ROOT / "content/causality_m0_full.json")
        self.teaching_pack = self.base_pack.model_copy(update={
            "pack_id": "causality.m0.general-teaching", "version": "1.0.0",
        })
        question_id = self.base_pack.activities[0].question_resource_id
        self.medical_pack = self.base_pack.model_copy(update={
            "pack_id": "causality.m0.medical", "version": "1.0.0",
            "resources": tuple(
                resource.model_copy(update={"text": "Medical fixture: " + resource.text})
                if resource.resource_id == question_id else resource
                for resource in self.base_pack.resources
            ),
        })
        self.general = DemoController(
            self.base_pack, store=JsonlEventStore(directory / "causality_m0-1.1.0.jsonl"),
            profile_id="general", teaching_pack=self.teaching_pack,
        )
        self.medical = DemoController(
            self.medical_pack, store=JsonlEventStore(directory / "causality_m0-medical-1.0.0.jsonl"),
            profile_id="medical",
        )
        plan = load_diagnostic_plan(ROOT / "content/causality_m0_diagnostic.json")
        self.general_diagnostic = DiagnosticSession(self.base_pack, plan)
        self.medical_diagnostic = DiagnosticSession(self.medical_pack, plan)
        self.module = ModuleRuntime(
            "causality_m0", "Causality foundations", False, (), None,
            self.general, self.general_diagnostic, profiles={
                "general": ProfileRuntime(self.general, self.general_diagnostic),
                "medical": ProfileRuntime(self.medical, self.medical_diagnostic),
            },
        )
        self.effect_module = ModuleRuntime(
            "m1_effect", "Effect of an intervention", True, ("causality_m0",), "effect",
            DemoController(load_content_pack(ROOT / "content/m1_effect_of_an_intervention.json")),
        )
        self.server = create_module_hub_server([self.module, self.effect_module], port=0, model=TestModel(), unguarded_tutor=True, open_modules=False)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.stop_server)
        self.base = f"http://127.0.0.1:{self.server.server_port}"

    def stop_server(self) -> None:
        self.server.shutdown()
        self.thread.join(timeout=5)
        self.server.server_close()

    def command(self, path: str, **body: object) -> dict:
        request = Request(self.base + path, data=json.dumps(body).encode(),
                          headers={"Content-Type": "application/json"})
        with urlopen(request, timeout=5) as response:
            return json.load(response)

    def state(self) -> dict:
        with urlopen(self.base + "/api/state", timeout=5) as response:
            return json.load(response)

    def test_selection_is_required_and_does_not_start_or_rewrite_saved_general_progress(self) -> None:
        started = self.general.start()
        original_bytes = self.general.store.path.read_bytes()
        initial = self.state()
        self.assertTrue(initial["profile_required"])
        self.assertEqual(initial["course_profiles"], ["general", "medical"])
        with self.assertRaises(HTTPError) as missing:
            self.command("/api/diagnostic/start")
        self.assertEqual(missing.exception.code, 409)
        resumed = self.command("/api/select-profile", profile_id="general")
        self.assertFalse(resumed["profile_required"])
        self.assertEqual(resumed["attempt_id"], started["attempt_id"])
        self.assertEqual(resumed["learning_pack_version"], "1.1.0")
        self.assertEqual(resumed["profile_content_version"], "1.0.0")
        self.assertEqual(self.general.store.path.read_bytes(), original_bytes)
        medical = self.command("/api/select-profile", profile_id="medical")
        self.assertEqual(medical["status"], "not_started")
        self.assertEqual(medical["learning_pack_id"], self.medical_pack.pack_id)
        self.assertFalse(self.medical.events)
        self.assertEqual(self.general.store.path.read_bytes(), original_bytes)

    def test_each_profile_diagnostic_uses_its_own_pack_and_response_history(self) -> None:
        self.command("/api/select-profile", profile_id="medical")
        medical = self.command("/api/diagnostic/start")
        self.assertTrue(medical["diagnostic"]["question"].startswith("Medical fixture:"))
        self.command("/api/diagnostic/respond", request_id="same.diagnostic", option_id=medical["diagnostic"]["choices"][0]["option_id"])
        self.command("/api/select-profile", profile_id="general")
        general = self.command("/api/diagnostic/start")
        self.assertFalse(general["diagnostic"]["question"].startswith("Medical fixture:"))
        self.assertEqual(general["diagnostic"]["answered_count"], 0)
        self.command("/api/diagnostic/respond", request_id="same.diagnostic", option_id=general["diagnostic"]["choices"][0]["option_id"])
        resumed = self.command("/api/select-profile", profile_id="medical")
        self.assertEqual(resumed["diagnostic"]["answered_count"], 1)
        self.assertFalse(self.general.events)
        self.assertFalse(self.medical.events)

    def test_profile_switch_restores_checked_answer_and_never_mixes_chat(self) -> None:
        self.command("/api/select-profile", profile_id="general")
        started = self.command("/api/diagnostic/skip")
        self.command("/api/message", request_id="same.chat", text="GENERAL_ONLY_MARKER")
        activity = next(item for item in self.base_pack.activities if item.activity_id == started["activity_id"])
        checked = self.command("/api/respond", request_id="same.answer", option_id=next(item.option_id for item in activity.choices if item.correct))
        original_bytes = self.general.store.path.read_bytes()
        self.command("/api/select-profile", profile_id="medical")
        self.command("/api/diagnostic/skip")
        medical = self.command("/api/message", request_id="same.chat", text="MEDICAL_ONLY_MARKER")
        self.assertNotIn("GENERAL_ONLY_MARKER", json.dumps(medical["conversation"]))
        resumed = self.command("/api/select-profile", profile_id="general")
        self.assertEqual(resumed["attempt_id"], checked["attempt_id"])
        self.assertTrue(resumed["can_continue"])
        self.assertNotIn("MEDICAL_ONLY_MARKER", json.dumps(resumed["conversation"]))
        self.assertEqual(self.general.store.path.read_bytes(), original_bytes)

    def test_reset_requires_exact_scope_and_preserves_the_other_profile_file(self) -> None:
        self.general.start()
        original_bytes = self.general.store.path.read_bytes()
        self.command("/api/select-profile", profile_id="medical")
        medical = self.command("/api/diagnostic/skip")
        with self.assertRaises(HTTPError) as stale:
            self.command("/api/reset", profile_id="general", pack_id=self.base_pack.pack_id, version=self.base_pack.version)
        self.assertEqual(stale.exception.code, 409)
        self.assertTrue(self.medical.events)
        reset = self.command("/api/reset", profile_id="medical", pack_id=medical["learning_pack_id"], version=medical["learning_pack_version"])
        self.assertTrue(reset["profile_required"])
        self.assertIsNone(reset["profile_id"])
        self.assertFalse(self.medical.events)
        self.assertEqual(self.medical.store.path.read_bytes(), b"")
        self.assertEqual(self.general.store.path.read_bytes(), original_bytes)
        resumed = self.command("/api/select-profile", profile_id="general")
        self.assertEqual(resumed["status"], "active")

    def test_controller_metadata_is_read_only_and_teacher_cannot_change_scoring(self) -> None:
        with self.assertRaises(AttributeError):
            self.general.profile_id = "medical"
        with self.assertRaises(AttributeError):
            self.general.teaching_pack = self.medical_pack
        activity = self.teaching_pack.activities[0]
        changed = activity.model_copy(update={"requires_revision": not activity.requires_revision})
        incompatible = self.teaching_pack.model_copy(update={"activities": (changed, *self.teaching_pack.activities[1:])})
        with self.assertRaisesRegex(ValueError, "assessment contract"):
            DemoController(self.base_pack, profile_id="general", teaching_pack=incompatible)

    def test_module_return_and_preview_restore_the_normal_medical_profile(self) -> None:
        self.command("/api/select-profile", profile_id="medical")
        original = self.command("/api/diagnostic/skip")
        original_bytes = self.medical.store.path.read_bytes()
        self.command("/api/select-module", module_id="m1_effect", test_only_force_unlock=True)
        returned = self.command("/api/select-module", module_id="causality_m0")
        self.assertEqual(returned["profile_id"], "medical")
        self.assertEqual(returned["attempt_id"], original["attempt_id"])
        self.command("/api/preview", enabled=True)
        self.command("/api/select-profile", profile_id="general")
        self.command("/api/select-module", module_id="m1_effect")
        self.command("/api/preview", enabled=True)
        restored = self.command("/api/preview", enabled=False)
        self.assertEqual(restored["profile_id"], "medical")
        self.assertEqual(restored["active_module_id"], "causality_m0")
        self.assertEqual(restored["attempt_id"], original["attempt_id"])
        self.assertEqual(self.medical.store.path.read_bytes(), original_bytes)
        self.assertFalse(self.general.events)

    def test_prerequisites_use_the_selected_normal_profile_completion(self) -> None:
        self.command("/api/select-profile", profile_id="general")
        complete_medical = {
            "status": "completed",
            "completed_concept_ids": tuple(item.concept_id for item in self.medical.pack.concepts),
            "completed_activity_ids": tuple(item.activity_id for item in self.medical.pack.activities),
        }
        with patch.object(self.medical, "view", return_value=complete_medical):
            selected = self.command("/api/select-profile", profile_id="medical")
            self.assertEqual(next(item for item in selected["modules"] if item["module_id"] == "m1_effect")["status"], "available")
            selected = self.command("/api/select-profile", profile_id="general")
            self.assertEqual(next(item for item in selected["modules"] if item["module_id"] == "m1_effect")["status"], "locked")

    def test_guided_tutor_receives_fixed_profile_and_separate_teaching_version(self) -> None:
        captured = []

        def reply(messages, _info):
            for message in messages:
                for part in message.parts:
                    if isinstance(part, UserPromptPart) and isinstance(part.content, str):
                        captured.append(json.loads(part.content))
            return ModelResponse(parts=[TextPart("A variable can have different recorded values.")])

        self.general.start()
        with override_allow_model_requests(False):
            asyncio.run(self.general.send_message_with_tutor(
                request_id="normal.context", text="What can vary?", model=FunctionModel(reply), unguarded=True,
            ))
        self.assertEqual(captured[-1]["profile_id"], "general")
        self.assertEqual(captured[-1]["teaching_pack_id"], self.teaching_pack.pack_id)
        self.assertEqual(captured[-1]["teaching_pack_version"], "1.0.0")
        self.assertEqual(self.general.pack.version, "1.1.0")
        self.assertNotIn("lessons", captured[-1])


class CompiledNormalCourseTest(unittest.TestCase):
    def test_current_shift_profiles_at_eight_and_ten_of_sixteen_are_not_completed(self) -> None:
        entry = next(item for item in json.loads((ROOT / "content/modules.json").read_text())["modules"]
                     if item["module_id"] == "m1_shift")
        for profile in ("general", "medical"):
            with self.subTest(profile=profile):
                pack = load_content_pack(ROOT / entry["profile_pack_paths"][profile])
                controller = DemoController(pack, profile_id=profile)
                controller.start(session_id=f"partial.shift.{profile}")
                module = ModuleRuntime("shift", pack.title, False, (), None, controller,
                                       profiles={profile: ProfileRuntime(controller)})
                server = create_module_hub_server([module], port=0, model=TestModel())
                thread = threading.Thread(target=server.serve_forever, daemon=True)
                thread.start()
                base = f"http://127.0.0.1:{server.server_port}"
                try:
                    request = Request(base + "/api/select-profile", data=json.dumps({"profile_id": profile}).encode(),
                                      headers={"Content-Type": "application/json"})
                    with urlopen(request, timeout=5) as response:
                        json.load(response)
                    for count in range(1, 11):
                        state = controller.view()
                        activity = next(item for item in pack.activities if item.activity_id == state["activity_id"])
                        finish_current_experiment(controller)
                        controller.respond(request_id=f"partial.answer.{count}",
                                           option_id=next(item.option_id for item in activity.choices if item.correct))
                        controller.continue_activity(request_id=f"partial.next.{count}")
                        if count in {8, 10}:
                            with urlopen(base + "/api/state", timeout=5) as response:
                                state = json.load(response)
                            self.assertEqual(state["status"], "active")
                            self.assertEqual(len(state["completed_activity_ids"]), count)
                            self.assertEqual(len(pack.activities), 16)
                            self.assertEqual(state["modules"][0]["status"], "available")
                            self.assertNotEqual(set(state["completed_concept_ids"]),
                                                {item.concept_id for item in pack.concepts})
                finally:
                    server.shutdown()
                    thread.join(timeout=5)
                    server.server_close()

    def test_concept_coverage_and_targeted_session_completion_do_not_complete_full_course(self) -> None:
        original = load_content_pack(ROOT / "content/m1_robust_prediction_or_generation.json")
        extra = original.activities[0].model_copy(update={"activity_id": "extra.full-course-check"})
        pack = original.model_copy(update={"activities": (*original.activities, extra)})
        for route_scope in ("all", "preferred"):
            with self.subTest(route_scope=route_scope):
                controller = DemoController(pack)
                controller.start(session_id=f"coverage.{route_scope}", route_scope=route_scope,
                                 preferred_activity_ids=tuple(item.activity_id for item in original.activities))
                for index in range(len(original.activities)):
                    state = controller.view()
                    activity = next(item for item in pack.activities if item.activity_id == state["activity_id"])
                    controller.respond(request_id=f"coverage.answer.{index}",
                                       option_id=next(item.option_id for item in activity.choices if item.correct))
                    controller.continue_activity(request_id=f"coverage.next.{index}")
                self.assertEqual(set(controller.view()["completed_concept_ids"]),
                                 {item.concept_id for item in pack.concepts})
                self.assertEqual(controller.view()["status"], "active" if route_scope == "all" else "completed")
                original_events = tuple(controller.events)
                modules = [
                    ModuleRuntime("course", pack.title, False, (), None, controller),
                    ModuleRuntime("next", "Next course", False, ("course",), None, DemoController(original)),
                ]
                server = create_module_hub_server(modules, port=0, model=TestModel(), open_modules=False)
                thread = threading.Thread(target=server.serve_forever, daemon=True)
                thread.start()
                try:
                    with urlopen(f"http://127.0.0.1:{server.server_port}/api/state", timeout=5) as response:
                        state = json.load(response)
                    statuses = {item["module_id"]: item["status"] for item in state["modules"]}
                    self.assertEqual(statuses, {"course": "available", "next": "locked"})
                    self.assertEqual(tuple(controller.events), original_events)
                finally:
                    server.shutdown()
                    thread.join(timeout=5)
                    server.server_close()

    def test_module_statuses_follow_current_profile_not_each_modules_previous_profile(self) -> None:
        pack = load_content_pack(ROOT / "content/m1_effect_of_an_intervention.json")
        with tempfile.TemporaryDirectory() as directory:
            modules = []
            for module_id in ("foundation", "effect", "shift"):
                profiles = {
                    profile: ProfileRuntime(DemoController(
                        pack, profile_id=profile,
                        store=JsonlEventStore(Path(directory) / f"{module_id}-{profile}.jsonl"),
                    ))
                    for profile in ("general", "medical")
                }
                modules.append(ModuleRuntime(
                    module_id, module_id.title(), False,
                    () if module_id == "foundation" else ("foundation",), None,
                    profiles["general"].controller, profiles=profiles,
                ))
                for profile, runtime in profiles.items():
                    controller = runtime.controller
                    complete = module_id == "foundation" or (module_id, profile) in {
                        ("effect", "general"), ("shift", "medical"),
                    }
                    controller.start(session_id=f"fixture.{module_id}.{profile}")
                    while controller.view()["status"] == "active":
                        state = controller.view()
                        activity = next(item for item in pack.activities if item.activity_id == state["activity_id"])
                        controller.respond(
                            request_id=f"fixture.answer.{len(controller.events)}",
                            option_id=next(item.option_id for item in activity.choices if item.correct),
                        )
                        controller.continue_activity(request_id=f"fixture.next.{len(controller.events)}")
                        if not complete:
                            break
                    self.assertEqual(controller.view()["status"], "completed" if complete else "active")
            saved = {
                runtime.controller.store.path: runtime.controller.store.path.read_bytes()
                for module in modules for runtime in module.profiles.values()
            }
            server = create_module_hub_server(modules, port=0, model=TestModel(), open_modules=False)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base = f"http://127.0.0.1:{server.server_port}"

            def command(path: str, **body: object) -> dict:
                request = Request(base + path, data=json.dumps(body).encode(),
                                  headers={"Content-Type": "application/json"})
                with urlopen(request, timeout=5) as response:
                    return json.load(response)

            def statuses(state: dict) -> dict:
                return {item["module_id"]: item["status"] for item in state["modules"]}

            try:
                command("/api/select-profile", profile_id="medical")
                command("/api/select-module", module_id="effect")
                command("/api/select-module", module_id="shift")
                medical = command("/api/select-module", module_id="foundation")
                self.assertEqual(statuses(medical), {
                    "foundation": "completed", "effect": "available", "shift": "completed",
                })
                general = command("/api/select-profile", profile_id="general")
                expected = {"foundation": "completed", "effect": "completed", "shift": "available"}
                self.assertEqual(statuses(general), expected)
                with urlopen(base + "/api/modules", timeout=5) as response:
                    self.assertEqual(statuses(json.load(response)), expected)
                effect = command("/api/select-module", module_id="effect")
                self.assertEqual(effect["profile_id"], "general")
                self.assertEqual(effect["status"], "completed")
                command("/api/select-module", module_id="foundation")
                medical = command("/api/select-profile", profile_id="medical")
                self.assertEqual(statuses(medical), {
                    "foundation": "completed", "effect": "available", "shift": "completed",
                })
                for path, original in saved.items():
                    self.assertEqual(path.read_bytes(), original)
            finally:
                server.shutdown()
                thread.join(timeout=5)
                server.server_close()

    def test_integrated_transfer_is_a_challenge_without_matching_the_lecture_challenge_id(self) -> None:
        from examples.playable_demo import _build_module

        entry = json.loads((ROOT / "content/modules.json").read_text(encoding="utf-8"))["modules"][0]
        with tempfile.TemporaryDirectory() as directory:
            module = _build_module(entry, events_root=Path(directory), reset=False)
            server = create_module_hub_server([module], port=0, model=TestModel(), unguarded_tutor=True)
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

                command("/api/select-profile", profile_id="general")
                command("/api/preview", enabled=True)
                state = command("/api/preview/navigate", activity_id="m0-integrated-transfer.01")
                self.assertTrue(state["activity_is_transfer"])
                self.assertEqual(state["activity_stage"], "challenge")
                self.assertFalse(state["lesson_is_sample"])
                self.assertNotEqual(state["lesson"]["challenge_activity_id"], state["activity_id"])
                self.assertFalse(module.controller.events)
            finally:
                server.shutdown()
                thread.join(timeout=5)
                server.server_close()

    def test_scene_hook_context_excludes_unshown_lecture_and_hidden_common_cause(self) -> None:
        base_pack = load_content_pack(ROOT / "content/causality_m0_full.json")
        teaching_pack = load_foundation_profiles(base_pack, ROOT / "content/foundation_profiles.json")["general"]
        controller = DemoController(base_pack, profile_id="general", teaching_pack=teaching_pack)
        controller.start(preferred_activity_ids=("association-is-not-causation.transfer",), route_scope="preferred")
        captured = []

        def reply(messages, _info):
            for message in messages:
                for part in message.parts:
                    if isinstance(part, UserPromptPart) and isinstance(part.content, str):
                        captured.append(json.loads(part.content))
            return ModelResponse(parts=[TextPart("Open the records to see what was observed.")])

        with override_allow_model_requests(False):
            asyncio.run(controller.send_message_with_tutor(
                request_id="scene.context", text="What should I try next?",
                model=FunctionModel(reply), unguarded=True,
            ))
        context = captured[-1]
        self.assertIsNone(context["visible_lesson"])
        self.assertIsNotNone(context["visible_scene"])
        self.assertEqual(context["profile_id"], "general")
        self.assertEqual(context["teaching_pack_version"], teaching_pack.version)
        self.assertNotIn("concept_explanation", context)
        visible_text = json.dumps(context).lower()
        self.assertNotIn("sunny weather", visible_text)
        self.assertNotIn("rain", visible_text)
        self.assertNotIn("worked_graph", visible_text)

    def test_factory_preserves_existing_general_scored_trace_and_binds_each_diagnostic(self) -> None:
        from examples.playable_demo import _build_module

        base_pack = load_content_pack(ROOT / "content/causality_m0_full.json")
        entry = {
            "module_id": "causality_m0", "title": "Causality foundations", "optional": False,
            "prerequisite_module_ids": [], "nirvana_task": None,
            "pack_path": "content/causality_m0_full.json", "diagnostic_path": "content/causality_m0_diagnostic.json",
            "profiles_path": "content/foundation_profiles.json",
        }
        with tempfile.TemporaryDirectory() as directory:
            events_root = Path(directory)
            legacy_store = JsonlEventStore(events_root / "causality_m0-1.1.0.jsonl")
            original = DemoController(base_pack, store=legacy_store)
            started = original.start(session_id="historical.general")
            activity = next(item for item in base_pack.activities if item.activity_id == started["activity_id"])
            original.respond(request_id="historical.answer", option_id=next(item.option_id for item in activity.choices if item.correct))
            original_bytes = legacy_store.path.read_bytes()
            module = _build_module(entry, events_root=events_root, reset=False)
            self.assertEqual(module.controller.pack, base_pack)
            self.assertIs(module.profiles["general"].controller, module.controller)
            self.assertEqual(module.controller.store.path, legacy_store.path)
            self.assertEqual(module.controller.store.path.read_bytes(), original_bytes)
            self.assertTrue(module.controller.view()["can_continue"])
            self.assertEqual(len(module.controller.teaching_pack.lessons), 9)
            self.assertEqual(module.profiles["medical"].controller.pack.pack_id, "causality.m0.medical")
            for runtime in module.profiles.values():
                self.assertEqual(runtime.diagnostic.pack, runtime.controller.pack)
                self.assertEqual(len(runtime.diagnostic.activities), 9)

    def test_tutor_gets_only_current_compiled_lecture_with_fixed_content_version(self) -> None:
        base_pack = load_content_pack(ROOT / "content/causality_m0_full.json")
        compiled = load_foundation_profiles(base_pack, ROOT / "content/foundation_profiles.json")
        captured = []

        def reply(messages, _info):
            for message in messages:
                for part in message.parts:
                    if isinstance(part, UserPromptPart) and isinstance(part.content, str):
                        captured.append(json.loads(part.content))
            return ModelResponse(parts=[TextPart("The arrows describe the assumed causal direction.")])

        for profile_id, teaching_pack in compiled.items():
            scored = base_pack if profile_id == "general" else teaching_pack
            controller = DemoController(scored, profile_id=profile_id, teaching_pack=teaching_pack)
            controller.start(session_id=f"lecture-context.{profile_id}")
            controller.navigate_to_concept(request_id="lecture-context.navigate", concept_id="basic-dag-language")
            with override_allow_model_requests(False):
                asyncio.run(controller.send_message_with_tutor(
                    request_id="lecture-context.question", text="What do the arrows mean?",
                    model=FunctionModel(reply), unguarded=True,
                ))
            context = captured[-1]
            self.assertEqual(context["profile_id"], profile_id)
            self.assertEqual(context["teaching_pack_version"], teaching_pack.version)
            self.assertIsNone(context["visible_lesson"])
            self.assertEqual(context["assessment_help"]["phase"], "topic_before_answer")
            self.assertNotIn("lessons", context)
            self.assertNotIn("concept_explanation", context)
            self.assertEqual(context["recent_conversation"], [])


if __name__ == "__main__":
    unittest.main()
