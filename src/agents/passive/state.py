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

    # ── Phase 2.5: Fact-check critique (domain expert review) ──────────
    # [{node_title, section, claim, problem, severity, suggestion}]
    fact_check_issues: list[dict[str, Any]]
    # True when fact-checking has already run upstream (for example, pipelined
    # directly after each content node) so the graph-level fact_checker skips.
    fact_check_completed: bool

    # Per-node QA routing decisions and issue counts (Story 5.3 AC-6/7/8).
    # [{node_title, qa_path, risk, issues, critical, rewrites}]
    # qa_path ∈ {"rule-only", "critic-ran", "critic-ran+rewrite",
    #            "critic-ran+rewrite+recheck", "critic-failed"}
    qa_log: list[dict[str, Any]]

    # ── Phase 3: Image generation ───────────────────────────────────────
    image_refs: list[dict[str, Any]]  # [{description, kind, section?, url, model}]
    # Set True when image.enabled=false short-circuits the generator (AC-9).
    image_skipped: bool

    # ── Cache metadata ──────────────────────────────────────────────────
    cache_key: str
    cache_hit: bool

    # ── Run metrics (Story 5.3 AC-11) ───────────────────────────────────
    # Keyed by phase name:
    #   {"outline": {"duration_s": ...},
    #    "content": {"duration_s": ..., "per_node_durations_s": [...], "nodes": N},
    #    "fact_check": {"duration_s": ..., "qa_log_summary": {...}},
    #    "image": {"duration_s": ..., "generated": N, "prompts": M, "skipped": bool}}
    # Persisted to run_metrics.json alongside content.json on successful run.
    run_metrics: dict[str, Any]
