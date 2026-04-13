"""
Prompt templates for passive_course_agent.

Phase 1 — Outline: passive_outline_generator.yaml
Phase 2 — Content: passive_content_generator.yaml
"""

from src.agents.prompts import load_prompt

_outline = load_prompt("passive_outline_generator")
_content = load_prompt("passive_content_generator")

OUTLINE_SYSTEM_PROMPT: str = _outline["system"]
OUTLINE_USER_TEMPLATE: str = _outline["user"]

CONTENT_SYSTEM_PROMPT: str = _content["system"]
CONTENT_USER_TEMPLATE: str = _content["user"]
