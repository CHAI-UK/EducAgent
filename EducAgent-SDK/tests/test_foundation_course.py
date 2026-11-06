"""The normal Portal adds an objective-specific final assessment to M0."""

import hashlib
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

from authoring.build_foundation_course import build
from educagent_sdk import load_content_pack, validate_release
from educagent_sdk.demo import DemoController
from educagent_sdk.diagnostic import DiagnosticSession, load_diagnostic_plan


ROOT = Path(__file__).resolve().parents[1]


class FoundationCourseTest(unittest.TestCase):
    def test_documented_direct_script_command_checks_current_outputs(self):
        result = subprocess.run(
            [sys.executable, "authoring/build_foundation_course.py", "--check"],
            cwd=ROOT, env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
            capture_output=True, text=True, timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("general: 9 concepts", result.stdout)
        self.assertIn("medical: 9 concepts", result.stdout)

    def test_historical_content_is_unchanged_by_expert_revision(self):
        expected = {
            "foundation_general_course.json": "47043ae48a9ec89510f848626d8c6a1f2a0ece16425a39c597375f1aecd19881",
            "foundation_medical_course.json": "8d21a99e9504a7156e01cd91ca27f65488f73568ed891ba54671c6a09c0d23c4",
            "foundation_profiles.json": "12e7a3bb8e910b56db81b432b2a284c447755dfb0929bc0fb1dcb9ddd15aef84",
            "causality_m0_full.json": "a40fb0d3c12a6c40ed8b70c491e8190325c095146e4880ed9a2647f9fab2ac3b",
            "foundation_general_course_1_3_0.json": "6f336b16152833c77632d62ca88d3202772bfca210e553405178d892fb9d33b1",
            "foundation_medical_course_1_3_0.json": "5df412859fbaf46e48f233ec7ee2b8b2b1a5b0f585bdac1875d2560ee386e111",
            "foundation_general_course_1_4_0.json": "2a5dbc2f130baf1a3f3e5eace8eb2e0294a6c65ec8bc4398cfd991cb84074ab3",
            "foundation_medical_course_1_4_0.json": "37c00d826d81638330db7a01ea067a6810a6afe2aa22755a858bda96b3d13f8c",
            "foundation_general_course_1_5_0.json": "bab613c25ccfa04648850a7f9a8ee32cc2296be9d47d6380bb4c330bc183c07b",
            "foundation_medical_course_1_5_0.json": "86e4ce9d4b776a6ee73aceca1cd67243d2047e7c8495be56bb6e25c21c013677",
            "foundation_general_course_1_6_0.json": "522dcd6e90900c7e512be093e5c7ccfc51d84eb68b18ca7a4e5cb11b04710cc4",
            "foundation_medical_course_1_6_0.json": "747f58751ff1ab7d4ea196b5a11e5bcbfa70d47e5a5966311b65800d44bfebcc",
            "foundation_general_course_1_7_0.json": "37e51972b928a1969d35cc22024601d5fbec3579d8d068f3e284ca24822ab5b7",
            "foundation_medical_course_1_7_0.json": "f1bfac6987337f52e29e729b7ba6a137a450855b66a796d01423b7bc2b08a147",
        }
        for filename, checksum in expected.items():
            with self.subTest(filename=filename):
                self.assertEqual(hashlib.sha256((ROOT / "content" / filename).read_bytes()).hexdigest(), checksum)

    def test_frozen_1_7_courses_preserve_the_original_backbone_and_test_every_objective(self):
        historical = load_content_pack(ROOT / "content/causality_m0_full.json")
        self.assertEqual(historical.version, "1.1.0")
        for profile in ("general", "medical"):
            with self.subTest(profile=profile):
                # Keep the earlier assessment regression on its frozen version.
                # Current builder fidelity and 1.8 scope have separate checks.
                pack = load_content_pack(ROOT / f"content/foundation_{profile}_course_1_7_0.json")
                self.assertEqual(pack.version, "1.7.0")
                previous = load_content_pack(ROOT / f"content/foundation_{profile}_course.json")
                self.assertEqual(previous.version, "1.2.0")
                self.assertNotEqual(previous, pack)
                self.assertEqual(len(pack.activities), 28)
                self.assertEqual(len(pack.lessons), 9)
                self.assertEqual(tuple(c.concept_id for c in pack.concepts),
                                 tuple(c.concept_id for c in historical.concepts))
                self.assertEqual(tuple(a.activity_id for a in pack.activities[:19]),
                                 tuple(a.activity_id for a in historical.activities))
                before_revision = load_content_pack(ROOT / f"content/foundation_{profile}_course_1_6_0.json")
                self.assertEqual(pack.concepts, before_revision.concepts)
                for before, after in zip(before_revision.activities, pack.activities, strict=True):
                    if after.activity_id == "world-data-model.transfer":
                        # The separately tested data/world choices have new IDs.
                        # Every other activity field still compares in full.
                        self.assertEqual(after.model_copy(update={
                            "choices": before.choices,
                            "explanation_resource_id": before.explanation_resource_id,
                        }), before)
                    elif after.activity_id in {"data-vs-assumptions.practice", "data-vs-assumptions.transfer"}:
                        # These two tasks only gain an illustrative record table;
                        # their complete choices, truth and other fields remain.
                        self.assertEqual(after.model_copy(update={"workbench": before.workbench}), before)
                    else:
                        self.assertEqual(after, before)
                for before, after in zip(before_revision.lessons, pack.lessons, strict=True):
                    if after.concept_id == "world-data-model":
                        self.assertEqual(after.challenge_title, "Identify data and the world")
                        self.assertEqual(after.model_copy(update={"challenge_title": before.challenge_title}), before)
                    else:
                        self.assertEqual(after, before)
                self.assertEqual(pack.sources, before_revision.sources)
                self.assertEqual(pack.causal_scenes, before_revision.causal_scenes)
                for before, after in zip(before_revision.claims, pack.claims, strict=True):
                    expected = before.model_dump(mode="json")
                    if before.claim_id == "foundation.final-case":
                        expected["deterministic_derivation"]["method_version"] = pack.version
                    self.assertEqual(after.model_dump(mode="json"), expected)
                old_resources = pack.resources[:len(before_revision.resources)]
                self.assertEqual(tuple(resource.resource_id for resource in old_resources),
                                 tuple(resource.resource_id for resource in before_revision.resources))
                for before, after in zip(before_revision.resources, old_resources, strict=True):
                    if after.resource_id in {
                        "world-data-model.question.transfer", "assumptions.question.practice",
                        "assumptions.question.transfer", "assumptions.explanation", "assumptions.consequence.rejected",
                    }:
                        self.assertEqual(after.model_copy(update={"text": before.text}), before)
                    else:
                        self.assertEqual(after, before)
                self.assertEqual(tuple(resource.resource_id for resource in pack.resources[len(old_resources):]),
                    tuple(f"world-data-model.transfer.data-world.{suffix}"
                          for suffix in ("explanation", "hint", "accepted", "rejected")))
                self.assertEqual(validate_release(pack).unused_resource_ids, ())
                for concept in pack.concepts:
                    activity = next(a for a in pack.activities
                                    if a.concept_id == concept.concept_id and a.workbench
                                    and a.workbench.stage == "capstone")
                    self.assertIn(activity.activity_id, concept.completion_activity_ids)
                    self.assertEqual(activity.workbench.stage, "capstone")
                    self.assertEqual(len(activity.choices), 4)
                dag_lesson = next(l for l in pack.lessons if l.concept_id == "basic-dag-language")
                definition = next(r.text for r in pack.resources
                                  if r.resource_id == dag_lesson.definition_resource_id)
                self.assertIn("graph", definition.lower())
                self.assertEqual({edge.parent_id for edge in dag_lesson.worked_graph.edges}, {"rain"})

    def test_assessments_do_not_reveal_answers_by_stem_position_or_feedback(self):
        diagnostic = json.loads((ROOT / "content/causality_m0_diagnostic.json").read_text(encoding="utf-8"))
        for profile in ("general", "medical"):
            with self.subTest(profile=profile):
                pack = build(profile)
                resources = {item.resource_id: item.text for item in pack.resources}
                activities = {item.activity_id: item for item in pack.activities}
                scored = [item for item in pack.activities if item.choices]
                for activity in scored:
                    stem = resources[activity.question_resource_id].casefold()
                    self.assertNotIn("does not change", stem)
                    self.assertNotIn("assigns no", stem)
                    if not activity.activity_id.startswith("m0-integrated"):
                        self.assertGreaterEqual(len(activity.choices), 3, activity.activity_id)
                    correct = next(choice for choice in activity.choices if choice.correct)
                    for choice in activity.choices:
                        if choice.correct:
                            continue
                        feedback = resources[choice.consequence_resource_id]
                        self.assertTrue(feedback.startswith("Not yet."), choice.option_id)
                        self.assertNotIn(correct.text.casefold().rstrip("."), feedback.casefold())
                        self.assertNotIn(resources[activity.explanation_resource_id], feedback)
                # Practice items (even indices) are shown as authored and challenges
                # (odd indices) reversed, so neither stage may fix the answer's place.
                for parity in (0, 1):
                    shown = []
                    for index, activity in enumerate(pack.activities):
                        if activity.choices and index % 2 == parity:
                            choices = activity.choices if parity == 0 else activity.choices[::-1]
                            shown.append(next(i for i, c in enumerate(choices) if c.correct))
                    self.assertGreater(len(set(shown)), 2, (parity, shown))
                entry = []
                for number, activity_id in enumerate(diagnostic["activity_ids"]):
                    choices = activities[activity_id].choices
                    choices = choices if number % 2 == 0 else choices[::-1]
                    entry.append(next(i for i, c in enumerate(choices) if c.correct))
                self.assertGreater(len(set(entry)), 2, entry)
                challenge = {choice.text for choice in activities["data-vs-assumptions.transfer"].choices}
                quiz = {choice.text for choice in activities["data-vs-assumptions.practice"].choices}
                self.assertFalse(challenge & quiz)

    def test_question_copy_keeps_the_definition_row_units_and_causal_conditions(self):
        for profile in ("general", "medical"):
            with self.subTest(profile=profile):
                pack = build(profile)
                resources = {item.resource_id: item.text for item in pack.resources}
                activities = {item.activity_id: item for item in pack.activities}
                setting, row_unit = ("clinic", "patient") if profile == "medical" else ("IT-service", "hour")
                question = activities["variables-and-values.practice"].workbench.prompt
                self.assertEqual(question,
                    "A variable is a feature that can take different values. "
                    f"This {setting} table has one row per {row_unit}. "
                    "Which option names the two recorded variables?")
                for activity in pack.activities:
                    if activity.workbench and activity.workbench.prompt:
                        self.assertTrue(resources[activity.question_resource_id].startswith(
                            activity.workbench.prompt + "\n\n"), activity.activity_id)
                self.assertIn("records alone", resources["not-causation.question.practice"])
                self.assertIn("choose to sleep", resources["integrated.question"])
                self.assertIn("records alone support", resources["integrated.question"])
                self.assertIn("chose whether to attend", resources["m0-final-quiz.03.final.question"])
                self.assertIn("help everyone", resources["m0-final-quiz.03.final.question"])
                self.assertIn("uses random numbers to assign", resources["m0-final-quiz.05.final.question"])
                self.assertIn("was not measured", resources["m0-final-quiz.06.final.question"])
                self.assertIn("Suppose", activities["m0-final-quiz.09"].workbench.prompt)
                self.assertIn("0.40", resources["m0-final-quiz.09.final.question"])
                self.assertIn("0.60", resources["m0-final-quiz.09.final.question"])
                self.assertIn("20 percentage points", resources["m0-final-quiz.09.final.explanation"])
                self.assertIn("not a real-world effect estimate", resources["m0-final-quiz.09.final.explanation"])

    def test_recorded_values_are_shown_as_tables_with_a_short_question(self):
        plan = load_diagnostic_plan(ROOT / "content/causality_m0_diagnostic.json")
        for profile in ("general", "medical"):
            with self.subTest(profile=profile):
                pack = load_content_pack(ROOT / f"content/foundation_{profile}_course_1_7_0.json")
                resources = {item.resource_id: item.text for item in pack.resources}
                for activity in pack.activities:
                    if not activity.choices:
                        continue
                    heading = (activity.workbench.prompt if activity.workbench and activity.workbench.prompt
                               else resources[activity.question_resource_id])
                    self.assertNotIn("->", heading)
                    self.assertNotRegex(heading, r"\d+[^\d.]*[;:] \d", activity.activity_id)
                for activity_id in ("variables-and-values.practice", "variables-and-values.transfer",
                                    "observed-association.practice", "observed-association.transfer"):
                    workbench = next(a for a in pack.activities if a.activity_id == activity_id).workbench
                    self.assertEqual(workbench.stage, "investigate")
                    self.assertGreaterEqual(len(workbench.tables[0].rows), 3)
                    self.assertNotRegex(workbench.prompt, r"\d")
                diagnostic = DiagnosticSession(pack, plan)
                diagnostic.start()
                self.assertIsNotNone(diagnostic.view()["workbench"])
                for activity_id in ("basic-dag-language.practice", "basic-dag-language.transfer", "m0-final-quiz.08"):
                    activity = next(a for a in pack.activities if a.activity_id == activity_id)
                    stem = (activity.workbench.prompt if activity.workbench
                            else resources[activity.question_resource_id])
                    self.assertRegex(stem, r"`[^`]+ → [^`]+`", "graph chains read as one marked unit")
                self.assertFalse(any(" -> " in text or " <- " in text for text in resources.values()))
                final = next(a for a in pack.activities if a.activity_id == "m0-final-quiz.09")
                self.assertEqual(final.workbench.tables[0].rows[1][1], "0.60")
                self.assertNotIn("0.60", final.workbench.prompt)

    def test_scene_distinguishes_hypothesis_reference_and_filtering(self):
        for profile in ("general", "medical"):
            pack = build(profile)
            scene = pack.causal_scenes[0]
            resources = {item.resource_id: item.text for item in pack.resources}
            self.assertEqual(sum(row.arrivals for row in scene.observed_records), 240)
            self.assertEqual(sum(row.arrivals for row in scene.intervention.result_records), 240)
            self.assertIn("server calculates", resources[scene.intervention_resource_id])
            self.assertIn("does not change that reference world", resources[scene.intervention_resource_id])
            self.assertIn("100%", resources[scene.result_resource_id])
            self.assertIn("40%", resources[scene.direct_explanation_resource_id])
            self.assertIn("not 240 different days", resources[scene.records_resource_id])
            self.assertEqual(scene.simulation.population_size, 240)
            self.assertEqual(scene.simulation.root_yes_count, 96)
            self.assertEqual(scene.simulation.minimum_hypotheses, 2)
            self.assertEqual(scene.simulation.reference_hypothesis_id, "rain-common-cause")

    def test_final_answers_are_evaluated_individually_without_granting_missing_course_credit(self):
        for profile in ("general", "medical"):
            with self.subTest(profile=profile):
                pack = build(profile)
                final = tuple(a for a in pack.activities
                              if a.workbench and a.workbench.stage == "capstone")
                controller = DemoController(pack)
                controller.start(session_id=f"final.{profile}", route_scope="preferred",
                                 preferred_activity_ids=tuple(a.activity_id for a in final))
                rejected = controller.respond(request_id=f"final.{profile}.wrong",
                    option_id=next(c.option_id for c in final[0].choices if not c.correct))
                self.assertFalse(rejected["can_continue"])
                self.assertEqual(rejected["completed_activity_ids"], ())
                for index, activity in enumerate(final):
                    self.assertEqual(controller.view()["activity_id"], activity.activity_id)
                    controller.respond(request_id=f"final.{profile}.answer.{index}",
                        option_id=next(c.option_id for c in activity.choices if c.correct))
                    controller.continue_activity(request_id=f"final.{profile}.continue.{index}")
                state = controller.view()
                self.assertEqual(state["status"], "completed")
                self.assertEqual(len(state["completed_activity_ids"]), 9)
                self.assertEqual(state["completed_concept_ids"], ())

    def test_topic_continuation_does_not_pull_final_questions_forward(self):
        for profile in ("general", "medical"):
            with self.subTest(profile=profile):
                pack = build(profile)
                self.assertTrue(all(a.activity_id.startswith("m0-final-quiz.")
                                    for a in pack.activities[-9:]))
                controller = DemoController(pack)
                controller.start(session_id=f"sequence.{profile}")
                for index, activity in enumerate(pack.activities[:2]):
                    self.assertEqual(controller.view()["activity_id"], activity.activity_id)
                    controller.respond(request_id=f"sequence.{profile}.answer.{index}",
                        option_id=next(c.option_id for c in activity.choices if c.correct))
                    controller.continue_activity(request_id=f"sequence.{profile}.continue.{index}")
                self.assertEqual(controller.view()["activity_id"], pack.activities[2].activity_id)


if __name__ == "__main__":
    unittest.main()
