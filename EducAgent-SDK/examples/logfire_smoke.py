"""Send a minimal, content-free Logfire trace for local setup verification."""

import logfire
from pydantic_ai import Agent
from pydantic_ai.models.test import TestModel


def main() -> None:
    logfire.configure(
        service_name="educagent-sdk-observability-smoke",
        console=False,
        inspect_arguments=False,
        advanced=logfire.AdvancedOptions(
            base_url="https://logfire-eu.pydantic.dev",
        ),
    )
    logfire.instrument_system_metrics()
    logfire.instrument_pydantic_ai(include_content=False)

    with logfire.span("verify EducAgent SDK observability"):
        logfire.info("EducAgent SDK Logfire smoke trace emitted")

    Agent(
        TestModel(custom_output_text="ok"),
        name="educagent_observability_smoke_agent",
    ).run_sync("content-free instrumentation check")

    logfire.force_flush()


if __name__ == "__main__":
    main()
