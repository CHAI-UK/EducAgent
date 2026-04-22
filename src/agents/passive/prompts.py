"""
Prompt templates for passive_course_agent.

Phase 1 — Outline: passive_outline_generator.yaml
Phase 2 — Content: tier-specific prompts selected by depth_tier router
  beginner     → passive_content_beginner.yaml
  intermediate → passive_content_intermediate.yaml
  advanced     → passive_content_advanced.yaml
Phase 2.5 — Fact-check: passive_fact_checker.yaml
"""

from src.agents.prompts import load_prompt

_outline = load_prompt("passive_outline_generator")
_fact_check = load_prompt("passive_fact_checker")

OUTLINE_SYSTEM_PROMPT: str = _outline["system"]
OUTLINE_USER_TEMPLATE: str = _outline["user"]

FACT_CHECK_SYSTEM_PROMPT: str = _fact_check["system"]
FACT_CHECK_USER_TEMPLATE: str = _fact_check["user"]

_content_beginner = load_prompt("passive_content_beginner")
_content_intermediate = load_prompt("passive_content_intermediate")
_content_advanced = load_prompt("passive_content_advanced")

TIER_CONTENT_PROMPTS: dict[str, dict[str, str]] = {
    "beginner": {
        "system": _content_beginner["system"],
        "user": _content_beginner["user"],
    },
    "intermediate": {
        "system": _content_intermediate["system"],
        "user": _content_intermediate["user"],
    },
    "advanced": {
        "system": _content_advanced["system"],
        "user": _content_advanced["user"],
    },
}

# Backwards-compatible aliases (used by fact_checker regeneration fallback)
CONTENT_SYSTEM_PROMPT: str = _content_intermediate["system"]
CONTENT_USER_TEMPLATE: str = _content_intermediate["user"]
