"""Replay-derived learner-profile contracts."""

import unittest
from pathlib import Path

from pydantic_ai.models import override_allow_model_requests
from pydantic_ai.models.test import TestModel

from educagent_sdk import (
    ChoiceEvidence,
    ClassificationEvidence,
    SupportRequest,
    build_tutor_deps,
    close_attempt,
    complete_session,
    load_content_pack,
    policy_learner_view,
    project_learner_profile,
    record_choice_response,
    record_classification_response,
    record_support_request,
    run_tutor_turn,
    start_attempt,
    start_session,
)


ROOT = Path(__file__).resolve().parents[1]
PACK_PATH = ROOT / "content" / "causality_m0_episode.json"
COMMITMENT_ID = "observation-vs-intervention.commitment.01"
ASSUMPTION_ID = "observation-vs-intervention.assumption.01"
TRANSFER_ID = "observation-vs-intervention.transfer.01"


class LearnerProfileTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.pack = load_content_pack(PACK_PATH)
        self.events = []
        start_session(self.events, self.pack, session_id="profile.session.01")

    async def choose_first(
        self,
        request_id: str,
        *,
        hypothesis_id: str | None = None,
        supporting_event_id: str | None = None,
    ):
        deps = build_tutor_deps(self.events, self.pack, request_id=request_id)
        output = {"candidate_id": deps.candidates[0].candidate_id}
        if hypothesis_id is not None:
            output["misconception_hypothesis_id"] = hypothesis_id
            output["supporting_event_ids"] = [supporting_event_id]
        with override_allow_model_requests(False):
            return await run_tutor_turn(
                self.events,
                self.pack,
                request_id=request_id,
                model=TestModel(custom_output_args=output),
            )

    async def test_profile_is_traceable_without_a_permanent_label(self) -> None:
        start_attempt(self.events, self.pack, attempt_id="profile.commitment")
        original = record_classification_response(
            self.events,
            self.pack,
            attempt_id="profile.commitment",
            request_id="profile.commitment.original",
            evidence=ClassificationEvidence(
                activity_id=COMMITMENT_ID,
                classification_id="commitment.interventional",
                artifact_id="profile.artifact.commitment",
            ),
            curriculum_requirements_met=True,
        )
        reflected = await self.choose_first(
            "profile.commitment.original",
            hypothesis_id="recording-is-assignment",
            supporting_event_id=original.event_id,
        )
        self.assertEqual(reflected.event.payload.move.strategy, "reflect")

        revised = record_classification_response(
            self.events,
            self.pack,
            attempt_id="profile.commitment",
            request_id="profile.commitment.revision",
            evidence=ClassificationEvidence(
                activity_id=COMMITMENT_ID,
                classification_id="commitment.observational",
                artifact_id="profile.artifact.commitment",
                revises_evidence_event_id=original.event_id,
            ),
            curriculum_requirements_met=True,
        )
        self.assertEqual(
            (await self.choose_first("profile.commitment.revision"))
            .event.payload.move.strategy,
            "advance",
        )
        close_attempt(
            self.events, self.pack, attempt_id="profile.commitment", status="completed"
        )

        start_attempt(self.events, self.pack, attempt_id="profile.assumption")
        record_choice_response(
            self.events,
            self.pack,
            attempt_id="profile.assumption",
            request_id="profile.assumption.wrong",
            evidence=ChoiceEvidence(
                activity_id=ASSUMPTION_ID,
                option_id="assumption.records-show-association",
            ),
            curriculum_requirements_met=False,
        )
        self.assertEqual(
            (await self.choose_first("profile.assumption.wrong"))
            .event.payload.move.strategy,
            "socratic_hint",
        )
        supported_success = record_choice_response(
            self.events,
            self.pack,
            attempt_id="profile.assumption",
            request_id="profile.assumption.correct",
            evidence=ChoiceEvidence(
                activity_id=ASSUMPTION_ID,
                option_id="assumption.assigning-sleep-improves-concentration",
            ),
            curriculum_requirements_met=True,
        )
        await self.choose_first("profile.assumption.correct")
        close_attempt(
            self.events, self.pack, attempt_id="profile.assumption", status="completed"
        )

        start_attempt(self.events, self.pack, attempt_id="profile.transfer")
        record_classification_response(
            self.events,
            self.pack,
            attempt_id="profile.transfer",
            request_id="profile.transfer.correct",
            evidence=ClassificationEvidence(
                activity_id=TRANSFER_ID,
                classification_id="transfer.observational",
                artifact_id="profile.artifact.transfer",
            ),
            curriculum_requirements_met=True,
        )
        self.assertEqual(
            (await self.choose_first("profile.transfer.correct"))
            .event.payload.move.strategy,
            "advance",
        )
        close_attempt(
            self.events, self.pack, attempt_id="profile.transfer", status="completed"
        )
        complete_session(self.events, self.pack)

        profile = project_learner_profile(self.events)
        concept = profile.concepts[0]
        self.assertEqual(concept.attempt_count, 3)
        self.assertIn(original.event_id, concept.rejected_event_ids)
        self.assertEqual(len(concept.rejected_event_ids), 2)
        self.assertIn(revised.event_id, concept.accepted_event_ids)
        self.assertEqual(concept.revision_event_ids, (revised.event_id,))
        self.assertEqual(
            concept.hint_dependent_success_event_ids, (supported_success.event_id,)
        )
        self.assertEqual(concept.transfer_status, "independent")
        self.assertEqual(len(concept.hypotheses), 1)
        self.assertEqual(concept.hypotheses[0].hypothesis_id, "recording-is-assignment")
        self.assertTrue(concept.expected_evidence)
        self.assertTrue(all(item.matched for item in concept.expected_evidence))

        restored = project_learner_profile(
            tuple(
                type(event).model_validate(event.model_dump(mode="python"))
                for event in self.events
            )
        )
        self.assertEqual(profile, restored)

        policy = policy_learner_view(profile, max_concepts=1)
        self.assertEqual(len(policy.concepts), 1)
        self.assertEqual(policy.concepts[0].accepted_count, 3)
        self.assertEqual(policy.concepts[0].rejected_count, 2)
        self.assertNotIn("event_id", policy.model_dump_json())
        self.assertNotIn("hypothes", policy.model_dump_json())
        with self.assertRaisesRegex(ValueError, "positive integer"):
            policy_learner_view(profile, max_concepts=0)

    async def test_support_is_counted_before_each_answer_not_retroactively(self) -> None:
        for revise in (False, True):
            with self.subTest(revise_after_explanation=revise):
                self.events = []
                start_session(self.events, self.pack, session_id="profile.support-order")
                start_attempt(
                    self.events, self.pack, attempt_id="profile.transfer",
                    activity_id=TRANSFER_ID,
                )
                original = record_classification_response(
                    self.events, self.pack, attempt_id="profile.transfer",
                    request_id="support-order.original",
                    evidence=ClassificationEvidence(
                        activity_id=TRANSFER_ID, classification_id="transfer.observational",
                        artifact_id="support-order.artifact",
                    ),
                    curriculum_requirements_met=True,
                )
                await self.choose_first("support-order.original")
                record_support_request(
                    self.events, self.pack, attempt_id="profile.transfer",
                    request_id="support-order.explain", request=SupportRequest(kind="explanation"),
                )
                explained = await self.choose_first("support-order.explain")
                self.assertEqual(explained.event.payload.move.strategy, "direct_instruction")
                concept = project_learner_profile(self.events).concepts[0]
                self.assertEqual(concept.hint_dependent_success_event_ids, ())

                supported = None
                if revise:
                    rejected = record_classification_response(
                        self.events, self.pack, attempt_id="profile.transfer",
                        request_id="support-order.rejected",
                        evidence=ClassificationEvidence(
                            activity_id=TRANSFER_ID, classification_id="transfer.interventional",
                            artifact_id="support-order.artifact",
                            revises_evidence_event_id=original.event_id,
                        ),
                        curriculum_requirements_met=True,
                    )
                    await self.choose_first("support-order.rejected")
                    supported = record_classification_response(
                        self.events, self.pack, attempt_id="profile.transfer",
                        request_id="support-order.revised",
                        evidence=ClassificationEvidence(
                            activity_id=TRANSFER_ID, classification_id="transfer.observational",
                            artifact_id="support-order.artifact",
                            revises_evidence_event_id=rejected.event_id,
                        ),
                        curriculum_requirements_met=True,
                    )
                    await self.choose_first("support-order.revised")
                close_attempt(
                    self.events, self.pack, attempt_id="profile.transfer", status="completed",
                )
                concept = project_learner_profile(self.events).concepts[0]
                self.assertEqual(
                    concept.hint_dependent_success_event_ids,
                    () if supported is None else (supported.event_id,),
                )
                self.assertEqual(concept.transfer_status, "supported" if revise else "independent")


if __name__ == "__main__":
    unittest.main()
