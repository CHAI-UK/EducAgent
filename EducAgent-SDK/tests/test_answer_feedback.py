"""Learner-visible answer feedback comes from scored events, not tutor prose."""

import json
from pathlib import Path
import tempfile
import unittest

from educagent_sdk import load_content_pack
from educagent_sdk.demo import DemoController, JsonlEventStore


ROOT = Path(__file__).resolve().parents[1]


class AnswerFeedbackTest(unittest.TestCase):
    def test_current_foundations_routes_expose_feedback_for_every_scored_choice(self) -> None:
        registry = json.loads((ROOT / "content/modules.json").read_text(encoding="utf-8"))
        foundation = next(item for item in registry["modules"] if item["module_id"] == "causality_m0")
        for profile, filename in foundation["profile_pack_paths"].items():
            pack = load_content_pack(ROOT / filename)
            self.assertEqual(len(pack.activities), 28)
            for activity in pack.activities:
                with self.subTest(profile=profile, activity=activity.activity_id):
                    demo = DemoController(pack)
                    opened = demo.start(preferred_activity_ids=(activity.activity_id,), route_scope="preferred")
                    self.assertTrue(opened["question"])
                    self.assertIsNone(opened["answer_feedback"])
                    if activity.activity_type == "causal_scene":
                        self.assertIsNotNone(opened["causal_scene"])
                        self.assertFalse(opened["choices"])
                        continue
                    wrong = next(item for item in activity.choices if not item.correct)
                    rejected = demo.respond(request_id="feedback.current.wrong", option_id=wrong.option_id)
                    self.assertFalse(rejected["answer_feedback"]["accepted"])
                    self.assertEqual(rejected["answer_feedback"]["option_id"], wrong.option_id)
                    self.assertFalse(rejected["can_continue"])
                    self.assertEqual(rejected["completed_activity_ids"], ())

    def test_wrong_feedback_survives_explanation_reload_and_correct_retry(self) -> None:
        for profile in ("general", "medical"):
            pack = load_content_pack(ROOT / f"content/foundation_{profile}_course_1_3_0.json")
            for activity_id in (
                "world-data-model.practice", "world-data-model.transfer",
                "m0-integrated-transfer.01", "m0-final-quiz.04",
            ):
                with self.subTest(profile=profile, activity=activity_id), tempfile.TemporaryDirectory() as directory:
                    store = JsonlEventStore(Path(directory) / "feedback.jsonl")
                    demo = DemoController(pack, store=store)
                    self.assertIsNone(demo.view()["answer_feedback"])
                    demo.start(preferred_activity_ids=(activity_id,), route_scope="preferred")
                    activity = next(item for item in pack.activities if item.activity_id == activity_id)
                    wrong = next(item for item in activity.choices if not item.correct)
                    correct = next(item for item in activity.choices if item.correct)
                    rejected = demo.respond(request_id="feedback.wrong", option_id=wrong.option_id)
                    feedback = rejected["answer_feedback"]
                    self.assertEqual(feedback, {
                        "accepted": False, "option_id": wrong.option_id,
                        "text": next(item.text for item in pack.resources if item.resource_id == wrong.consequence_resource_id),
                    })
                    self.assertFalse(rejected["can_continue"])
                    self.assertTrue(rejected["assessment_submitted"])
                    self.assertFalse(rejected["assessment_accepted"])
                    demo.request_explanation(request_id="feedback.explain")
                    self.assertEqual(demo.view()["answer_feedback"], feedback)
                    resumed = DemoController(pack, store=store)
                    self.assertEqual(resumed.view()["answer_feedback"], feedback)
                    with self.assertRaisesRegex(ValueError, "cannot advance"):
                        resumed.continue_activity(request_id="feedback.blocked")
                    accepted = resumed.respond(request_id="feedback.correct", option_id=correct.option_id)
                    self.assertTrue(accepted["answer_feedback"]["accepted"])
                    self.assertEqual(accepted["answer_feedback"]["option_id"], correct.option_id)
                    self.assertTrue(accepted["can_continue"])
                    completed = resumed.continue_activity(request_id="feedback.continue")
                    self.assertIsNone(completed["answer_feedback"])
                    self.assertEqual(completed["completed_activity_ids"], (activity_id,))

    def test_feedback_is_attempt_scoped_and_read_only(self) -> None:
        pack = load_content_pack(ROOT / "content/foundation_general_course_1_3_0.json")
        demo = DemoController(pack)
        demo.start(preferred_activity_ids=(
            "variables-and-values.practice", "variables-and-values.transfer",
        ), route_scope="preferred")
        activity = next(item for item in pack.activities if item.activity_id == demo.view()["activity_id"])
        demo.respond(request_id="feedback.first", option_id=next(item.option_id for item in activity.choices if item.correct))
        before = tuple(demo.events)
        self.assertTrue(demo.view()["answer_feedback"]["accepted"])
        self.assertEqual(tuple(demo.events), before)
        next_activity = demo.continue_activity(request_id="feedback.next")
        self.assertEqual(next_activity["activity_id"], "variables-and-values.transfer")
        self.assertIsNone(next_activity["answer_feedback"])
        self.assertFalse(next_activity["can_continue"])

    def test_m1_quiz_and_final_feedback_uses_the_same_contract(self) -> None:
        for module in ("effect", "shift"):
            for profile in ("general", "medical"):
                pack = load_content_pack(ROOT / f"content/m1_{module}_course_{profile}.json")
                activities = (pack.activities[0], pack.activities[-1])
                for activity in activities:
                    with self.subTest(module=module, profile=profile, activity=activity.activity_id):
                        demo = DemoController(pack)
                        demo.start(preferred_activity_ids=(activity.activity_id,), route_scope="preferred")
                        wrong = next(item for item in activity.choices if not item.correct)
                        rejected = demo.respond(request_id="feedback.m1.wrong", option_id=wrong.option_id)
                        self.assertFalse(rejected["answer_feedback"]["accepted"])
                        self.assertEqual(rejected["answer_feedback"]["option_id"], wrong.option_id)
                        self.assertFalse(rejected["can_continue"])
                        self.assertTrue(rejected["answer_feedback"]["text"])


if __name__ == "__main__":
    unittest.main()
