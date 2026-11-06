"""Role-stable hypothetical examples, without answer keys or grading authority."""

import json
from itertools import combinations
from pathlib import Path
import tempfile
import unittest

from pydantic import ValidationError
from pydantic_ai.messages import ModelResponse, TextPart, ToolCallPart, UserPromptPart
from pydantic_ai.models import override_allow_model_requests
from pydantic_ai.models.function import FunctionModel

from educagent_sdk import load_content_pack
from educagent_sdk.demo import DemoController, JsonlEventStore
from educagent_sdk.events import ResponseRecorded, TeachingMoveSelected, replay
from educagent_sdk.experiments import CommitExperimentPrediction, RunExperiment
from educagent_sdk.tutor_examples import (
    AdjustmentExampleReply, AdjustmentExampleRoles,
    example_roles_from_reply, render_adjustment_example,
)


ROOT = Path(__file__).resolve().parents[1]
ROLES = {
    "general": AdjustmentExampleRoles(
        treatment="watering plan", outcome="plant height after four weeks",
        common_cause="plant type", target_population="the plants in this garden",
    ),
    "medical": AdjustmentExampleRoles(
        treatment="dressing protocol", outcome="healed by day 14",
        common_cause="initial wound severity", target_population="fictional simulated wounds",
    ),
}


def prompt_context(messages):
    return json.loads(next(part.content for message in reversed(messages) for part in message.parts
        if isinstance(part, UserPromptPart) and isinstance(part.content, str)))


def final_controller(profile, *, store=None):
    pack = load_content_pack(ROOT / f"content/m1_effect_course_{profile}_1_2_0.json")
    activity = next(a for a in pack.activities if a.activity_id == "m1-effect-final.03")
    demo = DemoController(pack, profile_id=profile, store=store)
    demo.start(preferred_activity_ids=(activity.activity_id,), route_scope="preferred")
    return demo, activity


def tool_response(info, plan):
    tool = next(item for item in info.output_tools
        if "roles" in item.parameters_json_schema.get("properties", {}))
    return ModelResponse(parts=[ToolCallPart(tool.name, plan.model_dump(mode="json"))])


def raw_tutor_reply(demo):
    """Role anchors belong to persisted replies, not their learner-facing projection."""

    return next(event.payload.tutor_reply or "" for event in reversed(demo.events)
        if isinstance(event, TeachingMoveSelected))


