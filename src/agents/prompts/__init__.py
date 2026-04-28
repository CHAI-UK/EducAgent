"""
Agent prompt templates — loaded from YAML files.

Convention: prompt/config-like YAML files live under src/agents/prompts/.
Most prompt files expose 'system' and 'user', but some prompt-adjacent assets
may expose arbitrary structured keys.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

PROMPTS_DIR = Path(__file__).parent


def load_prompt(name: str) -> dict[str, Any]:
    """Load a YAML file from ``src/agents/prompts`` by stem name."""
    path = PROMPTS_DIR / f"{name}.yaml"
    with open(path) as f:
        return yaml.safe_load(f)
