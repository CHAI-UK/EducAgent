"""Offline contracts for the S39 student-model/reference-world investigation."""

import asyncio
import hashlib
import json
import unittest
from pathlib import Path

from pydantic import TypeAdapter, ValidationError
from pydantic_ai import ModelResponse
from pydantic_ai.messages import TextPart, ToolCallPart
from pydantic_ai.models import override_allow_model_requests
from pydantic_ai.models.function import FunctionModel

from educagent_sdk.causal_scene import (
    CausalSceneAction, apply_scene_action, initial_scene_snapshot, legal_scene_action_kinds,
    dialogue_job_for_scene_focus,
)
from educagent_sdk.contracts import load_content_pack
from educagent_sdk.demo import DemoController
from educagent_sdk.events import (
    LearningEvent, append_teaching_move, record_causal_scene_evidence, replay, select_fixed_policy_move,
)
from educagent_sdk.umbrella_simulation import (
    compute_records, hypothesis_edges, public_simulation_view,
)
from educagent_sdk.tutor import MAX_TUTOR_CONTEXT_CHARS, build_tutor_deps, run_tutor_turn
from educagent_sdk.web_demo import _handle_command


ROOT = Path(__file__).resolve().parents[1]
MISSION_ID = "association-is-not-causation.transfer"
ADAPTER = TypeAdapter(CausalSceneAction)


def current_pack(profile="general"):
    return load_content_pack(ROOT / f"content/foundation_{profile}_course_1_6_0.json")


def controller(profile="general", *, historical=False):
    version = "1_5_0" if historical else "1_6_0"
    pack = load_content_pack(ROOT / f"content/foundation_{profile}_course_{version}.json")
    demo = DemoController(pack)
    demo.start(session_id=f"dynamic.{profile}.{version}",
               preferred_activity_ids=(MISSION_ID,), route_scope="preferred")
    return demo


def act(demo, kind, *, request_id=None, input_revision=None, **fields):
    snapshot = demo.view()["causal_scene"]
    revision = snapshot["revision"] if input_revision is None else input_revision
    action = ADAPTER.validate_json(json.dumps({"kind": kind, **fields}))
    command_id = request_id or f"dynamic.action.{len(demo.events)}"
    demo.submit_scene_action(request_id=command_id, input_revision=revision, action=action)
    if replay(demo.events).phase == "awaiting_move":
        select_fixed_policy_move(demo.events, demo.pack, request_id=command_id)
    return demo.view()


def run_hypothesis(demo, hypothesis_id):
    act(demo, "select_hypothesis", hypothesis_id=hypothesis_id)
    act(demo, "submit_prediction", prediction_id="wet-pavement-unchanged")
    return act(demo, "run_intervention",
               intervention_action_id=demo.pack.causal_scenes[0].intervention.action_id)


def pure_action(scene, snapshot, kind, **fields):
    action = ADAPTER.validate_json(json.dumps({"kind": kind, **fields}))
    return apply_scene_action(scene, snapshot, action, input_revision=snapshot.revision)


def pure_run(scene, snapshot, hypothesis_id):
    snapshot = pure_action(scene, snapshot, "select_hypothesis", hypothesis_id=hypothesis_id)
    snapshot = pure_action(scene, snapshot, "submit_prediction", prediction_id="wet-pavement-unchanged")
    return pure_action(scene, snapshot, "run_intervention",
                       intervention_action_id=scene.intervention.action_id)


