"""Provider-independent tests for the deterministic M0 causal scene core."""

import asyncio
import unittest
from pathlib import Path

from educagent_sdk.causal_scene import (
    OpenRecords,
    RunIntervention,
    SubmitGraph,
    SubmitPrediction,
    SubmitRevision,
    apply_scene_action,
    initial_scene_snapshot,
    legal_scene_action_kinds,
    replay_scene_actions,
    scene_text_projection,
)
from educagent_sdk.contracts import (
    CausalScene,
    CausalSceneAssessment,
    CausalSceneEdge,
    CausalSceneIntervention,
    CausalSceneNode,
    CausalScenePrediction,
    CausalSceneRecord,
    load_content_pack,
)
from educagent_sdk.events import (
    record_causal_scene_action,
    record_causal_scene_evidence,
    record_learner_message,
    LearnerMessage,
    replay,
    select_fixed_policy_move,
    start_attempt,
    start_session,
)
from educagent_sdk.tutor import build_tutor_deps, run_tutor_turn
from pydantic_ai.models import override_allow_model_requests
from pydantic_ai.models.function import FunctionModel
from pydantic_ai.models.test import TestModel
from pydantic_ai import ModelResponse
from pydantic_ai.messages import ToolCallPart


ROOT = Path(__file__).resolve().parents[1]
PACK_PATH = ROOT / "content" / "causality_m0_full.json"


def scene() -> CausalScene:
    return CausalScene(
        scene_id="causality.rain-umbrella",
        title="Umbrellas and wet pavement",
        claim_ids=("scene.rain-umbrella.synthetic-world",),
        hook_resource_id="scene.hook",
        records_resource_id="scene.records",
        model_resource_id="scene.model",
        prediction_resource_id="scene.prediction",
        intervention_resource_id="scene.intervention",
        result_resource_id="scene.result",
        reflection_resource_id="scene.reflection",
        direct_explanation_resource_id="scene.explanation",
        nodes=(
            CausalSceneNode(node_id="rain", label="Rain", initially_visible=False),
            CausalSceneNode(
                node_id="umbrella-carried", label="Umbrella carried", initially_visible=True
            ),
            CausalSceneNode(
                node_id="pavement-wet", label="Pavement wet", initially_visible=True
            ),
        ),
        permitted_edges=(
            CausalSceneEdge(parent_id="umbrella-carried", child_id="pavement-wet"),
            CausalSceneEdge(parent_id="pavement-wet", child_id="umbrella-carried"),
            CausalSceneEdge(parent_id="rain", child_id="umbrella-carried"),
            CausalSceneEdge(parent_id="rain", child_id="pavement-wet"),
        ),
        observed_records=(
            CausalSceneRecord(umbrella_carried="yes", pavement_wet="yes", arrivals=96),
            CausalSceneRecord(umbrella_carried="no", pavement_wet="no", arrivals=144),
        ),
        intervention=CausalSceneIntervention(
            action_id="intervention.umbrella-yes",
            variable_id="umbrella-carried",
            value="yes",
            result_records=(
                CausalSceneRecord(umbrella_carried="yes", pavement_wet="yes", arrivals=96),
                CausalSceneRecord(umbrella_carried="yes", pavement_wet="no", arrivals=144),
            ),
        ),
        predictions=(
            CausalScenePrediction(
                prediction_id="wet-pavement-unchanged", label="No change"
            ),
            CausalScenePrediction(
                prediction_id="wet-pavement-less-often", label="Less often"
            ),
        ),
        assessment=CausalSceneAssessment(
            accepted_edges=(
                CausalSceneEdge(parent_id="rain", child_id="umbrella-carried"),
                CausalSceneEdge(parent_id="rain", child_id="pavement-wet"),
            ),
            hint_resource_ids=("scene.hint",),
            accepted_consequence_resource_id="scene.accepted",
            rejected_consequence_resource_id="scene.rejected",
            rejected_misconception_id="association-proves-cause",
        ),
    )


