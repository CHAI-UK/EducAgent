"""Reusable deterministic entry-diagnostic contracts."""

import json
import tempfile
import unittest
from pathlib import Path

from pydantic import ValidationError

from educagent_sdk import (
    DiagnosticPlan,
    DiagnosticSession,
    load_content_pack,
    load_diagnostic_plan,
)


ROOT = Path(__file__).resolve().parents[1]
PACK_PATH = ROOT / "content" / "causality_m0_full.json"
PLAN_PATH = ROOT / "content" / "causality_m0_diagnostic.json"
SCHEMA_PATH = ROOT / "schemas" / "diagnostic-plan-v1.schema.json"


class DiagnosticTest(unittest.TestCase):
    def setUp(self) -> None:
        self.pack = load_content_pack(PACK_PATH)
        self.plan = load_diagnostic_plan(PLAN_PATH)

    def test_plan_runs_released_activities_with_deterministic_results(self) -> None:
        diagnostic = DiagnosticSession(self.pack, self.plan)

        initial = diagnostic.view()
        self.assertEqual(initial["status"], "not_started")
        self.assertIsNone(initial["question"])

        started = diagnostic.start()
        self.assertEqual(started["status"], "in_progress")
        self.assertEqual(started["total"], 9)
        self.assertIn("resting heart rate", started["question"])
        self.assertEqual(
            started["scenario_image"],
            {
                "path": "media/causality-m0/variables-and-values-clinic.png",
                "alt_text": "A clinician reviews three anonymised heart-rate records while patients rest in a clinic.",
            },
        )

        for index, activity in enumerate(diagnostic.activities, start=1):
            correct = next(choice for choice in activity.choices if choice.correct)
            view = diagnostic.respond(
                request_id=f"diagnostic.answer.{index}", option_id=correct.option_id
            )

        self.assertEqual(view["status"], "completed")
        self.assertIsNone(view["question"])
        result = view["result"]
        assert isinstance(result, dict)
        self.assertEqual(result["accepted_count"], 9)
        self.assertEqual(result["starting_point"], "ready_to_begin")
        self.assertEqual(len(result["concept_results"]), 9)
        self.assertIn("does not replace", result["next_step"])

    def test_displayed_correct_choice_position_varies_across_questions(self) -> None:
        session = DiagnosticSession(pack=self.pack, plan=self.plan)
        session.start()
        correct_positions: list[int] = []

        for index, activity in enumerate(session.activities):
            view = session.view()
            correct = next(choice for choice in activity.choices if choice.correct)
            correct_positions.append(
                next(
                    position
                    for position, choice in enumerate(view["choices"])
                    if choice["option_id"] == correct.option_id
                )
            )
            session.respond(
                request_id=f"diagnostic.answer.order.{index}",
                option_id=correct.option_id,
            )

        self.assertEqual({0, 1}, set(correct_positions))

    def test_response_is_idempotent_and_wrong_answers_are_not_hidden(self) -> None:
        diagnostic = DiagnosticSession(self.pack, self.plan)
        diagnostic.start()
        first = diagnostic.respond(
            request_id="diagnostic.answer.01", option_id="variables.practice.fixed"
        )
        repeated = diagnostic.respond(
            request_id="diagnostic.answer.01", option_id="variables.practice.fixed"
        )

        self.assertEqual(first, repeated)
        self.assertEqual(first["answered_count"], 1)
        self.assertFalse(diagnostic.responses[0].evaluation.accepted)
        with self.assertRaisesRegex(ValueError, "different content"):
            diagnostic.respond(
                request_id="diagnostic.answer.01",
                option_id="variables.practice.variable",
            )

    def test_plan_rejects_duplicates_and_unknown_pack_activity(self) -> None:
        with self.assertRaises(ValidationError):
            DiagnosticPlan(
                schema_version="1.0",
                diagnostic_id="duplicate.plan",
                version="1.0.0",
                title="Duplicate plan",
                introduction="Duplicate entries are not meaningful.",
                activity_ids=(
                    "variables-and-values.practice",
                    "variables-and-values.practice",
                ),
            )

        unknown = DiagnosticPlan(
            schema_version="1.0",
            diagnostic_id="unknown.plan",
            version="1.0.0",
            title="Unknown activity plan",
            introduction="This plan must fail before it is presented.",
            activity_ids=("missing.activity",),
        )
        with self.assertRaisesRegex(ValueError, "unknown activities"):
            DiagnosticSession(self.pack, unknown)

    def test_json_loader_rejects_duplicate_object_keys(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "duplicate.json"
            path.write_text(
                '{"schema_version":"1.0","schema_version":"1.0"}',
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "duplicate JSON object key"):
                load_diagnostic_plan(path)

    def test_committed_schema_is_current(self) -> None:
        from scripts.generate_schema import render_diagnostic_schema

        self.assertEqual(
            SCHEMA_PATH.read_text(encoding="utf-8"), render_diagnostic_schema()
        )


if __name__ == "__main__":
    unittest.main()
