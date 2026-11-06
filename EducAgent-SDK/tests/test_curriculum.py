"""Full M0 curriculum and replay-derived status contracts."""

import unittest
from pathlib import Path

from pydantic_ai.models import override_allow_model_requests
from pydantic_ai.models.test import TestModel

from educagent_sdk.causal_scene import (
    OpenRecords,
    RunIntervention,
    SubmitGraph,
    SubmitPrediction,
    SubmitRevision,
    dialogue_job_for_scene_focus,
)
from educagent_sdk.contracts import CausalSceneEdge
from educagent_sdk.demo import DemoController
from educagent_sdk.events import record_causal_scene_action, record_causal_scene_evidence
from educagent_sdk import (
    ClassificationEvidence,
    build_tutor_deps,
    close_attempt,
    complete_session,
    load_content_pack,
    record_classification_response,
    replay,
    run_tutor_turn,
    start_attempt,
    start_session,
    validate_release,
)


ROOT = Path(__file__).resolve().parents[1]
PACK_PATH = ROOT / "content" / "causality_m0_full.json"


class FullM0CurriculumTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.pack = load_content_pack(PACK_PATH)
        self.events = []
        start_session(self.events, self.pack, session_id="m0.session.01")

    def test_single_integrated_choice_has_only_its_declared_evidence_scope(self) -> None:
        self.assertEqual(self.pack.version, "1.1.0")
        integrated = next(
            activity for activity in self.pack.activities
            if activity.activity_id == "m0-integrated-transfer.01"
        )
        self.assertEqual(integrated.concept_id, "association-is-not-causation")
        self.assertEqual(integrated.covered_concept_ids, ())
        for concept in self.pack.concepts:
            self.assertEqual(concept.m1_ready_activity_ids, ())
            if concept.concept_id != integrated.concept_id:
                self.assertNotIn(integrated.activity_id, concept.completion_activity_ids)

    def test_delayed_choice_does_not_award_nine_concepts_or_advanced_readiness(self) -> None:
        delayed = load_content_pack(ROOT / "content" / "causality_m0_delayed_transfer.json")
        validate_release(delayed)
        self.assertEqual(delayed.version, "1.1.0")
        self.assertEqual(len(delayed.concepts), 1)
        self.assertEqual(delayed.activities[0].covered_concept_ids, ())
        self.assertIn("CC BY-NC-ND 4.0", delayed.sources[0].rights)
        self.assertIn("/by-nc-nd/4.0/", delayed.sources[0].rights)
        demo = DemoController(delayed)
        demo.start()
        demo.respond(request_id="delayed.check", option_id="delayed.association-only")
        completed = demo.continue_activity(request_id="delayed.continue")
        self.assertEqual(completed["completed_concept_ids"], ("association-is-not-causation",))
        self.assertEqual(completed["m1_ready_concept_ids"], ())

    def test_scene_question_and_assessment_share_the_supplied_synthetic_context(self) -> None:
        resources = {resource.resource_id: resource.text for resource in self.pack.resources}
        activity = next(item for item in self.pack.activities if item.causal_scene_id)
        authored_scene = self.pack.causal_scenes[0]
        question = resources[activity.question_resource_id]
        self.assertIn("umbrella", question)
        self.assertNotIn("help pages", question)
        reflection = resources[authored_scene.reflection_resource_id]
        self.assertIn("does not uniquely identify", reflection)
        self.assertIn("supplied simulator assumptions", reflection)
        self.assertIn("no other direct arrows", reflection)
        self.assertIn("supplied simulator assumptions", resources[
            authored_scene.assessment.accepted_consequence_resource_id
        ])
        self.assertNotEqual(
            authored_scene.assessment.rejected_misconception_id,
            "association-proves-cause",
        )

    def test_reported_transfer_scenarios_have_local_images(self) -> None:
        expected = {
            "observation-vs-intervention.transfer": "focus-mode-observation.png",
            "data-vs-assumptions.transfer": "help-pages-bug-reports.png",
        }
        for activity_id, filename in expected.items():
            activity = next(
                item for item in self.pack.activities if item.activity_id == activity_id
            )
            self.assertIsNotNone(activity.scenario_image)
            assert activity.scenario_image is not None
            self.assertEqual(Path(activity.scenario_image.path).name, filename)
            self.assertTrue((ROOT / "web" / "public" / activity.scenario_image.path).is_file())

    def test_world_model_and_assumptions_practice_use_distinct_images(self) -> None:
        activities = {
            item.activity_id: item
            for item in self.pack.activities
            if item.activity_id in {"world-data-model.practice", "data-vs-assumptions.practice"}
        }
        world_image = activities["world-data-model.practice"].scenario_image
        assumptions_image = activities["data-vs-assumptions.practice"].scenario_image
        self.assertIsNotNone(world_image)
        self.assertIsNotNone(assumptions_image)
        assert world_image is not None and assumptions_image is not None
        self.assertNotEqual(world_image.path, assumptions_image.path)
        self.assertTrue((ROOT / "web" / "public" / assumptions_image.path).is_file())

    async def choose_first(self, request_id: str):
        deps = build_tutor_deps(self.events, self.pack, request_id=request_id)
        output = {"candidate_id": deps.candidates[0].candidate_id}
        if deps.legal_interaction_focus_ids:
            focus_id = deps.legal_interaction_focus_ids[0]
            output.update(
                {
                    "interaction_focus_id": focus_id,
                    "dialogue_job": dialogue_job_for_scene_focus(focus_id),
                }
            )
        with override_allow_model_requests(False):
            return await run_tutor_turn(
                self.events,
                self.pack,
                request_id=request_id,
                model=TestModel(
                    custom_output_args=output
                ),
            )

    async def test_full_curriculum_is_grounded_and_completes_through_the_tutor(self) -> None:
        report = validate_release(self.pack)
        self.assertEqual(report.unused_resource_ids, ())
        self.assertEqual(len(self.pack.concepts), 9)
        self.assertEqual(len(self.pack.activities), 19)

        for ordinal, activity in enumerate(self.pack.activities, start=1):
            attempt_id = f"m0.attempt.{ordinal}"
            start_attempt(self.events, self.pack, attempt_id=attempt_id)
            if activity.causal_scene_id is not None:
                for request_id, revision, action in (
                    ("records", 0, OpenRecords()),
                    (
                        "model",
                        1,
                        SubmitGraph(
                            edges=(
                                CausalSceneEdge(
                                    parent_id="umbrella-carried",
                                    child_id="pavement-wet",
                                ),
                            )
                        ),
                    ),
                    ("prediction", 2, SubmitPrediction(prediction_id="wet-pavement-less-often")),
                    ("intervention", 3, RunIntervention(intervention_action_id="intervention.umbrella-yes")),
                    (
                        "revision",
                        4,
                        SubmitRevision(
                            edges=(
                                CausalSceneEdge(
                                    parent_id="rain", child_id="umbrella-carried"
                                ),
                                CausalSceneEdge(
                                    parent_id="rain", child_id="pavement-wet"
                                ),
                            )
                        ),
                    ),
                ):
                    record_causal_scene_action(
                        self.events,
                        self.pack,
                        attempt_id=attempt_id,
                        request_id=f"m0.scene.{ordinal}.{request_id}",
                        input_revision=revision,
                        action=action,
                    )
                    await self.choose_first(f"m0.scene.{ordinal}.{request_id}")
                response = record_causal_scene_evidence(
                    self.events,
                    self.pack,
                    attempt_id=attempt_id,
                    request_id=f"m0.scene.{ordinal}.evidence",
                )
                self.assertTrue(response.payload.evaluation.accepted)
                advanced = await self.choose_first(f"m0.scene.{ordinal}.evidence")
                self.assertEqual(advanced.event.payload.move.strategy, "advance")
                close_attempt(
                    self.events,
                    self.pack,
                    attempt_id=attempt_id,
                    status="completed",
                )
                continue
            correct = next(choice for choice in activity.choices if choice.correct)
            if activity.requires_revision:
                incorrect = next(choice for choice in activity.choices if not choice.correct)
                original = record_classification_response(
                    self.events,
                    self.pack,
                    attempt_id=attempt_id,
                    request_id=f"m0.request.{ordinal}.original",
                    evidence=ClassificationEvidence(
                        activity_id=activity.activity_id,
                        classification_id=incorrect.option_id,
                        artifact_id=f"m0.artifact.{ordinal}",
                    ),
                    curriculum_requirements_met=True,
                )
                reflected = await self.choose_first(f"m0.request.{ordinal}.original")
                self.assertEqual(reflected.event.payload.move.strategy, "reflect")
                record_classification_response(
                    self.events,
                    self.pack,
                    attempt_id=attempt_id,
                    request_id=f"m0.request.{ordinal}.revision",
                    evidence=ClassificationEvidence(
                        activity_id=activity.activity_id,
                        classification_id=correct.option_id,
                        artifact_id=f"m0.artifact.{ordinal}",
                        revises_evidence_event_id=original.event_id,
                    ),
                    curriculum_requirements_met=True,
                )
                advanced = await self.choose_first(f"m0.request.{ordinal}.revision")
            else:
                self.assertTrue(activity.is_transfer)
                record_classification_response(
                    self.events,
                    self.pack,
                    attempt_id=attempt_id,
                    request_id=f"m0.request.{ordinal}.transfer",
                    evidence=ClassificationEvidence(
                        activity_id=activity.activity_id,
                        classification_id=correct.option_id,
                        artifact_id=f"m0.artifact.{ordinal}",
                    ),
                    curriculum_requirements_met=True,
                )
                advanced = await self.choose_first(f"m0.request.{ordinal}.transfer")
            self.assertEqual(advanced.event.payload.move.strategy, "advance")
            close_attempt(
                self.events,
                self.pack,
                attempt_id=attempt_id,
                status="completed",
            )

        completed = complete_session(self.events, self.pack)
        state = replay(self.events)
        concept_ids = tuple(concept.concept_id for concept in self.pack.concepts)
        self.assertEqual(state.completed_concept_ids, concept_ids)
        self.assertEqual(state.m1_ready_concept_ids, ())
        self.assertEqual(completed.payload.completed_concept_ids, concept_ids)
        self.assertEqual(completed.payload.m1_ready_concept_ids, ())
        self.assertEqual(replay(tuple(self.events)), state)


if __name__ == "__main__":
    unittest.main()
