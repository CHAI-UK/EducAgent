"""
Input loader and path helpers for passive_course_agent.

Canonical storage layout:
  data/user/{user_id}/passive_courses/{concept_id}/
    - input.json
    - output.json
    - preview.md
    - imgs/

Legacy input paths are still supported as fallbacks.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
LEGACY_INPUT_PATHS = [
    PROJECT_ROOT / "data" / "user" / "passive_content_generation_input.json",
    PROJECT_ROOT / "data" / "passive_content_generation_input.json",
]

_data_cache: dict[Path, dict] = {}


def _slugify_path_part(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", (value or "").strip())
    return slug.strip("-._") or "unknown"


def get_passive_course_dir(user_id: str, concept_id: str) -> Path:
    return (
        PROJECT_ROOT
        / "data"
        / "user"
        / _slugify_path_part(user_id)
        / "passive_courses"
        / _slugify_path_part(concept_id)
    )


def get_passive_input_path(user_id: str, concept_id: str) -> Path:
    return get_passive_course_dir(user_id, concept_id) / "input.json"


def get_passive_output_path(user_id: str, concept_id: str) -> Path:
    return get_passive_course_dir(user_id, concept_id) / "output.json"


def get_passive_preview_path(user_id: str, concept_id: str) -> Path:
    return get_passive_course_dir(user_id, concept_id) / "preview.md"


def get_passive_images_dir(user_id: str, concept_id: str) -> Path:
    return get_passive_course_dir(user_id, concept_id) / "imgs"


def _load_json(path: Path) -> dict:
    if path not in _data_cache:
        with open(path) as f:
            _data_cache[path] = json.load(f)
    return _data_cache[path]


def _discover_canonical_inputs() -> list[Path]:
    user_root = PROJECT_ROOT / "data" / "user"
    if not user_root.exists():
        return []
    return sorted(
        user_root.glob("*/passive_courses/*/input.json"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )


def get_mock_input(user_id: str | None = None, concept_id: str | None = None) -> dict:
    """Return the passive_course_agent input dict.

    If *user_id* and *concept_id* are given, load that specific input.
    Otherwise fall back to the most-recently-modified canonical input.
    """
    if user_id and concept_id:
        path = get_passive_input_path(user_id, concept_id)
        if path.exists():
            return _load_json(path)
        raise FileNotFoundError(f"Input not found for {user_id}/{concept_id}: {path}")

    canonical_inputs = _discover_canonical_inputs()
    if canonical_inputs:
        if len(canonical_inputs) > 1:
            logger.warning(
                "Multiple passive course inputs found; using most recent: %s",
                canonical_inputs[0],
            )
        return _load_json(canonical_inputs[0])

    for path in LEGACY_INPUT_PATHS:
        if path.exists():
            return _load_json(path)

    checked = [str(path) for path in LEGACY_INPUT_PATHS]
    raise FileNotFoundError(
        "No passive_course_agent input file found. Checked canonical inputs under "
        f"{PROJECT_ROOT / 'data' / 'user'} and legacy paths: {checked}"
    )