class DynamicUmbrellaTest(unittest.TestCase):
    def test_previous_scored_packs_are_frozen(self):
        expected = {
            "foundation_general_course_1_5_0.json": "bab613c25ccfa04648850a7f9a8ee32cc2296be9d47d6380bb4c330bc183c07b",
            "foundation_medical_course_1_5_0.json": "86e4ce9d4b776a6ee73aceca1cd67243d2047e7c8495be56bb6e25c21c013677",
        }
        # The previous release remains independently loadable, not migrated or
        # rewritten by opening the new version.
        before = {name: (ROOT / "content" / name).read_bytes() for name in expected}
        for name, checksum in expected.items():
            self.assertEqual(hashlib.sha256(before[name]).hexdigest(), checksum)
        for profile in ("general", "medical"):
            with self.subTest(profile=profile):
                new = current_pack(profile)
                old = load_content_pack(ROOT / f"content/foundation_{profile}_course_1_5_0.json")
                self.assertEqual(new.version, "1.6.0")
                self.assertEqual(old.version, "1.5.0")
                self.assertEqual(tuple(c.concept_id for c in new.concepts),
                                 tuple(c.concept_id for c in old.concepts))
                self.assertEqual(tuple(a.activity_id for a in new.activities),
                                 tuple(a.activity_id for a in old.activities))
                for previous, current in zip(old.activities, new.activities):
                    self.assertEqual([(c.option_id, c.correct) for c in previous.choices],
                                     [(c.option_id, c.correct) for c in current.choices])
                self.assertIsNone(old.causal_scenes[0].simulation)
                self.assertIsNotNone(new.causal_scenes[0].simulation)
        for name, raw in before.items():
            self.assertEqual((ROOT / "content" / name).read_bytes(), raw)

    def test_declared_mechanisms_share_observations_but_not_do_predictions(self):
        for profile in ("general", "medical"):
            scene = current_pack(profile).causal_scenes[0]
            for hypothesis_id, expected_wet in (
                ("umbrella-causes-wet", 240),
                ("wet-causes-umbrella", 96),
                ("rain-common-cause", 96),
            ):
                with self.subTest(profile=profile, hypothesis=hypothesis_id):
                    observed = compute_records(scene, hypothesis_id, intervene=False)
                    self.assertEqual(sum(row.arrivals for row in observed), 240)
                    self.assertEqual(sum(row.arrivals for row in observed if row.pavement_wet == "yes"), 96)
                    self.assertTrue(all(row.umbrella_carried == row.pavement_wet
                                        for row in observed if row.arrivals))
                    assigned = compute_records(scene, hypothesis_id, intervene=True)
                    self.assertEqual(sum(row.arrivals for row in assigned), 240)
                    self.assertEqual(sum(row.arrivals for row in assigned if row.pavement_wet == "yes"), expected_wet)
                    self.assertTrue(all(row.umbrella_carried == "yes"
                                        for row in assigned if row.arrivals))
                    self.assertEqual(assigned, compute_records(scene, hypothesis_id, intervene=True))

    def test_authoring_rejects_population_observation_and_reference_mismatches(self):
        original = current_pack().causal_scenes[0].model_dump(mode="json")
        from educagent_sdk.contracts import CausalScene
        for field, value in (("population_size", 241), ("root_yes_count", 97),
                             ("reference_hypothesis_id", "umbrella-causes-wet")):
            with self.subTest(field=field):
                changed = json.loads(json.dumps(original))
                changed["simulation"][field] = value
                with self.assertRaises(ValidationError):
                    CausalScene.model_validate_json(json.dumps(changed))

    def test_transport_never_accepts_a_client_computed_result(self):
        for result_field in ("result", "runs", "student_records", "reference_records"):
            with self.subTest(field=result_field):
                with self.assertRaises(ValidationError):
                    ADAPTER.validate_json(json.dumps({
                        "kind": "run_intervention",
                        "intervention_action_id": "intervention.umbrella-yes",
                        result_field: [{"arrivals": 240, "pavement_wet": "no"}],
                    }))

    def test_run_results_and_edges_are_frozen_across_subsequent_selections(self):
        scene = current_pack().causal_scenes[0]
        snapshot = pure_action(scene, initial_scene_snapshot(scene), "open_records")
        snapshot = pure_run(scene, snapshot, "umbrella-causes-wet")
        original_run = snapshot.simulation_runs[0].model_dump_json()
        snapshot = pure_run(scene, snapshot, "wet-causes-umbrella")
        self.assertEqual(snapshot.simulation_runs[0].model_dump_json(), original_run)
        self.assertEqual(snapshot.simulation_runs[0].hypothesis_edges,
                         hypothesis_edges("umbrella-causes-wet"))
        self.assertNotEqual(snapshot.simulation_runs[0].hypothesis_result_records,
                            snapshot.simulation_runs[1].hypothesis_result_records)
        self.assertEqual(snapshot.simulation_runs[0].reference_result_records,
                         snapshot.simulation_runs[1].reference_result_records)
        self.assertIsNone(snapshot.reflection)
        self.assertEqual(snapshot.simulation_runs[0].run_id, 1)
        self.assertEqual(snapshot.simulation_runs[1].run_id, 2)

    def test_public_results_and_reference_assumptions_have_separate_reveal_boundaries(self):
        scene = current_pack().causal_scenes[0]
        snapshot = initial_scene_snapshot(scene)
        public = public_simulation_view(scene, snapshot)
        self.assertEqual(public["hypotheses"], [])
        self.assertEqual(public["runs"], [])
        self.assertIsNone(public["reference_assumptions"])
        self.assertIsNone(public["reference_edges"])
        snapshot = pure_action(scene, snapshot, "open_records")
        public = public_simulation_view(scene, snapshot)
        self.assertEqual(len(public["hypotheses"]), 3)
        self.assertEqual(public["runs"], [])
        snapshot = pure_run(scene, snapshot, "umbrella-causes-wet")
        public = public_simulation_view(scene, snapshot)
        self.assertEqual(public["runs"][0]["hypothesis_wet_pct"], 100)
        self.assertEqual(public["runs"][0]["reference_wet_pct"], 40)
        self.assertFalse(public["ready_for_revision"])
        self.assertIsNone(public["reference_assumptions"])
        self.assertIsNone(public["reference_edges"])
        self.assertNotIn("reference_hypothesis_id", public)
        snapshot = pure_run(scene, snapshot, "wet-causes-umbrella")
        public = public_simulation_view(scene, snapshot)
        self.assertEqual(public["distinct_hypotheses_tried"], 2)
        self.assertTrue(public["ready_for_revision"])
        self.assertTrue(public["reference_assumptions"])
        self.assertEqual(public["reference_edges"],
                         [edge.model_dump() for edge in scene.assessment.accepted_edges])

    def test_arbitrary_dag_cannot_silently_invent_equations(self):
        scene = current_pack().causal_scenes[0]
        snapshot = pure_action(scene, initial_scene_snapshot(scene), "open_records")
        with self.assertRaisesRegex(ValueError, "declared hypothesis"):
            pure_action(scene, snapshot, "submit_graph", edges=[{
                "parent_id": "rain", "child_id": "umbrella-carried",
            }])
        matched = pure_action(scene, snapshot, "submit_graph", edges=[
            edge.model_dump() for edge in hypothesis_edges("wet-causes-umbrella")
        ])
        self.assertEqual(matched.hypothesis_id, "wet-causes-umbrella")

    def test_historical_scene_does_not_gain_repeat_or_selection_permissions(self):
        scene = controller(historical=True).pack.causal_scenes[0]
        snapshot = pure_action(scene, initial_scene_snapshot(scene), "open_records")
        self.assertEqual(legal_scene_action_kinds(snapshot), ("submit_graph",))
        with self.assertRaises(ValueError):
            pure_action(scene, snapshot, "select_hypothesis", hypothesis_id="rain-common-cause")
        snapshot = pure_action(scene, snapshot, "submit_graph", edges=[
            edge.model_dump() for edge in hypothesis_edges("umbrella-causes-wet")
        ])
        snapshot = pure_action(scene, snapshot, "submit_prediction", prediction_id="wet-pavement-unchanged")
        snapshot = pure_action(scene, snapshot, "run_intervention",
                               intervention_action_id=scene.intervention.action_id)
        self.assertEqual(legal_scene_action_kinds(snapshot), ("submit_revision",))
        with self.assertRaises(ValueError):
            pure_action(scene, snapshot, "submit_prediction", prediction_id="wet-pavement-unchanged")
        self.assertEqual(snapshot.simulation_runs, ())

    def test_unknown_hypothesis_and_stale_edit_leave_the_trace_unchanged(self):
        demo = controller()
        act(demo, "open_records")
        before = tuple(event.model_dump_json() for event in demo.events)
        with self.assertRaises(ValueError):
            act(demo, "select_hypothesis", hypothesis_id="unknown-model")
        self.assertEqual(tuple(event.model_dump_json() for event in demo.events), before)
        selected = demo.pack.causal_scenes[0].simulation.hypotheses[0].hypothesis_id
        with self.assertRaisesRegex(ValueError, "stale revision"):
            act(demo, "select_hypothesis", hypothesis_id=selected, input_revision=0)
        self.assertEqual(tuple(event.model_dump_json() for event in demo.events), before)

    def test_http_command_decodes_catalog_selection_and_rejects_spoofed_results(self):
        demo = controller()
        calls = []

        def select(_messages, info):
            request_id = demo.events[-1].request_id
            deps = build_tutor_deps(demo.events, demo.pack, request_id=request_id)
            calls.append(request_id)
            output = {"candidate_id": deps.candidates[0].candidate_id}
            if deps.candidates[0].move.strategy == "elicit":
                output["socratic_question"] = {
                    "scene.propose-model": "Which declared explanation would you like to test?",
                    "scene.elicit-prediction": "What would you predict for wet pavement before the test?",
                }[deps.legal_interaction_focus_ids[0]]
            return ModelResponse(parts=[ToolCallPart(info.output_tools[0].name, output)])

        with override_allow_model_requests(False):
            for index, action in enumerate((
                {"kind": "open_records"},
                {"kind": "select_hypothesis", "hypothesis_id": "umbrella-causes-wet"},
            )):
                state = asyncio.run(_handle_command(demo, "/api/scene-action", {
                    "request_id": f"dynamic.http.{index}", "input_revision": index,
                    "action": action,
                }, model=FunctionModel(select)))
            self.assertEqual(state["causal_scene"]["simulation"]["selected_hypothesis_id"],
                             "umbrella-causes-wet")
            self.assertEqual(len(calls), 0, "Dynamic button actions use authored feedback without model calls.")
            count = len(demo.events)
            with self.assertRaises(ValidationError):
                asyncio.run(_handle_command(demo, "/api/scene-action", {
                    "request_id": "dynamic.http.spoof", "input_revision": 2,
                    "action": {"kind": "run_intervention",
                        "intervention_action_id": "intervention.umbrella-yes",
                        "reference_result_records": [{"arrivals": 0}]},
                }, model=FunctionModel(select)))
            self.assertEqual(len(demo.events), count)
            self.assertEqual(len(calls), 0)

    def test_selecting_another_hypothesis_requires_a_fresh_prediction(self):
        demo = controller()
        act(demo, "open_records")
        hypotheses = demo.pack.causal_scenes[0].simulation.hypotheses
        run_hypothesis(demo, hypotheses[0].hypothesis_id)
        selected = act(demo, "select_hypothesis", hypothesis_id=hypotheses[1].hypothesis_id)
        scene = selected["causal_scene"]
        self.assertEqual(scene["phase"], "model")
        self.assertIsNone(scene["prediction_id"])
        self.assertIsNone(scene["intervention_action_id"])
        self.assertIsNone(scene["reflection"])
        self.assertFalse(selected["can_continue"])
        before = len(demo.events)
        with self.assertRaises(ValueError):
            act(demo, "run_intervention",
                intervention_action_id=demo.pack.causal_scenes[0].intervention.action_id)
        self.assertEqual(len(demo.events), before)

    def test_repeated_same_hypothesis_does_not_satisfy_two_model_comparison(self):
        demo = controller()
        act(demo, "open_records")
        hypothesis = demo.pack.causal_scenes[0].simulation.hypotheses[0]
        run_hypothesis(demo, hypothesis.hypothesis_id)
        run_hypothesis(demo, hypothesis.hypothesis_id)
        before = len(demo.events)
        with self.assertRaises(ValueError):
            act(demo, "submit_revision",
                edges=[edge.model_dump() for edge in demo.pack.causal_scenes[0].assessment.accepted_edges],
                reflection="I ran the same assumption twice, not two different explanations.")
        self.assertEqual(len(demo.events), before)
        self.assertIsNone(replay(demo.events).last_evaluation)
        self.assertEqual(replay(demo.events).completed_activity_ids, ())

    def test_same_request_is_idempotent_but_changed_content_is_rejected(self):
        demo = controller()
        act(demo, "open_records")
        hypotheses = demo.pack.causal_scenes[0].simulation.hypotheses
        first = act(demo, "select_hypothesis", request_id="dynamic.retry",
                    input_revision=1, hypothesis_id=hypotheses[0].hypothesis_id)
        count = len(demo.events)
        again = act(demo, "select_hypothesis", request_id="dynamic.retry",
                    input_revision=1, hypothesis_id=hypotheses[0].hypothesis_id)
        self.assertEqual(first["causal_scene"], again["causal_scene"])
        self.assertEqual(len(demo.events), count)
        with self.assertRaisesRegex(ValueError, "reused"):
            act(demo, "select_hypothesis", request_id="dynamic.retry",
                input_revision=1, hypothesis_id=hypotheses[1].hypothesis_id)
        self.assertEqual(len(demo.events), count)

    def test_two_distinct_runs_replay_without_credit_then_reference_revision_is_scored(self):
        for profile in ("general", "medical"):
            with self.subTest(profile=profile):
                demo = controller(profile)
                act(demo, "open_records")
                run_hypothesis(demo, "umbrella-causes-wet")
                run_hypothesis(demo, "wet-causes-umbrella")
                state = replay(demo.events)
                self.assertIsNone(state.last_evaluation)
                self.assertIsNone(state.advance_allowed_for_event_id)
                self.assertEqual(state.completed_activity_ids, ())
                adapter = TypeAdapter(LearningEvent)
                restored = [adapter.validate_json(event.model_dump_json()) for event in demo.events]
                self.assertEqual(replay(restored), state)
                self.assertEqual(len(state.causal_scene_snapshot.simulation_runs), 2)
                frozen_runs = tuple(run.model_dump_json() for run in state.causal_scene_snapshot.simulation_runs)
                revised = act(demo, "submit_revision", edges=[edge.model_dump()
                    for edge in demo.pack.causal_scenes[0].assessment.accepted_edges],
                    reflection="The models share the observations but can disagree under assignment. "
                               "I am representing the supplied reference assumptions, not a uniquely identified graph.")
                self.assertFalse(revised["can_continue"])
                state = replay(demo.events)
                self.assertEqual(tuple(run.model_dump_json() for run in state.causal_scene_snapshot.simulation_runs), frozen_runs)
                response = record_causal_scene_evidence(demo.events, demo.pack,
                    attempt_id=state.open_attempt_id, request_id=f"dynamic.final.{profile}")
                self.assertTrue(response.payload.evaluation.accepted)
                self.assertEqual(response.payload.evidence.prediction_id, "wet-pavement-unchanged")
                select_fixed_policy_move(demo.events, demo.pack, request_id=f"dynamic.final.{profile}")
                self.assertTrue(demo.view()["can_continue"])
                count = len(demo.events)
                with self.assertRaises(ValueError):
                    act(demo, "select_hypothesis", hypothesis_id="rain-common-cause")
                self.assertEqual(len(demo.events), count)

    def test_dynamic_revision_requires_an_unscored_comparison_text(self):
        demo = controller()
        act(demo, "open_records")
        run_hypothesis(demo, "umbrella-causes-wet")
        run_hypothesis(demo, "wet-causes-umbrella")
        count = len(demo.events)
        with self.assertRaisesRegex(ValueError, "comparison explanation"):
            act(demo, "submit_revision", reflection=None, edges=[edge.model_dump()
                for edge in demo.pack.causal_scenes[0].assessment.accepted_edges])
        self.assertEqual(len(demo.events), count)
        self.assertIsNone(replay(demo.events).last_evaluation)

    def test_accepted_artifact_stays_frozen_after_optional_tutor_discussion(self):
        demo = controller()
        act(demo, "open_records")
        run_hypothesis(demo, "umbrella-causes-wet")
        run_hypothesis(demo, "wet-causes-umbrella")
        act(demo, "submit_revision", edges=[edge.model_dump()
            for edge in demo.pack.causal_scenes[0].assessment.accepted_edges],
            reflection="The interventions compare models but do not identify a unique graph.")
        state = replay(demo.events)
        record_causal_scene_evidence(demo.events, demo.pack, attempt_id=state.open_attempt_id,
                                     request_id="dynamic.frozen.score")
        select_fixed_policy_move(demo.events, demo.pack, request_id="dynamic.frozen.score")

        def revise_after_score():
            count = len(demo.events)
            with self.assertRaisesRegex(ValueError, "frozen"):
                act(demo, "submit_revision", edges=[edge.model_dump()
                    for edge in hypothesis_edges("umbrella-causes-wet")],
                    reflection="This post-score edit must not alter the checked artifact.")
            self.assertEqual(len(demo.events), count)

        frozen = replay(demo.events).causal_scene_snapshot
        revise_after_score()
        with override_allow_model_requests(False):
            asyncio.run(demo.send_message_with_tutor(
                request_id="dynamic.frozen.discuss", text="Can we discuss why the model check is not causal discovery?",
                model=FunctionModel(lambda _messages, _info: ModelResponse(parts=[TextPart(
                    "The check records supplied assumptions; agreement with one intervention need not identify a unique graph."
                )])), unguarded=True))
        self.assertTrue(demo.view()["can_continue"])
        self.assertEqual(replay(demo.events).causal_scene_snapshot, frozen)
        revise_after_score()

    def test_explain_support_does_not_bypass_the_reference_reveal_boundary(self):
        demo = controller()
        act(demo, "open_records")
        hidden = next(resource.text for resource in demo.pack.resources
                      if resource.resource_id == demo.pack.causal_scenes[0].direct_explanation_resource_id)
        prompts = []

        def capture(messages, info):
            prompts.append(next(part.content for message in reversed(messages)
                                for part in message.parts if part.part_kind == "user-prompt"))
            deps = build_tutor_deps(demo.events, demo.pack, request_id=demo.events[-1].request_id)
            return ModelResponse(parts=[ToolCallPart(info.output_tools[0].name,
                {"candidate_id": deps.candidates[0].candidate_id})])

        for before_runs in (True, False):
            with self.subTest(before_any_run=before_runs):
                if not before_runs:
                    run_hypothesis(demo, "umbrella-causes-wet")
                with override_allow_model_requests(False):
                    view = asyncio.run(demo.request_explanation_with_tutor(
                        request_id=f"dynamic.explain.{len(demo.events)}", model=FunctionModel(capture)))
                self.assertFalse(hidden in prompts[-1],
                                 "Explicit explanation support exposes undisclosed reference-world assumptions to the Tutor.")
                self.assertFalse(view["causal_scene"]["resources"]["direct_explanation"])
                self.assertIsNone(view["causal_scene"]["simulation"]["reference_assumptions"])

    def test_renderer_api_withholds_unrun_results_and_early_reference_identity(self):
        demo = controller()
        for operation in (None, "open_records", "select_hypothesis", "submit_prediction"):
            if operation == "select_hypothesis":
                act(demo, operation, hypothesis_id="umbrella-causes-wet")
            elif operation == "submit_prediction":
                act(demo, operation, prediction_id="wet-pavement-unchanged")
            elif operation is not None:
                act(demo, operation)
            public = demo.view()["causal_scene"]
            self.assertEqual(public["intervention"]["result_records"], [])
            self.assertEqual(public["simulation"]["runs"], [])
            self.assertIsNone(public["simulation"]["reference_assumptions"])
            self.assertIsNone(public["simulation"]["reference_edges"])
            for name in ("result", "reflection", "direct_explanation"):
                self.assertFalse(public["resources"][name])
        first = act(demo, "run_intervention",
                    intervention_action_id=demo.pack.causal_scenes[0].intervention.action_id)["causal_scene"]
        self.assertEqual(len(first["simulation"]["runs"]), 1)
        self.assertTrue(first["intervention"]["result_records"])
        self.assertFalse(first["resources"]["reflection"])
        self.assertFalse(first["resources"]["direct_explanation"])
        self.assertIsNone(first["simulation"]["reference_assumptions"])
        second = run_hypothesis(demo, "wet-causes-umbrella")["causal_scene"]
        self.assertTrue(second["resources"]["reflection"])
        self.assertTrue(second["simulation"]["reference_assumptions"])
        self.assertEqual(len(second["simulation"]["runs"]), 2)

    def test_guided_tutor_uses_the_same_phase_visible_simulation_without_answers(self):
        demo = controller("medical")
        captured = []

        def capture(messages, _info):
            prompt = next(part.content for message in reversed(messages)
                          for part in message.parts if part.part_kind == "user-prompt")
            captured.append(json.loads(prompt))
            return ModelResponse(parts=[TextPart("Compare the displayed assumptions before the next experiment.")])

        def discuss():
            with override_allow_model_requests(False):
                asyncio.run(demo.send_message_with_tutor(
                    request_id=f"dynamic.chat.{len(demo.events)}",
                    text="Help me understand what is currently visible, without doing the task for me.",
                    model=FunctionModel(capture), unguarded=True))
            public = demo.view()["causal_scene"]
            context = captured[-1]
            visible = context["visible_scene"]
            self.assertEqual(visible["simulation"], public["simulation"])
            self.assertNotIn("accepted_edges", json.dumps(context))
            self.assertNotIn("reference_hypothesis_id", json.dumps(context))
            return visible

        initial = discuss()
        self.assertEqual(initial["simulation"]["runs"], [])
        act(demo, "open_records")
        discuss()
        run_hypothesis(demo, "umbrella-causes-wet")
        one = discuss()
        self.assertEqual(one["simulation"]["runs"][0]["hypothesis_wet_pct"], 100)
        self.assertEqual(one["simulation"]["runs"][0]["reference_wet_pct"], 40)
        self.assertIsNone(one["simulation"]["reference_assumptions"])
        direct = next(resource.text for resource in demo.pack.resources
                      if resource.resource_id == demo.pack.causal_scenes[0].direct_explanation_resource_id)
        self.assertNotIn(direct, json.dumps(captured[-1]))
        run_hypothesis(demo, "wet-causes-umbrella")
        two = discuss()
        self.assertTrue(two["simulation"]["ready_for_revision"])
        self.assertTrue(two["simulation"]["reference_assumptions"])
        self.assertEqual(demo.view()["learner_message_count"], 4)
        self.assertFalse(demo.view()["can_continue"])

    def test_dynamic_button_feedback_is_authored_and_cannot_repeat_a_stale_hypothesis(self):
        for profile in ("general", "medical"):
            with self.subTest(profile=profile):
                demo = controller(profile)
                scene = demo.pack.causal_scenes[0]
                resources = {resource.resource_id: resource.text for resource in demo.pack.resources}
                calls = []

                def stale_question(_messages, info):
                    calls.append(True)
                    deps = build_tutor_deps(demo.events, demo.pack, request_id=demo.events[-1].request_id)
                    return ModelResponse(parts=[ToolCallPart(info.output_tools[0].name, {
                        "candidate_id": deps.candidates[0].candidate_id,
                        "socratic_question": "Given the rain-as-common-cause hypothesis, what stays fixed?",
                    })])

                actions = (
                    ({"kind": "open_records"}, scene.model_resource_id),
                    ({"kind": "select_hypothesis", "hypothesis_id": "rain-common-cause"}, scene.prediction_resource_id),
                    ({"kind": "submit_prediction", "prediction_id": "wet-pavement-unchanged"}, scene.intervention_resource_id),
                    ({"kind": "run_intervention", "intervention_action_id": scene.intervention.action_id}, scene.result_resource_id),
                    ({"kind": "select_hypothesis", "hypothesis_id": "wet-causes-umbrella"}, scene.prediction_resource_id),
                    ({"kind": "submit_prediction", "prediction_id": "wet-pavement-unchanged"}, scene.intervention_resource_id),
                    ({"kind": "run_intervention", "intervention_action_id": scene.intervention.action_id}, scene.result_resource_id),
                    ({"kind": "submit_revision", "edges": [edge.model_dump() for edge in scene.assessment.accepted_edges],
                      "reflection": "Agreement with one intervention does not identify a unique graph; this graph represents supplied assumptions."},
                     scene.direct_explanation_resource_id),
                )
                with override_allow_model_requests(False):
                    for index, (action, resource_id) in enumerate(actions):
                        view = asyncio.run(demo.submit_scene_action_with_tutor(
                            request_id=f"dynamic.authored.{index}",
                            input_revision=view["causal_scene"]["revision"] if index else 0,
                            action=ADAPTER.validate_json(json.dumps(action)), model=FunctionModel(stale_question)))
                        self.assertEqual(view["conversation"][-1]["text"], resources[resource_id])
                        payload = demo.events[-1].payload
                        self.assertEqual(payload.move.resource_id, resource_id)
                        self.assertIsNone(payload.socratic_question)
                        self.assertIsNone(payload.tutor_reply)
                        self.assertTrue(payload.decision_trace_id.endswith(".authored-scene-action"))
                        self.assertEqual(calls, [])
                        self.assertFalse(view["can_continue"])
                restored = [TypeAdapter(LearningEvent).validate_json(event.model_dump_json())
                            for event in demo.events]
                self.assertEqual(replay(restored), replay(demo.events))

    def test_saved_dynamic_generated_questions_replay_as_recorded(self):
        demo = controller()
        act(demo, "open_records")
        request_id = "dynamic.saved.generated"
        demo.submit_scene_action(request_id=request_id, input_revision=1,
            action=ADAPTER.validate_json(json.dumps({"kind": "select_hypothesis",
                                                   "hypothesis_id": "wet-causes-umbrella"})))
        deps = build_tutor_deps(demo.events, demo.pack, request_id=request_id)
        focus = deps.legal_interaction_focus_ids[0]
        old_question = "Given the rain-as-common-cause hypothesis, what stays fixed?"
        append_teaching_move(demo.events, demo.pack, request_id=request_id,
            candidate=deps.candidates[0], selector_kind="tutor", socratic_question=old_question,
            interaction_focus_id=focus, dialogue_job=dialogue_job_for_scene_focus(focus),
            decision_trace_id="dynamic.legacy.generated.1.6.0")
        restored = [TypeAdapter(LearningEvent).validate_json(event.model_dump_json()) for event in demo.events]
        self.assertEqual(replay(restored), replay(demo.events))
        self.assertEqual(restored[-1].payload.socratic_question, old_question)
        saved = tuple(event.model_dump_json() for event in restored)

        def no_new_call(_messages, _info):
            self.fail("An already-recorded generated move must be replayed without a new model request.")

        with override_allow_model_requests(False):
            result = asyncio.run(run_tutor_turn(restored, demo.pack, request_id=request_id,
                                                model=FunctionModel(no_new_call)))
        self.assertEqual(result.rendered_turn.text, old_question)
        self.assertEqual(tuple(event.model_dump_json() for event in restored), saved)

    def test_tutor_compares_each_hypothesis_using_its_own_root_variable(self):
        for profile in ("general", "medical"):
            with self.subTest(profile=profile):
                demo = controller(profile)
                self.assertEqual(demo.view()["causal_scene"]["simulation"]["hypotheses"], [])
                act(demo, "open_records")
                captured = []

                def capture(messages, info):
                    self.assertIn("Equal counts across hypotheses do not imply a shared root", info.instructions)
                    self.assertIn("A variable absent from active_node_ids has no specified", info.instructions)
                    self.assertIn("correct it directly", info.instructions)
                    prompt = next(part.content for message in reversed(messages)
                                  for part in message.parts if part.part_kind == "user-prompt")
                    captured.append(json.loads(prompt))
                    return ModelResponse(parts=[TextPart(
                        "Equal percentages need not have the same cause. In the rain hypothesis, wetness "
                        "copies rain; in the reverse hypothesis, wetness is itself the root variable. "
                        "Agreement does not identify a unique graph."
                    )])

                async def ask(request_id, text):
                    return await demo.send_message_with_tutor(request_id=request_id, text=text,
                        model=FunctionModel(capture), unguarded=True)

                with override_allow_model_requests(False):
                    asyncio.run(ask("dynamic.roots.before", "How do these hypotheses differ before I run them?"))
                    public = captured[-1]["visible_scene"]["simulation"]
                    self.assertEqual(public["runs"], [])
                    self.assertIsNone(public["reference_assumptions"])
                    self.assertIsNone(public["reference_edges"])
                    self.assertNotIn("reference_hypothesis_id", json.dumps(captured[-1]))
                    hypotheses = {item["hypothesis_id"]: item for item in public["hypotheses"]}
                    self.assertEqual(hypotheses["rain-common-cause"]["root_variable_id"], "rain")
                    self.assertEqual(hypotheses["umbrella-causes-wet"]["root_variable_id"], "umbrella-carried")
                    reverse = hypotheses["wet-causes-umbrella"]
                    self.assertEqual(reverse["root_variable_id"], "pavement-wet")
                    self.assertEqual(reverse["root_variable_label"], "Pavement wet")
                    self.assertEqual(reverse["active_node_ids"], ["pavement-wet", "umbrella-carried"])
                    self.assertNotIn("rain", reverse["active_node_ids"])
                    for hypothesis_id in ("umbrella-causes-wet", "rain-common-cause", "wet-causes-umbrella"):
                        run_hypothesis(demo, hypothesis_id)
                    view = asyncio.run(ask("dynamic.roots.after",
                        "Why do the rain and reverse hypotheses both give 40%? "
                        "Does that establish rain as the real cause, or are those supplied assumptions?"))
                public = captured[-1]["visible_scene"]["simulation"]
                self.assertEqual({run["hypothesis_id"]: run["hypothesis_wet_pct"] for run in public["runs"]},
                                 {"umbrella-causes-wet": 100, "rain-common-cause": 40, "wet-causes-umbrella": 40})
                self.assertEqual(public["hypotheses"], demo.view()["causal_scene"]["simulation"]["hypotheses"])
                self.assertTrue(public["reference_assumptions"])
                self.assertEqual(view["learner_message_count"], 2)
                self.assertIsNone(view["pending_tutor_message"])
                self.assertFalse(view["can_continue"])

    def test_repeated_experiments_keep_tutor_context_bounded_without_losing_history(self):
        for profile in ("general", "medical"):
            with self.subTest(profile=profile):
                demo = controller(profile)
                act(demo, "open_records")
                captured_deps = []
                captured_contexts = []

                def discuss(messages, _info):
                    captured_deps.append(build_tutor_deps(
                        demo.events, demo.pack, request_id=demo.events[-1].request_id))
                    prompt = next(part.content for message in reversed(messages)
                                  for part in message.parts if part.part_kind == "user-prompt")
                    captured_contexts.append(json.loads(prompt))
                    return ModelResponse(parts=[TextPart(
                        "Your saved run belongs to its selected hypothesis; the reference world stays fixed."
                    )])

                with override_allow_model_requests(False):
                    for index in range(12):
                        # Repeating the third model must not forget the earlier
                        # distinct hypotheses or their comparison readiness.
                        run_hypothesis(demo, ("umbrella-causes-wet", "rain-common-cause")[index]
                                       if index < 2 else "wet-causes-umbrella")
                        saved = tuple(event.model_dump_json() for event in demo.events)
                        view = asyncio.run(demo.send_message_with_tutor(
                            request_id=f"dynamic.long-chat.{index}",
                            text="Help me compare this run with the earlier model without scoring my explanation.",
                            model=FunctionModel(discuss), unguarded=True))
                        self.assertEqual(tuple(event.model_dump_json()
                                               for event in demo.events[:len(saved)]), saved)
                        snapshot = replay(demo.events).causal_scene_snapshot
                        self.assertEqual(len(snapshot.simulation_runs), index + 1)
                        self.assertEqual(len(view["causal_scene"]["simulation"]["runs"]), index + 1)
                        self.assertIsNone(view["pending_tutor_message"])
                        self.assertEqual(view["learner_message_count"], index + 1)
                        self.assertFalse(view["can_continue"])
                        deps = captured_deps[-1]
                        self.assertLessEqual(deps.context_metrics.serialized_characters,
                                             MAX_TUTOR_CONTEXT_CHARS)
                        self.assertEqual(deps.causal_scene_snapshot,
                                         deps.state.causal_scene_snapshot)
                        self.assertLessEqual(len(deps.causal_scene_snapshot.simulation_runs), 6)
                        projection = captured_contexts[-1]["visible_scene"]["simulation"]
                        self.assertLessEqual(len(projection["runs"]), 4)
                        self.assertEqual(projection["ready_for_revision"], index >= 1)
                        self.assertEqual(projection["distinct_hypotheses_tried"],
                                         min(index + 1, 3))
                self.assertEqual([run.run_id for run in captured_deps[-1].causal_scene_snapshot.simulation_runs],
                                 [1, 2, 9, 10, 11, 12])
                restored = [TypeAdapter(LearningEvent).validate_json(event.model_dump_json())
                            for event in demo.events]
                self.assertEqual(replay(restored), replay(demo.events))
                self.assertEqual(len(replay(restored).causal_scene_snapshot.simulation_runs), 12)

    def test_legacy_serialized_scene_events_replay_without_simulation_fields(self):
        demo = controller(historical=True)
        act(demo, "open_records")
        adapter = TypeAdapter(LearningEvent)
        restored = []
        for event in demo.events:
            raw = json.loads(event.model_dump_json())
            if raw["event_type"] == "session_started":
                raw["payload"]["runtime_version"] = "0.9.1"
            if raw["event_type"] == "attempt_started":
                raw["payload"]["causal_scene"].pop("simulation", None)
            restored.append(adapter.validate_json(json.dumps(raw)))
        expected = replay(demo.events)
        self.assertEqual(replay(restored).causal_scene_snapshot, expected.causal_scene_snapshot)
        self.assertEqual(replay(restored).completed_activity_ids, ())


if __name__ == "__main__":
    unittest.main()
