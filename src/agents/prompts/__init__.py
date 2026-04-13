"""
Agent prompt templates — loaded from YAML files.

Convention: each agent's prompts live in a YAML file under src/agents/prompts/.
YAML keys are 'system' and 'user' (the two message roles).
"""

from __future__ import annotations

from pathlib import Path

import yaml

PROMPTS_DIR = Path(__file__).parent


def load_prompt(name: str) -> dict[str, str]:
    """Load a prompt YAML file by name (without .yaml extension).

    Returns dict with 'system' and 'user' keys.
    """
    path = PROMPTS_DIR / f"{name}.yaml"
    with open(path) as f:
        return yaml.safe_load(f)
