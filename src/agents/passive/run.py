#!/usr/bin/env python3
"""
CLI runner for the passive_course_agent ContentGenerator.

Usage:
    conda run -n edu python -m src.agents.passive.run

Environment variables:
    OPENROUTER_API_KEY   — required (or LLM_API_KEY as fallback)
    OPENROUTER_BASE_URL  — default: https://openrouter.ai/api/v1
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
import sys
import time
from pathlib import Path

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv

# Load env from project root
load_dotenv(PROJECT_ROOT / "EducAgent.env", override=False)
load_dotenv(PROJECT_ROOT / ".env", override=False)

from src.agents.passive.mock_data import (
    get_mock_input,
    get_passive_course_dir,
    get_passive_input_path,
    get_passive_output_path,
    get_passive_preview_path,
)
from src.agents.passive.markers import parse_image_marker
from src.agents.passive.text_normalization import normalize_llm_payload


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)-24s %(levelname)-5s │ %(message)s",
        datefmt="%H:%M:%S",
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def _expand_details_blocks(markdown: str) -> str:
    """Convert HTML details blocks into always-visible markdown for export/print."""
    pattern = re.compile(
        r"<details[^>]*>\s*<summary>(.*?)</summary>\s*(.*?)\s*</details>",
        flags=re.IGNORECASE | re.DOTALL,
    )

    def repl(match: re.Match[str]) -> str:
        summary_html = match.group(1).strip()
        body = match.group(2).strip()
        summary_text = re.sub(r"<[^>]+>", "", summary_html).strip() or "Answers"
        return f"\n**{summary_text}**\n\n{body}\n"

    return pattern.sub(repl, markdown)


def render_markdown(result: dict, output_dir: Path, *, expand_answers: bool = False) -> str:
    """Render the pipeline result as a clean markdown document."""
    concept_id = result.get("concept_ctx", {}).get("concept_id", "unknown")
    nodes = normalize_llm_payload(result.get("nodes", []))
    image_refs = result.get("image_refs", [])

    def to_markdown_alt_text(text: str) -> str:
        compact = re.sub(r"\s+", " ", text or "").strip()
        return compact.replace("[", r"\[").replace("]", r"\]")

    def to_relative_asset_path(url: str) -> str:
        path = Path(url)
        if path.is_absolute():
            resolved_path = path.resolve()
            try:
                return resolved_path.relative_to(output_dir.resolve()).as_posix()
            except ValueError:
                return resolved_path.as_posix()
        return url.replace("\\", "/")

    # Build image lookups
    img_by_marker: dict[tuple[str, str], str] = {}
    img_by_desc: dict[str, str] = {}
    used_markers: set[tuple[str, str]] = set()

    for r in image_refs:
        kind = r.get("kind", "PEDAGOGICAL_IMAGE")
        desc = r["description"]
        path = to_relative_asset_path(r["url"])
        img_by_marker[(kind, desc)] = path
        img_by_desc.setdefault(desc, path)

    lines = [f"# {concept_id.replace('-', ' ').title()}\n"]

    for node in nodes:
        sections = node.get("sections", [])

        for sec in sections:
            heading = sec.get("section", "")
            content = sec.get("content", "")

            def replace_image(match: re.Match[str]) -> str:
                parsed = parse_image_marker(match.group(0))
                if not parsed:
                    return match.group(0)
                kind, desc = parsed
                url = img_by_marker.get((kind, desc)) or img_by_desc.get(desc)
                if url:
                    used_markers.add((kind, desc))
                    return f"![{to_markdown_alt_text(desc)}]({url})"
                return f"*[Illustration: {kind}: {desc}]*"

            content = re.sub(r'\[(?:CONTEXT_IMAGE|PEDAGOGICAL_IMAGE|IMAGE):\s*[^\]]+\]', replace_image, content)
            if expand_answers:
                content = _expand_details_blocks(content)

            lines.append(f"## {heading}\n")
            lines.append(content)

            for marker in sec.get("markers", []):
                parsed = parse_image_marker(marker)
                if not parsed:
                    continue
                kind, desc = parsed
                if (kind, desc) not in used_markers:
                    url = img_by_marker.get((kind, desc)) or img_by_desc.get(desc)
                    if url:
                        used_markers.add((kind, desc))
                        lines.append(f"\n![{to_markdown_alt_text(desc)}]({url})")

            lines.append("")

        lines.append("---\n")

    rendered = "\n".join(lines)
    return _expand_details_blocks(rendered) if expand_answers else rendered


async def main():
    import argparse
    from src.agents.passive.graph import compile_graph

    parser = argparse.ArgumentParser(description="Run passive_course_agent pipeline")
    parser.add_argument("--user", type=str, default=None,
                        help="User ID to load input for (e.g. learner_40). "
                             "Defaults to most recent input.")
    parser.add_argument("--concept", type=str, default=None,
                        help="Concept ID (e.g. counterfactuals). "
                             "Required when --user is specified.")
    args = parser.parse_args()

    setup_logging()
    logger = logging.getLogger("passive_agent.run")

    logger.info("=" * 60)
    logger.info("passive_course_agent — ContentGenerator")
    logger.info("=" * 60)

    graph = compile_graph()

    if args.user:
        concept = args.concept or "counterfactuals"
        input_path = get_passive_input_path(args.user, concept)
        if not input_path.exists():
            logger.error("Input not found: %s", input_path)
            sys.exit(1)
        import json as _json
        with open(input_path) as f:
            mock_input = _json.load(f)
        logger.info("Loaded input for user=%s concept=%s", args.user, concept)
    else:
        mock_input = get_mock_input()

    initial_state = {
        "user_id": mock_input["user_id"],
        "concept_id": mock_input["concept_id"],
    }

    logger.info("Invoking pipeline with: %s", json.dumps(initial_state, indent=2))
    t0 = time.perf_counter()

    result = await graph.ainvoke(initial_state)

    elapsed = time.perf_counter() - t0
    logger.info("Pipeline completed in %.1fs", elapsed)

    # Summary
    outline = result.get("outline", [])
    nodes = result.get("nodes", [])
    images = result.get("image_refs", [])

    print("\n" + "=" * 70)
    print("PIPELINE SUMMARY")
    print("=" * 70)
    print(f"Cache key:    {result.get('cache_key', 'N/A')}")
    print(f"Depth tier:   {result.get('depth_tier', 'N/A')}")
    print(f"Profile:      {result.get('profile_sig', 'N/A')}")
    print(f"Outline:      {len(outline)} learning nodes")
    print(f"Content:      {len(nodes)} nodes generated")
    print(f"Images:       {len(images)} generated")
    print(f"Time:         {elapsed:.1f}s")

    print(f"\n--- OUTLINE ---")
    for i, node in enumerate(outline, 1):
        print(f"  {i}. {node.get('title', '?')}")
        print(f"     {node.get('summary', '')}")

    print(f"\n--- CONTENT ---")
    for node in nodes:
        print(f"\n{'='*50}")
        print(f"NODE: {node.get('node_title', '?')}")
        print(f"{'='*50}")
        for sec in node.get("sections", []):
            heading = sec.get("section", "?")
            content = sec.get("content", "")
            print(f"\n  ## {heading}")
            print(f"  {content[:400]}{'...' if len(content) > 400 else ''}")

    print("\n" + "=" * 70)

    # Save artifacts under the passive course directory
    user_id = initial_state["user_id"]
    concept_id = initial_state["concept_id"]
    output_dir = get_passive_course_dir(user_id, concept_id)
    output_dir.mkdir(parents=True, exist_ok=True)

    input_path = get_passive_input_path(user_id, concept_id)
    with open(input_path, "w") as f:
        json.dump(mock_input, f, indent=2, default=str)
    logger.info("Input snapshot: %s", input_path)

    json_path = get_passive_output_path(user_id, concept_id)
    with open(json_path, "w") as f:
        json.dump(result, f, indent=2, default=str)
    logger.info("Full output: %s", json_path)

    md_path = get_passive_preview_path(user_id, concept_id)
    md_content = render_markdown(result, output_dir)
    with open(md_path, "w") as f:
        f.write(md_content)
    logger.info("Markdown preview: %s", md_path)

    print_md_path = output_dir / "preview_print.md"
    print_md_content = render_markdown(result, output_dir, expand_answers=True)
    with open(print_md_path, "w") as f:
        f.write(print_md_content)
    logger.info("Print-friendly markdown: %s", print_md_path)


if __name__ == "__main__":
    asyncio.run(main())
