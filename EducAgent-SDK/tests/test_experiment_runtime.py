"""Replay, API ownership and grading gates for unscored experiment artifacts."""

import asyncio
import json
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from pydantic_ai.messages import ModelResponse, TextPart, ToolCallPart, UserPromptPart
from pydantic_ai.models import override_allow_model_requests
from pydantic_ai.models.function import FunctionModel
from pydantic_ai.models.test import TestModel

from educagent_sdk import (
    ContentPack, EffectExperimentConfig, EffectExperimentModel, ExperimentActionRecorded,
    ExperimentWorkbench, build_tutor_deps, load_content_pack, replay,
)
from educagent_sdk.demo import DemoController, JsonlEventStore
from educagent_sdk.events import (
    LearnerMessage, ResponseRecorded, SupportRequest, record_learner_message, record_support_request,
)
from educagent_sdk.experiments import CommitExperimentPrediction, ReflectOnExperiment, RunExperiment
from educagent_sdk.tutor import _tutor_prompt
from educagent_sdk.web_demo import create_demo_server
from tests.experiment_helpers import finish_current_experiment


ROOT = Path(__file__).resolve().parents[1]


def experiment_pack():
    original = load_content_pack(ROOT / "content/causality_m0.json")
    activity = original.activities[0]
    spec = ExperimentWorkbench(
        experiment_id="test.programme", title="Compare programme settings",
        instructions_resource_id=activity.explanation_resource_id,
        model=EffectExperimentModel(a_low=0.93, low_label="Lower baseline", high_label="Higher baseline",
            outcome_label="Success", treatment_a_label="Programme A", treatment_b_label="Programme B"),
        initial_config=EffectExperimentConfig(),
    )
    return original.model_copy(update={"activities": (activity.model_copy(update={"experiment": spec}),)})


