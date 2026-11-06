"""Playable local-demo controller and JSONL persistence contracts."""

import asyncio
import io
import json
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from pydantic_ai import ModelResponse, UnexpectedModelBehavior
from pydantic_ai.exceptions import ModelHTTPError
from pydantic_ai.messages import TextPart, ToolCallPart
from pydantic_ai.models import override_allow_model_requests
from pydantic_ai.models.function import FunctionModel
from pydantic_ai.models.test import TestModel

from educagent_sdk import load_content_pack
from educagent_sdk.causal_scene import (
    OpenRecords, RunIntervention, SubmitGraph, SubmitPrediction, SubmitRevision,
)
from educagent_sdk.contracts import CausalSceneEdge
from educagent_sdk.demo import DemoController, JsonlEventStore
from educagent_sdk.diagnostic import DiagnosticSession, load_diagnostic_plan
from educagent_sdk.events import ResponseRecorded, SupportRequested, TeachingMoveSelected, replay
from educagent_sdk.runtime import message_teaching_candidates
from educagent_sdk.tutor import DEMO_CHAT_POLICY_VERSION, build_tutor_deps
from educagent_sdk.web_demo import _handle_command, create_demo_server


ROOT = Path(__file__).resolve().parents[1]
PACK_PATH = ROOT / "content" / "causality_m0_episode.json"


