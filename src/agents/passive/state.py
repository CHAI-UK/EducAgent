"""
Pipeline state definitions for passive_course_agent.

Two-phase generation:
  Phase 1 — Outline: slice one concept into multiple learning nodes
  Phase 2 — Content: generate pedagogical content for each node
"""

from __future__ import annotations

from typing import Any

from typing_extensions import TypedDict


class PipelineState(TypedDict, total=False):
    """Full LangGraph state flowing through the passive_course_agent pipeline.

    Keys are populated progressively by each node.
    """

    # ── Request (provided at invocation) ────────────────────────────────
    user_id: str
    concept_id: str

    # ── From ProfileLoader (node ①) ─────────────────────────────────────
    # adaptation_ctx: structured dict from wizard fields
    adaptation_ctx: dict[str, Any]
    # depth_tier: mapped from wizard's 5 expertise levels → 3 generation tiers
    depth_tier: str  # "beginner" | "intermediate" | "advanced"
    # profile_sig: cluster label derived from profile transformation
    profile_sig: str  # e.g. "ECON-STATS-BEG"

    # ── From ProgressLoader (node ②) ────────────────────────────────────
    progress_ctx: dict[str, Any]
    confusion_fwd: list[str]

    # ── From ConceptLoader (node ③) ─────────────────────────────────────
    concept_ctx: dict[str, Any]
    grounded_chunks: list[dict[str, Any]]

    # ── Phase 1: Outline (concept → learning nodes) ─────────────────────
    # [{title, summary, rag_focus}] — how the concept is sliced
    outline: list[dict[str, str]]

    # ── Phase 2: Content (per learning node) ────────────────────────────
    # [{node_title, sections: [{section, content, markers}]}]
    nodes: list[dict[str, Any]]
    # Collected from all nodes
    image_prompts: list[dict[str, Any]]  # [{node_title, description, kind, section?}]

    # ── Phase 3: Image generation ───────────────────────────────────────
    image_refs: list[dict[str, Any]]  # [{description, kind, section?, url, model}]

    # ── Cache metadata ──────────────────────────────────────────────────
    cache_key: str
    cache_hit: bool