class ExperimentRuntimeTest(unittest.TestCase):
    def setUp(self):
        self.pack = experiment_pack()
        self.controller = DemoController(self.pack)
        self.controller.start(session_id="artifact.test")

    def action(self, action, request_id, **overrides):
        state = self.controller.view()
        body = dict(request_id=request_id, attempt_id=state["attempt_id"],
            experiment_id=state["experiment"]["experiment_id"],
            input_revision=state["experiment"]["revision"], action=action)
        body.update(overrides)
        return self.controller.submit_experiment_action(**body)

    def test_actions_are_idempotent_unscored_revision_checked_and_attempt_owned(self):
        with self.assertRaisesRegex(ValueError, "prediction"):
            self.action(RunExperiment(), "artifact.no-prediction")
        committed = self.action(CommitExperimentPrediction(config=EffectExperimentConfig(), prediction="A may have a lower pooled rate."), "artifact.predict")
        self.assertEqual(committed["phase"], "awaiting_response")
        self.assertIsNone(replay(self.controller.events).pending_request_id)
        self.assertFalse(committed["can_continue"])
        count = len(self.controller.events)
        self.action(CommitExperimentPrediction(config=EffectExperimentConfig(), prediction="A may have a lower pooled rate."), "artifact.predict", input_revision=0)
        self.assertEqual(len(self.controller.events), count)
        for overrides in ({"attempt_id": "another.attempt"}, {"experiment_id": "another.experiment"}, {"input_revision": 0}):
            with self.subTest(overrides=overrides), self.assertRaises(ValueError):
                self.action(RunExperiment(), "artifact.invalid", **overrides)
        result = self.action(RunExperiment(), "artifact.run")
        self.assertIsNotNone(result["experiment"]["result"])
        changed = self.action(CommitExperimentPrediction(config=EffectExperimentConfig(analysis="standardized"), prediction="A common target may change the contrast."), "artifact.changed")
        self.assertIsNone(changed["experiment"]["result"])
        self.assertEqual(len(changed["experiment"]["runs"]), 1)
        self.assertFalse(any(isinstance(event, ResponseRecorded) for event in self.controller.events))
        self.assertEqual(self.controller.view()["experiment"]["revision"], 3)
        tampered = self.controller.events[-1].model_copy(update={"payload": self.controller.events[-1].payload.model_copy(update={"output_revision": 99})})
        with self.assertRaisesRegex(ValueError, "not canonical"):
            replay((*self.controller.events[:-1], tampered))

    def test_score_gate_is_enforced_by_command_and_replay_then_freezes_operations(self):
        correct = next(choice.option_id for choice in self.pack.activities[0].choices if choice.correct)
        with self.assertRaisesRegex(ValueError, "not ready"):
            self.controller.respond(request_id="artifact.early", option_id=correct)
        plain = self.pack.model_copy(update={"activities": (self.pack.activities[0].model_copy(update={"experiment": None}),)})
        other = DemoController(plain)
        other.start(session_id="artifact.test")
        other.respond(request_id="artifact.forged", option_id=correct)
        forged = next(event for event in other.events if isinstance(event, ResponseRecorded))
        with self.assertRaisesRegex(ValueError, "not ready"):
            replay((*self.controller.events, forged))
        finish_current_experiment(self.controller)
        self.assertTrue(self.controller.view()["can_submit_response"])
        accepted = self.controller.respond(request_id="artifact.accepted", option_id=correct)
        self.assertTrue(accepted["assessment_accepted"])
        with self.assertRaisesRegex(ValueError, "frozen"):
            self.action(CommitExperimentPrediction(config=EffectExperimentConfig(), prediction="Try another setting."), "artifact.frozen")
        self.assertEqual(self.controller.continue_activity(request_id="artifact.complete")["status"], "completed")

    def test_jsonl_restores_the_exact_run_history_and_gate(self):
        with tempfile.TemporaryDirectory() as directory:
            store = JsonlEventStore(Path(directory) / "experiment.jsonl")
            controller = DemoController(self.pack, store=store)
            controller.start(session_id="artifact.saved")
            finish_current_experiment(controller)
            restored = DemoController(self.pack, store=store)
            self.assertEqual(restored.view(), controller.view())
            self.assertEqual(sum(isinstance(event, ExperimentActionRecorded) for event in restored.events), 5)

    def test_rejected_check_allows_revised_experiment_and_clears_current_grading(self):
        finish_current_experiment(self.controller)
        activity = self.pack.activities[0]
        rejected = self.controller.respond(request_id="artifact.rejected", option_id=next(choice.option_id for choice in activity.choices if not choice.correct))
        self.assertTrue(rejected["assessment_submitted"])
        revised = self.action(CommitExperimentPrediction(config=EffectExperimentConfig(target_high_pct=70), prediction="A larger high-baseline target may change the standardized contrast."), "artifact.after-rejection")
        self.assertFalse(revised["assessment_submitted"])
        self.assertFalse(revised["assessment_accepted"])
        self.assertFalse(revised["can_submit_response"])
        self.assertIsNone(replay(self.controller.events).last_evaluation)
        self.action(RunExperiment(), "artifact.revised-run")
        self.action(ReflectOnExperiment(reflection="I compared the new target with my earlier two runs."), "artifact.revised-reflection")
        accepted = self.controller.respond(request_id="artifact.revised-answer", option_id=next(choice.option_id for choice in activity.choices if choice.correct))
        self.assertTrue(accepted["assessment_accepted"])

    def test_tutor_receives_only_visible_results_and_bounded_history(self):
        captured = []

        def reply(messages, _info):
            for message in messages:
                for part in message.parts:
                    if isinstance(part, UserPromptPart) and isinstance(part.content, str):
                        captured.append(json.loads(part.content))
            return ModelResponse(parts=[TextPart("Compare the settings you chose and the result you have already run.")])

        async def chat(request):
            return await self.controller.send_message_with_tutor(request_id=request, text="What can I compare now?", model=FunctionModel(reply), unguarded=True)

        with override_allow_model_requests(False):
            asyncio.run(chat("artifact.before-run"))
        before = captured[-1]
        self.assertIsNone(before["visible_experiment"]["result"])
        self.assertEqual(before["visible_experiment"]["runs"], [])
        self.assertNotIn("quantity_definitions", before["visible_experiment"])
        self.assertIsNone(before["visible_lesson"])
        self.assertNotIn("concept_explanation", before)
        self.assertNotIn("a_low", json.dumps(before))
        for index in range(10):
            self.action(CommitExperimentPrediction(config=EffectExperimentConfig(target_high_pct=index * 10), prediction="The target mixture may affect the comparison."), f"artifact.repeat.{index}")
            self.action(RunExperiment(), f"artifact.repeat-run.{index}")
        with override_allow_model_requests(False):
            asyncio.run(chat("artifact.after-run"))
        self.assertIsNotNone(captured[-1]["visible_experiment"]["result"])
        self.assertEqual(len(captured[-1]["visible_experiment"]["runs"]), 3)
        self.assertNotIn("a_low", json.dumps(captured[-1]))