class PlayableDemoTest(unittest.TestCase):
    def test_scene_action_updates_a_replay_derived_workbench_view(self) -> None:
        pack = load_content_pack(ROOT / "content" / "causality_m0_full.json")
        demo = DemoController(pack)
        demo.start(
            session_id="demo.scene.01",
            preferred_activity_ids=("association-is-not-causation.transfer",),
            route_scope="preferred",
        )

        opened = demo.submit_scene_action(
            request_id="demo.scene.records.01",
            input_revision=0,
            action=OpenRecords(),
        )

        scene = opened["causal_scene"]
        self.assertIsNotNone(scene)
        assert scene is not None
        self.assertEqual(scene["phase"], "records")
        self.assertEqual(len(scene["observed_records"]), 4)
        self.assertFalse(opened["can_continue"])
        self.assertEqual(
            demo.developer_trace()["events"][-1]["type"],
            "causal_scene_action_recorded",
        )

    def test_scene_http_boundary_accepts_json_array_edges(self) -> None:
        demo = DemoController(load_content_pack(ROOT / "content" / "causality_m0_full.json"))
        asyncio.run(
            _handle_command(
                demo,
                "/api/start-scene",
                {"session_id": "demo.scene.http.01"},
                model=TestModel(),
            )
        )
        asyncio.run(
            _handle_command(
                demo,
                "/api/scene-action",
                {
                    "request_id": "demo.scene.http.records.01",
                    "input_revision": 0,
                    "action": {"kind": "open_records"},
                },
                model=TestModel(),
            )
        )
        state = asyncio.run(
            _handle_command(
                demo,
                "/api/scene-action",
                {
                    "request_id": "demo.scene.http.graph.01",
                    "input_revision": 1,
                    "action": {
                        "kind": "submit_graph",
                        "edges": [
                            {
                                "parent_id": "umbrella-carried",
                                "child_id": "pavement-wet",
                            }
                        ],
                    },
                },
                model=TestModel(),
            )
        )
        self.assertEqual(state["causal_scene"]["phase"], "model")

    def test_initial_correct_classification_can_advance_without_a_fake_revision(self) -> None:
        pack = load_content_pack(ROOT / "content" / "causality_m0_full.json")
        demo = DemoController(pack)
        started = demo.start(session_id="demo.correct-first.01")
        activity = next(
            item for item in pack.activities if item.activity_id == started["activity_id"]
        )
        correct = next(choice for choice in activity.choices if choice.correct)

        view = demo.respond(
            request_id="demo.correct-first.response.01",
            option_id=correct.option_id,
        )

        self.assertTrue(view["can_continue"])
        self.assertNotIn("Which detail", view["turn"])
        self.assertNotIn(
            "Your response meets the current requirement.",
            [message["text"] for message in view["conversation"]],
        )

    def test_initial_activity_keeps_static_prompts_out_of_conversation(self) -> None:
        pack = load_content_pack(ROOT / "content" / "causality_m0_full.json")
        demo = DemoController(pack)
        view = demo.start(
            session_id="demo.opening-question.01",
            preferred_activity_ids=("observed-association.practice",),
            route_scope="preferred",
        )

        self.assertEqual(view["conversation"], [])
        self.assertIn("exercise", view["question"].lower())

    def test_answer_follow_up_explanation_reload_and_continue_preserve_credit(self) -> None:
        pack = load_content_pack(ROOT / "content" / "causality_m0_full.json")
        activity_id = "observed-association.transfer"
        correct = next(
            option for activity in pack.activities if activity.activity_id == activity_id
            for option in activity.choices if option.correct
        )
        calls = 0

        def reply(_messages, _info):
            nonlocal calls
            calls += 1
            return ModelResponse(parts=[TextPart("The association describes a pattern in the records.")])

        with tempfile.TemporaryDirectory() as directory:
            store = JsonlEventStore(Path(directory) / "optional-discussion.jsonl")
            demo = DemoController(pack, store=store)
            demo.start(preferred_activity_ids=(activity_id,), route_scope="preferred")
            with override_allow_model_requests(False):
                demo.respond(request_id="checked.answer", option_id=correct.option_id)
                for index in range(3):
                    view = asyncio.run(demo.send_message_with_tutor(
                        request_id=f"checked.follow-up.{index}",
                        text="Why is this an association?", model=FunctionModel(reply),
                        unguarded=True,
                    ))
                    self.assertTrue(view["can_continue"])
                    self.assertTrue(view["can_send_message"])
                view = demo.request_explanation(request_id="checked.explanation")
            self.assertTrue(view["can_continue"])
            self.assertEqual(calls, 3)
            self.assertEqual(replay(demo.events).response_ordinal, 1)
            self.assertEqual(sum(isinstance(event, ResponseRecorded) for event in demo.events), 1)
            resumed = DemoController(pack, store=store)
            self.assertTrue(resumed.view()["can_continue"])
            completed = resumed.continue_activity(request_id="checked.continue")
            self.assertEqual(completed["status"], "completed")
            self.assertIn(activity_id, completed["completed_activity_ids"])

    def test_failed_follow_up_is_retryable_idempotent_and_keeps_checked_answer(self) -> None:
        pack = load_content_pack(ROOT / "content" / "causality_m0_full.json")
        demo = DemoController(pack)
        started = demo.start()
        correct = next(
            option for activity in pack.activities if activity.activity_id == started["activity_id"]
            for option in activity.choices if option.correct
        )
        demo.respond(request_id="retry.answer", option_id=correct.option_id)
        calls = 0

        def invalid(_messages, _info):
            return ModelResponse(parts=[TextPart("")])

        def valid(_messages, _info):
            nonlocal calls
            calls += 1
            return ModelResponse(parts=[TextPart("A variable can take different values.")])

        with override_allow_model_requests(False):
            with self.assertRaises(UnexpectedModelBehavior):
                asyncio.run(demo.send_message_with_tutor(
                    request_id="retry.follow-up", text="Why?", model=FunctionModel(invalid),
                    unguarded=True,
                ))
            failed = demo.view()
            self.assertTrue(failed["can_continue"])
            self.assertFalse(failed["can_send_message"])
            self.assertEqual(failed["pending_tutor_message"]["request_id"], "retry.follow-up")
            with self.assertRaisesRegex(ValueError, "retry pending tutor request"):
                asyncio.run(demo.send_message_with_tutor(
                    request_id="retry.new", text="Another question", model=FunctionModel(valid),
                    unguarded=True,
                ))
            with self.assertRaisesRegex(ValueError, "different content"):
                asyncio.run(demo.send_message_with_tutor(
                    request_id="retry.follow-up", text="Changed", model=FunctionModel(valid),
                    unguarded=True,
                ))
            for _ in range(2):
                retried = asyncio.run(demo.send_message_with_tutor(
                    request_id="retry.follow-up", text="Why?", model=FunctionModel(valid),
                    unguarded=True,
                ))
        self.assertEqual(calls, 1)
        self.assertEqual(retried["learner_message_count"], 1)
        self.assertIsNone(retried["pending_tutor_message"])
        self.assertTrue(retried["can_continue"])
        continued = demo.continue_activity(request_id="retry.continue")
        self.assertIn(started["activity_id"], continued["completed_activity_ids"])

    def test_continue_can_close_a_failed_optional_discussion_without_regrading(self) -> None:
        pack = load_content_pack(ROOT / "content" / "causality_m0_full.json")
        demo = DemoController(pack)
        started = demo.start()
        correct = next(
            option for activity in pack.activities if activity.activity_id == started["activity_id"]
            for option in activity.choices if option.correct
        )
        demo.respond(request_id="leave.answer", option_id=correct.option_id)

        def invalid(_messages, _info):
            return ModelResponse(parts=[TextPart("")])

        with override_allow_model_requests(False):
            with self.assertRaises(UnexpectedModelBehavior):
                asyncio.run(demo.send_message_with_tutor(
                    request_id="leave.follow-up", text="Why?", model=FunctionModel(invalid),
                    unguarded=True,
                ))
        continued = demo.continue_activity(request_id="leave.continue")
        event_count = len(demo.events)
        self.assertIn(started["activity_id"], continued["completed_activity_ids"])
        self.assertIsNone(continued["pending_tutor_message"])
        demo.continue_activity(request_id="leave.continue")
        self.assertEqual(len(demo.events), event_count)
        reply = next(
            event for event in demo.events if isinstance(event, TeachingMoveSelected)
            and event.request_id == "leave.follow-up"
        )
        self.assertEqual(reply.payload.selector_kind, "recovery")
        self.assertEqual(reply.payload.move.strategy, "hold")

    def test_explicit_explanation_retry_after_checked_answer_is_idempotent(self) -> None:
        pack = load_content_pack(ROOT / "content" / "causality_m0_full.json")
        demo = DemoController(pack)
        started = demo.start()
        correct = next(
            option for activity in pack.activities if activity.activity_id == started["activity_id"]
            for option in activity.choices if option.correct
        )
        demo.respond(request_id="explain.answer", option_id=correct.option_id)
        with patch.object(demo, "_select_with_tutor", side_effect=RuntimeError("interrupted")):
            with self.assertRaisesRegex(RuntimeError, "interrupted"):
                asyncio.run(demo.request_explanation_with_tutor(
                    request_id="explain.retry", model=TestModel(),
                ))
        self.assertTrue(demo.view()["can_continue"])
        deps = build_tutor_deps(demo.events, pack, request_id="explain.retry")
        candidate = next(item for item in deps.candidates if item.move.strategy == "direct_instruction")
        with override_allow_model_requests(False):
            for _ in range(2):
                retried = asyncio.run(demo.request_explanation_with_tutor(
                    request_id="explain.retry",
                    model=TestModel(custom_output_args={"candidate_id": candidate.candidate_id}),
                ))
        self.assertTrue(retried["can_continue"])
        self.assertTrue(retried["can_send_message"])
        self.assertEqual(sum(isinstance(event, SupportRequested) for event in demo.events), 1)
        demo.continue_activity(request_id="explain.continue")

    def test_preferred_route_completes_without_falling_back_to_the_full_pack(self) -> None:
        pack = load_content_pack(ROOT / "content" / "causality_m0_full.json")
        activity_id = "observation-vs-intervention.transfer"
        demo = DemoController(pack)
        started = demo.start(
            session_id="demo.targeted.01",
            preferred_activity_ids=(activity_id,),
            route_scope="preferred",
        )
        activity = next(item for item in pack.activities if item.activity_id == activity_id)
        correct = next(choice for choice in activity.choices if choice.correct)
        demo.respond(
            request_id="demo.targeted.response.01",
            option_id=correct.option_id,
        )

        completed = demo.continue_activity(request_id="demo.targeted.continue.01")

        self.assertEqual(started["activity_id"], activity_id)
        self.assertEqual(completed["status"], "completed")
        self.assertNotEqual(completed.get("activity_id"), "variables-and-values.practice")

    def test_route_navigation_switches_to_the_selected_concept(self) -> None:
        pack = load_content_pack(ROOT / "content" / "causality_m0_full.json")
        demo = DemoController(pack)
        demo.start(
            session_id="demo.navigate.01",
            preferred_activity_ids=("observation-vs-intervention.practice",),
            route_scope="preferred",
        )

        navigated = demo.navigate_to_concept(
            request_id="demo.navigate.request.01",
            concept_id="data-vs-assumptions",
        )

        self.assertEqual(navigated["activity_id"], "data-vs-assumptions.practice")
        self.assertTrue(
            all(
                message["attempt_id"] == navigated["attempt_id"]
                for message in navigated["conversation"]
                if message["activity_id"] == navigated["activity_id"]
            )
        )
        correct = demo.respond(
            request_id="demo.navigate.answer.01",
            option_id="assumptions.practice.assumption",
        )
        self.assertTrue(correct["can_continue"])
        transfer = demo.continue_activity(request_id="demo.navigate.continue.01")
        self.assertEqual(transfer["activity_id"], "data-vs-assumptions.transfer")

    def test_route_navigation_finishes_the_selected_concept_before_returning(self) -> None:
        pack = load_content_pack(ROOT / "content" / "causality_m0_full.json")
        demo = DemoController(pack)
        demo.start(
            session_id="demo.navigate.sequence.01",
            preferred_activity_ids=(
                "variables-and-values.practice",
                "variables-and-values.transfer",
                "observation-vs-intervention.practice",
                "observation-vs-intervention.transfer",
            ),
            route_scope="preferred",
        )
        navigated = demo.navigate_to_concept(
            request_id="demo.navigate.sequence.request.01",
            concept_id="observation-vs-intervention",
        )
        correct = demo.respond(
            request_id="demo.navigate.sequence.answer.01",
            option_id="intervention.practice.observation",
        )

        self.assertTrue(correct["can_continue"])
        transfer = demo.continue_activity(
            request_id="demo.navigate.sequence.continue.01"
        )
        self.assertEqual(
            navigated["activity_id"], "observation-vs-intervention.practice"
        )
        self.assertEqual(
            transfer["activity_id"], "observation-vs-intervention.transfer"
        )

    def test_server_requires_a_guarded_tutor_model(self) -> None:
        with self.assertRaisesRegex(ValueError, "requires a guarded tutor model"):
            create_demo_server(DemoController(load_content_pack(PACK_PATH)), model=None)  # type: ignore[arg-type]

    def test_server_refuses_a_non_loopback_bind(self) -> None:
        with self.assertRaisesRegex(ValueError, "127.0.0.1"):
            create_demo_server(
                DemoController(load_content_pack(PACK_PATH)),
                host="0.0.0.0",
                model=TestModel(),
            )

    def test_episode_resumes_from_jsonl_and_completes_keyboard_flow(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = JsonlEventStore(Path(directory) / "events.jsonl")
            demo = DemoController(load_content_pack(PACK_PATH), store=store)

            start = demo.start(session_id="demo.test.session.01")
            self.assertEqual(start["phase"], "awaiting_response")
            wrong = demo.respond(
                request_id="demo.test.response.01",
                option_id="commitment.interventional",
            )
            self.assertIn("clinic only observed", wrong["turn"])
            self.assertFalse(wrong["can_continue"])
            revised = demo.respond(
                request_id="demo.test.response.02",
                option_id="commitment.observational",
            )
            self.assertTrue(revised["can_continue"])
            self.assertEqual(
                demo.respond(
                    request_id="demo.test.response.02",
                    option_id="commitment.observational",
                ),
                revised,
            )
            with self.assertRaisesRegex(ValueError, "different content"):
                demo.respond(
                    request_id="demo.test.response.02",
                    option_id="commitment.interventional",
                )
            assumption = demo.continue_activity(request_id="demo.test.continue.01")
            self.assertEqual(
                assumption["activity_id"], "observation-vs-intervention.assumption.01"
            )

            hinted = demo.respond(
                request_id="demo.test.response.03",
                option_id="assumption.records-show-association",
            )
            self.assertIn("Separate seeing patients", hinted["turn"])
            demo.respond(
                request_id="demo.test.response.04",
                option_id="assumption.assigning-sleep-improves-concentration",
            )
            transfer = demo.continue_activity(request_id="demo.test.continue.02")
            self.assertEqual(
                transfer["activity_id"], "observation-vs-intervention.transfer.01"
            )
            demo.respond(
                request_id="demo.test.response.05",
                option_id="transfer.observational",
            )
            complete = demo.continue_activity(request_id="demo.test.continue.03")
            self.assertEqual(complete["status"], "completed")
            self.assertEqual(
                complete["m1_ready_concept_ids"], ("observation-vs-intervention",)
            )

            resumed = DemoController(load_content_pack(PACK_PATH), store=store)
            self.assertEqual(resumed.view(), complete)
            trace = json.dumps(resumed.developer_trace())
            self.assertNotIn("event_id", trace)
            self.assertNotIn("artifact", trace)
            self.assertGreater(len(store.load()), 1)

            self.assertEqual(resumed.reset()["status"], "not_started")
            self.assertEqual(store.load(), [])

    def test_local_server_is_loopback_only_and_uses_an_ephemeral_port(self) -> None:
        demo = DemoController(load_content_pack(PACK_PATH))
        server = create_demo_server(demo, port=0, model=TestModel())
        try:
            self.assertEqual(server.server_address[0], "127.0.0.1")
            self.assertGreater(server.server_address[1], 0)
        finally:
            server.server_close()

    def test_agent_mode_uses_the_guarded_tutor_for_selection(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = JsonlEventStore(Path(directory) / "events.jsonl")
            demo = DemoController(
                load_content_pack(PACK_PATH), store=store, mode="guarded_tutor"
            )
            demo.start(session_id="demo.agent.session.01")
            with override_allow_model_requests(False):
                view = asyncio.run(
                    demo.respond_with_tutor(
                        request_id="demo.agent.response.01",
                        option_id="commitment.interventional",
                        model=TestModel(
                            custom_output_args={
                                "candidate_id": "tutor.reflect.episode.commitment.consequence.rejected"
                            }
                        ),
                    )
                )

            self.assertEqual(view["mode"], "guarded_tutor")
            self.assertIn("clinic only observed", view["turn"])
            self.assertEqual(
                demo.developer_trace()["events"][-1]["selector_kind"], "tutor"
            )
            resumed = DemoController(
                load_content_pack(PACK_PATH), store=store, mode="guarded_tutor"
            )
            self.assertEqual(resumed.view()["turn"], view["turn"])

    def test_start_with_tutor_persists_a_socratic_opening(self) -> None:
        pack = load_content_pack(ROOT / "content" / "causality_m0_full.json")
        demo = DemoController(pack, mode="guarded_tutor")
        model = TestModel(
            custom_output_args={
                "candidate_id": "tutor.elicit.variables.question.practice",
                "socratic_question": (
                    "What detail could take a different value from one patient to another?"
                ),
            }
        )

        with override_allow_model_requests(False):
            view = asyncio.run(
                demo.start_with_tutor(model=model, session_id="demo.agent.opening.01")
            )

        self.assertEqual(view["conversation"][0]["role"], "tutor")
        self.assertEqual(view["conversation"][0]["kind"], "elicit")
        self.assertEqual(
            view["conversation"][0]["text"],
            "What detail could take a different value from one patient to another?",
        )
        self.assertEqual(view["conversation"][0]["references"], [])
        self.assertEqual(view["learner_message_count"], 0)
        self.assertFalse(view["can_continue"])

    def test_agent_server_scores_fixed_responses_without_waiting_for_tutor(self) -> None:
        demo = DemoController(load_content_pack(PACK_PATH), mode="guarded_tutor")
        model = TestModel(
            custom_output_args={
                "candidate_id": "tutor.reflect.episode.commitment.consequence.rejected"
            }
        )
        server = create_demo_server(demo, port=0, model=model)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base_url = f"http://{server.server_address[0]}:{server.server_address[1]}"

        def post(path: str, body: dict[str, str]) -> dict[str, object]:
            request = Request(
                f"{base_url}{path}",
                data=json.dumps(body).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urlopen(request, timeout=5) as response:
                return json.loads(response.read())

        try:
            post("/api/start", {"session_id": "demo.agent.server.01"})
            view = post(
                "/api/respond",
                {
                    "request_id": "demo.agent.server.response.01",
                    "option_id": "commitment.interventional",
                },
            )
            self.assertEqual(view["mode"], "guarded_tutor")
            self.assertIn("clinic only observed", view["turn"])
            self.assertEqual(
                demo.developer_trace()["events"][-1]["selector_kind"], "baseline"
            )
            post(
                "/api/respond",
                {
                    "request_id": "demo.agent.server.response.02",
                    "option_id": "commitment.observational",
                },
            )
            moves = [
                event
                for event in demo.developer_trace()["events"]
                if event["type"] == "teaching_move_selected"
            ]
            self.assertEqual(len(moves), 3)
            self.assertEqual(moves[0]["selector_kind"], "invalid_output")
            self.assertEqual(moves[-1]["selector_kind"], "baseline")
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)

    def test_agent_message_is_persisted_before_a_guarded_tutor_turn(self) -> None:
        demo = DemoController(load_content_pack(PACK_PATH), mode="guarded_tutor")
        demo.start(session_id="demo.agent.message.01")
        model = TestModel(
            custom_output_args={
                "candidate_id": "tutor.clarify.episode.commitment.question",
                "socratic_question": "Which detail makes this an observation?",
            }
        )

        with override_allow_model_requests(False):
            view = asyncio.run(
                demo.send_message_with_tutor(
                    request_id="demo.agent.message.request.01",
                    text="Why is this only an observation?",
                    model=model,
                )
            )

        self.assertEqual(view["conversation"][-2]["role"], "learner")
        self.assertEqual(view["conversation"][-1]["role"], "tutor")
        self.assertEqual(view["learner_message_count"], 1)
        self.assertEqual(view["conversation"][-1]["references"], [])
        self.assertEqual(
            view["conversation"][-1]["concept_id"], "observation-vs-intervention"
        )
        self.assertEqual(
            demo.developer_trace()["events"][-1]["selector_kind"], "tutor"
        )
        self.assertNotIn("Why is this", json.dumps(demo.developer_trace()))

    def test_demo_open_reply_allows_follow_up_questions(self) -> None:
        demo = DemoController(load_content_pack(PACK_PATH), mode="guarded_tutor")
        demo.start(session_id="demo.open.reply.01")

        def normal_reply(_messages, _info):
            return ModelResponse(
                parts=[
                    TextPart(
                        "That is a useful observation. Which recorded detail could vary across patients?"
                    )
                ]
            )

        with override_allow_model_requests(False):
            view = asyncio.run(
                demo.send_message_with_tutor(
                    request_id="demo.open.reply.request.01",
                    text="I think different patients can have different rates.",
                    model=FunctionModel(normal_reply),
                    unguarded=True,
                )
            )
            view = asyncio.run(
                demo.send_message_with_tutor(
                    request_id="demo.open.reply.request.02",
                    text="Why would that still be a variable?",
                    model=FunctionModel(normal_reply),
                    unguarded=True,
                )
            )

        self.assertEqual(
            view["conversation"][-1]["text"],
            "That is a useful observation. Which recorded detail could vary across patients?",
        )
        self.assertEqual(
            demo.developer_trace()["events"][-1]["selector_kind"], "tutor"
        )
        self.assertEqual(view["learner_message_count"], 2)

    def test_open_demo_reply_records_the_required_scene_focus(self) -> None:
        pack = load_content_pack(ROOT / "content" / "causality_m0_full.json")
        demo = DemoController(pack, mode="guarded_tutor")
        demo.start(
            session_id="demo.open.scene.reply.01",
            preferred_activity_ids=("association-is-not-causation.transfer",),
            route_scope="preferred",
        )

        def reply(_messages, _info):
            return ModelResponse(parts=[TextPart("Let us inspect the records first.")])

        with override_allow_model_requests(False):
            view = asyncio.run(
                demo.send_message_with_tutor(
                    request_id="demo.open.scene.reply.request.01",
                    text="Maybe rain explains both observations.",
                    model=FunctionModel(reply),
                    unguarded=True,
                )
            )

        self.assertIsNone(view["pending_tutor_message"])
        move = demo.events[-1]
        self.assertIsInstance(move, TeachingMoveSelected)
        self.assertEqual(move.payload.interaction_focus_id, "scene.open-records")
        self.assertEqual(move.payload.dialogue_job, "orient")
        self.assertTrue(move.payload.decision_trace_id.endswith(f".guided-chat.{DEMO_CHAT_POLICY_VERSION}"))

    def test_open_reply_context_follows_visible_scene_phases(self) -> None:
        pack = load_content_pack(ROOT / "content" / "causality_m0_full.json")
        scene = pack.causal_scenes[0]
        demo = DemoController(pack)
        demo.start(preferred_activity_ids=("association-is-not-causation.transfer",), route_scope="preferred")
        contexts = []

        def capture(messages, _info):
            prompt = next(part.content for message in reversed(messages) for part in message.parts if part.part_kind == "user-prompt")
            contexts.append(json.loads(prompt))
            return ModelResponse(parts=[TextPart("Let us use the current task controls.")])

        def select(_messages, info):
            deps = build_tutor_deps(demo.events, pack, request_id=demo.events[-1].request_id)
            return ModelResponse(parts=[ToolCallPart(info.output_tools[0].name, {"candidate_id": deps.candidates[0].candidate_id})])

        wrong_edges = (CausalSceneEdge(parent_id="umbrella-carried", child_id="pavement-wet"),)
        actions = (
            None,
            OpenRecords(),
            SubmitGraph(edges=wrong_edges),
            SubmitPrediction(prediction_id="wet-pavement-more-often"),
            RunIntervention(intervention_action_id=scene.intervention.action_id),
            SubmitRevision(edges=scene.assessment.accepted_edges, reflection="The result differs from my prediction; the arrows are supplied assumptions."),
        )
        resources = {resource.resource_id: resource.text for resource in pack.resources}
        with override_allow_model_requests(False):
            for index, action in enumerate(actions):
                if action is not None:
                    asyncio.run(demo.submit_scene_action_with_tutor(request_id=f"visible.action.{index}", input_revision=index - 1, action=action, model=FunctionModel(select)))
                view = asyncio.run(demo.send_message_with_tutor(
                    request_id=f"visible.message.{index}", text="What should I do next?",
                    model=FunctionModel(capture), unguarded=True,
                ))
                context = contexts[-1]
                visible = context["visible_scene"]
                self.assertEqual(context["learner_message"], "What should I do next?")
                self.assertNotIn("accepted_edges", json.dumps(context))
                self.assertFalse(view["can_continue"])
                if index < 4:
                    self.assertIn("No intervention result has been revealed", visible["state"])
                    self.assertNotIn(resources[scene.result_resource_id], json.dumps(context))
                    self.assertNotIn(resources[scene.reflection_resource_id], json.dumps(context))
                    self.assertNotIn(resources[scene.direct_explanation_resource_id], json.dumps(context))
                else:
                    self.assertIn("Intervention result:", visible["state"])
                    self.assertIn(resources[scene.result_resource_id], visible["phase_guidance"])
                if index == 0:
                    self.assertIn("records are not yet open", visible["state"])
                    self.assertNotIn("96", json.dumps(context))
                if index >= 3:
                    self.assertIn("more common", visible["recorded_prediction"])
        self.assertEqual(contexts[0]["next_focus"], "scene.open-records")
        self.assertEqual(contexts[-1]["next_focus"], "scene.formal-evidence")
        self.assertIn("supplied assumptions", contexts[-1]["visible_scene"]["unscored_reflection"])

    def test_open_reply_history_is_attempt_scoped_with_current_message_once(self) -> None:
        pack = load_content_pack(ROOT / "content" / "causality_m0_full.json")
        demo = DemoController(pack)
        demo.start()
        prompts = []

        def capture(messages, _info):
            prompts.append(next(part.content for message in reversed(messages) for part in message.parts if part.part_kind == "user-prompt"))
            return ModelResponse(parts=[TextPart("A short explanation.")])

        with override_allow_model_requests(False):
            asyncio.run(demo.send_message_with_tutor(request_id="scope.first", text="PRIOR_ATTEMPT_ONLY", model=FunctionModel(capture), unguarded=True))
            demo.navigate_to_concept(request_id="scope.navigate", concept_id="data-vs-assumptions")
            asyncio.run(demo.send_message_with_tutor(request_id="scope.second", text="CURRENT_MESSAGE_ONCE", model=FunctionModel(capture), unguarded=True))
        self.assertNotIn("PRIOR_ATTEMPT_ONLY", prompts[-1])
        self.assertEqual(prompts[-1].count("CURRENT_MESSAGE_ONCE"), 1)
        self.assertEqual(json.loads(prompts[-1])["recent_conversation"], [])

    def test_open_reply_retries_instead_of_truncating_and_is_idempotent(self) -> None:
        demo = DemoController(load_content_pack(PACK_PATH))
        demo.start()
        calls = 0

        def reply(_messages, _info):
            nonlocal calls
            calls += 1
            return ModelResponse(parts=[TextPart("x" * 1201 if calls == 1 else "Here is a complete short explanation.")])

        with override_allow_model_requests(False):
            for _ in range(2):
                view = asyncio.run(demo.send_message_with_tutor(
                    request_id="reply.retry", text="Please explain.", model=FunctionModel(reply), unguarded=True,
                ))
        self.assertEqual(calls, 2)
        self.assertEqual(view["conversation"][-1]["text"], "Here is a complete short explanation.")
        self.assertEqual(view["learner_message_count"], 1)
        self.assertFalse(view["can_continue"])

    def test_invalid_open_replies_leave_one_saved_message_for_retry(self) -> None:
        for output in ("", "x" * 1201):
            with self.subTest(output_length=len(output)):
                demo = DemoController(load_content_pack(PACK_PATH))
                demo.start()
                def invalid(_messages, _info):
                    return ModelResponse(parts=[TextPart(output)])

                def valid(_messages, _info):
                    return ModelResponse(parts=[TextPart("Let us inspect the current evidence.")])

                with override_allow_model_requests(False):
                    with self.assertRaises(UnexpectedModelBehavior):
                        asyncio.run(demo.send_message_with_tutor(request_id="invalid.retry", text="Help me understand.", model=FunctionModel(invalid), unguarded=True))
                    failed = demo.view()
                    self.assertEqual(failed["learner_message_count"], 1)
                    self.assertEqual(failed["conversation"][-1]["role"], "learner")
                    self.assertEqual(failed["pending_tutor_message"]["request_id"], "invalid.retry")
                    recovered = asyncio.run(demo.send_message_with_tutor(request_id="invalid.retry", text="Help me understand.", model=FunctionModel(valid), unguarded=True))
                self.assertIsNone(recovered["pending_tutor_message"])
                self.assertEqual(recovered["learner_message_count"], 1)
                self.assertFalse(recovered["can_continue"])

    def test_server_reports_a_safe_tutor_failure_and_retries_the_saved_message(
        self,
    ) -> None:
        demo = DemoController(load_content_pack(PACK_PATH), mode="guarded_tutor")
        demo.start(session_id="demo.retry.message.01")
        attempts = 0

        def flaky_reply(_messages, _info):
            nonlocal attempts
            attempts += 1
            if attempts == 1:
                raise ModelHTTPError(429, "synthetic-model-name",
                    body={"error": "provider secret must not reach the browser",
                          "api_key": "synthetic-provider-key-do-not-log"})
            return ModelResponse(parts=[TextPart("Let us examine that idea.")])

        server = create_demo_server(
            demo,
            port=0,
            model=FunctionModel(flaky_reply),
            unguarded_tutor=True,
        )
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base_url = f"http://{server.server_address[0]}:{server.server_address[1]}"
        body = {
            "request_id": "demo.retry.message.request.01",
            "text": "Could rain explain both details?",
        }

        def post() -> dict[str, object]:
            request = Request(
                f"{base_url}/api/message",
                data=json.dumps(body).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urlopen(request, timeout=5) as response:
                return json.loads(response.read())

        try:
            with override_allow_model_requests(False):
                with patch("educagent_sdk.web_demo.sys.stderr", new=io.StringIO()) as diagnostic_log:
                    with self.assertRaises(HTTPError) as failed:
                        post()
                failure = json.loads(failed.exception.read())
                self.assertEqual(failed.exception.code, 503)
                self.assertEqual(failure["error"], "tutor unavailable")
                self.assertEqual(failure["diagnostic"], "ModelHTTPError")
                self.assertEqual(failure["upstream_status"], 429)
                self.assertEqual(failure["request_id"], body["request_id"])
                self.assertNotIn("provider secret", json.dumps(failure))
                self.assertNotIn("synthetic-provider-key-do-not-log", json.dumps(failure))
                self.assertIn("ModelHTTPError; upstream HTTP 429", diagnostic_log.getvalue())
                self.assertNotIn("provider secret", diagnostic_log.getvalue())
                self.assertNotIn("synthetic-provider-key-do-not-log", diagnostic_log.getvalue())
                self.assertEqual(
                    demo.view()["pending_tutor_message"],
                    {"request_id": body["request_id"], "text": body["text"]},
                )
                retried = post()
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)

        self.assertEqual(attempts, 2)
        self.assertIsNone(retried["pending_tutor_message"])
        self.assertEqual(retried["learner_message_count"], 1)
        self.assertEqual(retried["conversation"][-1]["role"], "tutor")

    def test_demo_allows_open_ended_free_text_discussion(self) -> None:
        pack = load_content_pack(ROOT / "content" / "causality_m0_full.json")
        demo = DemoController(pack, mode="guarded_tutor")
        demo.start(session_id="demo.dialogue-limit.01")
        clarify = next(
            candidate
            for candidate in message_teaching_candidates(
                pack.activities[0], support_level=0, support_budget=0
            )
            if candidate.move.strategy == "clarify"
        )

        async def send(index: int, question: str) -> None:
            request_id = f"demo.dialogue-limit.message.{index}"
            with override_allow_model_requests(False):
                await demo.send_message_with_tutor(
                    request_id=request_id,
                    text="treatment" if index == 1 else "yes",
                    model=TestModel(
                        custom_output_args={
                            "candidate_id": clarify.candidate_id,
                            "socratic_question": question,
                        }
                    ),
                )

        asyncio.run(send(1, "What part of your reasoning should we examine next?"))
        asyncio.run(send(2, "What judgment will you commit after this discussion?"))
        asyncio.run(send(3, "Can we look at another part of the scenario?"))
        self.assertEqual(demo.view()["learner_message_count"], 3)

    def test_entry_diagnostic_gates_m0_and_static_root_is_served(self) -> None:
        pack = load_content_pack(ROOT / "content" / "causality_m0_full.json")
        diagnostic = DiagnosticSession(
            pack, load_diagnostic_plan(ROOT / "content" / "causality_m0_diagnostic.json")
        )
        with tempfile.TemporaryDirectory() as directory:
            static_root = Path(directory) / "client"
            static_root.mkdir()
            (static_root / "index.html").write_text("<title>client</title>", encoding="utf-8")
            demo = DemoController(pack, mode="guarded_tutor")
            first_message_candidate = message_teaching_candidates(
                pack.activities[0], support_level=0, support_budget=0
            )[0]
            server = create_demo_server(
                demo,
                port=0,
                model=TestModel(
                    custom_output_args={
                        "candidate_id": first_message_candidate.candidate_id,
                        "socratic_question": "Which part of your idea should we examine first?",
                    }
                ),
                diagnostic=diagnostic,
                static_root=static_root,
            )
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base_url = f"http://{server.server_address[0]}:{server.server_address[1]}"

            def post(path: str, body: dict[str, str]) -> dict[str, object]:
                request = Request(
                    f"{base_url}{path}",
                    data=json.dumps(body).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urlopen(request, timeout=5) as response:
                    return json.loads(response.read())

            try:
                with urlopen(f"{base_url}/", timeout=5) as response:
                    self.assertIn(b"client", response.read())
                with self.assertRaises(HTTPError) as blocked:
                    post("/api/start", {})
                self.assertEqual(blocked.exception.code, 409)
                state = post("/api/diagnostic/start", {})
                self.assertEqual(state["diagnostic"]["status"], "in_progress")
                for index, activity in enumerate(diagnostic.activities, start=1):
                    choice = next(
                        choice
                        for choice in activity.choices
                        if choice.correct is (index != 1)
                    )
                    state = post(
                        "/api/diagnostic/respond",
                        {
                            "request_id": f"demo.diagnostic.answer.{index}",
                            "option_id": choice.option_id,
                        },
                    )
                self.assertTrue(state["learning_unlocked"])
                active = post("/api/start", {"session_id": "demo.diagnostic.session.01"})
                self.assertEqual(active["status"], "active")
                self.assertEqual(
                    active["scenario_image"],
                    {
                        "path": "media/causality-m0/variables-and-values-clinic.png",
                        "alt_text": "A clinician reviews three anonymised heart-rate records while patients rest in a clinic.",
                    },
                )
                message = post(
                    "/api/message",
                    {
                        "request_id": "demo.diagnostic.message.01",
                        "text": "Could you help me examine my idea?",
                    },
                )
                self.assertEqual(message["conversation"][-2]["role"], "learner")
                self.assertEqual(message["conversation"][-1]["role"], "tutor")
                self.assertEqual(
                    demo.developer_trace()["events"][-1]["selector_kind"], "tutor"
                )
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)

    def test_static_directory_url_serves_nested_index(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            static_root = Path(directory) / "client"
            portal_root = static_root / "portal"
            portal_root.mkdir(parents=True)
            (portal_root / "index.html").write_text(
                "<title>portal</title>", encoding="utf-8"
            )
            server = create_demo_server(
                DemoController(load_content_pack(PACK_PATH)),
                port=0,
                model=TestModel(),
                static_root=static_root,
            )
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base_url = f"http://{server.server_address[0]}:{server.server_address[1]}"
            try:
                with urlopen(f"{base_url}/portal/", timeout=5) as response:
                    self.assertEqual(response.status, 200)
                    self.assertIn(b"portal", response.read())
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)


if __name__ == "__main__":
    unittest.main()
