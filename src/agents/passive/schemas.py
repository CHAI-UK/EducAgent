"""Pydantic schemas for passive_course_agent LLM responses.

These models guard against the well-known failure mode where an LLM emits
unescaped quotes inside JSON string values (e.g. ``*"text"*`` italic-quoted
phrases). When that happens, ``json_repair`` salvages the broken JSON by
splitting the string at the unescaped quote and inventing bogus keys such as
``"earlier."`` or ``"CT?"``. Validating with these schemas makes the failure
loud — and the post-parse check in ``graph.py`` flags those bogus keys
explicitly so the repair retry can fire.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class PedagogicalPart(str, Enum):
    """Canonical pedagogical part for two-layer part/section routing (Story 5.3 AC-1).

    The ``part`` field gives downstream code (risk classifier, QA router,
    metrics) a stable enum to route on, while the ``section`` field remains
    a free-form reader-facing heading chosen by the generator prompt. Missing
    or invalid values default to ``extra`` to preserve backward compatibility
    with sections generated before this enum existed.
    """

    HOOK = "hook"
    RECALL = "recall"
    DEFINITION = "definition"
    INTUITION = "intuition"
    VISUAL = "visual"
    CHECKPOINT = "checkpoint"
    EXTRA = "extra"


class Section(BaseModel):
    section: str
    content: str
    markers: list[str] = Field(default_factory=list)
    part: PedagogicalPart = PedagogicalPart.EXTRA


class ContentResponse(BaseModel):
    sections: list[Section]


class FactCheckIssue(BaseModel):
    section: str
    claim: str
    problem: str
    severity: str = Field(description="'critical' | 'minor'")
    suggestion: str = ""


class FactCheckResponse(BaseModel):
    issues: list[FactCheckIssue] = Field(default_factory=list)