class CausalSceneTest(unittest.TestCase):
    def _function_turn(
        self,
        events: list,
        pack,
        *,
        request_id: str,
        focus_id: str,
        dialogue_job: str,
        question: str | None = None,
    ):
        deps = build_tutor_deps(events, pack, request_id=request_id)

        def scripted_model(messages, info):
            output = {
                "candidate_id": deps.candidates[0].candidate_id,
                "interaction_focus_id": focus_id,
                "dialogue_job": dialogue_job,
            }
            if question is not None:
                output["socratic_question"] = question
            return ModelResponse(
                parts=[ToolCallPart(info.output_tools[0].name, output)]
            )

        with override_allow_model_requests(False):
            return asyncio.run(
                run_tutor_turn(
                    events,
                    pack,
                    request_id=request_id,
                    model=FunctionModel(scripted_model),
                )
            )

    def test_function_model_covers_the_investigation_and_recovery_loop(self) -> None:
        pack = load_content_pack(PACK_PATH)
        events = []
        start_session(
            events,
            pack,
            session_id="scene.function.loop",
            preferred_activity_ids=("association-is-not-causation.transfer",),
            route_scope="preferred",
        )
        start_attempt(events, pack, attempt_id="scene.function.loop.attempt")

        record_learner_message(
            events,
            pack,
            attempt_id="scene.function.loop.attempt",
            request_id="scene.function.hook",
            message=LearnerMessage(text="Maybe umbrellas make pavement wet."),
        )
        hook = self._function_turn(
            events,
            pack,
            request_id="scene.function.hook",
            focus_id="scene.open-records",
            dialogue_job="orient",
            question="Which records would you inspect before deciding on a direction?",
        )
        self.assertEqual(hook.event.payload.interaction_focus_id, "scene.open-records")

        actions = (
            (
                "records",
                0,
                OpenRecords(),
                "scene.propose-model",
                "elicit",
                "Which arrow would you propose from these records?",
            ),
            (
                "wrong-model",
                1,
                SubmitGraph(
                    edges=(
                        CausalSceneEdge(
                            parent_id="umbrella-carried", child_id="pavement-wet"
                        ),
                    )
                ),
                "scene.elicit-prediction",
                "elicit",
                "What would you predict before the result is revealed?",
            ),
            (
                "prediction",
                2,
                SubmitPrediction(prediction_id="wet-pavement-less-often"),
                "scene.run-intervention",
                "orient",
                "What deliberate change should we inspect next?",
            ),
            (
                "intervention",
                3,
                RunIntervention(intervention_action_id="intervention.umbrella-yes"),
                "scene.interpret-result",
                "interpret",
                None,
            ),
            (
                "revision",
                4,
                SubmitRevision(
                    edges=(
                        CausalSceneEdge(
                            parent_id="umbrella-carried", child_id="pavement-wet"
                        ),
                    )
                ),
                "scene.formal-evidence",
                "consolidate",
                None,
            ),
        )
        for suffix, revision, action, focus_id, job, question in actions:
            request_id = f"scene.function.{suffix}"
            record_causal_scene_action(
                events,
                pack,
                attempt_id="scene.function.loop.attempt",
                request_id=request_id,
                action=action,
                input_revision=revision,
            )
            result = self._function_turn(
                events,
                pack,
                request_id=request_id,
                focus_id=focus_id,
                dialogue_job=job,
                question=question,
            )
            self.assertFalse(result.used_fallback)

        record_learner_message(
            events,
            pack,
            attempt_id="scene.function.loop.attempt",
            request_id="scene.function.clarify",
            message=LearnerMessage(text="What does the intervention result change?"),
        )
        clarification = self._function_turn(
            events,
            pack,
            request_id="scene.function.clarify",
            focus_id="scene.formal-evidence",
            dialogue_job="consolidate",
            question="How does the intervention result compare with your first model?",
        )
        self.assertEqual(clarification.event.payload.move.strategy, "clarify")

        rejected = record_causal_scene_evidence(
            events,
            pack,
            attempt_id="scene.function.loop.attempt",
            request_id="scene.function.rejected-evidence",
        )
        self.assertFalse(rejected.payload.evaluation.accepted)
        recovery = self._function_turn(
            events,
            pack,
            request_id="scene.function.rejected-evidence",
            focus_id="scene.formal-evidence",
            dialogue_job="consolidate",
        )
        self.assertEqual(recovery.event.payload.move.strategy, "socratic_hint")

        record_causal_scene_action(
            events,
            pack,
            attempt_id="scene.function.loop.attempt",
            request_id="scene.function.retry-revision",
            action=SubmitRevision(
                edges=(
                    CausalSceneEdge(
                        parent_id="umbrella-carried", child_id="pavement-wet"
                    ),
                )
            ),
            input_revision=5,
        )
        self._function_turn(
            events,
            pack,
            request_id="scene.function.retry-revision",
            focus_id="scene.formal-evidence",
            dialogue_job="consolidate",
        )
        rejected_again = record_causal_scene_evidence(
            events,
            pack,
            attempt_id="scene.function.loop.attempt",
            request_id="scene.function.rejected-evidence-again",
        )
        self.assertFalse(rejected_again.payload.evaluation.accepted)
        direct = self._function_turn(
            events,
            pack,
            request_id="scene.function.rejected-evidence-again",
            focus_id="scene.formal-evidence",
            dialogue_job="consolidate",
        )
        self.assertEqual(direct.event.payload.move.strategy, "direct_instruction")

        record_causal_scene_action(
            events,
            pack,
            attempt_id="scene.function.loop.attempt",
            request_id="scene.function.recovery-revision",
            action=SubmitRevision(
                edges=(
                    CausalSceneEdge(parent_id="rain", child_id="umbrella-carried"),
                    CausalSceneEdge(parent_id="rain", child_id="pavement-wet"),
                )
            ),
            input_revision=6,
        )
        self._function_turn(
            events,
            pack,
            request_id="scene.function.recovery-revision",
            focus_id="scene.formal-evidence",
            dialogue_job="consolidate",
        )
        accepted = record_causal_scene_evidence(
            events,
            pack,
            attempt_id="scene.function.loop.attempt",
            request_id="scene.function.accepted-evidence",
        )
        self.assertTrue(accepted.payload.evaluation.accepted)
        advanced = self._function_turn(
            events,
            pack,
            request_id="scene.function.accepted-evidence",
            focus_id="scene.formal-evidence",
            dialogue_job="consolidate",
        )
        self.assertEqual(advanced.event.payload.move.strategy, "advance")
        self.assertEqual(replay(events).last_strategy, "advance")

    def test_function_model_records_a_scene_specific_focus(self) -> None:
        pack = load_content_pack(PACK_PATH)
        events = []
        start_session(
            events,
            pack,
            session_id="scene.function.session",
            preferred_activity_ids=("association-is-not-causation.transfer",),
            route_scope="preferred",
        )
        start_attempt(events, pack, attempt_id="scene.function.attempt")
        record_causal_scene_action(
            events,
            pack,
            attempt_id="scene.function.attempt",
            request_id="scene.function.records",
            action=OpenRecords(),
            input_revision=0,
        )
        deps = build_tutor_deps(events, pack, request_id="scene.function.records")
        observed_tools: list[str] = []

        def scripted_model(messages, info):
            observed_tools.extend(tool.name for tool in info.function_tools)
            return ModelResponse(
                parts=[
                    ToolCallPart(
                        info.output_tools[0].name,
                        {
                            "candidate_id": deps.candidates[0].candidate_id,
                            "interaction_focus_id": "scene.open-records",
                            "dialogue_job": "orient",
                            "socratic_question": "Which arrow would you propose from these records?",
                        },
                    )
                ]
            )

        with override_allow_model_requests(False):
            result = asyncio.run(
                run_tutor_turn(
                    events,
                    pack,
                    request_id="scene.function.records",
                    model=FunctionModel(scripted_model),
                )
            )

        self.assertEqual(
            observed_tools,
            ["inspect_scene", "inspect_last_result", "list_legal_focuses"],
        )
        self.assertFalse(result.used_fallback)
        self.assertEqual(result.event.payload.interaction_focus_id, "scene.propose-model")
        self.assertEqual(replay(events).causal_scene_snapshot.phase, "records")

    def test_declared_investigation_replays_to_one_snapshot(self) -> None:
        authored_scene = scene()
        actions = (
            (0, OpenRecords()),
            (
                1,
                SubmitGraph(
                    edges=(
                        CausalSceneEdge(
                            parent_id="umbrella-carried", child_id="pavement-wet"
                        ),
                    )
                ),
            ),
            (2, SubmitPrediction(prediction_id="wet-pavement-less-often")),
            (3, RunIntervention(intervention_action_id="intervention.umbrella-yes")),
            (
                4,
                SubmitRevision(
                    edges=(
                        CausalSceneEdge(parent_id="rain", child_id="umbrella-carried"),
                        CausalSceneEdge(parent_id="rain", child_id="pavement-wet"),
                    ),
                    reflection="The recorded association did not settle the causal direction.",
                ),
            ),
        )
        snapshot = replay_scene_actions(authored_scene, actions)

        self.assertEqual(snapshot.phase, "revision")
        self.assertEqual(snapshot.revision, 5)
        self.assertEqual(snapshot.prediction_id, "wet-pavement-less-often")
        self.assertEqual(snapshot.intervention_action_id, "intervention.umbrella-yes")
        self.assertIn("144 arrival records", scene_text_projection(authored_scene, snapshot))

    def test_record_totals_and_filter_comparison_only_follow_the_reveal(self) -> None:
        authored_scene = scene()
        snapshot = initial_scene_snapshot(authored_scene)
        hidden = scene_text_projection(authored_scene, snapshot)
        self.assertNotIn("240", hidden)
        self.assertNotIn("96", hidden)
        self.assertNotIn("144", hidden)
        actions = (
            OpenRecords(),
            SubmitGraph(edges=(CausalSceneEdge(
                parent_id="umbrella-carried", child_id="pavement-wet",
            ),)),
            SubmitPrediction(prediction_id="wet-pavement-unchanged"),
        )
        for action in actions:
            snapshot = apply_scene_action(
                authored_scene, snapshot, action, input_revision=snapshot.revision,
            )
            visible = scene_text_projection(authored_scene, snapshot)
            self.assertIn("Observed records: 240 arrival records total", visible)
            self.assertNotIn("Intervention result:", visible)
            self.assertNotIn("Population comparison:", visible)
            self.assertNotIn("Filtering the original records", visible)
            self.assertNotIn("umbrella carried yes, pavement wet no, 144", visible)
        snapshot = apply_scene_action(
            authored_scene, snapshot,
            RunIntervention(intervention_action_id=authored_scene.intervention.action_id),
            input_revision=snapshot.revision,
        )
        visible = scene_text_projection(authored_scene, snapshot)
        self.assertIn("Intervention result: 240 arrival records total", visible)
        self.assertIn("240 arrival records before; 240 after", visible)
        self.assertIn("would retain 96 arrival records", visible)
        self.assertIn("umbrella carried yes, pavement wet no, 144 arrival records", visible)

    def test_projection_record_totals_are_derived_from_the_authored_rows(self) -> None:
        authored_scene = scene()
        counts = (7, 11)
        authored_scene = authored_scene.model_copy(update={
            "observed_records": tuple(
                row.model_copy(update={"arrivals": count})
                for row, count in zip(authored_scene.observed_records, counts)
            ),
            "intervention": authored_scene.intervention.model_copy(update={
                "result_records": tuple(
                    row.model_copy(update={"arrivals": count})
                    for row, count in zip(authored_scene.intervention.result_records, counts)
                ),
            }),
        })
        snapshot = replay_scene_actions(authored_scene, (
            (0, OpenRecords()),
            (1, SubmitGraph(edges=(CausalSceneEdge(
                parent_id="umbrella-carried", child_id="pavement-wet",
            ),))),
            (2, SubmitPrediction(prediction_id="wet-pavement-unchanged")),
            (3, RunIntervention(intervention_action_id=authored_scene.intervention.action_id)),
        ))
        visible = scene_text_projection(authored_scene, snapshot)
        self.assertIn("Observed records: 18 arrival records total", visible)
        self.assertIn("Intervention result: 18 arrival records total", visible)
        self.assertIn("18 arrival records before; 18 after", visible)
        self.assertIn("would retain 7 arrival records", visible)
        self.assertNotIn("240", visible)
        self.assertNotIn("96", visible)

    def test_actions_are_phase_bound_and_revision_bound(self) -> None:
        authored_scene = scene()
        snapshot = initial_scene_snapshot(authored_scene)
        with self.assertRaisesRegex(ValueError, "not legal"):
            apply_scene_action(
                authored_scene,
                snapshot,
                SubmitPrediction(prediction_id="wet-pavement-unchanged"),
                input_revision=0,
            )
        snapshot = apply_scene_action(
            authored_scene, snapshot, OpenRecords(), input_revision=0
        )
        with self.assertRaisesRegex(ValueError, "stale revision"):
            apply_scene_action(authored_scene, snapshot, OpenRecords(), input_revision=0)

    def test_unknown_and_cyclic_graphs_are_rejected(self) -> None:
        authored_scene = scene()
        snapshot = apply_scene_action(
            authored_scene, initial_scene_snapshot(authored_scene), OpenRecords(), input_revision=0
        )
        with self.assertRaisesRegex(ValueError, "undeclared edge"):
            apply_scene_action(
                authored_scene,
                snapshot,
                SubmitGraph(
                    edges=(
                        CausalSceneEdge(parent_id="rain", child_id="pavement-wet"),
                        CausalSceneEdge(parent_id="pavement-wet", child_id="rain"),
                    )
                ),
                input_revision=1,
            )
        with self.assertRaisesRegex(ValueError, "acyclic"):
            apply_scene_action(
                authored_scene,
                snapshot,
                SubmitGraph(
                    edges=(
                        CausalSceneEdge(parent_id="umbrella-carried", child_id="pavement-wet"),
                        CausalSceneEdge(parent_id="pavement-wet", child_id="umbrella-carried"),
                    )
                ),
                input_revision=1,
            )

    def test_only_one_action_is_legal_per_scene_phase(self) -> None:
        authored_scene = scene()
        snapshot = initial_scene_snapshot(authored_scene)
        self.assertEqual(legal_scene_action_kinds(snapshot), ("open_records",))
        snapshot = apply_scene_action(
            authored_scene, snapshot, OpenRecords(), input_revision=0
        )
        self.assertEqual(legal_scene_action_kinds(snapshot), ("submit_graph",))

    def test_scene_actions_replay_without_awarding_evidence(self) -> None:
        pack = load_content_pack(PACK_PATH)
        events = []
        start_session(
            events,
            pack,
            session_id="scene.events.session",
            preferred_activity_ids=("association-is-not-causation.transfer",),
            route_scope="preferred",
        )
        start_attempt(events, pack, attempt_id="scene.events.attempt")
        state = replay(events)
        self.assertEqual(state.causal_scene_snapshot.phase, "hook")
        with self.assertRaisesRegex(ValueError, "complete the causal-scene revision"):
            record_causal_scene_evidence(
                events,
                pack,
                attempt_id="scene.events.attempt",
                request_id="scene.events.too-early",
            )
        for request_id, revision, action in (
            ("scene.events.records", 0, OpenRecords()),
            (
                "scene.events.graph",
                1,
                SubmitGraph(
                    edges=(
                        CausalSceneEdge(
                            parent_id="umbrella-carried", child_id="pavement-wet"
                        ),
                    )
                ),
            ),
            ("scene.events.prediction", 2, SubmitPrediction(prediction_id="wet-pavement-less-often")),
            ("scene.events.intervention", 3, RunIntervention(intervention_action_id="intervention.umbrella-yes")),
            (
                "scene.events.revision",
                4,
                SubmitRevision(
                    edges=(
                        CausalSceneEdge(parent_id="rain", child_id="umbrella-carried"),
                        CausalSceneEdge(parent_id="rain", child_id="pavement-wet"),
                    )
                ),
            ),
        ):
            record_causal_scene_action(
                events,
                pack,
                attempt_id="scene.events.attempt",
                request_id=request_id,
                action=action,
                input_revision=revision,
            )
            deps = build_tutor_deps(events, pack, request_id=request_id)
            output = {
                "candidate_id": deps.candidates[0].candidate_id,
                "interaction_focus_id": deps.legal_interaction_focus_ids[0],
                "dialogue_job": {
                    "scene.propose-model": "elicit",
                    "scene.elicit-prediction": "elicit",
                    "scene.run-intervention": "orient",
                    "scene.interpret-result": "interpret",
                    "scene.formal-evidence": "consolidate",
                }[deps.legal_interaction_focus_ids[0]],
            }
            if deps.candidates[0].move.strategy == "elicit":
                output["socratic_question"] = {
                    "scene.propose-model": "Which arrow would you propose from these records?",
                    "scene.elicit-prediction": "What would you predict before the result is revealed?",
                    "scene.run-intervention": "What deliberate change should we inspect next?",
                }[deps.legal_interaction_focus_ids[0]]
            with override_allow_model_requests(False):
                asyncio.run(
                    run_tutor_turn(
                        events,
                        pack,
                        request_id=request_id,
                        model=TestModel(custom_output_args=output),
                    )
                )
            self.assertEqual(
                events[-1].payload.interaction_focus_id,
                deps.legal_interaction_focus_ids[0],
            )

        state = replay(events)
        self.assertEqual(state.causal_scene_snapshot.phase, "revision")
        self.assertIsNone(state.last_evaluation)
        response = record_causal_scene_evidence(
            events,
            pack,
            attempt_id="scene.events.attempt",
            request_id="scene.events.transfer",
        )
        self.assertEqual(
            response.payload.evidence.prediction_id, "wet-pavement-less-often"
        )
        self.assertTrue(response.payload.evaluation.accepted)
        select_fixed_policy_move(events, pack, request_id="scene.events.transfer")
        self.assertEqual(replay(events).last_strategy, "advance")


if __name__ == "__main__":
    unittest.main()
