"""Focused experience contracts: intent, deadlines and readable example memory."""

import asyncio
import json
from pathlib import Path
import unittest

from pydantic_ai.messages import ModelResponse, TextPart, ToolCallPart, UserPromptPart
from pydantic_ai.models import override_allow_model_requests
from pydantic_ai.models.function import FunctionModel

from educagent_sdk import load_content_pack
from educagent_sdk.demo import DemoController
from educagent_sdk.events import LearnerMessage, LearnerMessageRecorded, TeachingMoveSelected, record_learner_message, replay
from educagent_sdk.tutor import DEMO_CHAT_POLICY_VERSION, _requests_single_question, run_open_demo_reply
from educagent_sdk.tutor_examples import AdjustmentExampleReply, AdjustmentExampleRoles, example_roles_from_reply


ROOT = Path(__file__).resolve().parents[1]


def controller(profile="general"):
    pack = load_content_pack(ROOT / f"content/m1_effect_course_{profile}_1_2_0.json")
    demo = DemoController(pack, profile_id=profile)
    demo.start(preferred_activity_ids=("m1-effect-final.03",), route_scope="preferred")
    return demo


def context(messages):
    return json.loads(next(part.content for message in reversed(messages) for part in message.parts
        if isinstance(part, UserPromptPart) and isinstance(part.content, str)))


def tool_reply(info, roles, focus="roles", new=False):
    tool = next(t for t in info.output_tools if "roles" in t.parameters_json_schema.get("properties", {}))
    plan = AdjustmentExampleReply(roles=roles, focus=focus, introduce_new_example=new)
    return ModelResponse(parts=[ToolCallPart(tool.name, plan.model_dump(mode="json"))])


