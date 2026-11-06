"""Final opening and explanation help never receive or render an answer key."""

import asyncio
import json
from pathlib import Path
import tempfile
import unittest

from pydantic_ai import UnexpectedModelBehavior
from pydantic_ai.messages import ModelResponse, TextPart, ToolCallPart, UserPromptPart
from pydantic_ai.models import override_allow_model_requests
from pydantic_ai.models.function import FunctionModel

from educagent_sdk import load_content_pack
from educagent_sdk.demo import DemoController, JsonlEventStore
from educagent_sdk.events import (
    LearnerMessageRecorded, ResponseRecorded, SupportRequest, SupportRequested,
    TeachingMoveSelected, append_teaching_move, pending_turn, record_support_request,
    replay,
)
from educagent_sdk.tutor import DEMO_CHAT_POLICY_VERSION, run_tutor_turn


ROOT = Path(__file__).resolve().parents[1]


def released_packs():
    modules = json.loads((ROOT / "content/modules.json").read_text(encoding="utf-8"))["modules"]
    return [load_content_pack(ROOT / path) for module in modules
        for path in module["profile_pack_paths"].values()]


def final_controller(*, store=None):
    pack = load_content_pack(ROOT / "content/m1_effect_course_general_1_2_0.json")
    activity = next(item for item in pack.activities if item.activity_id == "m1-effect-final.03")
    demo = DemoController(pack, store=store)
    demo.start(preferred_activity_ids=(activity.activity_id,), route_scope="preferred")
    return demo, activity


def prompt_context(messages):
    return json.loads(next(part.content for message in reversed(messages) for part in message.parts
        if isinstance(part, UserPromptPart) and isinstance(part.content, str)))


