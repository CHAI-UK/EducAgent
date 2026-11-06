"""Guided practice preserves replay, results and evaluator authority."""

import asyncio
import json
import tempfile
import unittest
from pathlib import Path

from pydantic import ValidationError
from pydantic_ai.messages import ModelResponse, TextPart, UserPromptPart
from pydantic_ai.models import override_allow_model_requests
from pydantic_ai.models.function import FunctionModel

from educagent_sdk import load_content_pack
from educagent_sdk.contracts import ExperimentGuide, ExperimentWorkbench
from educagent_sdk.demo import DemoController, JsonlEventStore
from educagent_sdk.events import (
    ResponseRecorded, SupportRequest, TeachingMoveSelected, record_support_request,
)
from educagent_sdk.experiments import (
    CommitExperimentPrediction, RunExperiment, apply_experiment_action,
    experiment_view, initial_experiment_snapshot,
)
from tests.test_experiments import effect_spec, run_setup, shift_spec
from tests.experiment_helpers import finish_current_experiment
from educagent_sdk.tutor import _experiment_comparison_arithmetic, build_tutor_deps, run_tutor_turn


ROOT = Path(__file__).resolve().parents[1]


def guide_data():
    return {
        "section": "prediction", "story": "A warehouse label helps predict parcel damage.",
        "goal": "Check the same prediction rule after the label changes.",
        "parameter_id": "cue_accuracy_pct", "parameter_label": "Labels matching parcel condition",
        "parameter_description": "Change how often the warehouse label matches parcel condition.",
        "prediction_prompt": "Will fewer predictions be correct?",
        "comparison_prompt": "What changed after the labels became less useful?",
        "metrics": [{"metric_label": "Reference prediction accuracy", "label": "Correct predictions"}],
    }


class ExperimentComparisonArithmeticTest(unittest.TestCase):
    def visible(self, before, after, unit="%"):
        def run(run_id, setting, value):
            return {"run_id": run_id, "config": {"setting": setting}, "metrics": [
                {"label": "Displayed metric", "value": value, "display_value": f"{value:g}{unit}"},
            ]}
        return {"guide": {"parameter_id": "setting"}, "result": {},
                "runs": [run(1, "original", before), run(2, "changed", after)]}

    def test_disclosed_metric_arithmetic_preserves_units_signs_and_undefined_baselines(self):
        cases = (
            (90, 50, "%", -40, 55.5556, -44.4444, False, False),
            (90, 45, "%", -45, 50, -50, True, False),
            (25, 50, "%", 25, 200, 100, False, True),
            (0, 50, "%", 50, None, None, None, None),
            (0, 0, "%", 0, None, None, None, None),
            (-6, 15, " pp", 21, None, None, None, None),
            (15, -6, " pp", -21, None, None, None, None),
        )
        for before, after, unit, difference, percent, relative, half, twice in cases:
            with self.subTest(before=before, after=after, unit=unit):
                facts = _experiment_comparison_arithmetic(self.visible(before, after, unit))
                self.assertEqual((facts["from_run_id"], facts["to_run_id"]), (1, 2))
                values = facts["metrics"][0]
                self.assertEqual(values["difference"], difference)
                self.assertEqual(values["difference_unit"], "percentage_points")
                self.assertEqual(values["to_as_percent_of_from"], percent)
                self.assertEqual(values["relative_change_percent"], relative)
                self.assertEqual(values["is_exactly_half"], half)
                self.assertEqual(values["is_exactly_twice"], twice)
                self.assertEqual(values["relative_status"] == "defined", percent is not None)
        facts = _experiment_comparison_arithmetic(self.visible(90, 50))
        self.assertAlmostEqual(facts["metrics"][0]["to_over_from"], 0.5555555555555556)
        undefined = self.visible(0, 50)
        undefined["runs"][0]["metrics"][0]["display_value"] = "Not defined: no reports emitted"
        values = _experiment_comparison_arithmetic(undefined)["metrics"][0]
        self.assertIsNone(values["difference"])
        self.assertIsNone(values["to_over_from"])

    def test_comparison_uses_prior_distinct_displayed_setting_and_never_an_unrun_result(self):
        visible = self.visible(90, 50)
        visible["runs"].append({**visible["runs"][-1], "run_id": 3})
        visible["result"] = None
        facts = _experiment_comparison_arithmetic(visible)
        self.assertEqual((facts["from_run_id"], facts["to_run_id"]), (1, 3))
        self.assertEqual(facts["scope"], "recorded_runs_only")
        self.assertFalse(facts["current_configuration_has_result"])
        self.assertEqual(facts["metrics"][0]["difference"], -40)
        visible["runs"] = visible["runs"][-2:]
        self.assertIsNone(_experiment_comparison_arithmetic(visible))
        visible["runs"] = []
        self.assertIsNone(_experiment_comparison_arithmetic(visible))


