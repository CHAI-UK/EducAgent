"""Generate or check the committed ContentPack JSON Schema."""

import argparse
import json
from pathlib import Path

from educagent_sdk import ContentPack, DiagnosticPlan


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "content-pack-v3.schema.json"
DIAGNOSTIC_SCHEMA_PATH = ROOT / "schemas" / "diagnostic-plan-v1.schema.json"


def render_schema() -> str:
    """Return the canonical schema bytes as text."""

    return json.dumps(
        ContentPack.model_json_schema(),
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ) + "\n"


def render_diagnostic_schema() -> str:
    """Return the canonical diagnostic-plan schema bytes as text."""

    return json.dumps(
        DiagnosticPlan.model_json_schema(),
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail when the committed schema differs from the generated schema",
    )
    args = parser.parse_args()
    generated = {
        SCHEMA_PATH: render_schema(),
        DIAGNOSTIC_SCHEMA_PATH: render_diagnostic_schema(),
    }

    if args.check:
        stale_paths = [
            str(path)
            for path, value in generated.items()
            if not path.exists() or path.read_text(encoding="utf-8") != value
        ]
        if stale_paths:
            parser.error(
                ", ".join(stale_paths) + " is out of date; run this script without --check"
            )
        return 0

    for path, value in generated.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