class AdjustmentExampleContractTest(unittest.TestCase):
    def test_causal_roles_are_pairwise_distinct_after_label_normalization(self):
        base = ROLES["general"].model_dump()
        for first, second in combinations(("treatment", "outcome", "common_cause"), 2):
            for equivalent in ("plant type", "PLANT TYPE", "  Plant   Type  ", "plant-type", "plant type!"):
                with self.subTest(first=first, second=second, equivalent=equivalent):
                    invalid = {**base, first: "plant type", second: equivalent}
                    with self.assertRaises(ValidationError):
                        AdjustmentExampleRoles.model_validate(invalid)

    def test_all_role_labels_accept_the_length_boundary_but_not_an_overflow(self):
        values = {
            "treatment": "t" * 75, "outcome": "o" * 75,
            "common_cause": "c" * 75, "target_population": "p" * 75,
        }
        self.assertEqual(AdjustmentExampleRoles.model_validate(values).model_dump(), values)
        for field in values:
            with self.subTest(field=field), self.assertRaises(ValidationError):
                AdjustmentExampleRoles.model_validate({**values, field: values[field] + "x"})

    def test_all_maximum_labels_prefixes_and_extra_variables_render_within_existing_bound(self):
        for alphabet in (("t", "o", "c", "p", "e"), ("治", "果", "因", "群", "土")):
            roles = AdjustmentExampleRoles(**dict(zip(
                ("treatment", "outcome", "common_cause", "target_population"),
                (letter * 75 for letter in alphabet[:4]), strict=True,
            )))
            for focus in AdjustmentExampleReply.model_fields["focus"].annotation.__args__:
                for switch in (False, True):
                    for extra in (None, alphabet[4] * 75, roles.common_cause):
                        with self.subTest(alphabet=alphabet[0], focus=focus, switch=switch, extra=extra):
                            text = render_adjustment_example(AdjustmentExampleReply(
                                roles=roles, focus=focus, extra_variable=extra,
                                introduce_new_example=switch,
                            ))
                            self.assertLessEqual(len(text), 1200)
                            self.assertEqual(example_roles_from_reply(text), roles)
                            for label in roles.model_dump().values():
                                self.assertIn(label, text)
                            if switch:
                                self.assertIn("Switching explicitly to a new hypothetical example", text)

    def test_compact_aliases_preserve_the_full_role_mapping_and_scientific_premises(self):
        roles = AdjustmentExampleRoles(treatment="t" * 75, outcome="o" * 75,
            common_cause="c" * 75, target_population="p" * 75)
        text = render_adjustment_example(AdjustmentExampleReply(
            roles=roles, focus="compare", introduce_new_example=True,
        ))
        self.assertEqual(example_roles_from_reply(text), roles)
        body = text.split("\n", 1)[1]
        self.assertIn("Using these roles", body)
        self.assertIn("hypothetical", body)
        self.assertIn("measured before treatment", body)
        self.assertIn("affects both the treatment and the outcome", body)
        self.assertIn("within each starting-condition group", body)
        self.assertIn("the same starting-condition distribution", body)
        self.assertIn("the target population", body)

    def test_clarifying_the_existing_common_cause_does_not_claim_it_is_a_different_variable(self):
        roles = ROLES["general"]
        for label in ("plant type", "PLANT TYPE", "  plant-type!  "):
            with self.subTest(label=label):
                text = render_adjustment_example(AdjustmentExampleReply(
                    roles=roles, focus="clarify", extra_variable=label,
                ))
                self.assertIn("existing starting condition, plant type, not a different variable", text)
                self.assertNotIn("is not automatically the same variable", text)
                self.assertIn("hypothetical assumption", text)
                self.assertIn("does not by itself establish adequate confounding control", text)
                self.assertIn("within each plant type group", text)

    def test_schema_cannot_accept_independent_grouping_or_free_prose(self):
        roles = ROLES["general"]
        for extra in ({"adjust_for": "soil type"}, {"prose": "Group by soil type."}):
            with self.subTest(extra=extra), self.assertRaises(ValidationError):
                AdjustmentExampleReply.model_validate({"roles": roles.model_dump(), "focus": "compare", **extra})
        with self.assertRaises(ValidationError):
            AdjustmentExampleRoles.model_validate({**roles.model_dump(), "adjust_for": "soil type"})
        for invalid in ("", "plant type; soil type", "plant type\nsoil type", "x" * 76):
            with self.subTest(label=invalid), self.assertRaises(ValidationError):
                AdjustmentExampleRoles.model_validate({**roles.model_dump(), "common_cause": invalid})
        with self.assertRaises(ValidationError):
            AdjustmentExampleReply(roles=roles, focus="select_answer")

    def test_every_rendered_focus_recovers_the_same_roles_in_both_profiles(self):
        for profile, roles in ROLES.items():
            for focus in ("roles", "compare", "simple", "timing", "standardize", "assumptions", "clarify", "correction", "question"):
                with self.subTest(profile=profile, focus=focus):
                    text = render_adjustment_example(AdjustmentExampleReply(roles=roles, focus=focus))
                    self.assertEqual(example_roles_from_reply(text), roles)
                    self.assertLessEqual(len(text), 1200)
                    self.assertNotIn("soil type", text)
                    body = text.split("\n", 1)[1]
                    self.assertIn(roles.common_cause, body)
                    if focus in {"roles", "compare", "clarify", "correction"}:
                        self.assertIn(f"{roles.common_cause} group", body)
                    if focus in {"compare", "standardize", "correction"}:
                        self.assertIn(f"{roles.common_cause} distribution", body)
                    if focus == "standardize":
                        self.assertIn("different starting-group mixtures", body)
                        self.assertIn("treatment differences", body)
                    if focus == "assumptions":
                        self.assertIn("hypothetical", body)
                        self.assertIn("removes confounding", body)
                        self.assertIn("both strategies are possible", body)
                        self.assertIn("consistent meanings", body)
                    if focus == "timing":
                        self.assertIn(f"{roles.common_cause} is a starting condition", body)
                        self.assertIn(f"not a consequence of {roles.treatment}", body)
                        self.assertIn(f"{roles.outcome} is the outcome", body)
                        self.assertIn("not a replacement adjustment variable", body)
                        self.assertIn("does not by itself make an adjustment set sufficient", body)
                        self.assertNotIn("that was inconsistent", body)
                    if focus == "simple":
                        self.assertIn(f"one {roles.common_cause} group at a time", body)
                        self.assertIn(roles.treatment, body)
                        self.assertIn(roles.outcome, body)
                        self.assertIn(roles.target_population, body)
                        self.assertNotIn("that was inconsistent", body)
                    if focus == "question":
                        self.assertEqual(body.count("?"), 1)
                        self.assertTrue(body.endswith("?"))
                        for label in (roles.treatment, roles.outcome, roles.common_cause):
                            self.assertIn(label, body)
                        self.assertNotIn("that was inconsistent", body)

    def test_clarification_names_a_new_variable_without_reassigning_its_role(self):
        roles = ROLES["general"]
        text = render_adjustment_example(AdjustmentExampleReply(
            roles=roles, focus="clarify", extra_variable="soil type"))
        self.assertEqual(example_roles_from_reply(text), roles)
        self.assertIn("soil type is not automatically the same variable as plant type", text)
        self.assertIn("within each plant type group", text)
        self.assertIsNone(example_roles_from_reply("Plant type was mentioned; perhaps group by soil type."))
        self.assertIsNone(example_roles_from_reply("Example roles: treatment = watering plan\nIncomplete roles."))


