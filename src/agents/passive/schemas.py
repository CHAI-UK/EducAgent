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


class SelfFlaggedRiskReason(str, Enum):
    """Why the generator self-flagged a specific claim for critic attention.

    The three reasons correspond to the narrow set of failure modes LLMs can
    introspect about reliably:

    - ``domain_fact_substituted``: specific factual claim (number, protocol,
      mechanism, tool name) not directly derivable from the grounded RAG
      chunks — generator filled it in from general knowledge.
    - ``unstated_assumption``: an absolute claim that in the source actually
      depends on a named assumption (Markov, faithfulness, positivity, etc.)
      which the generator may not have stated explicitly.
    - ``countable_detail_uncertain``: narrative references counts (N nodes,
      M arrows, K steps) that may not match what the diagram or worked
      example actually shows.

    Abstract causal concepts (confounder, do-operator, collider, etc.) are
    NOT to be self-flagged — that is the fact-checker's scope.
    """

    DOMAIN_FACT_SUBSTITUTED = "domain_fact_substituted"
    UNSTATED_ASSUMPTION = "unstated_assumption"
    COUNTABLE_DETAIL_UNCERTAIN = "countable_detail_uncertain"


class SelfFlaggedRisk(BaseModel):
    """One generator-side uncertainty flag attached to a specific claim.

    See Section.self_flagged_risks for scope and caps.
    """

    claim: str = Field(description="Verbatim quote of the section text being flagged.")
    reason: SelfFlaggedRiskReason
    detail: str = Field(
        default="",
        description="One short sentence explaining the gap or ambiguity.",
    )


class Section(BaseModel):
    section: str
    content: str
    markers: list[str] = Field(default_factory=list)
    part: PedagogicalPart = PedagogicalPart.EXTRA
    # Optional self-flags (max 2 per section, empty list = fully confident).
    # Generator uses these to point the critic at specific claims; see prompt
    # rules in passive_content_*.yaml.
    self_flagged_risks: list[SelfFlaggedRisk] = Field(default_factory=list)


class ContentResponse(BaseModel):
    sections: list[Section]


class FactCheckIssue(BaseModel):
    section: str
    claim: str
    problem: str
    severity: str = Field(description="'critical' | 'minor'")
    suggestion: str = ""
    # True when this issue corresponds to a generator self_flagged_risks
    # claim (critic confirmed the generator's hedge was real). Optional so
    # older critic outputs remain valid.
    was_self_flagged: bool = False


class FactCheckResponse(BaseModel):
    issues: list[FactCheckIssue] = Field(default_factory=list)
