# Logfire observability

The package does not configure telemetry when it is imported. Applications that
use EducAgent SDK must opt in at their process startup, before importing or
starting the components they want to observe.

For local development, authenticate the repository with the EU Logfire region:

```powershell
python -m logfire --base-url https://logfire-eu.pydantic.dev auth
python -m logfire --base-url https://logfire-eu.pydantic.dev projects use --org yuyang-xue starter-project
```

The resulting `.logfire/logfire_credentials.json` is ignored by Git. Never
commit its token or print it in logs. In CI, containers, and deployed services,
provide the same project's write token through the `LOGFIRE_TOKEN` secret.

Use this minimal startup configuration in an application entry point:

```python
import logfire

logfire.configure(
    service_name="your-service-name",
    send_to_logfire="if-token-present",
    inspect_arguments=False,
    advanced=logfire.AdvancedOptions(
        base_url="https://logfire-eu.pydantic.dev",
    ),
)
logfire.instrument_system_metrics()
logfire.instrument_pydantic_ai(include_content=False)
```

Do not put `logfire.configure()` in EducAgent SDK library code. Keep learner
responses, prompts, tool arguments, and released teaching content out of traces
unless a separate, explicit data-capture review approves it. Passing
`include_content=False` keeps Pydantic AI spans useful for timing, model, usage,
retry, and failure analysis without exporting prompt or response bodies.

For the SDK's own decision span, pass the supplied observer at the application
boundary:

```python
from educagent_sdk import logfire_tutor_observer, run_tutor_turn

result = await run_tutor_turn(
    events,
    pack,
    request_id="request.01",
    model=model,
    observer=logfire_tutor_observer,
)
```

The resulting `educagent.tutor.decision` span has only model/provider labels,
versions, context counts, proposal/selected candidate IDs, validation/fallback
facts, latency, and aggregate token/request counts. It intentionally excludes
session IDs, event IDs, learner text, prompts, resource text, and claim text.

To check that local credentials and export work without learner data, run:

```powershell
python examples/logfire_smoke.py
```

Look for service `educagent-sdk-observability-smoke`, operation `verify
EducAgent SDK observability`, and agent `educagent_observability_smoke_agent`
in the target project's Live view.
