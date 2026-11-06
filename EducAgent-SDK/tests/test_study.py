"""Reproducible de-identified study-export contracts."""

import unittest
from pathlib import Path

from educagent_sdk import (
    build_study_run_manifest,
    export_study_run,
    frozen_m0_arm_manifests,
    load_content_pack,
)
from educagent_sdk.demo import DemoController


ROOT = Path(__file__).resolve().parents[1]
PACK_PATH = ROOT / "content" / "causality_m0_episode.json"


class StudyExportTest(unittest.TestCase):
    def test_model_backed_arms_require_researcher_selected_model_ids(self) -> None:
        pack = load_content_pack(PACK_PATH)
        model_backed_arms = tuple(
            arm
            for arm in frozen_m0_arm_manifests()
            if arm.kind in {"source_grounded_chat", "guarded_pydantic_ai"}
        )

        for arm in model_backed_arms:
            with self.subTest(arm=arm.arm_id):
                with self.assertRaisesRegex(ValueError, "concrete model_id"):
                    build_study_run_manifest(
                        pack,
                        study_id="m0.pilot.01",
                        run_id=f"m0.pilot.{arm.kind}",
                        arm=arm,
                        renderer_version="1.0.0",
                    )

        configured = model_backed_arms[0].model_copy(
            update={"model_id": "reviewer-selected-model"}
        )
        self.assertEqual(
            build_study_run_manifest(
                pack,
                study_id="m0.pilot.01",
                run_id="m0.pilot.configured-source-chat",
                arm=configured,
                renderer_version="1.0.0",
            ).arm.model_id,
            "reviewer-selected-model",
        )

    def test_export_is_deidentified_and_reproduces_separate_reports(self) -> None:
        pack = load_content_pack(PACK_PATH)
        demo = DemoController(pack)
        demo.start(session_id="research.session.private.01")
        demo.respond(
            request_id="research.response.01", option_id="commitment.interventional"
        )
        demo.respond(
            request_id="research.response.02", option_id="commitment.observational"
        )
        demo.continue_activity(request_id="research.continue.01")
        demo.respond(
            request_id="research.response.03",
            option_id="assumption.assigning-sleep-improves-concentration",
        )
        demo.continue_activity(request_id="research.continue.02")
        demo.respond(
            request_id="research.response.04", option_id="transfer.observational"
        )
        demo.continue_activity(request_id="research.continue.03")

        arm = next(
            item
            for item in frozen_m0_arm_manifests()
            if item.kind == "fixed_policy_control"
        )
        manifest = build_study_run_manifest(
            pack,
            study_id="m0.pilot.01",
            run_id="m0.pilot.run.01",
            arm=arm,
            renderer_version="1.0.0",
        )
        exported = export_study_run(
            demo.events,
            pack,
            manifest=manifest,
            pseudonym_secret="test-only-secret",
        )
        restored = export_study_run(
            tuple(demo.events),
            pack,
            manifest=manifest,
            pseudonym_secret="test-only-secret",
        )

        self.assertEqual(exported, restored)
        self.assertNotIn("research.session.private.01", exported.model_dump_json())
        self.assertNotIn("event_id", exported.model_dump_json())
        self.assertNotIn("artifact", exported.model_dump_json())
        self.assertEqual(exported.subject_correctness.accepted_response_count, 3)
        self.assertEqual(exported.subject_correctness.rejected_response_count, 1)
        self.assertEqual(exported.learning_outcomes.m1_ready_concept_count, 1)
        self.assertTrue(exported.pedagogy_protocol.quality.decision_count)

        wrong_manifest = manifest.model_copy(update={"pack_id": "different.pack"})
        with self.assertRaisesRegex(ValueError, "does not match"):
            export_study_run(
                demo.events,
                pack,
                manifest=wrong_manifest,
                pseudonym_secret="test-only-secret",
            )


if __name__ == "__main__":
    unittest.main()
