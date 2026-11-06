# Causal-scene quality rubric

- **Version:** 1.0
- **Applies to:** the released `causality.rain-umbrella` scene and its guarded tutor director
- **Purpose:** qualify interaction quality; it does not establish a learning-effect claim or replace the S11 pilot.

## Review unit

Review one complete attempt, including the hook, a graph submission, a prediction,
the intervention result, a revision, and final causal-model evidence. Inspect the
append-only trace beside the rendered workbench. Do not infer a tutor's hidden
reasoning from prose.

## Human rubric

Score each item `0` (absent or harmful), `1` (adequate), or `2` (clear and useful).

| Item | Question | Required floor |
| --- | --- | --- |
| Action acknowledgement | Does the turn respond to the learner's latest graph, prediction, result, or revision? | 1 |
| Productive direction | Does it direct one visible next action rather than reopen a general chat topic? | 1 |
| Non-repetition | Does it avoid restating the original activity prompt or a recent teaching question? | 1 |
| Visible-result grounding | After intervention, does it point to the displayed deterministic result before asking for revision? | 1 |
| Authority boundary | Does it avoid awarding correctness, changing state, or inventing causal facts/tools? | 2 |
| Recovery | After an incorrect final model, does the bounded released hint ladder, then direct teaching if needed, lead to a fresh editable model action? | 1 |

The attempt fails qualification if `Authority boundary` is below `2`, any other
item is `0`, or a runtime fallback prevents the learner from taking the declared
next action. A passing review is not evidence of learning improvement.

## Failure taxonomy

Record the first actionable category; record a secondary category only if it
changes the remediation owner.

| Category | Examples | Owner / first remediation |
| --- | --- | --- |
| Content | missing released resource, misleading scene label, incorrect deterministic table | content and causal reviewer |
| Prompt | repeated question, generic chat response, ignores latest learner action | tutor master instruction or output validation |
| Tool contract | missing frozen snapshot field, undeclared focus, wrong action/result lookup | causal-scene/tutor boundary |
| Runtime | invalid proposal not rejected, stale action accepted, rejected evidence advances | event replay and evaluator |
| Renderer / accessibility | keyboard cannot reach a graph action, result lacks text equivalent, narrow layout hides active controls | Astryx client |
| Provider | timeout, invalid structured output, unavailable model | provider configuration and retry/fallback telemetry |

## Required evidence for S23

1. Run the provider-independent FunctionModel trajectory for hook, incorrect
   graph, prediction, result, clarification, rejected final model, bounded
   hint, direct teaching after the hint budget, revision, and accepted final
   model.
2. Run at least one configured ELM trajectory and retain its redacted event
   trace ID, focus/job sequence, fallback count, and reviewer scores.
3. Check the browser with mouse, keyboard, text alternative, and a narrow-screen
   layout. Record the browser/version and any taxonomy entries.
4. Keep immediate/delayed transfer comparison under the frozen S11 protocol;
   do not label this review a learning-effect result.
