"""
Agent LLM configuration — loaded from YAML files.

Convention: each agent's LLM config lives in a YAML file under src/agents/config/.
"""

from __future__ import annotations

from pathlib import Path

import yaml

CONFIG_DIR = Path(__file__).parent


def load_agent_config(name: str) -> dict:
    """Load an agent config YAML file by name (without .yaml extension)."""
    path = CONFIG_DIR / f"{name}.yaml"
    with open(path) as f:
        return yaml.safe_load(f)
