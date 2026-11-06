# Task latency profile — 11 September 2026

## Implemented follow-up: task-first background generation

The recommendation below is now implemented; its timing table remains a
historical direct-agent experiment, not a measurement of the new full flow.

1. Browser sends the question to `/api/classify` (task + reason only), reusing
   the same task rules and shared ELM configuration.
2. Classification unlocks Task confirmation, then starts `/api/frame` with
   `selected_task`. The backend validates task membership and rejects a mismatched
   result rather than silently changing the user's task.
3. A global status shows background preparation, readiness or failure. Users
   may continue through Framing/Brief while waiting. Completion updates content
   without navigation or opening the chatbot; edits still invalidate confirmation.
4. Task changes discard obsolete results; cached working specs can be restored.
   Problem edits, manual spec/ reasoning edits and reset abort the browser request.
   Failed drafts have a separate retry and a manual path. `other` skips drafting.

The local API now uses threaded HTTP handling with a shared asyncio event loop.
Provider calls may overlap, while frontend request identity prevents stale writes.
Browser cancellation does not guarantee cancellation of a request already being
processed by ELM; server calls retain a 90-second bound. This is not a persistent
job service. No new dependency or provider/model selection was introduced.

Validation: 4 Node tests and 14 Python tests pass, including delayed drafting,
early Task confirmation, task-switch cancellation, preserved cached fields,
obsolete-response isolation, failed-draft retry and concurrent classify/frame
HTTP requests. Chrome with the actual ELM showed Task Next enabled and the
background status before readiness, then populated MRI concepts and worked specs.
This is a smoke check, not a new latency distribution or classifier benchmark.

## Method

Explicitly requested live diagnosis using built-in, fictional Example 2 and the
shared ELM configuration. `tests/profile_task.py --live` runs four requests with
the browser-equivalent question/context. It times prompt assembly, each model
request and the remainder of Pydantic AI execution. It reports token counts but
does not log prompts, responses or secrets. No production classification change.

The control uses the same agent instructions and prompt but restricts output to
Task and reason. It is a payload-size experiment, not an implemented classifier
or a historical-build comparison. The full agent outputs Task, reason, tags,
all Brief fields, a chat reply and 2–4 concepts in one non-streaming response.

| Run | Total seconds | Model request seconds | Other local seconds | Requests | Input tokens | Output tokens |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Full 1 | 9.037 | 9.023 | 0.014 | 1 | 2489 | 894 |
| Task-only 1 | 2.170 | 2.165 | 0.005 | 1 | 2279 | 81 |
| Task-only 2 | 2.823 | 2.817 | 0.007 | 1 | 2279 | 139 |
| Full 2 | 9.015 | 9.007 | 0.008 | 1 | 2489 | 914 |

Prompt construction: 0.009 ms, 3176 characters. All four returned `shift`.
No agent-level retry occurred. Full mean: 9.026 s; task-only mean: 2.497 s.

## Interpretation and limits

Over 99.8% of measured full-run time was inside the model request. Local agent
orchestration/validation is not the measured bottleneck. The much larger output
is consistent with the slower response, but this probe cannot separate provider
queueing, network transport, prefill, reasoning and token generation. It also
does not measure browser paint, HTTP ingress queue time, or historical latency.
Two samples per variant are not a p95/SLA benchmark; caching/load can affect them.

The frontend labels this wait as categorisation, although it waits for the whole
artifact. Built-in worked examples subsequently use authored fields, so asking
the model to draft those fields duplicates work in that mode. The local backend
also uses single-threaded HTTPServer: another active request can add queue delay,
though these sequential direct probes do not measure that scenario.

Suggested next implementation, subject to approval: return a small task+reason
first; request task-specific Brief/concepts after confirmation (or background
prefetch with cancellation and task-change invalidation). For worked examples,
reuse authored specs and request only concepts rather than regenerating fields.
This changes request boundaries and should get its own interaction tests. It
has deliberately not been implemented as part of this diagnosis.

## UI verification in the same change

Chrome verified Problem help inline with its title, definition blockquotes,
three Framing actions on one desktop row, and causal applicability above tools.
Narrow layouts may wrap buttons rather than overflow. The two requested helper
sentences were removed; shared ELM disclosure remains elsewhere on the page.
