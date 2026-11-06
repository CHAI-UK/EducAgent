"""Public reference-label provenance reaches Shift lessons and safe final help."""

import json
from pathlib import Path
import unittest

from pydantic_ai.messages import ModelResponse, TextPart, UserPromptPart
from pydantic_ai.models import override_allow_model_requests
from pydantic_ai.models.function import FunctionModel

from educagent_sdk import load_content_pack
from educagent_sdk.demo import DemoController
from educagent_sdk.events import ResponseRecorded


ROOT = Path(__file__).resolve().parents[1]


def prompt_context(messages):
    return json.loads(next(part.content for message in reversed(messages) for part in message.parts
        if isinstance(part, UserPromptPart) and isinstance(part.content, str)))


class ShiftLessonScopeTest(unittest.IsolatedAsyncioTestCase):
    def assert_public_scope(self, context, activity, pack):
        scope = context["public_teaching_scope"]
        self.assertEqual(set(scope), {"portal_reference", "real_research_reference"})
        self.assertIn("preset before measurement error", scope["portal_reference"])
        self.assertIn("not a real clinical or inspection review", scope["portal_reference"])
        self.assertIn("established separately", scope["real_research_reference"])
        self.assertIn("Clinical adjudication can be one source", scope["real_research_reference"])
        self.assertIn("this teaching model does not supply it", scope["real_research_reference"])
        serialized = json.dumps(scope)
        self.assertNotRegex(serialized, r"\d")
        for private in ("a_low", "a_high", "b_low", "source_positive", "source_negative",
                        "unsupported_detail", "qualifier", '"choices"', '"correct"'):
            self.assertNotIn(private, json.dumps(context))
        resources = {item.resource_id: item.text for item in pack.resources}
        self.assertNotIn(resources[activity.question_resource_id], serialized)
        self.assertNotIn(resources[activity.explanation_resource_id], serialized)
        for choice in activity.choices:
            self.assertNotIn(choice.text, serialized)

    async def test_both_fourth_lessons_get_scope_without_an_active_experiment_or_course_name_heuristic(self):
        for profile in ("general", "medical"):
            with self.subTest(profile=profile):
                original = load_content_pack(ROOT / f"content/m1_shift_course_{profile}_1_2_0.json")
                pack = original.model_copy(update={"pack_id": f"scope.neutral.{profile}", "title": "Neutral review"})
                activity = next(item for item in pack.activities if item.activity_id == "when-predictions-can-still-fail.quiz")
                self.assertIsNone(activity.experiment)
                demo = DemoController(pack, profile_id=profile)
                demo.start(preferred_activity_ids=(activity.activity_id,), route_scope="preferred")
                captured = []

                async def reply(messages, info):
                    context = prompt_context(messages)
                    captured.append(context)
                    self.assertIn("When public_teaching_scope is provided", info.instructions)
                    self.assert_public_scope(context, activity, pack)
                    self.assertIsNone(context["visible_experiment"])
                    self.assertIsNone(context["visible_lesson"])
                    self.assertEqual(context["profile_id"], profile)
                    return ModelResponse(parts=[TextPart(
                        "Here the reference is preset before measurement errors, not a real clinical review. "
                        "Real research needs suitable reference evidence established separately.")])

                with override_allow_model_requests(False):
                    view = await demo.send_message_with_tutor(request_id="scope.lesson", unguarded=True,
                        text="Is reference a preset teaching label here, or a real clinical review?",
                        model=FunctionModel(reply))
                self.assertEqual(len(captured), 1)
                self.assertFalse(view["can_continue"])
                self.assertFalse(any(isinstance(event, ResponseRecorded) for event in demo.events))

    async def test_both_final_support_and_chat_keep_scope_without_question_or_answer_material(self):
        for profile in ("general", "medical"):
            with self.subTest(profile=profile):
                pack = load_content_pack(ROOT / f"content/m1_shift_course_{profile}_1_2_0.json")
                activity = next(item for item in pack.activities if item.activity_id == "m1-shift-final.04")
                demo = DemoController(pack, profile_id=profile)
                demo.start(preferred_activity_ids=(activity.activity_id,), route_scope="preferred")
                captured = []
                resources = {item.resource_id: item.text for item in pack.resources}

                async def reply(messages, _info):
                    context = prompt_context(messages)
                    captured.append(context)
                    self.assert_public_scope(context, activity, pack)
                    self.assertEqual(context["assessment_help"]["phase"], "final_before_answer")
                    for field in ("visible_lesson", "visible_experiment", "visible_scene", "visible_workbench"):
                        self.assertIsNone(context[field])
                    serialized = json.dumps(context)
                    self.assertNotIn(activity.workbench.prompt, serialized)
                    self.assertNotIn(resources[activity.question_resource_id], serialized)
                    self.assertNotIn(resources[activity.explanation_resource_id], serialized)
                    for choice in activity.choices:
                        self.assertNotIn(choice.text, serialized)
                    return ModelResponse(parts=[TextPart("The teaching-model reference is preset, not clinical adjudication.")])

                with override_allow_model_requests(False):
                    await demo.request_explanation_with_tutor(request_id="scope.final.explain", model=FunctionModel(reply))
                    view = await demo.send_message_with_tutor(request_id="scope.final.chat", unguarded=True,
                        text="Where does the reference come from in this teaching model?", model=FunctionModel(reply))
                self.assertEqual(len(captured), 2)
                self.assertEqual(captured[0]["public_teaching_scope"], captured[1]["public_teaching_scope"])
                self.assertFalse(view["assessment_submitted"])
                self.assertFalse(view["can_continue"])

    async def test_an_effect_model_with_a_shift_like_name_does_not_receive_shift_scope(self):
        original = load_content_pack(ROOT / "content/m1_effect_course_general_1_2_0.json")
        pack = original.model_copy(update={"pack_id": "causality.m1.shift.named", "title": "Robust prediction or generation"})
        activity = pack.activities[0]
        demo = DemoController(pack, profile_id="general")
        demo.start(preferred_activity_ids=(activity.activity_id,), route_scope="preferred")
        captured = []

        async def reply(messages, _info):
            context = prompt_context(messages)
            captured.append(context)
            self.assertNotIn("public_teaching_scope", context)
            return ModelResponse(parts=[TextPart("An intervention changes assignment rather than filtering existing records.")])

        with override_allow_model_requests(False):
            await demo.send_message_with_tutor(request_id="scope.effect", text="Explain the concept.",
                model=FunctionModel(reply), unguarded=True)
        self.assertEqual(len(captured), 1)


if __name__ == "__main__":
    unittest.main()
