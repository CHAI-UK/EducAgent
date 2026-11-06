"""Opt-in ELM latency probe; prints metrics only, never prompts or credentials."""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from time import perf_counter
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pydantic import BaseModel
from demo_server import ROOT, FramingResult, framing_agent, build_prompt, build_elm_model, load_elm_settings


class TaskOnly(BaseModel):
    task: FramingResult.model_fields["task"].annotation
    reason: str


async def measure(model, prompt, label, output_type):
    calls = []
    original = model.request

    async def timed(*args, **kwargs):
        start = perf_counter()
        try:
            return await original(*args, **kwargs)
        finally:
            calls.append(perf_counter() - start)

    start = perf_counter()
    with patch.object(model, "request", side_effect=timed):
        result = await framing_agent.run(prompt, model=model, output_type=output_type)
    elapsed = perf_counter() - start
    usage = result.usage() if callable(result.usage) else result.usage
    row = {"case": label, "total_s": round(elapsed, 3),
           "model_request_s": [round(t, 3) for t in calls],
           "non_model_s": round(elapsed - sum(calls), 3),
           "requests": usage.requests, "input_tokens": usage.input_tokens,
           "output_tokens": usage.output_tokens, "task": result.output.task,
           "output_chars": len(result.output.model_dump_json())}
    print(json.dumps(row), flush=True)


async def main():
    # Match the browser's unchanged Example 2 request, including teaching specs.
    source = (ROOT / "demo/worked-examples.js").read_text(encoding="utf-8")
    example = json.loads(source.split("const NirvanaWorkedExamples = ", 1)[1].strip().removesuffix(";"))["shift"]
    payload = {"message": example["problem"], "context":
        "Paper-anchored teaching example. Use these authored specifications as context, retaining teaching labels and unresolved decisions. Independently classify the question and explain relevant concepts. Specs: "
        + json.dumps(example["fields"], separators=(",", ":"), ensure_ascii=False), "history": []}
    start = perf_counter()
    prompt = build_prompt(payload)
    print(json.dumps({"prompt_build_ms": round((perf_counter() - start) * 1000, 3), "prompt_chars": len(prompt)}), flush=True)
    model = build_elm_model(load_elm_settings(ROOT.parent / "EducAgent-SDK/.env"))
    # Alternating order reduces, but cannot remove, provider/cache noise.
    for label, schema in [("full_1", FramingResult), ("task_only_1", TaskOnly),
                          ("task_only_2", TaskOnly), ("full_2", FramingResult)]:
        await measure(model, prompt, label, schema)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="Send the built-in example to configured ELM")
    if not parser.parse_args().live:
        parser.error("Explicit --live is required; this calls ELM four times")
    asyncio.run(main())