class GuidedPracticeOpeningTest(unittest.IsolatedAsyncioTestCase):
    def contexts(self):
        modules = json.loads((ROOT / "content/modules.json").read_text(encoding="utf-8"))["modules"]
        for module in modules:
            if module["module_id"] not in {"m1_effect", "m1_shift"}:
                continue
            for path in module["profile_pack_paths"].values():
                pack = load_content_pack(ROOT / path)
                for activity in pack.activities:
                    if activity.experiment is not None and activity.experiment.guide is not None:
                        yield pack, activity

    async def test_all_current_guided_practices_open_with_prediction_without_a_model_call(self):
        calls = []

        def unused_model(messages, info):
            calls.append(True)
            raise AssertionError("The released opening needs no model request")

        for pack, activity in self.contexts():
            with self.subTest(pack=pack.pack_id, activity=activity.activity_id):
                with tempfile.TemporaryDirectory() as directory:
                    store = JsonlEventStore(Path(directory) / "opening.jsonl")
                    controller = DemoController(pack, store=store)
                    with override_allow_model_requests(False):
                        view = await controller.start_with_tutor(
                            model=FunctionModel(unused_model),
                            preferred_activity_ids=(activity.activity_id,), route_scope="preferred",
                        )
                    expected = activity.experiment.guide.prediction_prompt.split("?", 1)[0] + "?"
                    if activity.experiment.guide.parameter_id == "measurement_error_pct":
                        expected = ("At 10% and then 40% measurement error, how often do you expect "
                                    "the image-reading rule to agree with the reference target?")
                    self.assertEqual(view["turn"], expected)
                    self.assertEqual(view["conversation"][-1]["text"], expected)
                    self.assertIsNone(view["experiment"]["result"])
                    self.assertFalse(view["can_submit_response"])
                    self.assertEqual(view["completed_activity_ids"], ())
                    self.assertFalse(any(isinstance(event, ResponseRecorded) for event in controller.events))
                    opening = next(event for event in controller.events if isinstance(event, TeachingMoveSelected))
                    self.assertTrue(opening.payload.decision_trace_id.endswith(".authored-experiment-orientation"))
                    self.assertEqual(opening.payload.socratic_question, expected)
                    restored = DemoController(pack, store=store).view()
                    self.assertEqual(restored["conversation"], view["conversation"])
        self.assertEqual(calls, [])

    async def test_tutor_question_matches_the_prediction_then_the_recorded_interpretation_stage(self):
        for pack, activity in self.contexts():
            with self.subTest(pack=pack.pack_id, activity=activity.activity_id):
                controller = DemoController(pack)
                controller.start(preferred_activity_ids=(activity.activity_id,), route_scope="preferred")

                def deps_for(request_id):
                    state = controller.view()
                    record_support_request(controller.events, pack, attempt_id=state["attempt_id"],
                        request_id=request_id, request=SupportRequest(kind="orientation"))
                    return build_tutor_deps(controller.events, pack, request_id=request_id)

                before = deps_for("guide.open.before")
                self.assertEqual(before.current_question.text, activity.experiment.guide.prediction_prompt)
                with override_allow_model_requests(False):
                    await run_tutor_turn(controller.events, pack, request_id="guide.open.before",
                        model=FunctionModel(lambda messages, info: self.fail("Opening requested a model")))
                original_opening = controller.events[-1].model_dump_json()
                finish_current_experiment(controller)
                self.assertTrue(controller.view()["experiment"]["can_submit_check"])
                after = deps_for("guide.open.after")
                self.assertEqual(after.current_question.text, activity.workbench.prompt)
                self.assertEqual(controller.view()["workbench"]["prompt"], activity.workbench.prompt)
                self.assertIn(original_opening, [event.model_dump_json() for event in controller.events])

    def test_legacy_unguided_practice_keeps_its_released_question(self):
        pack = load_content_pack(ROOT / "content/m1_effect_course_general_1_2_0.json")
        activity = next(item for item in pack.activities if item.experiment is not None)
        self.assertIsNone(activity.experiment.guide)
        controller = DemoController(pack)
        view = controller.start(preferred_activity_ids=(activity.activity_id,), route_scope="preferred")
        record_support_request(controller.events, pack, attempt_id=view["attempt_id"],
            request_id="guide.legacy", request=SupportRequest(kind="orientation"))
        deps = build_tutor_deps(controller.events, pack, request_id="guide.legacy")
        self.assertEqual(deps.current_question.text, activity.workbench.prompt)


