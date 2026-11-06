"""Content-free tutor telemetry and deterministic quality-audit contracts."""

import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from pydantic_ai.models import override_allow_model_requests
from pydantic_ai.models.test import TestModel

from educagent_sdk import (
    ChoiceEvidence,
    FROZEN_TUTOR_QUALITY_CASES,
    TUTOR_SPAN_NAME,
    assess_tutor_quality,
    audit_tutor_trace,
    build_tutor_deps,
    load_content_pack,
    logfire_tutor_observer,
    record_choice_response,
    run_tutor_turn,
    start_attempt,
    start_session,
    tutor_agent,
)


ROOT = Path(__file__).resolve().parents[1]
PACK_PATH = ROOT / "content" / "causality_m0.json"
ACTIVITY_ID = "observation-vs-intervention.01"


class TutorObservabilityTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.pack = load_content_pack(PACK_PATH)
        self.events = []
        start_session(self.events, self.pack, session_id="telemetry.session.01")
        start_attempt(self.events, self.pack, attempt_id="telemetry.attempt.01")
        record_choice_response(
            self.events,
            self.pack,
            attempt_id="telemetry.attempt.01",
            request_id="telemetry.request.01",
            evidence=ChoiceEvidence(
                activity_id=ACTIVITY_ID,
                option_id="association-proves-intervention",
            ),
            curriculum_requirements_met=False,
        )

    async def test_telemetry_is_redacted_and_quality_audit_is_repeatable(self) -> None:
        observed = []
        deps = build_tutor_deps(self.events, self.pack, request_id="telemetry.request.01")
        with override_allow_model_requests(False):
            result = await run_tutor_turn(
                self.events,
                self.pack,
                request_id="telemetry.request.01",
                model=TestModel(
                    custom_output_args={"candidate_id": deps.candidates[0].candidate_id}
                ),
                observer=observed.append,
            )

        self.assertFalse(result.used_fallback)
        self.assertEqual(len(observed), 1)
        self.assertFalse(tutor_agent.instrument.include_content)
        self.assertFalse(tutor_agent.instrument.include_model_request_parameters)
        telemetry = observed[0]
        self.assertEqual(telemetry.validation_result, "accepted")
        self.assertEqual(telemetry.context.candidate_count, 1)
        self.assertGreater(telemetry.context.serialized_characters, 0)
        self.assertNotIn("association-proves-intervention", telemetry.model_dump_json())
        self.assertNotIn("telemetry.session.01", telemetry.model_dump_json())
        self.assertNotIn("event_id", telemetry.model_dump_json())

        report = audit_tutor_trace(self.events, self.pack)
        assessment = assess_tutor_quality(report)
        self.assertEqual(report.decision_count, 1)
        self.assertEqual(report.grounding_violation_count, 0)
        self.assertEqual(report.illegal_advance_count, 0)
        self.assertTrue(assessment.qualified)
        self.assertEqual(len(FROZEN_TUTOR_QUALITY_CASES), 6)

    async def test_observer_and_logfire_export_cannot_change_runtime(self) -> None:
        deps = build_tutor_deps(self.events, self.pack, request_id="telemetry.request.01")

        def unavailable_observer(_telemetry) -> None:
            raise RuntimeError("telemetry destination unavailable")

        with override_allow_model_requests(False):
            result = await run_tutor_turn(
                self.events,
                self.pack,
                request_id="telemetry.request.01",
                model=TestModel(
                    custom_output_args={"candidate_id": deps.candidates[0].candidate_id}
                ),
                observer=unavailable_observer,
            )
        self.assertEqual(result.event.payload.move.strategy, "socratic_hint")

        span = MagicMock()
        span.__enter__.return_value = span
        span.__exit__.return_value = False
        with patch("logfire.span", return_value=span) as mock_span:
            logfire_tutor_observer(
                observed_telemetry(
                    model=TestModel(),
                    candidate_id=deps.candidates[0].candidate_id,
                )
            )
        self.assertEqual(mock_span.call_args.args[0], TUTOR_SPAN_NAME)
        attributes = mock_span.call_args.kwargs
        self.assertNotIn("context", attributes)
        self.assertNotIn("usage", attributes)
        self.assertNotIn("telemetry.session.01", str(attributes))


def observed_telemetry(*, model: TestModel, candidate_id: str):
    """Produce one real redacted item through the public callback shape."""

    from educagent_sdk import TutorContextMetrics, TutorDecisionTelemetry, TutorUsage

    return TutorDecisionTelemetry(
        agent_name="educagent_socratic_tutor",
        provider=model.system,
        model_name=model.model_name,
        input_kind="scored_response",
        tutor_version="1.1.0",
        prompt_version="1.1.0",
        observability_version="1.0.0",
        context=TutorContextMetrics(
            serialized_characters=100,
            candidate_count=1,
            grounding_resource_count=1,
            grounding_claim_count=1,
            recent_event_count=1,
        ),
        proposed_candidate_id=candidate_id,
        selected_candidate_id=candidate_id,
        selected_strategy="socratic_hint",
        selector_kind="tutor",
        validation_result="accepted",
        latency_ms=1,
        usage=TutorUsage(
            request_count=1,
            input_tokens=0,
            output_tokens=0,
            retry_count=0,
        ),
    )


if __name__ == "__main__":
    unittest.main()
