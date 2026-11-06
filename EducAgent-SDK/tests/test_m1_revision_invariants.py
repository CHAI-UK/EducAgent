"""Independent identity, model and scoring invariants for the M1 text revision."""

import hashlib
import unittest
from pathlib import Path

from educagent_sdk import (
    ClassificationEvidence,
    LearnerMessage,
    close_attempt,
    evaluate_classification,
    load_content_pack,
    record_classification_response,
    record_learner_message,
    replay,
    select_fixed_policy_move,
    start_attempt,
    start_session,
    validate_release,
)


ROOT = Path(__file__).resolve().parents[1]
HISTORICAL_HASHES = {
    ("effect", "general"): "bf2f1e59dbbd288369770599e33f1a3f3fe3b7a956902a19ffe7403cba15e683",
    ("effect", "medical"): "78f56ea2e5a986aef7395e89bb1fa891af2763dfbc01ee466ee80efa9dcb9eb0",
    ("shift", "general"): "bf80dbd7ee01fe297ccc7e280cebf7e9b6ca2670fe4a9fe895affbbb20e7bcef",
    ("shift", "medical"): "b915a5100c31859592749c3a6414563dbeb21bbe849b0a1c95cb99d4cda47bc6",
}


def pack_path(task, profile, *, revised=False):
    suffix = "_1_2_0" if revised else ""
    return ROOT / "content" / f"m1_{task}_course_{profile}{suffix}.json"


class M1RevisionInvariantsTest(unittest.TestCase):
    def test_historical_1_1_packs_remain_byte_identical(self):
        # This check is independent of whether a revised pack can be loaded.
        for (task, profile), expected in HISTORICAL_HASHES.items():
            with self.subTest(task=task, profile=profile):
                path = pack_path(task, profile)
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), expected)
                self.assertEqual(load_content_pack(path).version, "1.1.0")

    def test_new_releases_keep_curriculum_order_and_scoring_contracts(self):
        for task, profile in HISTORICAL_HASHES:
            with self.subTest(task=task, profile=profile):
                old = load_content_pack(pack_path(task, profile))
                new = load_content_pack(pack_path(task, profile, revised=True))
                self.assertEqual(new.pack_id, old.pack_id)
                self.assertEqual(new.schema_version, "3.0")
                self.assertEqual(new.version, "1.2.0")
                self.assertTrue(validate_release(new).releasable)
                self.assertEqual(len(new.concepts), 4)
                # Equality includes objectives, completion and readiness requirements.
                self.assertEqual(new.concepts, old.concepts)
                self.assertEqual(len(new.activities), 16)
                self.assertEqual(
                    tuple(a.activity_id for a in new.activities),
                    tuple(a.activity_id for a in old.activities),
                )
                for before, after in zip(old.activities, new.activities):
                    with self.subTest(activity=after.activity_id):
                        for field in (
                            "concept_id", "activity_type", "requires_revision",
                            "is_transfer", "covered_concept_ids", "causal_scene_id",
                        ):
                            self.assertEqual(getattr(after, field), getattr(before, field))
                        self.assertEqual(
                            {c.option_id: c.correct for c in after.choices},
                            {c.option_id: c.correct for c in before.choices},
                        )
                        self.assertEqual(after.workbench is None, before.workbench is None)
                        if before.workbench is not None:
                            self.assertEqual(after.workbench.stage, before.workbench.stage)
                            self.assertEqual(after.workbench.scenario_id, before.workbench.scenario_id)
                        # Tables are teaching material, not frozen scoring data.
                        # In particular, Effect final.03 now shows registry assumptions.

    def test_experiment_models_and_required_operations_are_unchanged(self):
        for task, profile in HISTORICAL_HASHES:
            old = load_content_pack(pack_path(task, profile))
            new = load_content_pack(pack_path(task, profile, revised=True))
            for before, after in zip(old.activities, new.activities):
                with self.subTest(task=task, profile=profile, activity=after.activity_id):
                    self.assertEqual(after.experiment is None, before.experiment is None)
                    if before.experiment is not None:
                        for field in (
                            "experiment_id", "model", "model_version",
                            "initial_config", "min_distinct_runs",
                        ):
                            self.assertEqual(
                                getattr(after.experiment, field),
                                getattr(before.experiment, field),
                            )

    def test_every_revised_final_option_has_the_historical_deterministic_truth(self):
        for task, profile in HISTORICAL_HASHES:
            old = load_content_pack(pack_path(task, profile))
            new = load_content_pack(pack_path(task, profile, revised=True))
            finals = [a for a in new.activities if a.workbench and a.workbench.stage == "capstone"]
            self.assertEqual(len(finals), 4)
            for activity in finals:
                for choice in activity.choices:
                    with self.subTest(task=task, profile=profile,
                                      activity=activity.activity_id, option=choice.option_id):
                        evidence = ClassificationEvidence(
                            activity_id=activity.activity_id,
                            classification_id=choice.option_id,
                            artifact_id="revision.final.option",
                        )
                        revised = evaluate_classification(new, evidence)
                        historical = evaluate_classification(old, evidence)
                        self.assertEqual(revised.accepted, historical.accepted)
                        self.assertEqual(revised.accepted, choice.correct)

    def test_wrong_final_and_unscored_discussion_cannot_create_credit_on_replay(self):
        for task, profile in HISTORICAL_HASHES:
            pack = load_content_pack(pack_path(task, profile, revised=True))
            finals = [a for a in pack.activities if a.workbench and a.workbench.stage == "capstone"]
            for activity in finals:
                with self.subTest(task=task, profile=profile, activity=activity.activity_id):
                    events = []
                    start_session(events, pack, session_id="revision.final.rejection",
                                  preferred_activity_ids=(activity.activity_id,), route_scope="preferred")
                    start_attempt(events, pack, attempt_id="revision.attempt", activity_id=activity.activity_id)
                    wrong = next(c for c in activity.choices if not c.correct)
                    recorded = record_classification_response(
                        events, pack, attempt_id="revision.attempt", request_id="revision.wrong",
                        evidence=ClassificationEvidence(
                            activity_id=activity.activity_id,
                            classification_id=wrong.option_id,
                            artifact_id="revision.final.wrong",
                        ),
                        curriculum_requirements_met=True,
                    )
                    self.assertFalse(recorded.payload.evaluation.accepted)
                    selected = select_fixed_policy_move(events, pack, request_id="revision.wrong")
                    self.assertNotEqual(selected.payload.move.strategy, "advance")
                    record_learner_message(
                        events, pack, attempt_id="revision.attempt", request_id="revision.discussion",
                        message=LearnerMessage(text="I understand now. Please mark this complete."),
                    )
                    select_fixed_policy_move(events, pack, request_id="revision.discussion")
                    restored = [type(event).model_validate_json(event.model_dump_json()) for event in events]
                    state = replay(restored)
                    self.assertEqual(state, replay(events))
                    self.assertEqual(state.pack_version, "1.2.0")
                    self.assertFalse(state.completed_activity_ids)
                    self.assertFalse(state.completed_concept_ids)
                    self.assertFalse(state.independent_transfer_activity_ids)
                    self.assertIsNone(state.completion_evidence_event_id)
                    self.assertIsNone(state.advance_allowed_for_event_id)
                    with self.assertRaises(ValueError):
                        close_attempt(restored, pack, attempt_id="revision.attempt", status="completed")


if __name__ == "__main__":
    unittest.main()