class ExperimentGuideContractTest(unittest.TestCase):
    def test_guide_rejects_unrelated_controls_unknown_metrics_and_report_metrics_in_prediction(self):
        for changes in (
            {"parameter_id": "target_high_pct"},
            {"parameter_id": "generator"},
            {"section": "generation"},
            {"metrics": [{"metric_label": "Invented score", "label": "Score"}]},
            {"metrics": [{"metric_label": "Full-report coverage", "label": "Reports"}]},
            {"metrics": [guide_data()["metrics"][0]] * 2},
            {"hidden_result": 90},
        ):
            with self.subTest(changes=changes), self.assertRaises(ValidationError):
                ExperimentGuide.model_validate_json(json.dumps({**guide_data(), **changes}))
        effect = effect_spec().model_dump(mode="json")
        with self.assertRaisesRegex(ValidationError, "match the experiment model"):
            ExperimentWorkbench.model_validate_json(json.dumps({**effect, "guide": guide_data()}))

    def test_effect_guide_validates_its_own_control_metrics_and_model_kind(self):
        data = {**guide_data(), "section": "intervention", "parameter_id": "assignment",
                "metrics": [{"metric_label": "Source pooled A minus B", "label": "Programme difference"}]}
        guide = ExperimentGuide.model_validate_json(json.dumps(data))
        for changes in (
            {"parameter_id": "flip_cue"},
            {"section": "prediction"},
            {"metrics": guide_data()["metrics"]},
        ):
            with self.subTest(changes=changes), self.assertRaises(ValidationError):
                ExperimentGuide.model_validate_json(json.dumps({**data, **changes}))
        with self.assertRaisesRegex(ValidationError, "match the experiment model"):
            ExperimentWorkbench.model_validate_json(json.dumps({
                **shift_spec().model_dump(mode="json"), "guide": guide.model_dump(mode="json"),
            }))
        legacy = effect_spec()
        spec = ExperimentWorkbench.model_validate_json(json.dumps({
            **legacy.model_dump(mode="json"), "guide": data,
        }))
        recorded = run_setup(spec, initial_experiment_snapshot(spec), spec.initial_config)
        original = run_setup(legacy, initial_experiment_snapshot(legacy), legacy.initial_config)
        self.assertEqual(recorded, original)
        view = experiment_view(spec, recorded, "Compare the two recorded setups")
        self.assertEqual([p["parameter_id"] for p in view["parameters"]], ["assignment"])
        self.assertEqual(view["result"]["title"], "Programme comparison result")
        self.assertEqual([m["label"] for m in view["result"]["metrics"]], ["Source pooled A minus B"])
        self.assertEqual(view["result"]["tables"][0]["columns"],
                         ["Starting group", "Programme A count", "Programme B count"])
        self.assertTrue(recorded.result.tables)

    def test_optional_guide_does_not_change_legacy_views_or_recorded_calculations(self):
        legacy = shift_spec()
        spec = ExperimentWorkbench.model_validate_json(json.dumps({
            **legacy.model_dump(mode="json"), "guide": guide_data(),
        }))
        original = run_setup(legacy, initial_experiment_snapshot(legacy), legacy.initial_config)
        guided = run_setup(spec, initial_experiment_snapshot(spec), spec.initial_config)
        self.assertEqual(original, guided)
        old_view = experiment_view(legacy, original, "Legacy instructions")
        self.assertNotIn("guide", old_view)
        self.assertEqual(old_view["result"], original.result.model_dump(mode="json"))
        view = experiment_view(spec, guided, "Guided instructions")
        self.assertEqual([p["parameter_id"] for p in view["parameters"]], ["cue_accuracy_pct"])
        self.assertEqual([m["label"] for m in view["result"]["metrics"]], ["Reference prediction accuracy"])
        self.assertEqual(view["result"]["bars"], [])
        self.assertEqual(view["result"]["tables"], [])
        self.assertNotIn("generated_text", view["result"]["cases"][0])
        self.assertNotIn("report", json.dumps(view["result"]).lower())
        # The projection cannot strip report evidence from the immutable trace.
        self.assertTrue(guided.runs[0].result.cases[0].generated_text)

    def test_repeated_runs_keep_another_setting_available_without_a_run_quota(self):
        legacy = shift_spec()
        spec = ExperimentWorkbench.model_validate_json(json.dumps({
            **legacy.model_dump(mode="json"), "guide": guide_data(),
        }))
        snapshot = run_setup(spec, initial_experiment_snapshot(spec), spec.initial_config)
        changed = spec.initial_config.model_copy(update={"cue_accuracy_pct": 50})
        for _ in range(12):
            snapshot = run_setup(spec, snapshot, changed)
        view = experiment_view(spec, snapshot, "Compare your recorded runs")
        self.assertEqual(len(snapshot.runs), 13)
        self.assertEqual(view["distinct_runs"], 2)
        self.assertEqual({run["config"]["cue_accuracy_pct"] for run in view["runs"]}, {90, 50})
        self.assertEqual(view["runs"][-1]["run_id"], 13)
        self.assertLessEqual(len(view["runs"]), 6)


