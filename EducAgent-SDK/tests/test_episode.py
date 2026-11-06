"""Contract test for one complete observation-versus-intervention episode."""

import unittest
from pathlib import Path

from pydantic_ai import ModelResponse
from pydantic_ai.messages import ToolCallPart
from pydantic_ai.models import override_allow_model_requests
from pydantic_ai.models.function import FunctionModel
from pydantic_ai.models.test import TestModel

from educagent_sdk import (
    ChoiceEvidence,
    ClassificationEvidence,
    build_tutor_deps,
    close_attempt,
    complete_session,
    load_content_pack,
    record_choice_response,
    record_classification_response,
    replay,
    record_support_request,
    run_tutor_turn,
    start_attempt,
    start_session,
    SupportRequest,
    validate_release,
)


ROOT = Path(__file__).resolve().parents[1]
PACK_PATH = ROOT / "content" / "causality_m0_episode.json"
COMMITMENT_ID = "observation-vs-intervention.commitment.01"
ASSUMPTION_ID = "observation-vs-intervention.assumption.01"
TRANSFER_ID = "observation-vs-intervention.transfer.01"


class ObservationInterventionEpisodeTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.pack = load_content_pack(PACK_PATH)
        self.assertEqual(validate_release(self.pack).unused_resource_ids, ())
        self.events = []
        start_session(self.events, self.pack, session_id="episode.session.01")
        start_attempt(self.events, self.pack, attempt_id="episode.attempt.commitment")

    async def choose_first(self, request_id: str):
        deps = build_tutor_deps(self.events, self.pack, request_id=request_id)
        with override_allow_model_requests(False):
            result = await run_tutor_turn(
                self.events,
                self.pack,
                request_id=request_id,
                model=TestModel(
                    custom_output_args={"candidate_id": deps.candidates[0].candidate_id}
                ),
            )
        return result

    async def complete_commitment_revision(self) -> None:
        original = record_classification_response(
            self.events,
            self.pack,
            attempt_id="episode.attempt.commitment",
            request_id="episode.request.commitment.original",
            evidence=ClassificationEvidence(
                activity_id=COMMITMENT_ID,
                classification_id="commitment.interventional",
                artifact_id="artifact.commitment.01",
            ),
            curriculum_requirements_met=True,
        )
        first = await self.choose_first("episode.request.commitment.original")
        self.assertEqual(first.event.payload.move.strategy, "reflect")
        self.assertIn("The clinic only observed", first.rendered_turn.text)
        self.assertEqual(
            first.event.payload.expected_evidence_predicate_ids,
            ("learner.revision",),
        )
        with self.assertRaisesRegex(ValueError, "validated advance"):
            close_attempt(
                self.events,
                self.pack,
                attempt_id="episode.attempt.commitment",
                status="completed",
            )
        self.assertEqual(replay(self.events).classification_artifact_id, "artifact.commitment.01")

        with self.assertRaisesRegex(ValueError, "later classification must name"):
            record_classification_response(
                self.events,
                self.pack,
                attempt_id="episode.attempt.commitment",
                request_id="episode.request.commitment.missing-revision",
                evidence=ClassificationEvidence(
                    activity_id=COMMITMENT_ID,
                    classification_id="commitment.observational",
                    artifact_id="artifact.commitment.01",
                ),
                curriculum_requirements_met=True,
            )
        with self.assertRaisesRegex(ValueError, "current artifact_id"):
            record_classification_response(
                self.events,
                self.pack,
                attempt_id="episode.attempt.commitment",
                request_id="episode.request.commitment.other-artifact",
                evidence=ClassificationEvidence(
                    activity_id=COMMITMENT_ID,
                    classification_id="commitment.observational",
                    artifact_id="artifact.other.01",
                    revises_evidence_event_id=original.event_id,
                ),
                curriculum_requirements_met=True,
            )
        with self.assertRaisesRegex(ValueError, "earlier in this session"):
            record_classification_response(
                self.events,
                self.pack,
                attempt_id="episode.attempt.commitment",
                request_id="episode.request.commitment.future",
                evidence=ClassificationEvidence(
                    activity_id=COMMITMENT_ID,
                    classification_id="commitment.observational",
                    artifact_id="artifact.commitment.01",
                    revises_evidence_event_id="episode.session.01.event.99",
                ),
                curriculum_requirements_met=True,
            )
        with self.assertRaisesRegex(ValueError, "earlier in this session"):
            record_classification_response(
                self.events,
                self.pack,
                attempt_id="episode.attempt.commitment",
                request_id="episode.request.commitment.cross-session",
                evidence=ClassificationEvidence(
                    activity_id=COMMITMENT_ID,
                    classification_id="commitment.observational",
                    artifact_id="artifact.commitment.01",
                    revises_evidence_event_id="other.session.event.3",
                ),
                curriculum_requirements_met=True,
            )

        revised = record_classification_response(
            self.events,
            self.pack,
            attempt_id="episode.attempt.commitment",
            request_id="episode.request.commitment.revision",
            evidence=ClassificationEvidence(
                activity_id=COMMITMENT_ID,
                classification_id="commitment.observational",
                artifact_id="artifact.commitment.01",
                revises_evidence_event_id=original.event_id,
            ),
            curriculum_requirements_met=True,
        )
        self.assertEqual(revised.payload.evaluation.accepted, True)
        advanced = await self.choose_first("episode.request.commitment.revision")
        self.assertEqual(advanced.event.payload.move.strategy, "advance")
        close_attempt(
            self.events,
            self.pack,
            attempt_id="episode.attempt.commitment",
            status="completed",
        )

    async def test_complete_episode_is_replayable_and_transfers_without_hint(self) -> None:
        await self.complete_commitment_revision()

        start_attempt(self.events, self.pack, attempt_id="episode.attempt.assumption")
        self.assertEqual(replay(self.events).current_activity_id, ASSUMPTION_ID)
        record_choice_response(
            self.events,
            self.pack,
            attempt_id="episode.attempt.assumption",
            request_id="episode.request.assumption.wrong",
            evidence=ChoiceEvidence(
                activity_id=ASSUMPTION_ID,
                option_id="assumption.records-show-association",
            ),
            curriculum_requirements_met=False,
        )
        hint = await self.choose_first("episode.request.assumption.wrong")
        self.assertEqual(hint.event.payload.move.strategy, "socratic_hint")
        self.assertIn("Separate seeing patients", hint.rendered_turn.text)

        record_choice_response(
            self.events,
            self.pack,
            attempt_id="episode.attempt.assumption",
            request_id="episode.request.assumption.correct",
            evidence=ChoiceEvidence(
                activity_id=ASSUMPTION_ID,
                option_id="assumption.assigning-sleep-improves-concentration",
            ),
            curriculum_requirements_met=True,
        )
        self.assertEqual(
            (await self.choose_first("episode.request.assumption.correct"))
            .event.payload.move.strategy,
            "advance",
        )
        close_attempt(
            self.events,
            self.pack,
            attempt_id="episode.attempt.assumption",
            status="completed",
        )

        transfer = start_attempt(
            self.events,
            self.pack,
            attempt_id="episode.attempt.transfer",
        )
        self.assertEqual(transfer.activity_id, TRANSFER_ID)
        self.assertEqual(replay(self.events).support_level, 0)
        self.assertEqual(transfer.payload.activity.question_resource_id, "episode.transfer.question")
        self.assertNotIn("hint", transfer.payload.activity.question_resource_id)

        record_classification_response(
            self.events,
            self.pack,
            attempt_id="episode.attempt.transfer",
            request_id="episode.request.transfer.correct",
            evidence=ClassificationEvidence(
                activity_id=TRANSFER_ID,
                classification_id="transfer.observational",
                artifact_id="artifact.transfer.01",
            ),
            curriculum_requirements_met=True,
        )

        def select_advance(messages, info):
            return ModelResponse(
                parts=[ToolCallPart(info.output_tools[0].name, {"candidate_id": "tutor.advance"})]
            )

        with override_allow_model_requests(False):
            transfer_result = await run_tutor_turn(
                self.events,
                self.pack,
                request_id="episode.request.transfer.correct",
                model=FunctionModel(select_advance),
            )
        self.assertEqual(transfer_result.event.payload.move.strategy, "advance")
        close_attempt(
            self.events,
            self.pack,
            attempt_id="episode.attempt.transfer",
            status="completed",
        )
        complete_session(self.events, self.pack)

        live = replay(self.events)
        restored = replay(
            tuple(type(event).model_validate(event.model_dump(mode="python")) for event in self.events)
        )
        self.assertEqual(live, restored)
        self.assertEqual(live.status, "completed")
        self.assertEqual(
            live.completed_activity_ids,
            (COMMITMENT_ID, ASSUMPTION_ID, TRANSFER_ID),
        )

    async def test_revised_wrong_classification_uses_hint_and_direct_teaching_needs_retry(self) -> None:
        original = record_classification_response(
            self.events,
            self.pack,
            attempt_id="episode.attempt.commitment",
            request_id="episode.request.commitment.wrong-original",
            evidence=ClassificationEvidence(
                activity_id=COMMITMENT_ID,
                classification_id="commitment.interventional",
                artifact_id="artifact.commitment.02",
            ),
            curriculum_requirements_met=True,
        )
        await self.choose_first("episode.request.commitment.wrong-original")
        record_classification_response(
            self.events,
            self.pack,
            attempt_id="episode.attempt.commitment",
            request_id="episode.request.commitment.wrong-revision",
            evidence=ClassificationEvidence(
                activity_id=COMMITMENT_ID,
                classification_id="commitment.interventional",
                artifact_id="artifact.commitment.02",
                revises_evidence_event_id=original.event_id,
            ),
            curriculum_requirements_met=True,
        )
        self.assertEqual(
            (await self.choose_first("episode.request.commitment.wrong-revision"))
            .event.payload.move.strategy,
            "socratic_hint",
        )

        record_support_request(
            self.events,
            self.pack,
            attempt_id="episode.attempt.commitment",
            request_id="episode.request.commitment.explain",
            request=SupportRequest(kind="explanation"),
        )
        direct = await self.choose_first("episode.request.commitment.explain")
        self.assertEqual(direct.event.payload.move.strategy, "direct_instruction")
        self.assertTrue(replay(self.events).requires_new_learner_action)
        with self.assertRaisesRegex(ValueError, "validated advance"):
            close_attempt(
                self.events,
                self.pack,
                attempt_id="episode.attempt.commitment",
                status="completed",
            )

    def test_activity_discriminator_rejects_the_wrong_evidence_type(self) -> None:
        with self.assertRaisesRegex(ValueError, "does not accept choice evidence"):
            record_choice_response(
                self.events,
                self.pack,
                attempt_id="episode.attempt.commitment",
                request_id="episode.request.commitment.wrong-type",
                evidence=ChoiceEvidence(
                    activity_id=COMMITMENT_ID,
                    option_id="commitment.observational",
                ),
                curriculum_requirements_met=True,
            )


if __name__ == "__main__":
    unittest.main()