class TutorExampleConsistencyTest(unittest.IsolatedAsyncioTestCase):
    def assert_safe_final_context(self, context, demo, activity, *, roles=None):
        self.assertEqual(context["assessment_help"]["phase"], "final_before_answer")
        for key in ("visible_scene", "visible_workbench", "visible_lesson", "visible_experiment"):
            self.assertIsNone(context[key])
        serialized = json.dumps(context)
        for choice in activity.choices:
            self.assertNotIn(choice.text, serialized)
        resources = {r.resource_id: r.text for r in demo.pack.resources}
        self.assertNotIn(resources[activity.explanation_resource_id], serialized)
        self.assertNotIn(resources[activity.question_resource_id], serialized)
        self.assertNotIn(activity.workbench.prompt, serialized)
        for key in ('"choices"', '"correct"', '"protected_answer_texts"'):
            self.assertNotIn(key, serialized)
        if roles is not None:
            self.assertEqual(context["active_adjustment_example"], roles.model_dump(mode="json"))
            self.assert_example_scope(context)
        else:
            self.assertNotIn("example_evidence_scope", context)

    def assert_example_scope(self, context):
        scope = context["example_evidence_scope"]
        self.assertIn("Hypothetical analogy only", scope)
        self.assertIn("a separate setting", scope)
        self.assertIn("not measurements or results for these example roles", scope)
        self.assertNotRegex(scope, r"\d")
        for private in ("a_low", "a_high", "b_low", "b_high", "correct", "protected_answer_texts"):
            self.assertNotIn(private, scope)

    async def test_visible_programme_results_remain_separate_from_both_profile_analogies(self):
        for profile, roles in ROLES.items():
            with self.subTest(profile=profile):
                pack = load_content_pack(ROOT / f"content/m1_effect_course_{profile}_1_2_0.json")
                activity = next(a for a in pack.activities if a.activity_id == "m1-effect-investigation.01")
                demo = DemoController(pack, profile_id=profile)
                view = demo.start(preferred_activity_ids=(activity.activity_id,), route_scope="preferred")
                view = demo.submit_experiment_action(
                    request_id="scope.predict", attempt_id=view["attempt_id"],
                    experiment_id=view["experiment"]["experiment_id"], input_revision=view["experiment"]["revision"],
                    action=CommitExperimentPrediction(config=activity.experiment.initial_config,
                        prediction="I will compare the computed programme rates."))
                ran = demo.submit_experiment_action(
                    request_id="scope.run", attempt_id=view["attempt_id"],
                    experiment_id=view["experiment"]["experiment_id"], input_revision=view["experiment"]["revision"],
                    action=RunExperiment())
                contexts = []

                async def reply(messages, info):
                    context = prompt_context(messages)
                    self.assertIn("Do not import the visible lesson/experiment", info.instructions)
                    self.assertIn("the page's data are not example data", info.instructions)
                    self.assertEqual(context["visible_experiment"]["result"], ran["experiment"]["result"])
                    serialized = json.dumps(context)
                    for private in ('"a_low"', '"a_high"', '"b_low"', '"b_high"', '"choices"', '"correct"'):
                        self.assertNotIn(private, serialized)
                    if contexts:
                        self.assertEqual(context["active_adjustment_example"], roles.model_dump(mode="json"))
                        self.assert_example_scope(context)
                    else:
                        self.assertNotIn("example_evidence_scope", context)
                    contexts.append(context)
                    return tool_response(info, AdjustmentExampleReply(roles=roles, focus="compare"))

                with override_allow_model_requests(False):
                    await demo.send_message_with_tutor(request_id="scope.example", text="Please explain adjustment using a different hypothetical example.",
                        model=FunctionModel(reply), unguarded=True)
                    view = await demo.send_message_with_tutor(request_id="scope.reasoning", text="I am explaining our hypothetical example, not the programme experiment. Are the variables and comparisons consistent?",
                        model=FunctionModel(reply), unguarded=True)
                self.assertEqual(len(contexts), 2)
                self.assertEqual(example_roles_from_reply(raw_tutor_reply(demo)), roles)
                self.assertNotIn("-6", view["turn"])
                self.assertNotIn("+15", view["turn"])
                self.assertFalse(view["assessment_submitted"])
                self.assertFalse(view["can_continue"])

    async def test_nine_followups_explain_and_replay_keep_both_profiles_unlimited_and_unscored(self):
        for profile, roles in ROLES.items():
            with self.subTest(profile=profile), tempfile.TemporaryDirectory() as directory:
                store = JsonlEventStore(Path(directory) / "examples.jsonl")
                demo, activity = final_controller(profile, store=store)
                contexts = []
                ordinary_help = "A baseline variable is recorded before the action. We can clarify one idea at a time."

                async def reply(messages, info):
                    context = prompt_context(messages)
                    self.assert_safe_final_context(context, demo, activity,
                        roles=roles if contexts else None)
                    contexts.append(context)
                    if "support_request" not in context:
                        return ModelResponse(parts=[TextPart(ordinary_help)])
                    return tool_response(info, AdjustmentExampleReply(roles=roles, focus="compare"))

                with override_allow_model_requests(False):
                    view = await demo.request_explanation_with_tutor(
                        request_id="example.initial", model=FunctionModel(reply))
                    for index in range(9):
                        view = await demo.send_message_with_tutor(
                            request_id=f"example.followup.{index}", text=f"Please explain step {index + 1} more simply, using the same example.",
                            model=FunctionModel(reply), unguarded=True)
                        self.assertEqual(view["turn"], ordinary_help)
                        self.assertTrue(view["can_send_message"])
                        self.assertIsNone(view["pending_tutor_message"])
                    view = await demo.request_explanation_with_tutor(
                        request_id="example.explain.again", model=FunctionModel(reply))
                    self.assertEqual(example_roles_from_reply(raw_tutor_reply(demo)), roles)
                    # The initial header has left recent chat, but its role anchor
                    # still comes from the full safe, same-attempt trace.
                    self.assertFalse(any(example_roles_from_reply(item["text"])
                        for item in contexts[-1]["recent_conversation"]))
                    event_count = len(demo.events)
                    await demo.request_explanation_with_tutor(
                        request_id="example.explain.again", model=FunctionModel(reply))
                    self.assertEqual(len(demo.events), event_count)
                self.assertEqual(len(contexts), 11)
                self.assertEqual(view["learner_message_count"], 9)
                self.assertFalse(view["assessment_submitted"])
                self.assertFalse(view["can_continue"])
                self.assertFalse(any(isinstance(event, ResponseRecorded) for event in demo.events))
                self.assertFalse(replay(demo.events).completed_activity_ids)
                restored = DemoController(demo.pack, profile_id=profile, store=store)
                self.assertEqual(restored.view(), view)
                with override_allow_model_requests(False):
                    recovered = await restored.request_explanation_with_tutor(
                        request_id="example.after-replay", model=FunctionModel(reply))
                self.assertEqual(example_roles_from_reply(raw_tutor_reply(restored)), roles)
                rejected = restored.respond(request_id="example.wrong", option_id=next(
                    choice.option_id for choice in activity.choices if not choice.correct))
                self.assertFalse(rejected["assessment_accepted"])
                self.assertFalse(rejected["can_continue"])

    async def test_role_drift_retries_but_an_explicit_new_example_is_allowed(self):
        demo, activity = final_controller("general")
        roles = ROLES["general"]
        changed = roles.model_copy(update={"common_cause": "soil type"})

        async def initial(_messages, info):
            return tool_response(info, AdjustmentExampleReply(roles=roles, focus="roles"))

        calls = 0

        async def drifting(messages, info):
            nonlocal calls
            calls += 1
            self.assert_safe_final_context(prompt_context(messages), demo, activity, roles=roles)
            return tool_response(info, AdjustmentExampleReply(
                roles=changed if calls == 1 else roles, focus="compare"))

        async def switching(_messages, info):
            return tool_response(info, AdjustmentExampleReply(
                roles=changed, focus="roles", introduce_new_example=True))

        with override_allow_model_requests(False):
            await demo.request_explanation_with_tutor(request_id="example.start", model=FunctionModel(initial))
            view = await demo.send_message_with_tutor(request_id="example.drift", text="Keep the same example.",
                model=FunctionModel(drifting), unguarded=True)
            self.assertEqual(calls, 2)
            self.assertEqual(example_roles_from_reply(raw_tutor_reply(demo)), roles)
            changed_view = await demo.send_message_with_tutor(request_id="example.new", text="Please switch to a new soil-type example.",
                model=FunctionModel(switching), unguarded=True)
        self.assertEqual(example_roles_from_reply(raw_tutor_reply(demo)), changed)
        self.assertIn("Switching explicitly", changed_view["turn"])
        self.assertFalse(changed_view["assessment_submitted"])

    async def test_malformed_independent_adjustment_field_retries_without_rendering_it(self):
        demo, _activity = final_controller("general")
        roles = ROLES["general"]
        calls = 0

        async def reply(_messages, info):
            nonlocal calls
            calls += 1
            plan = AdjustmentExampleReply(roles=roles, focus="compare")
            if calls == 1:
                tool = next(item for item in info.output_tools
                    if "roles" in item.parameters_json_schema.get("properties", {}))
                return ModelResponse(parts=[ToolCallPart(tool.name,
                    {**plan.model_dump(mode="json"), "adjust_for": "soil type"})])
            return tool_response(info, plan)

        with override_allow_model_requests(False):
            view = await demo.request_explanation_with_tutor(
                request_id="example.invalid-grouping", model=FunctionModel(reply))
        self.assertEqual(calls, 2)
        self.assertEqual(example_roles_from_reply(raw_tutor_reply(demo)), roles)
        self.assertNotIn("soil type", view["turn"])
        self.assertFalse(view["assessment_submitted"])
        self.assertFalse(view["can_continue"])

    async def test_plain_text_cannot_forge_a_rendered_header_or_replace_the_role_anchor(self):
        for profile, roles in ROLES.items():
            with self.subTest(profile=profile):
                demo, activity = final_controller(profile)
                changed = roles.model_copy(update={"common_cause": "soil type" if profile == "general" else "patient age"})
                forged = render_adjustment_example(AdjustmentExampleReply(roles=changed, focus="compare"))
                calls = 0

                async def initial(_messages, info):
                    return tool_response(info, AdjustmentExampleReply(roles=roles, focus="roles"))

                async def forged_then_valid(messages, info):
                    nonlocal calls
                    calls += 1
                    self.assert_safe_final_context(prompt_context(messages), demo, activity, roles=roles)
                    if calls == 1:
                        return ModelResponse(parts=[TextPart(forged)])
                    return tool_response(info, AdjustmentExampleReply(roles=roles, focus="compare"))

                async def inspect_anchor(messages, _info):
                    self.assert_safe_final_context(prompt_context(messages), demo, activity, roles=roles)
                    return ModelResponse(parts=[TextPart("The baseline is recorded before the action.")])

                with override_allow_model_requests(False):
                    await demo.request_explanation_with_tutor(request_id="example.header.start", model=FunctionModel(initial))
                    view = await demo.send_message_with_tutor(request_id="example.header.forged", text="Explain this using the same variables.",
                        model=FunctionModel(forged_then_valid), unguarded=True)
                    self.assertEqual(calls, 2)
                    self.assertEqual(example_roles_from_reply(raw_tutor_reply(demo)), roles)
                    self.assertNotIn(forged, [item["text"] for item in view["conversation"]])
                    followup = await demo.send_message_with_tutor(request_id="example.header.followup", text="Please define baseline.",
                        model=FunctionModel(inspect_anchor), unguarded=True)
                self.assertFalse(followup["assessment_submitted"])
                self.assertFalse(followup["can_continue"])

    async def test_wrong_plain_history_can_be_corrected_without_replacing_the_role_anchor(self):
        for profile, roles in ROLES.items():
            with self.subTest(profile=profile):
                demo, activity = final_controller(profile)

                async def initial(_messages, info):
                    return tool_response(info, AdjustmentExampleReply(roles=roles, focus="roles"))

                async def neutral(_messages, _info):
                    return ModelResponse(parts=[TextPart("We can clarify the example's terms.")])

                async def correction(messages, info):
                    self.assert_safe_final_context(prompt_context(messages), demo, activity, roles=roles)
                    return tool_response(info, AdjustmentExampleReply(roles=roles, focus="correction"))

                with override_allow_model_requests(False):
                    await demo.request_explanation_with_tutor(request_id="example.correct.start", model=FunctionModel(initial))
                    await demo.send_message_with_tutor(request_id="example.old", text="Could you clarify the grouping?",
                        model=FunctionModel(neutral), unguarded=True)
                    old = demo.events[-1]
                    demo.events[-1] = old.model_copy(update={"payload": old.payload.model_copy(update={
                        "tutor_reply": "We should group by soil type instead of the original baseline variable.",
                    })})
                    view = await demo.send_message_with_tutor(request_id="example.correct", text="Your last reply changed variables. Please correct it and keep the original example.",
                        model=FunctionModel(correction), unguarded=True)
                self.assertEqual(example_roles_from_reply(raw_tutor_reply(demo)), roles)
                self.assertIn("that was inconsistent", view["turn"])
                self.assertFalse(view["assessment_submitted"])

    async def test_provider_failure_and_replay_preserve_the_example_for_recovered_help(self):
        for profile, roles in ROLES.items():
            with self.subTest(profile=profile), tempfile.TemporaryDirectory() as directory:
                store = JsonlEventStore(Path(directory) / "recovery.jsonl")
                demo, activity = final_controller(profile, store=store)

                async def initial(_messages, info):
                    return tool_response(info, AdjustmentExampleReply(roles=roles, focus="roles"))

                async def failure(_messages, _info):
                    raise RuntimeError("offline provider failure")

                async def recovery(messages, info):
                    self.assert_safe_final_context(prompt_context(messages), demo, activity, roles=roles)
                    return tool_response(info, AdjustmentExampleReply(roles=roles, focus="standardize"))

                with override_allow_model_requests(False):
                    await demo.request_explanation_with_tutor(request_id="example.saved", model=FunctionModel(initial))
                    failed = await demo.request_explanation_with_tutor(request_id="example.failed", model=FunctionModel(failure))
                    self.assertEqual(demo.events[-1].payload.selector_kind, "provider_failure")
                    self.assertTrue(failed["can_send_message"])
                    restored = DemoController(demo.pack, profile_id=profile, store=store)
                    self.assertEqual(restored.view(), failed)
                    recovered = await restored.request_explanation_with_tutor(
                        request_id="example.recovered", model=FunctionModel(recovery))
                self.assertEqual(example_roles_from_reply(raw_tutor_reply(restored)), roles)
                self.assertIsNone(recovered["pending_tutor_message"])
                self.assertFalse(recovered["assessment_submitted"])
                self.assertFalse(recovered["can_continue"])


if __name__ == "__main__":
    unittest.main()