class GuidedShiftContextTest(unittest.TestCase):
    def contexts(self):
        for profile in ("general", "medical"):
            pack = load_content_pack(ROOT / f"content/m1_shift_course_{profile}_1_3_0.json")
            for activity in pack.activities:
                if activity.experiment is not None:
                    yield profile, pack, activity

    def test_both_profiles_send_computed_comparison_facts_for_recorded_runs(self):
        for profile, pack, activity in self.contexts():
            if activity.activity_id != "m1-shift-investigation.01":
                continue
            with self.subTest(profile=profile):
                controller = DemoController(pack)
                controller.start(preferred_activity_ids=(activity.activity_id,), route_scope="preferred")
                captured = []

                def reply(messages, info):
                    prompt = next(part.content for message in reversed(messages) for part in message.parts
                                  if isinstance(part, UserPromptPart) and isinstance(part.content, str))
                    captured.append(json.loads(prompt)["visible_experiment"])
                    self.assertIn("Use visible_experiment.comparison_arithmetic", info.instructions)
                    self.assertIn("to_as_percent_of_from is not", info.instructions)
                    self.assertIn("not counts of people or reports", info.instructions)
                    return ModelResponse(parts=[TextPart("Use the recorded comparison and its stated units.")])

                def chat(request):
                    with override_allow_model_requests(False):
                        asyncio.run(controller.send_message_with_tutor(request_id=request,
                            text="Is the second accuracy exactly half the first?", model=FunctionModel(reply),
                            unguarded=True))
                    return captured[-1]["comparison_arithmetic"]

                def action(value, request):
                    view = controller.view()
                    return controller.submit_experiment_action(request_id=request, attempt_id=view["attempt_id"],
                        experiment_id=view["experiment"]["experiment_id"], input_revision=view["experiment"]["revision"],
                        action=value)

                self.assertIsNone(chat("arithmetic.before"))
                for index, accuracy in enumerate((90, 50)):
                    config = activity.experiment.initial_config.model_copy(update={"cue_accuracy_pct": accuracy})
                    action(CommitExperimentPrediction(config=config, prediction="I will compare the same rule."),
                           f"arithmetic.predict.{index}")
                    action(RunExperiment(), f"arithmetic.run.{index}")
                facts = chat("arithmetic.ran")
                self.assertEqual((facts["from_run_id"], facts["to_run_id"]), (1, 2))
                self.assertTrue(facts["current_configuration_has_result"])
                values = facts["metrics"][0]
                self.assertEqual((values["from_value"], values["to_value"], values["difference"]), (90, 50, -40))
                self.assertEqual(values["to_as_percent_of_from"], 55.5556)
                self.assertEqual(values["relative_change_percent"], -44.4444)
                self.assertFalse(values["is_exactly_half"])
                action(CommitExperimentPrediction(config=config.model_copy(update={"cue_accuracy_pct": 75}),
                       prediction="This setup is not run yet."), "arithmetic.unrun")
                prior = chat("arithmetic.saved-only")
                self.assertFalse(prior["current_configuration_has_result"])
                self.assertEqual(prior["metrics"], facts["metrics"])
                self.assertFalse(controller.view()["assessment_submitted"])

    def test_both_profiles_have_one_control_and_no_unrun_results_then_only_task_results(self):
        for profile, pack, activity in self.contexts():
            with self.subTest(profile=profile, activity=activity.activity_id):
                spec = activity.experiment
                before = experiment_view(spec, initial_experiment_snapshot(spec), "Read the story")
                self.assertEqual(len(before["parameters"]), 1)
                self.assertEqual(before["parameters"][0]["parameter_id"], spec.guide.parameter_id)
                self.assertIsNone(before["result"])
                self.assertEqual(before["runs"], [])
                ran = run_setup(spec, initial_experiment_snapshot(spec), spec.initial_config)
                shown = experiment_view(spec, ran, "Compare the result")
                self.assertEqual(shown["config"], spec.initial_config.model_dump(mode="json"))
                self.assertEqual([m["label"] for m in shown["result"]["metrics"]],
                                 [m.metric_label for m in spec.guide.metrics])
                self.assertFalse(shown["can_submit_check"])
                if spec.guide.section == "prediction":
                    self.assertNotIn("report", json.dumps(shown["result"]).lower())
                else:
                    self.assertTrue(any(not case["metadata_known"] for case in shown["result"]["cases"]))
                    self.assertTrue(all("generated_text" in case for case in shown["result"]["cases"]))

    def test_tutor_uses_the_same_stage_projection_and_remains_available_after_twelve_messages(self):
        for profile, pack, activity in self.contexts():
            with self.subTest(profile=profile, activity=activity.activity_id):
                controller = DemoController(pack)
                controller.start(preferred_activity_ids=(activity.activity_id,), route_scope="preferred")
                captured = []

                def reply(messages, info):
                    prompt = next(part.content for message in reversed(messages) for part in message.parts
                                  if isinstance(part, UserPromptPart) and isinstance(part.content, str))
                    captured.append(json.loads(prompt))
                    return ModelResponse(parts=[TextPart("Compare the displayed setup and result. Your prediction is unscored.")])

                with override_allow_model_requests(False):
                    for index in range(12):
                        asyncio.run(controller.send_message_with_tutor(
                            request_id=f"guide.chat.{index}",
                            text=f"Please explain the next action in this example, question {index + 1}.",
                            model=FunctionModel(reply), unguarded=True,
                        ))
                self.assertEqual(len(captured), 12)
                for context in captured:
                    visible = context["visible_experiment"]
                    self.assertEqual(visible["guide"]["section"], activity.experiment.guide.section)
                    self.assertIsNone(visible["result"])
                    self.assertIn("single control", visible["phase_guidance"])
                    self.assertEqual(len(visible["parameters"]), 1)
                    if activity.experiment.guide.section == "prediction":
                        self.assertNotIn("report_generation", visible["quantity_definitions"])
                        self.assertNotIn("generator", visible["config"])
                        self.assertNotIn("metadata_available_pct", visible["config"])
                state = controller.view()
                self.assertFalse(state["experiment"]["can_submit_check"])
                committed = controller.submit_experiment_action(
                    request_id="guide.predict", attempt_id=state["attempt_id"],
                    experiment_id=state["experiment"]["experiment_id"],
                    input_revision=state["experiment"]["revision"],
                    action=CommitExperimentPrediction(config=activity.experiment.initial_config, prediction="I expect a change."),
                )
                ran = controller.submit_experiment_action(
                    request_id="guide.run", attempt_id=state["attempt_id"],
                    experiment_id=committed["experiment"]["experiment_id"],
                    input_revision=committed["experiment"]["revision"], action=RunExperiment(),
                )
                with override_allow_model_requests(False):
                    asyncio.run(controller.send_message_with_tutor(request_id="guide.after-run",
                        text="What does this recorded result mean?", model=FunctionModel(reply), unguarded=True))
                self.assertEqual(captured[-1]["visible_experiment"]["result"], ran["experiment"]["result"])
                self.assertFalse(controller.view()["experiment"]["can_submit_check"])