class ExperimentHttpTest(unittest.TestCase):
    def test_http_actions_do_not_invoke_tutor_and_enforce_transport_and_ownership(self):
        pack = experiment_pack()
        controller = DemoController(pack)
        started = controller.start(session_id="artifact.http")

        def forbidden_request(_messages, _info):
            raise AssertionError("artifact edits must not request a Tutor")

        server = create_demo_server(controller, port=0, model=FunctionModel(forbidden_request))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            def command(path, body):
                request = Request(f"http://127.0.0.1:{server.server_port}" + path,
                    data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
                with urlopen(request, timeout=5) as response:
                    return json.load(response)

            body = {"request_id": "artifact.http.commit", "attempt_id": started["attempt_id"],
                "experiment_id": "test.programme", "input_revision": 0,
                "action": {"kind": "commit_prediction", "config": {"kind": "effect"}, "prediction": "The comparison may change."}}
            committed = command("/api/experiment-action", body)
            self.assertEqual(committed["experiment"]["phase"], "predicted")
            self.assertIsNone(committed["pending_tutor_message"])
            self.assertEqual(committed, command("/api/experiment-action", body))
            for overrides, expected_status in (({"input_revision": True}, 400), ({"attempt_id": "foreign.attempt"}, 409), ({"input_revision": 0}, 409)):
                invalid = {**body, "request_id": "artifact.http.invalid", "input_revision": 1, "action": {"kind": "run"}, **overrides}
                with self.subTest(overrides=overrides), self.assertRaises(HTTPError) as error:
                    command("/api/experiment-action", invalid)
                self.assertEqual(error.exception.code, expected_status)
            with self.assertRaises(HTTPError) as gated:
                command("/api/respond", {"request_id": "artifact.http.early", "option_id": next(choice.option_id for choice in pack.activities[0].choices if choice.correct)})
            self.assertEqual(gated.exception.code, 409)
            result = command("/api/experiment-action", {**body, "request_id": "artifact.http.run", "input_revision": 1, "action": {"kind": "run"}})
            self.assertIsNotNone(result["experiment"]["result"])
        finally:
            server.shutdown()
            thread.join(timeout=5)
            server.server_close()


class OperationalExperimentTutorContextTest(unittest.TestCase):
    def packs(self):
        for course in ("effect", "shift"):
            for profile in ("general", "medical"):
                yield load_content_pack(ROOT / f"content/m1_{course}_course_{profile}.json")

    def test_every_operational_orientation_excludes_hidden_reference_tables(self):
        for pack in self.packs():
            for activity in pack.activities:
                if activity.experiment is None:
                    continue
                with self.subTest(pack=pack.pack_id, activity=activity.activity_id):
                    controller = DemoController(pack)
                    started = controller.start(preferred_activity_ids=(activity.activity_id,), route_scope="preferred")
                    record_support_request(controller.events, pack, attempt_id=started["attempt_id"],
                        request_id="context.orientation", request=SupportRequest(kind="orientation"))
                    deps = build_tutor_deps(controller.events, pack, request_id="context.orientation")
                    self.assertEqual(deps.current_question.text, activity.workbench.prompt)
                    for resource in deps.grounding_resources:
                        if resource.resource_id == activity.question_resource_id:
                            self.assertEqual(resource.text, activity.workbench.prompt)
                    serialized = _tutor_prompt(deps)
                    self.assertNotIn("Records available in this step:", serialized)
                    for table in activity.workbench.tables:
                        self.assertNotIn(table.label, serialized)
                    visible = json.loads(deps.visible_experiment)
                    self.assertIsNone(visible["result"])
                    self.assertEqual(visible["runs"], [])
                    self.assertIn("No experiment outcome records or results", visible["phase_guidance"])
                    # This is a Tutor-only visibility projection, not a pack rewrite.
                    question = next(item for item in pack.resources if item.resource_id == activity.question_resource_id)
                    self.assertIn("Records available in this step:", question.text)

    def test_controller_conversation_without_generated_wording_omits_hidden_table(self):
        for pack in self.packs():
            with self.subTest(pack=pack.pack_id):
                activity = next(item for item in pack.activities if item.experiment is not None)
                with tempfile.TemporaryDirectory() as directory:
                    store = JsonlEventStore(Path(directory) / "context.jsonl")
                    controller = DemoController(pack, store=store)
                    # A valid elicit may omit generated wording; rendering must
                    # not fall back to the hidden legacy reference appendix.
                    with override_allow_model_requests(False):
                        view = asyncio.run(controller.start_with_tutor(
                            preferred_activity_ids=(activity.activity_id,), route_scope="preferred",
                            model=TestModel(custom_output_args={
                                "candidate_id": f"tutor.elicit.{activity.question_resource_id}",
                            })))
                        clarified = asyncio.run(controller.send_message_with_tutor(
                            request_id="context.clarification", text="What should I look at?",
                            model=TestModel(custom_output_args={
                                "candidate_id": f"tutor.clarify.{activity.question_resource_id}",
                            })))
                    for projected in (view, clarified, DemoController(pack, store=store).view()):
                        tutor_messages = [message["text"] for message in projected["conversation"] if message["role"] == "tutor"]
                        self.assertTrue(tutor_messages)
                        self.assertTrue(all(text == activity.workbench.prompt for text in tutor_messages))
                        self.assertEqual(projected["turn"], activity.workbench.prompt)
                        for text in tutor_messages:
                            self.assertNotIn("Records available in this step:", text)
                            self.assertNotIn("94%", text)
                            for table in activity.workbench.tables:
                                self.assertNotIn(table.label, text)
                    recorded = next(event for event in controller.events if event.event_type == "teaching_move_selected")
                    self.assertIsNone(recorded.payload.socratic_question)
                    self.assertIsNone(recorded.payload.tutor_reply)
                    self.assertEqual(recorded.payload.grounding_resource_ids, (activity.question_resource_id,))

    def test_guided_chat_uses_only_revealed_runs_before_and_after_configuration_changes(self):
        for pack in self.packs():
            with self.subTest(pack=pack.pack_id):
                activity = next(item for item in pack.activities if item.experiment is not None)
                controller = DemoController(pack)
                controller.start(preferred_activity_ids=(activity.activity_id,), route_scope="preferred")
                captured = []
                reply_text = "Use the displayed settings, then compare only the runs you have recorded."

                def reply(messages, info):
                    for message in messages:
                        for part in message.parts:
                            if isinstance(part, UserPromptPart) and isinstance(part.content, str):
                                captured.append(json.loads(part.content))
                    self.assertIn("Quote the displayed values and units when comparing runs", info.instructions)
                    self.assertIn('as "half as many" or "twice as many" only when that relationship is exact', info.instructions)
                    self.assertIn("correct an earlier numerical description", info.instructions)
                    return ModelResponse(parts=[TextPart(reply_text)])

                def chat(request_id, text="What can I inspect now? I have never studied causality."):
                    with override_allow_model_requests(False):
                        asyncio.run(controller.send_message_with_tutor(request_id=request_id,
                            text=text,
                            model=FunctionModel(reply), unguarded=True))
                    context = captured[-1]
                    self.assertEqual(context["activity"], activity.workbench.prompt)
                    serialized = json.dumps(context)
                    self.assertNotIn("Records available in this step:", serialized)
                    self.assertNotIn("94%", serialized)
                    self.assertNotIn("88%", serialized)
                    self.assertNotIn("a_low", serialized)
                    for table in activity.workbench.tables:
                        self.assertNotIn(table.label, serialized)
                    return context["visible_experiment"]

                def action(value, request_id):
                    view = controller.view()
                    return controller.submit_experiment_action(request_id=request_id,
                        attempt_id=view["attempt_id"], experiment_id=view["experiment"]["experiment_id"],
                        input_revision=view["experiment"]["revision"], action=value)

                before = chat("context.before")
                self.assertIsNone(before["result"])
                self.assertEqual(before["runs"], [])
                config = activity.experiment.initial_config
                action(CommitExperimentPrediction(config=config, prediction="I am unsure; I will test these settings."), "context.first-predict")
                predicted = chat("context.predicted")
                self.assertIsNone(predicted["result"])
                self.assertIn("prediction is recorded", predicted["phase_guidance"])
                first = action(RunExperiment(), "context.first-run")
                after = chat("context.after-first")
                self.assertEqual(after["result"], first["experiment"]["result"])
                changed = config.model_copy(update={"analysis": "standardized"} if config.kind == "effect" else {"cue_accuracy_pct": 50})
                action(CommitExperimentPrediction(config=changed, prediction="Changing one setting may change the comparison."), "context.next-predict")
                unrun = chat("context.changed-unrun")
                self.assertIsNone(unrun["result"])
                self.assertEqual(len(unrun["runs"]), 1)
                self.assertIn("current committed settings have not been run", unrun["phase_guidance"])
                second = action(RunExperiment(), "context.second-run")
                if config.kind == "shift":
                    # Inject a past model mistake to check correction context,
                    # not to claim that a mock proves the model's arithmetic.
                    reply_text = "Half as many predictions matched after the change from 90% to 50%."
                final = chat("context.after-second")
                self.assertEqual(final["result"], second["experiment"]["result"])
                self.assertEqual([run["config"] for run in final["runs"]], [config.model_dump(mode="json"), changed.model_dump(mode="json")])
                if config.kind == "shift":
                    self.assertEqual([run["metrics"][0]["value"] for run in final["runs"]], [90, 50])
                    mistaken_reply = reply_text
                    recorded_mistake = controller.events[-1].model_dump_json()
                    reply_text = "The displayed values are 90% and 50%, a decrease of 40 percentage points."
                    corrected = chat("context.correct-ratio", "Is 50% exactly half of 90%? Please check your earlier wording.")
                    self.assertEqual([run["metrics"][0]["value"] for run in corrected["runs"]], [90, 50])
                    self.assertIn(mistaken_reply, [item["text"] for item in captured[-1]["recent_conversation"]])
                    self.assertIn("Please check your earlier wording", captured[-1]["learner_message"])
                    self.assertIn(recorded_mistake, [event.model_dump_json() for event in controller.events])
                    self.assertFalse(controller.view()["assessment_submitted"])


class ShiftQuantityTutorContextTest(unittest.TestCase):
    def contexts(self):
        for profile in ("general", "medical"):
            pack = load_content_pack(ROOT / f"content/m1_shift_course_{profile}_1_2_0.json")
            self.assertEqual(pack.version, "1.2.0")
            for activity in pack.activities:
                if activity.experiment is not None:
                    yield pack, activity

    def assert_public_definitions(self, context, activity):
        visible = context["visible_experiment"]
        definitions = visible["quantity_definitions"]
        self.assertEqual(set(definitions), {
            "reference", "measurement", "prediction", "cue", "source_text",
            "report_generation", "source_fidelity", "reference_accuracy", "coverage",
            "reference_group_checks",
        })
        self.assertIn("target, set before measurement errors", definitions["reference"])
        self.assertIn("not the measured flag", definitions["reference"])
        self.assertIn("or a real clinical or inspection review", definitions["reference"])
        self.assertIn("can disagree", definitions["measurement"])
        self.assertIn("cue rule reads the cue", definitions["prediction"])
        self.assertIn("content rule reads the measurement", definitions["prediction"])
        self.assertIn("not the underlying condition", definitions["cue"])
        self.assertIn("not the reference target", definitions["source_text"])
        self.assertIn("Fixed teaching templates, not an LLM evaluation", definitions["report_generation"])
        self.assertIn("fluent rule uses the prediction", definitions["report_generation"])
        self.assertIn("grounded rule preserves the measurement", definitions["report_generation"])
        self.assertIn("not reference truth", definitions["source_fidelity"])
        self.assertIn("undefined if none", definitions["coverage"])
        self.assertIn("not by fixed input features", definitions["reference_group_checks"])
        self.assertIn("P(Y|X)", definitions["reference_group_checks"])
        # Definitions disclose meanings, not coefficients or computed answers.
        self.assertNotRegex(json.dumps(definitions), r"\d")
        serialized = json.dumps(context)
        for private in ("source_positive", "source_negative", "unsupported_detail", "qualifier", "a_low"):
            self.assertNotIn(f'"{private}"', serialized)
        self.assertNotIn('"choices"', serialized)
        self.assertNotIn('"correct"', serialized)
        for choice in activity.choices:
            self.assertNotIn(choice.text, serialized)
        for table in activity.workbench.tables:
            self.assertNotIn(table.label, serialized)
        return visible

    def test_guided_chat_receives_public_meanings_before_and_after_each_shift_stage(self):
        mistaken_reply = "The reference is the recorded flag before cue edits."
        for pack, activity in self.contexts():
            with self.subTest(pack=pack.pack_id, activity=activity.activity_id):
                controller = DemoController(pack)
                controller.start(preferred_activity_ids=(activity.activity_id,), route_scope="preferred")
                captured = []

                def reply(messages, info):
                    for message in messages:
                        for part in message.parts:
                            if isinstance(part, UserPromptPart) and isinstance(part.content, str):
                                captured.append(json.loads(part.content))
                    self.assertIn("Use visible_experiment.quantity_definitions", info.instructions)
                    self.assertIn("Correct earlier chat that conflicts", info.instructions)
                    return ModelResponse(parts=[TextPart(mistaken_reply if len(captured) == 1 else
                        "The reference is the teaching-model target; the noisy measurement can disagree with it.")])

                def chat(request, text):
                    with override_allow_model_requests(False):
                        asyncio.run(controller.send_message_with_tutor(request_id=request, text=text,
                            model=FunctionModel(reply), unguarded=True))
                    return self.assert_public_definitions(captured[-1], activity)

                before = chat("quantities.before", "What do reference, measurement and prediction mean?")
                self.assertIsNone(before["result"])
                self.assertEqual(before["runs"], [])
                self.assertIn("No experiment outcome records or results", before["phase_guidance"])
                # A real recorded run makes measurement/reference disagreement visible.
                config = activity.experiment.initial_config.model_copy(update={"measurement_error_pct": 40})
                view = controller.view()
                controller.submit_experiment_action(request_id="quantities.predict",
                    attempt_id=view["attempt_id"], experiment_id=view["experiment"]["experiment_id"],
                    input_revision=view["experiment"]["revision"],
                    action=CommitExperimentPrediction(config=config, prediction="The measurement may disagree with the reference."))
                view = controller.view()
                ran = controller.submit_experiment_action(request_id="quantities.run",
                    attempt_id=view["attempt_id"], experiment_id=view["experiment"]["experiment_id"],
                    input_revision=view["experiment"]["revision"], action=RunExperiment())
                after = chat("quantities.after", "Was your earlier definition right? Is the measurement noisy?")
                self.assertEqual(after["quantity_definitions"], before["quantity_definitions"])
                self.assertEqual(after["result"], ran["experiment"]["result"])
                self.assertTrue(any(case["measurement"] != case["target"] for case in after["result"]["cases"]))
                self.assertIn(mistaken_reply, [item["text"] for item in captured[-1]["recent_conversation"]])
                for case in after["result"]["cases"]:
                    self.assertEqual(case["prediction"], case["cue"] if config.predictor == "cue" else case["measurement"])
                    source_flag = activity.experiment.model.source_positive if case["measurement"] else activity.experiment.model.source_negative
                    self.assertTrue(case["source_text"].startswith(source_flag))
                    if case["emitted"]:
                        flag = case["prediction"] if config.generator == "fluent" else case["measurement"]
                        report_flag = activity.experiment.model.source_positive if flag else activity.experiment.model.source_negative
                        self.assertTrue(case["generated_text"].startswith(report_flag))

    def test_structured_tutor_receives_the_same_shift_definitions_without_unrun_results(self):
        for pack, activity in self.contexts():
            with self.subTest(pack=pack.pack_id, activity=activity.activity_id):
                controller = DemoController(pack)
                controller.start(preferred_activity_ids=(activity.activity_id,), route_scope="preferred")
                captured = []

                def reply(messages, info):
                    prompt = next(part.content for message in reversed(messages) for part in message.parts
                        if isinstance(part, UserPromptPart) and isinstance(part.content, str))
                    context = json.loads(prompt.split("<context>\n", 1)[1].split("\n</context>", 1)[0])
                    captured.append(context)
                    self.assertIn("Use visible_experiment.quantity_definitions", info.instructions)
                    self.assertIn("Correct earlier chat that conflicts", info.instructions)
                    return ModelResponse(parts=[ToolCallPart(info.output_tools[0].name, {
                        "candidate_id": f"tutor.clarify.{activity.question_resource_id}",
                        "tutor_reply": "The reference is the teaching-model target, not the noisy measurement.",
                    })])

                with override_allow_model_requests(False):
                    asyncio.run(controller.send_message_with_tutor(request_id="quantities.structured",
                        text="Please define the reference target.", model=FunctionModel(reply)))
                self.assertEqual(len(captured), 1)
                visible = json.loads(captured[0]["visible_experiment"])
                self.assertIsNone(visible["result"])
                self.assertEqual(visible["runs"], [])
                self.assertIn("target, set before measurement errors", visible["quantity_definitions"]["reference"])
                self.assertIsNone(captured[0]["activity"]["experiment"])
                self.assertIsNone(captured[0]["state"]["experiment_snapshot"])