class TutorExperienceReviewTest(unittest.IsolatedAsyncioTestCase):
    async def send(self, demo, request, message, reply):
        with override_allow_model_requests(False):
            return await demo.send_message_with_tutor(request_id=request, text=message,
                model=FunctionModel(reply), unguarded=True)

    def test_single_question_preference_is_narrow_not_all_learner_questions(self):
        for text in ("Ask me one small Socratic question.", "Could you give me just one short question?", "问我一个简单的问题"):
            with self.subTest(text=text):
                self.assertTrue(_requests_single_question(text))
        for text in ("Why do we compare groups?", "Explain confounding.", "Don't ask me a question.",
                "Do not give me a question; just explain.", "Do not pose me a question; explain the term.", "不要问我一个问题"):
            with self.subTest(text=text):
                self.assertFalse(_requests_single_question(text))

    async def test_explicit_question_request_retries_explanation_then_accepts_question(self):
        for profile in ("general", "medical"):
            demo = controller(profile)
            calls = []

            async def reply(messages, info):
                calls.append(context(messages))
                return ModelResponse(parts=[TextPart(
                    "Confounding is a pre-existing difference." if len(calls) == 1 else
                    "What else could explain an observed difference between two groups?"
                )])

            view = await self.send(demo, "question.only", "Ask me one small Socratic question.", reply)
            self.assertEqual(len(calls), 2)
            self.assertEqual(calls[0]["requested_response"], "one_question")
            self.assertTrue(view["turn"].endswith("?"))
            self.assertFalse(view["can_continue"])
            self.assertIsNone(replay(demo.events).last_evaluation)

    async def test_failed_question_preference_recovers_without_role_change_or_dialogue_limit(self):
        demo = controller()
        roles = AdjustmentExampleRoles(treatment="watering plan", outcome="plant height",
            common_cause="plant type", target_population="the garden plants")

        async def introduce(messages, info):
            return tool_reply(info, roles)

        await self.send(demo, "example.start", "Show a plant example.", introduce)

        async def mismatched(messages, info):
            self.assertEqual(context(messages)["active_adjustment_example"], roles.model_dump())
            return tool_reply(info, roles, "compare")

        view = await self.send(demo, "question.recover", "Ask me one small question.", mismatched)
        self.assertTrue(view["turn"].endswith("?"))
        self.assertEqual(view["turn"].count("?"), 1)
        move = next(e for e in reversed(demo.events) if isinstance(e, TeachingMoveSelected))
        self.assertEqual(example_roles_from_reply(move.payload.tutor_reply), roles)
        self.assertTrue(move.payload.decision_trace_id.endswith(f".guided-chat.{DEMO_CHAT_POLICY_VERSION}.question-recovery"))

        async def next_reply(messages, info):
            self.assertEqual(context(messages)["active_adjustment_example"], roles.model_dump())
            self.assertTrue(any(item["text"].endswith("?") for item in context(messages)["recent_conversation"] if item["role"] == "tutor"))
            return ModelResponse(parts=[TextPart("Yes: different plant-type mixtures can affect that overall comparison.")])

        await self.send(demo, "question.followup", "Could it be their different plant types?", next_reply)

    async def test_open_reply_deadline_releases_request_and_retry_preserves_one_input(self):
        demo = controller()
        record_learner_message(demo.events, demo.pack, attempt_id=demo.view()["attempt_id"],
            request_id="slow.request", message=LearnerMessage(text="Explain a causal comparison."))
        cancelled = []

        async def slow(messages, info):
            try:
                await asyncio.sleep(1)
            finally:
                cancelled.append(True)
            return ModelResponse(parts=[TextPart("Too late.")])

        with override_allow_model_requests(False), self.assertRaises(TimeoutError):
            await run_open_demo_reply(demo.events, demo.pack, request_id="slow.request",
                model=FunctionModel(slow), timeout_seconds=0.5)
        self.assertEqual(cancelled, [True])

        async def reply(messages, info):
            return ModelResponse(parts=[TextPart("A causal comparison asks what would change under a different action.")])

        await self.send(demo, "slow.request", "Explain a causal comparison.", reply)
        self.assertEqual(sum(isinstance(e, LearnerMessageRecorded) and e.request_id == "slow.request" for e in demo.events), 1)
        self.assertIsNone(replay(demo.events).last_evaluation)

    async def test_public_role_details_show_once_and_again_after_explicit_switch(self):
        demo = controller()
        garden = AdjustmentExampleRoles(treatment="watering plan", outcome="plant height",
            common_cause="plant type", target_population="the garden plants")
        wound = AdjustmentExampleRoles(treatment="dressing protocol", outcome="healing",
            common_cause="initial severity", target_population="fictional wounds")
        for index, roles in enumerate((garden, garden, wound, garden)):
            async def reply(messages, info, roles=roles, index=index):
                return tool_reply(info, roles, new=index > 1)

            view = await self.send(demo, f"roles.{index}", "Explain this example.", reply)
            self.assertNotIn("Example roles:", view["turn"])
            message = view["conversation"][-1]
            self.assertNotIn("Example roles:", message["text"])
            if index == 1:
                self.assertNotIn("example_roles", message)
            else:
                self.assertEqual(message["example_roles"], roles.model_dump())
            move = next(e for e in reversed(demo.events) if isinstance(e, TeachingMoveSelected))
            self.assertEqual(example_roles_from_reply(move.payload.tutor_reply), roles)
        replay(demo.events)

    async def test_policy_upgrade_keeps_previously_safe_example_memory_at_unanswered_final(self):
        demo = controller()
        roles = AdjustmentExampleRoles(treatment="watering plan", outcome="plant height",
            common_cause="plant type", target_population="the garden plants")

        async def introduce(messages, info):
            return tool_reply(info, roles)

        await self.send(demo, "legacy.example", "Show a plant example.", introduce)
        position = next(i for i in range(len(demo.events) - 1, -1, -1)
            if isinstance(demo.events[i], TeachingMoveSelected))
        event = demo.events[position]
        demo.events[position] = event.model_copy(update={"payload": event.payload.model_copy(update={
            "decision_trace_id": "legacy.guided-chat.1.6.0",
        })})

        async def followup(messages, info):
            snapshot = context(messages)
            self.assertEqual(snapshot["active_adjustment_example"], roles.model_dump())
            self.assertIsNone(snapshot["visible_experiment"])
            self.assertTrue(any("Example roles:" in entry["text"]
                for entry in snapshot["recent_conversation"] if entry["role"] == "tutor"))
            return ModelResponse(parts=[TextPart("Keep plant type as the starting common cause in this hypothetical example.")])

        await self.send(demo, "upgraded.followup", "Please keep the same example.", followup)
        replay(demo.events)


if __name__ == "__main__":
    unittest.main()