class GuidedEffectContextTest(unittest.TestCase):
    def contexts(self):
        for profile in ("general", "medical"):
            pack = load_content_pack(ROOT / f"content/m1_effect_course_{profile}_1_3_0.json")
            for activity in pack.activities:
                if activity.experiment is not None:
                    yield profile, pack, activity

    def test_all_effect_guides_project_one_control_without_changing_computed_evidence(self):
        for profile, pack, activity in self.contexts():
            with self.subTest(profile=profile, activity=activity.activity_id):
                spec = activity.experiment
                self.assertEqual(spec.guide.section, "intervention")
                initial = initial_experiment_snapshot(spec)
                before = experiment_view(spec, initial, "Read the story")
                self.assertIsNone(before["result"])
                self.assertEqual([p["parameter_id"] for p in before["parameters"]], [spec.guide.parameter_id])
                ran = run_setup(spec, initial, spec.initial_config)
                legacy = spec.model_copy(update={"guide": None})
                self.assertEqual(ran, run_setup(legacy, initial_experiment_snapshot(legacy), legacy.initial_config))
                shown = experiment_view(spec, ran, "Compare the result")
                self.assertEqual(shown["config"], spec.initial_config.model_dump(mode="json"))
                self.assertEqual([m["label"] for m in shown["result"]["metrics"]],
                                 [m.metric_label for m in spec.guide.metrics])
                counts = shown["result"]["tables"][0]
                self.assertEqual(counts["rows"], [[row[0], row[1], row[4]] for row in ran.result.tables[0].rows[:-1]])
                self.assertEqual(len(counts["columns"]), 3)
                self.assertTrue(ran.result.tables)
                self.assertFalse(shown["can_submit_check"])

    def test_effect_tutor_context_remains_scoped_through_thirteen_messages(self):
        for profile, pack, activity in self.contexts():
            with self.subTest(profile=profile, activity=activity.activity_id):
                controller = DemoController(pack)
                controller.start(preferred_activity_ids=(activity.activity_id,), route_scope="preferred")
                captured = []

                def reply(messages, info):
                    prompt = next(part.content for message in reversed(messages) for part in message.parts
                                  if isinstance(part, UserPromptPart) and isinstance(part.content, str))
                    captured.append(json.loads(prompt)["visible_experiment"])
                    return ModelResponse(parts=[TextPart("Compare the two saved programme setups. Your prediction is unscored.")])

                with override_allow_model_requests(False):
                    for index in range(12):
                        asyncio.run(controller.send_message_with_tutor(
                            request_id=f"effect.guide.chat.{index}", text=f"Explain the next action, question {index + 1}.",
                            model=FunctionModel(reply), unguarded=True))
                for visible in captured:
                    self.assertIsNone(visible["result"])
                    self.assertEqual(len(visible["parameters"]), 1)
                    self.assertEqual(set(visible["config"]), {"kind", activity.experiment.guide.parameter_id})
                    self.assertNotIn("reference_accuracy", visible["quantity_definitions"])
                    self.assertNotIn("report_generation", visible["quantity_definitions"])
                    self.assertIn("single control", visible["phase_guidance"])
                state = controller.view()
                committed = controller.submit_experiment_action(
                    request_id="effect.guide.predict", attempt_id=state["attempt_id"],
                    experiment_id=state["experiment"]["experiment_id"], input_revision=state["experiment"]["revision"],
                    action=CommitExperimentPrediction(config=activity.experiment.initial_config, prediction="I expect a difference."))
                ran = controller.submit_experiment_action(
                    request_id="effect.guide.run", attempt_id=state["attempt_id"],
                    experiment_id=committed["experiment"]["experiment_id"],
                    input_revision=committed["experiment"]["revision"], action=RunExperiment())
                with override_allow_model_requests(False):
                    asyncio.run(controller.send_message_with_tutor(
                        request_id="effect.guide.after-run", text="Explain this saved result.",
                        model=FunctionModel(reply), unguarded=True))
                self.assertEqual(len(captured), 13)
                self.assertEqual(captured[-1]["result"], ran["experiment"]["result"])
                self.assertEqual(captured[-1]["runs"][-1]["tables"], ran["experiment"]["result"]["tables"])
                self.assertFalse(controller.view()["experiment"]["can_submit_check"])


if __name__ == "__main__":
    unittest.main()
