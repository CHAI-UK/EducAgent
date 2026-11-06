"""Redacted, opt-in observability for guarded tutor decisions."""

from collections.abc import Callable
from typing import Literal

from pydantic import Field

from .contracts import ContractModel, SemanticVersion, StableId


OBSERVABILITY_VERSION: SemanticVersion = "1.0.0"
TUTOR_SPAN_NAME = "educagent.tutor.decision"
ValidationResult = Literal["accepted", "fallback", "idempotent"]


class TutorContextMetrics(ContractModel):
    """Counts and size only; no prompt, learner text, or content payload."""

    serialized_characters: int = Field(ge=0)
    candidate_count: int = Field(ge=0)
    grounding_resource_count: int = Field(ge=0)
    grounding_claim_count: int = Field(ge=0)
    recent_event_count: int = Field(ge=0)


class TutorUsage(ContractModel):
    """Provider-neutral aggregate usage values for one agent run."""

    request_count: int = Field(ge=0)
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    retry_count: int = Field(ge=0)


class TutorDecisionTelemetry(ContractModel):
    """One redacted, non-authoritative tutor-decision observation."""

    agent_name: StableId
    provider: str = Field(min_length=1, max_length=120)
    model_name: str = Field(min_length=1, max_length=240)
    input_kind: Literal["scored_response", "support_request", "learner_message"] | None
    tutor_version: SemanticVersion
    prompt_version: SemanticVersion
    observability_version: SemanticVersion
    context: TutorContextMetrics | None = None
    proposed_candidate_id: StableId | None = None
    proposed_hypothesis_id: StableId | None = None
    selected_candidate_id: StableId | None = None
    selected_strategy: str | None = Field(default=None, max_length=80)
    selector_kind: str | None = Field(default=None, max_length=80)
    validation_result: ValidationResult
    fallback_reason: str | None = Field(default=None, max_length=120)
    latency_ms: int = Field(ge=0)
    usage: TutorUsage


TutorObserver = Callable[[TutorDecisionTelemetry], None]


def logfire_tutor_observer(telemetry: TutorDecisionTelemetry) -> None:
    """Emit one content-free Logfire span after application startup configures Logfire.

    Applications opt in by passing this observer to ``run_tutor_turn``.  This
    library deliberately does not configure Logfire, select a destination, or
    attach learner prompts, messages, released resources, or event identifiers.
    """

    import logfire

    attributes = telemetry.model_dump(mode="json")
    context = attributes.pop("context", None)
    usage = attributes.pop("usage")
    attributes.update(
        {
            f"educagent.context.{key}": value
            for key, value in (context or {}).items()
        }
    )
    attributes.update(
        {f"educagent.usage.{key}": value for key, value in usage.items()}
    )
    with logfire.span(TUTOR_SPAN_NAME, **attributes):
        pass