class FinalSupportHelpTest(unittest.IsolatedAsyncioTestCase):
    async def test_all_six_profiles_get_safe_opening_and_repeatable_explanations(self):
        for pack in released_packs():
            activity = next(item for item in pack.activities
                if item.workbench is not None and item.workbench.stage == "capstone")
            with self.subTest(pack=pack.pack_id):
                demo = DemoController(pack)
                captured = []
                correct = next(choice.text for choice in activity.choices if choice.correct)
                explanation = next(item.text for item in pack.resources
                    if item.resource_id == activity.explanation_resource_id)

                async def reply(messages, info):
                    context = prompt_context(messages)
                    captured.append(context)
                    self.assertTrue(info.output_tools)
                    self.assertIn("different example", info.instructions)
                    self.assertIn("neutral", info.instructions)
                    self.assertEqual(context["assessment_help"]["phase"], "final_before_answer")
                    self.assertEqual(context["profile_id"], pack.lessons[0].profile_id)
                    self.assertNotIn("learner_message", context)
                    for field in ("visible_workbench", "visible_lesson", "visible_experiment", "visible_scene"):
                        self.assertIsNone(context[field])
                    serialized = json.dumps(context)
                    self.assertNotIn(correct, serialized)
                    self.assertNotIn(explanation, serialized)
                    self.assertNotIn(activity.workbench.prompt, serialized)
                    self.assertNotIn("protected_answer_texts", serialized)
                    self.assertNotIn('"choices"', serialized)
                    text = ("Read the case and make your own judgment; you can ask for concept help."
                        if context["support_request"]["kind"] == "orientation" else
                        f"Here is the underlying idea: {context.get('concept_definition', 'Compare concepts using a different example.')}")
                    return ModelResponse(parts=[TextPart(text)])

                with override_allow_model_requests(False):
                    view = await demo.start_with_tutor(model=FunctionModel(reply),
                        preferred_activity_ids=(activity.activity_id,), route_scope="preferred")
                    for index in range(3):
                        view = await demo.request_explanation_with_tutor(
                            request_id=f"final.support.{index}", model=FunctionModel(reply))
                        tutor_texts = [item["text"] for item in view["conversation"] if item["role"] == "tutor"]
                        self.assertNotIn(explanation, tutor_texts)
                        self.assertNotEqual(view["turn"], explanation)
                        self.assertEqual(view["turn"], tutor_texts[-1])
                        self.assertFalse(view["assessment_submitted"])
                        self.assertFalse(view["can_continue"])
                        self.assertEqual(view["learner_message_count"], 0)
                    count = len(demo.events)
                    await demo.request_explanation_with_tutor(request_id="final.support.2", model=FunctionModel(reply))
                    self.assertEqual(len(demo.events), count)
                self.assertEqual(len(captured), 4)
                self.assertEqual(sum(isinstance(item, SupportRequested) for item in demo.events), 4)
                self.assertFalse(any(isinstance(item, (LearnerMessageRecorded, ResponseRecorded)) for item in demo.events))
                self.assertEqual(replay(demo.events).response_ordinal, 0)
                self.assertTrue(demo.events[-1].payload.decision_trace_id.endswith(f".guided-chat.{DEMO_CHAT_POLICY_VERSION}"))

    async def test_final03_explanation_is_persisted_not_accepted_resource_and_survives_replay(self):
        with tempfile.TemporaryDirectory() as directory:
            store = JsonlEventStore(Path(directory) / "final.jsonl")
            demo, activity = final_controller(store=store)
            safe_reply = (
                "Adjustment compares cases with similar recorded starting conditions. "
                "For example, compare plant growth under two watering plans within each soil type, "
                "rather than mixing different soils without checking them."
            )
            accepted = next(item.text for item in demo.pack.resources
                if item.resource_id == activity.explanation_resource_id)

            async def reply(messages, _info):
                self.assertNotIn(accepted, json.dumps(prompt_context(messages)))
                return ModelResponse(parts=[TextPart(safe_reply)])

            with override_allow_model_requests(False):
                view = await demo.request_explanation_with_tutor(request_id="final03.explain", model=FunctionModel(reply))
            self.assertEqual(view["turn"], safe_reply)
            self.assertEqual(view["conversation"][-1]["text"], safe_reply)
            self.assertNotIn(accepted, [item["text"] for item in view["conversation"]])
            restored = DemoController(demo.pack, store=store).view()
            self.assertEqual(restored["turn"], safe_reply)
            self.assertEqual(restored["conversation"], view["conversation"])

    async def test_old_support_explanation_is_not_sent_to_new_help(self):
        demo, activity = final_controller()
        state = replay(demo.events)
        record_support_request(demo.events, demo.pack, attempt_id=state.open_attempt_id,
            request_id="old.explanation", request=SupportRequest(kind="explanation"))
        pending = pending_turn(demo.events, demo.pack, request_id="old.explanation")
        append_teaching_move(demo.events, demo.pack, request_id="old.explanation",
            candidate=pending.candidates[0], selector_kind="tutor", decision_trace_id="old.policy")
        accepted = next(item.text for item in demo.pack.resources
            if item.resource_id == activity.explanation_resource_id)
        self.assertEqual(demo.view()["turn"], accepted)

        async def reply(messages, _info):
            self.assertNotIn(accepted, json.dumps(prompt_context(messages)))
            return ModelResponse(parts=[TextPart("We can explain the concept using a different example.")])

        with override_allow_model_requests(False):
            view = await demo.request_explanation_with_tutor(request_id="new.explanation", model=FunctionModel(reply))
        self.assertNotEqual(view["turn"], accepted)
        self.assertEqual(replay(demo.events).response_ordinal, 0)

    async def test_repeated_answer_copy_returns_concept_help_not_a_quota_or_hold(self):
        demo, activity = final_controller()
        answer = next(choice.text for choice in activity.choices if choice.correct)
        calls = 0

        async def reply(_messages, _info):
            nonlocal calls
            calls += 1
            return ModelResponse(parts=[TextPart(answer)])

        with override_allow_model_requests(False):
            view = await demo.request_explanation_with_tutor(request_id="final.copy", model=FunctionModel(reply))
        self.assertEqual(calls, 2)
        self.assertNotEqual(view["turn"], answer)
        self.assertIn("underlying idea", view["turn"])
        self.assertNotEqual(demo.events[-1].payload.move.strategy, "hold")
        self.assertFalse(view["assessment_submitted"])

    async def test_failed_safe_support_holds_replays_and_recovers_without_an_answer_reveal(self):
        for kind in ("orientation", "explanation"):
            for failure in ("provider_failure", "invalid_output", "timeout"):
                with self.subTest(kind=kind, failure=failure), tempfile.TemporaryDirectory() as directory:
                    store = JsonlEventStore(Path(directory) / "failed-support.jsonl")
                    demo, activity = final_controller(store=store)
                    accepted = next(item.text for item in demo.pack.resources
                        if item.resource_id == activity.explanation_resource_id)
                    state = replay(demo.events)
                    demo._mutate(lambda: record_support_request(demo.events, demo.pack,
                        attempt_id=state.open_attempt_id, request_id="support.failed",
                        request=SupportRequest(kind=kind)))
                    captured = []

                    async def failing_model(messages, _info):
                        captured.append(prompt_context(messages))
                        if failure == "provider_failure":
                            raise RuntimeError("provider unavailable")
                        if failure == "invalid_output":
                            raise UnexpectedModelBehavior("invalid provider output")
                        await asyncio.sleep(1)
                        return ModelResponse(parts=[TextPart("This response should time out.")])

                    start = len(demo.events)
                    with override_allow_model_requests(False):
                        result = await run_tutor_turn(demo.events, demo.pack, request_id="support.failed",
                            model=FunctionModel(failing_model), timeout_seconds=0.03 if failure == "timeout" else 1)
                    store.append(demo.events[start:])
                    self.assertEqual(result.event.payload.selector_kind, failure)
                    self.assertEqual(result.event.payload.move.strategy, "hold")
                    self.assertTrue(result.used_fallback)
                    # A deadline may expire during agent preparation, before any model request.
                    if failure != "timeout":
                        self.assertTrue(captured)
                    self.assertNotIn(accepted, json.dumps(captured))
                    failed = demo.view()
                    self.assertNotEqual(failed["turn"], accepted)
                    self.assertNotIn(accepted, [item["text"] for item in failed["conversation"]])
                    self.assertFalse(failed["assessment_submitted"])
                    self.assertFalse(failed["can_continue"])
                    self.assertTrue(failed["can_send_message"])
                    restored = DemoController(demo.pack, store=store)
                    self.assertEqual(restored.view(), failed)
                    count = len(restored.events)

                    async def forbidden_model(_messages, _info):
                        raise AssertionError("An idempotent retry must not invoke a provider.")

                    with override_allow_model_requests(False):
                        repeated = await run_tutor_turn(restored.events, restored.pack,
                            request_id="support.failed", model=FunctionModel(forbidden_model))
                    self.assertEqual(repeated.event, result.event)
                    self.assertEqual(len(restored.events), count)

                    async def recovered_model(messages, _info):
                        context = prompt_context(messages)
                        self.assertEqual(context["assessment_help"]["phase"], "final_before_answer")
                        return ModelResponse(parts=[TextPart("We can explain the concept with a different example, without deciding this item.")])

                    with override_allow_model_requests(False):
                        for index in range(3):
                            recovered = await restored.request_explanation_with_tutor(
                                request_id=f"support.recovered.{index}", model=FunctionModel(recovered_model))
                            self.assertIsNone(recovered["pending_tutor_message"])
                            self.assertNotEqual(restored.events[-1].payload.move.strategy, "hold")
                    self.assertFalse(recovered["assessment_submitted"])
                    self.assertEqual(recovered["learner_message_count"], 0)
                    self.assertNotIn(accepted, [item["text"] for item in recovered["conversation"]])
                    self.assertEqual(DemoController(restored.pack, store=store).view(), recovered)

    async def test_support_after_first_scored_response_keeps_normal_feedback_and_continue_rules(self):
        for accepted in (False, True):
            with self.subTest(accepted=accepted):
                demo, activity = final_controller()
                scored = demo.respond(request_id="final.first-score", option_id=next(
                    choice.option_id for choice in activity.choices if choice.correct == accepted))
                explanation = next(item.text for item in demo.pack.resources
                    if item.resource_id == activity.explanation_resource_id)
                captured = []

                async def structured_model(messages, info):
                    prompt = next(part.content for message in reversed(messages) for part in message.parts
                        if isinstance(part, UserPromptPart) and isinstance(part.content, str))
                    context = json.loads(prompt.split("<context>\n", 1)[1].split("\n</context>", 1)[0])
                    captured.append(context)
                    return ModelResponse(parts=[ToolCallPart(info.output_tools[0].name, {
                        "candidate_id": context["candidates"][0]["candidate_id"],
                    })])

                with override_allow_model_requests(False):
                    explained = await demo.request_explanation_with_tutor(
                        request_id="final.after-score", model=FunctionModel(structured_model))
                self.assertEqual(len(captured), 1)
                self.assertEqual(captured[0]["state"]["response_ordinal"], 1)
                self.assertEqual(explained["turn"], explanation)
                self.assertIsNone(demo.events[-1].payload.tutor_reply)
                self.assertEqual(explained["assessment_accepted"], accepted)
                self.assertEqual(explained["can_continue"], scored["can_continue"])
                self.assertTrue(explained["assessment_submitted"])
                if not accepted:
                    with self.assertRaisesRegex(ValueError, "cannot advance"):
                        demo.continue_activity(request_id="final.too-early")
                    revised = demo.respond(request_id="final.revised-score", option_id=next(
                        choice.option_id for choice in activity.choices if choice.correct))
                    self.assertTrue(revised["can_continue"])
                self.assertEqual(demo.continue_activity(request_id="final.complete")["status"], "completed")

    def test_other_inputs_reject_support_replies_at_append_and_replay(self):
        for scenario in ("ordinary", "clarification", "after_rejected", "after_accepted"):
            with self.subTest(scenario=scenario):
                demo, activity = final_controller()
                if scenario == "ordinary":
                    activity = activity.model_copy(update={"workbench": activity.workbench.model_copy(update={"stage": "investigate"})})
                    pack = demo.pack.model_copy(update={"activities": tuple(activity if item.activity_id == activity.activity_id else item for item in demo.pack.activities)})
                    demo = DemoController(pack)
                    demo.start(preferred_activity_ids=(activity.activity_id,), route_scope="preferred")
                if scenario.startswith("after_"):
                    demo.respond(request_id="support.scored", option_id=next(choice.option_id for choice in activity.choices
                        if choice.correct == (scenario == "after_accepted")))
                state = replay(demo.events)
                record_support_request(demo.events, demo.pack, attempt_id=state.open_attempt_id,
                    request_id="support.invalid", request=SupportRequest(kind="clarification" if scenario == "clarification" else "explanation"))
                pending = pending_turn(demo.events, demo.pack, request_id="support.invalid")
                with self.assertRaisesRegex(ValueError, "only a learner message"):
                    append_teaching_move(demo.events, demo.pack, request_id="support.invalid",
                        candidate=pending.candidates[0], selector_kind="tutor", tutor_reply="An unauthorized generated explanation.")
                before = tuple(demo.events)
                valid = append_teaching_move(demo.events, demo.pack, request_id="support.invalid",
                    candidate=pending.candidates[0], selector_kind="tutor")
                forged = valid.model_copy(update={"payload": valid.payload.model_copy(update={"tutor_reply": "An unauthorized generated explanation."})})
                with self.assertRaisesRegex(ValueError, "only a learner message"):
                    replay((*before, forged))

    def test_scored_response_and_non_tutor_hold_cannot_acquire_a_reply(self):
        demo, activity = final_controller()
        demo.respond(request_id="final.scored", option_id=next(choice.option_id for choice in activity.choices if choice.correct))
        valid = demo.events[-1]
        self.assertIsInstance(valid, TeachingMoveSelected)
        forged = valid.model_copy(update={"payload": valid.payload.model_copy(update={
            "selector_kind": "tutor", "tutor_reply": "A scored response cannot carry this reply.",
        })})
        with self.assertRaisesRegex(ValueError, "only a learner message"):
            replay((*demo.events[:-1], forged))
        demo, _ = final_controller()
        state = replay(demo.events)
        record_support_request(demo.events, demo.pack, attempt_id=state.open_attempt_id,
            request_id="support.hold", request=SupportRequest(kind="orientation"))
        pending = pending_turn(demo.events, demo.pack, request_id="support.hold")
        hold = next(item for item in pending.candidates if item.move.strategy == "hold")
        with self.assertRaisesRegex(ValueError, "only a tutor proposal"):
            append_teaching_move(demo.events, demo.pack, request_id="support.hold", candidate=hold,
                selector_kind="invalid_output", fallback_reason="invalid_output", tutor_reply="Not a legal hold reply.")


if __name__ == "__main__":
    unittest.main()
