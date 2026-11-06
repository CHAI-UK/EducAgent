"""Profile lesson authoring, release grounding and assessment isolation."""

import json
import unittest
from pathlib import Path
from unittest.mock import patch

from pydantic import ValidationError

from educagent_sdk import ContentPack, ReleaseValidationError, load_content_pack, validate_release
from educagent_sdk.evaluation import ChoiceEvidence, evaluate_choice
from educagent_sdk.demo import DemoController
from educagent_sdk.events import replay
from educagent_sdk.lesson_samples import load_lesson_samples, lesson_lecture_context, lesson_projection, lesson_view


ROOT = Path(__file__).resolve().parents[1]
SAMPLES_PATH = ROOT / "content/foundation_lesson_samples.json"


class LessonSamplesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.base = load_content_pack(ROOT / "content/causality_m0_full.json")
        cls.source_data = json.loads(SAMPLES_PATH.read_text(encoding="utf-8"))
        cls.samples = load_lesson_samples(cls.base, SAMPLES_PATH)

    def compile_changed(self, change):
        data = json.loads(json.dumps(self.source_data))
        change(data)
        with patch.object(Path, "read_text", return_value=json.dumps(data)):
            return load_lesson_samples(self.base, Path("sample.json"))

    def test_profiles_share_one_unchanged_objective_without_editing_base(self) -> None:
        original = self.base.model_dump_json()
        samples = load_lesson_samples(self.base, SAMPLES_PATH)
        self.assertEqual(self.base.model_dump_json(), original)
        self.assertEqual(len(self.base.concepts), 9)
        self.assertIsNone(self.base.lesson)
        self.assertEqual(set(samples), {"general", "medical"})
        self.assertEqual(len({pack.pack_id for pack in samples.values()}), 2)
        expected = next(concept for concept in self.base.concepts
                        if concept.concept_id == "association-is-not-causation")
        for profile_id, pack in samples.items():
            with self.subTest(profile=profile_id):
                self.assertEqual(pack.version, "1.0.0")
                self.assertEqual(len(pack.concepts), 1)
                self.assertEqual(pack.concepts[0].concept_id, expected.concept_id)
                self.assertEqual(pack.concepts[0].objective, expected.objective)
                self.assertEqual(pack.concepts[0].m1_ready_activity_ids, ())
                self.assertEqual(pack.lesson.profile_id, profile_id)
                self.assertEqual(pack.lesson.review_status, "author_draft")
                self.assertEqual(len(pack.activities), 2)
                self.assertFalse(pack.activities[0].is_transfer)
                self.assertTrue(pack.activities[1].is_transfer)
                self.assertNotEqual(pack.activities[0].question_resource_id,
                                    pack.activities[1].question_resource_id)

    def test_all_resources_and_claims_are_grounded_and_deterministic_choices_work(self) -> None:
        for pack in self.samples.values():
            with self.subTest(pack=pack.pack_id):
                self.assertEqual(validate_release(pack).unused_resource_ids, ())
                used_claims = {claim_id for resource in pack.resources for claim_id in resource.claim_ids}
                self.assertEqual({claim.claim_id for claim in pack.claims}, used_claims)
                used_sources = {ref.source_id for claim in pack.claims for ref in claim.source_refs}
                self.assertEqual({source.source_id for source in pack.sources}, used_sources)
                self.assertIn("peters-janzing-scholkopf-2017", used_sources)
                self.assertTrue(any(claim.deterministic_derivation for claim in pack.claims))
                for activity in pack.activities:
                    self.assertEqual(activity.activity_type, "choice")
                    for choice in activity.choices:
                        verdict = evaluate_choice(pack, ChoiceEvidence(
                            activity_id=activity.activity_id, option_id=choice.option_id,
                        ))
                        self.assertEqual(verdict.accepted, choice.correct)
                        self.assertEqual(verdict.consequence_resource_id, choice.consequence_resource_id)

    def test_lecture_projection_is_frozen_and_contains_no_assessment_answers(self) -> None:
        self.assertIsNone(lesson_view(self.base))
        self.assertEqual(lesson_lecture_context(self.base), ())
        for pack in self.samples.values():
            view = lesson_projection(pack)
            visible = view.model_dump_json()
            api_view = lesson_view(pack)
            self.assertEqual(api_view["version"], "1.0.0")
            self.assertEqual(set(api_view["worked_graph"]["edges"][0]), {"from", "to"})
            self.assertIsInstance(json.dumps(api_view), str)
            context = lesson_lecture_context(pack)
            self.assertIsInstance(context, tuple)
            self.assertTrue(view.sources)
            self.assertTrue(view.example_label.startswith("Synthetic teaching example"))
            self.assertIn("possible", view.worked_graph.label.lower())
            self.assertNotIn('"correct"', visible)
            self.assertNotIn('"choices"', visible)
            self.assertNotIn("feedback", visible)
            for activity in pack.activities:
                for choice in activity.choices:
                    self.assertNotIn(choice.option_id, visible)
                    self.assertNotIn(choice.consequence_resource_id, "\n".join(context))
            transfer_question = next(resource.text for resource in pack.resources
                                     if resource.resource_id == pack.activities[1].question_resource_id)
            self.assertNotIn(transfer_question, "\n".join(context))
            with self.assertRaises(ValidationError):
                view.title = "Changed"

    def test_practice_retry_and_independent_transfer_complete_through_runtime(self) -> None:
        for profile_id, pack in self.samples.items():
            with self.subTest(profile=profile_id):
                controller = DemoController(pack)
                view = controller.start(session_id=f"lesson.{profile_id}")
                self.assertEqual(view["activity_id"], pack.lesson.practice_activity_id)
                for index, activity in enumerate(pack.activities):
                    if index == 0:
                        wrong = next(choice for choice in activity.choices if not choice.correct)
                        view = controller.respond(request_id=f"lesson.{profile_id}.wrong", option_id=wrong.option_id)
                        self.assertFalse(view["can_continue"])
                        self.assertFalse(view["completed_activity_ids"])
                    correct = next(choice for choice in activity.choices if choice.correct)
                    view = controller.respond(request_id=f"lesson.{profile_id}.answer.{index}", option_id=correct.option_id)
                    self.assertTrue(view["can_continue"])
                    view = controller.continue_activity(request_id=f"lesson.{profile_id}.continue.{index}")
                    if index == 0:
                        self.assertEqual(view["activity_id"], pack.lesson.challenge_activity_id)
                        self.assertEqual(view["status"], "active")
                self.assertEqual(view["status"], "completed")
                self.assertEqual(set(view["completed_activity_ids"]), {item.activity_id for item in pack.activities})
                self.assertEqual(replay(controller.events).pack_id, pack.pack_id)

    def test_authoring_rejects_changed_objective_profile_and_answer_contract(self) -> None:
        with self.assertRaisesRegex(ValueError, "objective must exactly match"):
            self.compile_changed(lambda data: data.__setitem__("objective", "A different curriculum"))
        with self.assertRaises(ValidationError):
            self.compile_changed(lambda data: data["profiles"].pop("medical"))
        with self.assertRaises(ValidationError):
            self.compile_changed(lambda data: data["profiles"]["general"]["practice"]["choices"][1].__setitem__("correct", True))
        with self.assertRaisesRegex(ValueError, "unknown base source"):
            self.compile_changed(lambda data: data["source_refs"][0].__setitem__("source_id", "missing-source"))

    def test_typed_lesson_rejects_invalid_activity_and_hypothesis_graph(self) -> None:
        cases = (
            lambda data: data["lesson"].__setitem__("practice_activity_id", data["lesson"]["challenge_activity_id"]),
            lambda data: data["lesson"].__setitem__("concept_id", "another-concept"),
            lambda data: data["activities"][1].__setitem__("is_transfer", False),
            lambda data: data["lesson"]["worked_graph"]["edges"][0].__setitem__("parent_id", "missing-node"),
            lambda data: data["lesson"]["worked_graph"]["edges"].append({"parent_id": "sales", "child_id": "weather"}),
        )
        for change in cases:
            with self.subTest(change=change):
                data = self.samples["general"].model_dump(mode="json")
                change(data)
                with self.assertRaises(ValidationError):
                    ContentPack.model_validate_json(json.dumps(data))

    def test_lesson_resource_references_fail_closed_at_release(self) -> None:
        mutations = (
            (lambda data: data["lesson"].__setitem__("definition_resource_id", "missing-resource"), "missing-resource"),
            (lambda data: data["lesson"].__setitem__("definition_resource_id", data["lesson"]["hook_resource_id"]), "incompatible-resource-kind"),
            (lambda data: data["resources"][0].__setitem__("release_status", "draft"), "draft-resource"),
        )
        for change, expected in mutations:
            with self.subTest(code=expected):
                data = self.samples["general"].model_dump(mode="json")
                change(data)
                pack = ContentPack.model_validate_json(json.dumps(data))
                with self.assertRaises(ReleaseValidationError) as caught:
                    lesson_view(pack)
                self.assertTrue(any(issue.code == expected and issue.path.startswith("/lesson/")
                                    for issue in caught.exception.report.issues))


if __name__ == "__main__":
    unittest.main()
