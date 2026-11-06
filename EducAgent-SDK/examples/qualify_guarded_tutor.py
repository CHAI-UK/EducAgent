"""Run the real-provider S6/S9 qualification; never use this in the test suite."""

import argparse
import asyncio
import json
from pathlib import Path

from educagent_sdk import (
    ChoiceEvidence,
    ClassificationEvidence,
    SupportRequest,
    assess_tutor_quality,
    audit_tutor_trace,
    close_attempt,
    complete_session,
    load_content_pack,
    logfire_tutor_observer,
    record_choice_response,
    record_classification_response,
    record_support_request,
    replay,
    run_tutor_turn,
    start_attempt,
    start_session,
)
from educagent_sdk.elm import build_elm_model, load_elm_settings


ROOT = Path(__file__).resolve().parents[1]
EPISODE_PATH = ROOT / "content" / "causality_m0_episode.json"
SEED_PATH = ROOT / "content" / "causality_m0.json"


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--model",
        help="Override MODEL from the ELM .env file.",
    )
    parser.add_argument(
        "--env-file",
        type=Path,
        default=ROOT / ".env",
        help="ELM configuration file; process environment takes precedence.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Write the non-secret qualification record to this JSON file.",
    )
    parser.add_argument(
        "--logfire",
        action="store_true",
        help="Configure content-free Logfire instrumentation for this run.",
    )
    args = parser.parse_args()
    settings = load_elm_settings(args.env_file, model_name=args.model)
    model = build_elm_model(settings)
    observer = _configure_logfire() if args.logfire else None

    episode_events = []
    episode = load_content_pack(EPISODE_PATH)
    start_session(episode_events, episode, session_id="qualification.episode.01")
    start_attempt(episode_events, episode, attempt_id="qualification.commitment.01")

    original = record_classification_response(
        episode_events,
        episode,
        attempt_id="qualification.commitment.01",
        request_id="qualification.commitment.original",
        evidence=ClassificationEvidence(
            activity_id="observation-vs-intervention.commitment.01",
            classification_id="commitment.interventional",
            artifact_id="qualification.artifact.commitment",
        ),
        curriculum_requirements_met=True,
    )
    await _expect_strategy(
        episode_events, episode, "qualification.commitment.original", model, observer, "reflect"
    )
    record_classification_response(
        episode_events,
        episode,
        attempt_id="qualification.commitment.01",
        request_id="qualification.commitment.revision",
        evidence=ClassificationEvidence(
            activity_id="observation-vs-intervention.commitment.01",
            classification_id="commitment.observational",
            artifact_id="qualification.artifact.commitment",
            revises_evidence_event_id=original.event_id,
        ),
        curriculum_requirements_met=True,
    )
    await _expect_strategy(
        episode_events, episode, "qualification.commitment.revision", model, observer, "advance"
    )
    close_attempt(
        episode_events, episode, attempt_id="qualification.commitment.01", status="completed"
    )

    start_attempt(episode_events, episode, attempt_id="qualification.assumption.01")
    record_choice_response(
        episode_events,
        episode,
        attempt_id="qualification.assumption.01",
        request_id="qualification.assumption.wrong",
        evidence=ChoiceEvidence(
            activity_id="observation-vs-intervention.assumption.01",
            option_id="assumption.records-show-association",
        ),
        curriculum_requirements_met=False,
    )
    await _expect_strategy(
        episode_events, episode, "qualification.assumption.wrong", model, observer, "socratic_hint"
    )
    record_choice_response(
        episode_events,
        episode,
        attempt_id="qualification.assumption.01",
        request_id="qualification.assumption.correct",
        evidence=ChoiceEvidence(
            activity_id="observation-vs-intervention.assumption.01",
            option_id="assumption.assigning-sleep-improves-concentration",
        ),
        curriculum_requirements_met=True,
    )
    await _expect_strategy(
        episode_events, episode, "qualification.assumption.correct", model, observer, "advance"
    )
    close_attempt(
        episode_events, episode, attempt_id="qualification.assumption.01", status="completed"
    )

    start_attempt(episode_events, episode, attempt_id="qualification.transfer.01")
    record_classification_response(
        episode_events,
        episode,
        attempt_id="qualification.transfer.01",
        request_id="qualification.transfer.correct",
        evidence=ClassificationEvidence(
            activity_id="observation-vs-intervention.transfer.01",
            classification_id="transfer.observational",
            artifact_id="qualification.artifact.transfer",
        ),
        curriculum_requirements_met=True,
    )
    await _expect_strategy(
        episode_events, episode, "qualification.transfer.correct", model, observer, "advance"
    )
    close_attempt(
        episode_events, episode, attempt_id="qualification.transfer.01", status="completed"
    )
    complete_session(episode_events, episode)

    escalation_events = []
    seed = load_content_pack(SEED_PATH)
    start_session(escalation_events, seed, session_id="qualification.escape.01")
    start_attempt(escalation_events, seed, attempt_id="qualification.escape.attempt.01")
    record_choice_response(
        escalation_events,
        seed,
        attempt_id="qualification.escape.attempt.01",
        request_id="qualification.escape.wrong",
        evidence=ChoiceEvidence(
            activity_id="observation-vs-intervention.01",
            option_id="association-proves-intervention",
        ),
        curriculum_requirements_met=False,
    )
    await _expect_strategy(
        escalation_events, seed, "qualification.escape.wrong", model, observer, "socratic_hint"
    )
    record_support_request(
        escalation_events,
        seed,
        attempt_id="qualification.escape.attempt.01",
        request_id="qualification.escape.explain",
        request=SupportRequest(kind="explanation"),
    )
    await _expect_strategy(
        escalation_events, seed, "qualification.escape.explain", model, observer, "direct_instruction"
    )

    episode_assessment = assess_tutor_quality(audit_tutor_trace(episode_events, episode))
    escape_assessment = assess_tutor_quality(audit_tutor_trace(escalation_events, seed))
    if not episode_assessment.qualified or not escape_assessment.qualified:
        raise RuntimeError("the frozen automatic quality thresholds were not met")
    if replay(episode_events).status != "completed":
        raise RuntimeError("the provider did not complete the S6 episode")

    record = {
        "qualification_protocol_version": "1.0.0",
        "provider": "elm",
        "model": settings.model_name,
        "episode_status": "completed",
        "episode_quality": episode_assessment.model_dump(mode="json"),
        "escape_quality": escape_assessment.model_dump(mode="json"),
        "selected_strategies": [
            event.payload.move.strategy
            for event in (*episode_events, *escalation_events)
            if hasattr(event, "payload") and hasattr(event.payload, "move")
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(f"Qualification passed; wrote {args.output}")


async def _expect_strategy(events, pack, request_id, model, observer, strategy) -> None:
    result = await run_tutor_turn(
        events, pack, request_id=request_id, model=model, observer=observer
    )
    if result.used_fallback or result.event.payload.move.strategy != strategy:
        raise RuntimeError(
            f"{request_id} expected {strategy}; got {result.event.payload.move.strategy}"
        )


def _configure_logfire():
    import logfire

    logfire.configure(
        service_name="educagent-sdk-provider-qualification",
        send_to_logfire="if-token-present",
        advanced=logfire.AdvancedOptions(
            base_url="https://logfire-eu.pydantic.dev",
        ),
    )
    logfire.instrument_pydantic_ai(include_content=False)
    return logfire_tutor_observer


if __name__ == "__main__":
    asyncio.run(main())
