import json
import unittest
from pathlib import Path

from pydantic import ValidationError

from educagent_sdk import (
    ChoiceEvidence,
    Evaluation,
    LearnerMessage,
    SessionStarted,
    SupportRequest,
    TeachingMove,
    append_teaching_move,
    close_attempt,
    complete_session,
    load_content_pack,
    pending_turn,
    record_choice_response,
    record_learner_message,
    record_support_request,
    recover_pending_turn,
    replay,
    select_fixed_policy_move,
    select_s4_move,
    start_attempt,
    start_session,
)
from educagent_sdk.events import (
    LearnerMessageRecorded, ResponseRecorded, can_complete_attempt,
)
from educagent_sdk.turns import validate_socratic_question_focus


ROOT = Path(__file__).resolve().parents[1]
PACK_PATH = ROOT / "content" / "causality_m0.json"
ACTIVITY_ID = "observation-vs-intervention.01"


def choice(option_id: str) -> ChoiceEvidence:
    return ChoiceEvidence(activity_id=ACTIVITY_ID, option_id=option_id)


class EventRuntimeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.pack = load_content_pack(PACK_PATH)
        self.events = []
        start_session(self.events, self.pack, session_id="session.01")
        start_attempt(self.events, self.pack, attempt_id="attempt.01")

    def test_event_models_enforce_specific_envelopes(self) -> None:
        dumped = self.events[0].model_dump(mode="python")
        dumped["attempt_id"] = "injected"
        with self.assertRaises(ValidationError):
            SessionStarted.model_validate(dumped)

        response = record_choice_response(
            self.events,
            self.pack,
            attempt_id="attempt.01",
            request_id="request.01",
            evidence=choice("association-only"),
            curriculum_requirements_met=True,
        )
        missing_request = response.model_dump(mode="python")
        del missing_request["request_id"]
        with self.assertRaises(ValidationError):
            ResponseRecorded.model_validate(missing_request)

    def test_historical_runtime_start_replays_without_rewriting_its_provenance(self) -> None:
        self.assertEqual(self.events[0].payload.runtime_version, "0.10.0")
        historical = self.events[0].model_dump(mode="json")
        historical["payload"]["runtime_version"] = "0.8.0"
        serialized = json.dumps(historical)
        restored = SessionStarted.model_validate_json(serialized)
        events = [restored, *self.events[1:]]
        original_prefix = tuple(event.model_dump_json() for event in events)
        self.assertEqual(replay(events).runtime_version, "0.8.0")
        record_choice_response(
            events, self.pack, attempt_id="attempt.01", request_id="historical.answer",
            evidence=choice("association-only"), curriculum_requirements_met=True,
        )
        select_fixed_policy_move(events, self.pack, request_id="historical.answer")
        self.assertTrue(can_complete_attempt(replay(events)))
        close_attempt(events, self.pack, attempt_id="attempt.01", status="completed")
        self.assertIn(ACTIVITY_ID, replay(events).completed_activity_ids)
        self.assertEqual(replay(events).runtime_version, "0.8.0")
        self.assertEqual(tuple(event.model_dump_json() for event in events[:2]), original_prefix)

        for version in ("0.7.9", "0.8.2", "9.0.0"):
            with self.subTest(version=version), self.assertRaisesRegex(ValueError, "unsupported runtime_version"):
                incompatible = dict(historical)
                incompatible["payload"] = {**historical["payload"], "runtime_version": version}
                replay([SessionStarted.model_validate_json(json.dumps(incompatible))])

    def test_scored_response_is_recorded_before_the_move(self) -> None:
        response = record_choice_response(
            self.events,
            self.pack,
            attempt_id="attempt.01",
            request_id="request.01",
            evidence=choice("association-only"),
            curriculum_requirements_met=True,
        )
        pending = replay(self.events)

        self.assertEqual(response.sequence, 3)
        self.assertEqual(pending.phase, "awaiting_move")
        self.assertEqual(pending.pending_input_event_id, response.event_id)
        self.assertEqual(pending.advance_allowed_for_event_id, response.event_id)

        move = select_s4_move(self.events, self.pack, request_id="request.01")
        self.assertEqual(move.payload.move.strategy, "advance")
        self.assertEqual(move.payload.selector_kind, "baseline")
        self.assertEqual(move.payload.evidence_event_ids, (response.event_id,))

    def test_fixed_policy_control_reuses_the_same_baseline_gate(self) -> None:
        response = record_choice_response(
            self.events,
            self.pack,
            attempt_id="attempt.01",
            request_id="request.fixed.01",
            evidence=choice("association-only"),
            curriculum_requirements_met=True,
        )
        move = select_fixed_policy_move(
            self.events, self.pack, request_id="request.fixed.01"
        )
        self.assertEqual(move.payload.selector_kind, "baseline")
        self.assertEqual(move.payload.move.strategy, "advance")
        self.assertEqual(move.payload.evidence_event_ids, (response.event_id,))

    def test_repeated_explicit_explanation_keeps_direct_teaching_and_legacy_clarify_legal(self) -> None:
        def request(request_id):
            record_support_request(self.events, self.pack, attempt_id="attempt.01",
                request_id=request_id, request=SupportRequest(kind="explanation"))
            return pending_turn(self.events, self.pack, request_id=request_id)

        first = request("explain.first")
        self.assertEqual([item.move.strategy for item in first.candidates], ["direct_instruction", "hold"])
        append_teaching_move(self.events, self.pack, request_id="explain.first",
            candidate=first.candidates[0], selector_kind="tutor")
        second = request("explain.historical")
        self.assertEqual([item.move.strategy for item in second.candidates],
            ["direct_instruction", "clarify", "hold"])
        legacy = next(item for item in second.candidates if item.move.strategy == "clarify")
        append_teaching_move(self.events, self.pack, request_id="explain.historical",
            candidate=legacy, selector_kind="tutor", decision_trace_id="historical.explanation")
        # Existing repeated-Explanation events cite this old clarify candidate.
        frozen_history = tuple(event.model_dump_json() for event in self.events)
        restored = [type(event).model_validate_json(text)
            for event, text in zip(self.events, frozen_history, strict=True)]
        self.assertEqual(replay(restored), replay(self.events))
        third = request("explain.repeat")
        direct = next(item for item in third.candidates if item.move.strategy == "direct_instruction")
        repeated = append_teaching_move(self.events, self.pack, request_id="explain.repeat",
            candidate=direct, selector_kind="tutor")
        count = len(self.events)
        self.assertEqual(append_teaching_move(self.events, self.pack, request_id="explain.repeat",
            candidate=direct, selector_kind="tutor"), repeated)
        self.assertEqual(len(self.events), count)
        state = replay(self.events)
        self.assertEqual(state.response_ordinal, 0)
        self.assertIsNone(state.completion_evidence_event_id)
        self.assertEqual(tuple(event.model_dump_json() for event in self.events[:len(restored)]), frozen_history)

    def test_repeat_explanation_does_not_remove_the_ordinary_direct_instruction_reuse_gate(self) -> None:
        record_support_request(self.events, self.pack, attempt_id="attempt.01",
            request_id="explain.once", request=SupportRequest(kind="explanation"))
        first = pending_turn(self.events, self.pack, request_id="explain.once")
        append_teaching_move(self.events, self.pack, request_id="explain.once",
            candidate=first.candidates[0], selector_kind="tutor")
        record_learner_message(self.events, self.pack, attempt_id="attempt.01",
            request_id="explain.normal-message", message=LearnerMessage(text="I am considering the comparison."))
        normal = pending_turn(self.events, self.pack, request_id="explain.normal-message")
        self.assertEqual([item.move.strategy for item in normal.candidates], ["clarify", "hold"])
        append_teaching_move(self.events, self.pack, request_id="explain.normal-message",
            candidate=normal.candidates[0], selector_kind="tutor")
        record_support_request(self.events, self.pack, attempt_id="attempt.01",
            request_id="explain.clarification", request=SupportRequest(kind="clarification"))
        clarify = pending_turn(self.events, self.pack, request_id="explain.clarification")
        self.assertEqual([item.move.strategy for item in clarify.candidates], ["clarify", "hold"])

    def test_rejected_response_uses_hint_and_increments_support(self) -> None:
        record_choice_response(
            self.events,
            self.pack,
            attempt_id="attempt.01",
            request_id="request.01",
            evidence=choice("association-proves-intervention"),
            curriculum_requirements_met=False,
        )
        move = select_s4_move(self.events, self.pack, request_id="request.01")
        state = replay(self.events)

        self.assertEqual(move.payload.move.strategy, "socratic_hint")
        self.assertEqual(state.phase, "awaiting_response")
        self.assertEqual(state.support_level, 1)
        self.assertFalse(state.last_evaluation.accepted)
        self.assertIsNone(state.advance_allowed_for_event_id)

    def test_checked_answer_survives_optional_discussion_without_stale_advance(self) -> None:
        response = record_choice_response(
            self.events, self.pack, attempt_id="attempt.01",
            request_id="request.answer", evidence=choice("association-only"),
            curriculum_requirements_met=True,
        )
        select_fixed_policy_move(self.events, self.pack, request_id="request.answer")
        checked = replay(self.events)
        self.assertEqual(checked.phase, "awaiting_response")
        self.assertTrue(can_complete_attempt(checked))
        self.assertEqual(checked.completion_evidence_event_id, response.event_id)

        record_learner_message(
            self.events, self.pack, attempt_id="attempt.01",
            request_id="request.follow-up", message=LearnerMessage(text="Why?"),
        )
        pending = replay(self.events)
        self.assertIsNone(pending.advance_allowed_for_event_id)
        self.assertFalse(can_complete_attempt(pending))
        with self.assertRaisesRegex(ValueError, "validated advance"):
            close_attempt(self.events, self.pack, attempt_id="attempt.01", status="completed")
        turn = pending_turn(self.events, self.pack, request_id="request.follow-up")
        self.assertNotIn("advance", [candidate.move.strategy for candidate in turn.candidates])
        recover_pending_turn(self.events, self.pack, request_id="request.follow-up")
        self.assertTrue(can_complete_attempt(replay(self.events)))

        record_support_request(
            self.events, self.pack, attempt_id="attempt.01",
            request_id="request.explain", request=SupportRequest(kind="explanation"),
        )
        select_fixed_policy_move(self.events, self.pack, request_id="request.explain")
        discussed = replay(self.events)
        self.assertTrue(discussed.last_evaluation.accepted)
        self.assertTrue(can_complete_attempt(discussed))
        self.assertEqual(discussed.completion_evidence_event_id, response.event_id)
        self.assertEqual(discussed.response_ordinal, 1)
        self.assertEqual(discussed.support_level, checked.support_level)
        close_attempt(self.events, self.pack, attempt_id="attempt.01", status="completed")
        self.assertIn(ACTIVITY_ID, replay(self.events).completed_activity_ids)
        self.assertIsNone(replay(self.events).completion_evidence_event_id)

    def test_new_scored_response_revokes_the_previous_checked_answer(self) -> None:
        record_choice_response(
            self.events, self.pack, attempt_id="attempt.01",
            request_id="request.answer", evidence=choice("association-only"),
            curriculum_requirements_met=True,
        )
        select_fixed_policy_move(self.events, self.pack, request_id="request.answer")
        record_choice_response(
            self.events, self.pack, attempt_id="attempt.01",
            request_id="request.revise", evidence=choice("association-proves-intervention"),
            curriculum_requirements_met=True,
        )
        select_fixed_policy_move(self.events, self.pack, request_id="request.revise")
        self.assertFalse(can_complete_attempt(replay(self.events)))
        self.assertIsNone(replay(self.events).completion_evidence_event_id)
        with self.assertRaisesRegex(ValueError, "validated advance"):
            close_attempt(self.events, self.pack, attempt_id="attempt.01", status="completed")

    def test_support_request_is_unscored_and_receives_scoped_hold(self) -> None:
        support = record_support_request(
            self.events,
            self.pack,
            attempt_id="attempt.01",
            request_id="request.01",
            request=SupportRequest(kind="clarification"),
        )
        pending = replay(self.events)

        self.assertIsNone(pending.last_evaluation)
        self.assertEqual(pending.response_ordinal, 0)
        self.assertEqual(pending.explicit_support_request.kind, "clarification")

        move = select_s4_move(self.events, self.pack, request_id="request.01")
        state = replay(self.events)
        self.assertEqual(move.payload.move.strategy, "hold")
        self.assertEqual(move.payload.selector_kind, "unsupported_request")
        self.assertEqual(move.payload.evidence_event_ids, (support.event_id,))
        self.assertEqual(state.phase, "awaiting_response")
        self.assertEqual(state.support_level, 0)
        self.assertIsNone(state.last_evaluation)

    def test_recovery_preserves_scored_evidence_but_clears_advance(self) -> None:
        response = record_choice_response(
            self.events,
            self.pack,
            attempt_id="attempt.01",
            request_id="request.01",
            evidence=choice("association-only"),
            curriculum_requirements_met=True,
        )
        recovered = recover_pending_turn(
            self.events,
            self.pack,
            request_id="request.01",
        )
        repeated = recover_pending_turn(
            self.events,
            self.pack,
            request_id="request.01",
        )
        state = replay(self.events)

        self.assertEqual(recovered, repeated)
        self.assertEqual(len(self.events), 4)
        self.assertEqual(recovered.payload.move.strategy, "hold")
        self.assertEqual(recovered.payload.selector_kind, "recovery")
        self.assertEqual(recovered.payload.evidence_event_ids, (response.event_id,))
        self.assertTrue(state.last_evaluation.accepted)
        self.assertIsNone(state.advance_allowed_for_event_id)

    def test_recovery_preserves_unscored_support_identity(self) -> None:
        record_support_request(
            self.events,
            self.pack,
            attempt_id="attempt.01",
            request_id="request.01",
            request=SupportRequest(kind="do_not_know"),
        )
        recovered = recover_pending_turn(
            self.events,
            self.pack,
            request_id="request.01",
        )
        state = replay(self.events)

        self.assertEqual(recovered.payload.move.strategy, "hold")
        self.assertEqual(state.response_ordinal, 0)
        self.assertIsNone(state.last_evaluation)

    def test_request_id_is_idempotent_and_changed_content_conflicts(self) -> None:
        first = record_choice_response(
            self.events,
            self.pack,
            attempt_id="attempt.01",
            request_id="request.01",
            evidence=choice("association-only"),
            curriculum_requirements_met=True,
        )
        repeated = record_choice_response(
            self.events,
            self.pack,
            attempt_id="attempt.01",
            request_id="request.01",
            evidence=choice("association-only"),
            curriculum_requirements_met=True,
        )
        self.assertEqual(first, repeated)
        self.assertEqual(len(self.events), 3)

        with self.assertRaisesRegex(ValueError, "different content"):
            record_choice_response(
                self.events,
                self.pack,
                attempt_id="attempt.01",
                request_id="request.01",
                evidence=choice("association-proves-intervention"),
                curriculum_requirements_met=False,
            )
        with self.assertRaisesRegex(ValueError, "different content"):
            record_support_request(
                self.events,
                self.pack,
                attempt_id="attempt.01",
                request_id="request.01",
                request=SupportRequest(kind="explanation"),
            )

    def test_one_request_cannot_receive_two_moves(self) -> None:
        record_choice_response(
            self.events,
            self.pack,
            attempt_id="attempt.01",
            request_id="request.01",
            evidence=choice("association-proves-intervention"),
            curriculum_requirements_met=False,
        )
        first = select_s4_move(self.events, self.pack, request_id="request.01")
        second = select_s4_move(self.events, self.pack, request_id="request.01")

        self.assertEqual(first, second)
        self.assertEqual(len(self.events), 4)

    def test_only_exact_accepted_current_response_can_complete(self) -> None:
        record_choice_response(
            self.events,
            self.pack,
            attempt_id="attempt.01",
            request_id="request.01",
            evidence=choice("association-proves-intervention"),
            curriculum_requirements_met=True,
        )
        select_s4_move(self.events, self.pack, request_id="request.01")
        with self.assertRaisesRegex(ValueError, "validated advance"):
            close_attempt(
                self.events,
                self.pack,
                attempt_id="attempt.01",
                status="completed",
            )

    def test_complete_lifecycle_replays_to_identical_state(self) -> None:
        record_choice_response(
            self.events,
            self.pack,
            attempt_id="attempt.01",
            request_id="request.01",
            evidence=choice("association-only"),
            curriculum_requirements_met=True,
        )
        select_s4_move(self.events, self.pack, request_id="request.01")
        close_attempt(
            self.events,
            self.pack,
            attempt_id="attempt.01",
            status="completed",
        )
        complete_session(self.events, self.pack)

        live = replay(self.events)
        copied = tuple(
            type(event).model_validate(event.model_dump(mode="python"))
            for event in self.events
        )
        restored = replay(copied)

        self.assertEqual(live, restored)
        self.assertEqual(live.status, "completed")
        self.assertEqual(live.phase, "complete")
        self.assertEqual(live.completed_activity_ids, (ACTIVITY_ID,))
        self.assertEqual([event.sequence for event in self.events], list(range(1, 7)))

    def test_empty_preferred_route_is_complete_instead_of_expanding_to_all(self) -> None:
        events = []
        start_session(
            events,
            self.pack,
            session_id="session.targeted.01",
            preferred_activity_ids=(),
            route_scope="preferred",
        )

        completed = complete_session(events, self.pack)

        self.assertEqual(completed.payload.satisfied_predicate_ids, ("curriculum.completed",))
        self.assertEqual(replay(events).status, "completed")

    def test_replay_rejects_non_monotonic_history_without_mutating_it(self) -> None:
        original = tuple(self.events)
        invalid = list(self.events)
        invalid[1] = invalid[1].model_copy(update={"sequence": 3})

        with self.assertRaisesRegex(ValueError, "expected event sequence"):
            replay(invalid)
        self.assertEqual(tuple(self.events), original)

    def test_replay_rejects_a_forged_support_budget(self) -> None:
        invalid = list(self.events)
        started = invalid[1]
        invalid[1] = started.model_copy(
            update={
                "payload": started.payload.model_copy(update={"support_budget": 99})
            }
        )

        with self.assertRaisesRegex(ValueError, "support_budget"):
            replay(invalid)

    def test_replay_rejects_a_forged_evaluation(self) -> None:
        response = record_choice_response(
            self.events,
            self.pack,
            attempt_id="attempt.01",
            request_id="request.01",
            evidence=choice("association-only"),
            curriculum_requirements_met=True,
        )
        invalid = list(self.events)
        invalid[-1] = response.model_copy(
            update={
                "payload": response.payload.model_copy(
                    update={
                        "evaluation": Evaluation(
                            accepted=False,
                            misconception_id="association-implies-intervention",
                            consequence_resource_id=(
                                "observation-vs-intervention.consequence.rejected"
                            ),
                        )
                    }
                )
            }
        )

        with self.assertRaisesRegex(ValueError, "evaluation does not match"):
            replay(invalid)

    def test_replay_rejects_a_forged_baseline_move(self) -> None:
        record_choice_response(
            self.events,
            self.pack,
            attempt_id="attempt.01",
            request_id="request.01",
            evidence=choice("association-only"),
            curriculum_requirements_met=True,
        )
        move = select_s4_move(self.events, self.pack, request_id="request.01")
        invalid = list(self.events)
        invalid[-1] = move.model_copy(
            update={
                "payload": move.payload.model_copy(
                    update={
                        "move": TeachingMove(
                            strategy="elicit",
                            resource_id="observation-vs-intervention.question.01",
                        )
                    }
                )
            }
        )

        with self.assertRaisesRegex(ValueError, "not canonical"):
            replay(invalid)

    def test_learner_message_is_bounded_idempotent_and_unscored(self) -> None:
        for text in ("", " " * 4, "x" * 1001):
            with self.subTest(length=len(text)), self.assertRaises(ValidationError):
                LearnerMessage(text=text)

        message = LearnerMessage(text="Could you explain what intervention means?")
        first = record_learner_message(
            self.events,
            self.pack,
            attempt_id="attempt.01",
            request_id="request.message.01",
            message=message,
        )
        repeated = record_learner_message(
            self.events,
            self.pack,
            attempt_id="attempt.01",
            request_id="request.message.01",
            message=message,
        )
        state = replay(self.events)

        self.assertEqual(first, repeated)
        self.assertEqual(len(self.events), 3)
        self.assertEqual(state.pending_learner_message, message)
        self.assertEqual(state.response_ordinal, 0)
        self.assertIsNone(state.last_evaluation)
        self.assertIsNone(state.advance_allowed_for_event_id)

        with self.assertRaisesRegex(ValueError, "different content"):
            record_learner_message(
                self.events,
                self.pack,
                attempt_id="attempt.01",
                request_id="request.message.01",
                message=LearnerMessage(text="Changed message"),
            )

    def test_replay_allows_open_ended_learner_messages(self) -> None:
        for ordinal in (1, 2):
            record_learner_message(
                self.events,
                self.pack,
                attempt_id="attempt.01",
                request_id=f"request.message.0{ordinal}",
                message=LearnerMessage(text="Please help me inspect this."),
            )
            recover_pending_turn(
                self.events,
                self.pack,
                request_id=f"request.message.0{ordinal}",
            )

        state = replay(self.events)
        self.assertEqual(state.learner_message_count, 2)
        last_message = next(
            event
            for event in reversed(self.events)
            if isinstance(event, LearnerMessageRecorded)
        )
        overspent = last_message.model_copy(
            update={
                "event_id": "session.01.event.7",
                "sequence": 7,
                "request_id": "request.message.03",
                "payload": last_message.payload.model_copy(
                    update={"message": LearnerMessage(text="One more question.")}
                ),
            }
        )
        state = replay((*self.events, overspent))
        self.assertEqual(state.learner_message_count, 3)

    def test_question_focus_check_covers_every_question_strategy(self) -> None:
        question = "Which part of the record should we inspect next?"
        for strategy in ("elicit", "socratic_hint", "reflect"):
            with self.subTest(strategy=strategy), self.assertRaisesRegex(
                ValueError,
                "current activity question",
            ):
                validate_socratic_question_focus(
                    question,
                    strategy,
                    activity_question=question,
                )

    def test_replay_allows_a_free_form_clarify_reply(self) -> None:
        record_learner_message(
            self.events,
            self.pack,
            attempt_id="attempt.01",
            request_id="request.message.01",
            message=LearnerMessage(text="What should I look at?"),
        )
        pending = pending_turn(self.events, self.pack, request_id="request.message.01")
        clarify = next(
            candidate
            for candidate in pending.candidates
            if candidate.move.strategy == "clarify"
        )
        move = append_teaching_move(
            self.events,
            self.pack,
            request_id="request.message.01",
            candidate=clarify,
            selector_kind="tutor",
            socratic_question=(
                "What evidence would you inspect before deciding what changes the outcome?"
            ),
        )
        self.assertIsNotNone(move.payload.activity_question_text)
        invalid = list(self.events)
        invalid[-1] = move.model_copy(
            update={
                "payload": move.payload.model_copy(
                    update={
                        "socratic_question": "That is the correct classification.",
                    }
                )
            }
        )
        replay(invalid)

    def test_learner_message_recovery_appends_one_hold(self) -> None:
        record_learner_message(
            self.events,
            self.pack,
            attempt_id="attempt.01",
            request_id="request.message.01",
            message=LearnerMessage(text="I am not sure."),
        )
        first = recover_pending_turn(
            self.events,
            self.pack,
            request_id="request.message.01",
        )
        repeated = recover_pending_turn(
            self.events,
            self.pack,
            request_id="request.message.01",
        )

        self.assertEqual(first, repeated)
        self.assertEqual(first.payload.move.strategy, "hold")
        self.assertEqual(len(self.events), 4)
        self.assertIsNone(replay(self.events).last_evaluation)


if __name__ == "__main__":
    unittest.main()
