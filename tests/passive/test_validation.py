"""Tests for the post-parse validation that catches the unescaped-quote bug.

The original failure (learner_43, counterfactuals): the LLM emitted
``*"Did we even need that contrast earlier."*`` inside a JSON string without
escaping the inner quotes. ``json_repair`` salvaged the broken JSON by
inventing keys like ``"earlier."`` / ``"CT?"``. The preview renderer only
reads ``content``, so everything after the first unescaped quote was lost,
leaving a dangling ``*`` at the end of the section.

These tests lock in the structural check that flags both shapes of corruption.
"""

from __future__ import annotations

import pytest

from src.agents.passive.graph import (
    _salvage_sections,
    _sanitize_italic_quotes,
    _validate_sections,
)


def test_validate_sections_accepts_clean_payload() -> None:
    payload = {
        "sections": [
            {
                "section": "Intro",
                "content": "Hello world.",
                "markers": [],
            }
        ]
    }
    out = _validate_sections(payload)
    # part defaults to "extra" when not provided (Story 5.3 backward compat)
    assert out == [
        {"section": "Intro", "content": "Hello world.", "markers": [], "part": "extra"}
    ]


def test_validate_sections_accepts_bare_list() -> None:
    payload = [{"section": "Intro", "content": "Hello world.", "markers": []}]
    out = _validate_sections(payload)
    assert len(out) == 1
    assert out[0]["section"] == "Intro"


def test_validate_sections_rejects_bogus_keys_from_json_repair() -> None:
    """Reproduces the learner_43 corruption shape verbatim."""
    payload = {
        "sections": [
            {
                "section": "What If We Had Chosen a Different Scan?",
                "content": "...attending says, almost under her breath: *",
                "earlier.": "n\n\nThat sentence...",
                "markers": [],
            }
        ]
    }
    with pytest.raises(ValueError, match="unexpected keys"):
        _validate_sections(payload)


def test_validate_sections_rejects_lone_trailing_star() -> None:
    payload = {
        "sections": [
            {
                "section": "Intro",
                "content": "The attending says: *",
                "markers": [],
            }
        ]
    }
    with pytest.raises(ValueError, match="lone '\\*'"):
        _validate_sections(payload)


def test_validate_sections_allows_bold_terminator() -> None:
    """A trailing `**` is closed bold, not an unterminated italic."""
    payload = {
        "sections": [
            {
                "section": "Intro",
                "content": "The key term is **counterfactual**",
                "markers": [],
            }
        ]
    }
    out = _validate_sections(payload)
    assert out[0]["content"].endswith("**")


def test_validate_sections_rejects_missing_required_field() -> None:
    payload = {"sections": [{"section": "Intro", "markers": []}]}
    with pytest.raises(ValueError):
        _validate_sections(payload)


def test_salvage_sections_drops_unknown_keys_and_keeps_valid_entries() -> None:
    payload = {
        "sections": [
            {
                "section": "Intro",
                "content": "Hello.",
                "markers": [],
                "bogus": "ignore me",
            },
            "not a dict",
            {"section": "Missing content"},
            {"section": "OK", "content": "world", "markers": ["[CONTEXT_IMAGE: x]"]},
        ]
    }
    out = _salvage_sections(payload)
    assert len(out) == 2
    # part defaults to "extra" when not provided (Story 5.3 backward compat)
    assert out[0] == {
        "section": "Intro",
        "content": "Hello.",
        "markers": [],
        "part": "extra",
    }
    assert out[1]["markers"] == ["[CONTEXT_IMAGE: x]"]


# ---------------------------------------------------------------------------
# Tests for the trailing-star fix in _salvage_sections  (new)
# ---------------------------------------------------------------------------


def test_salvage_sections_strips_lone_trailing_star() -> None:
    """_salvage_sections should fix truncated italic (`*`) instead of keeping it."""
    payload = {
        "sections": [
            {
                "section": "Visual Synthesis: The PC Algorithm Pipeline",
                "content": "The attending whispers: *",
                "markers": [],
            }
        ]
    }
    out = _salvage_sections(payload)
    assert len(out) == 1
    # The lone trailing '*' should be stripped
    assert not out[0]["content"].endswith("*")
    assert out[0]["content"] == "The attending whispers:"


def test_salvage_sections_preserves_bold_terminator() -> None:
    """Trailing `**` (closed bold) must NOT be stripped."""
    payload = {
        "sections": [
            {
                "section": "Intro",
                "content": "Key term: **counterfactual**",
                "markers": [],
            }
        ]
    }
    out = _salvage_sections(payload)
    assert out[0]["content"] == "Key term: **counterfactual**"


def test_salvage_sections_handles_empty_dict() -> None:
    """When nothing is salvageable, return an empty list (no crash)."""
    assert _salvage_sections({"sections": []}) == []
    assert _salvage_sections({}) == []
    assert _salvage_sections({"sections": "not a list"}) == []


# ---------------------------------------------------------------------------
# Integration-style: simulate the full repair→regen→salvage fallback chain
# ---------------------------------------------------------------------------


@pytest.fixture()
def _good_section():
    return {
        "section": "Basics",
        "content": "Graph theory fundamentals.",
        "markers": [],
    }


@pytest.fixture()
def _truncated_section():
    return {
        "section": "Visual Synthesis: The PC Algorithm Pipeline",
        "content": "The model says *",
        "markers": [],
    }


def test_validate_rejects_then_salvage_recovers(_truncated_section) -> None:
    """The exact flow that caused the crash: validate raises, salvage recovers."""
    payload = {"sections": [_truncated_section]}

    # validate must reject it
    with pytest.raises(ValueError, match="lone '\\*'"):
        _validate_sections(payload)

    # salvage must recover it gracefully
    out = _salvage_sections(payload)
    assert len(out) == 1
    assert not out[0]["content"].endswith("*")


def test_salvage_mixed_good_and_truncated(_good_section, _truncated_section) -> None:
    """Good sections survive alongside truncated ones."""
    payload = {"sections": [_good_section, _truncated_section]}
    out = _salvage_sections(payload)
    assert len(out) == 2
    assert out[0]["content"] == "Graph theory fundamentals."
    assert not out[1]["content"].endswith("*")


# ---------------------------------------------------------------------------
# Tests for _sanitize_italic_quotes  (pre-parse fix)
# ---------------------------------------------------------------------------


def test_sanitize_replaces_straight_quotes_inside_italics() -> None:
    """The exact pattern that breaks JSON: *"text"* → *\u201ctext\u201d*."""
    raw = 'the attending whispers: *"Did we even need that contrast?"*'
    out = _sanitize_italic_quotes(raw)
    assert out == 'the attending whispers: *\u201cDid we even need that contrast?\u201d*'


def test_sanitize_leaves_normal_json_quotes_alone() -> None:
    """Straight quotes that are JSON structural delimiters must not be touched."""
    raw = '{"section": "Intro", "content": "Hello world.", "markers": []}'
    assert _sanitize_italic_quotes(raw) == raw


def test_sanitize_leaves_escaped_quotes_alone() -> None:
    """Already-escaped quotes inside strings should not be changed."""
    raw = r'{"content": "She said: *\"hello\"*"}'
    # The regex looks for *"..."* — the \" are escaped so they won't match
    # the pattern (the backslash prevents the lookbehind from matching)
    assert _sanitize_italic_quotes(raw) == raw


def test_sanitize_handles_multiple_italic_quotes() -> None:
    """Multiple occurrences in the same string should all be fixed."""
    raw = '*"first"* and then *"second"*'
    out = _sanitize_italic_quotes(raw)
    assert "\u201cfirst\u201d" in out
    assert "\u201csecond\u201d" in out
    assert '"first"' not in out
    assert '"second"' not in out


def test_sanitize_preserves_bold_markers() -> None:
    """**bold** should not be affected."""
    raw = '**important** and *"italic quote"*'
    out = _sanitize_italic_quotes(raw)
    assert "**important**" in out
    assert "\u201citalic quote\u201d" in out


def test_sanitize_produces_valid_json() -> None:
    """End-to-end: a JSON string with *"..."* should parse after sanitization."""
    import json

    # This is what the LLM produces — broken JSON due to unescaped quote
    broken = '{"sections": [{"section": "Test", "content": "She says: *"Did we need that?"* and moves on.", "markers": []}]}'
    # Without sanitization, json.loads would fail or parse wrong
    sanitized = _sanitize_italic_quotes(broken)
    parsed = json.loads(sanitized)
    assert parsed["sections"][0]["content"] == "She says: *\u201cDid we need that?\u201d* and moves on."


# ---------------------------------------------------------------------------
# Tests for the two-layer part/section model (Story 5.3 AC-1, AC-2, AC-3)
# ---------------------------------------------------------------------------


def test_validate_sections_accepts_valid_part_values() -> None:
    """All 7 canonical parts must validate: hook, recall, definition, intuition, visual, checkpoint, extra."""
    payload = {
        "sections": [
            {"section": "Opening", "content": "...", "markers": [], "part": "hook"},
            {"section": "Refresher", "content": "...", "markers": [], "part": "recall"},
            {"section": "Formal", "content": "...", "markers": [], "part": "definition"},
            {"section": "Analogy", "content": "...", "markers": [], "part": "intuition"},
            {"section": "Diagram", "content": "...", "markers": [], "part": "visual"},
            {"section": "Why it matters", "content": "...", "markers": [], "part": "extra"},
            {"section": "Quiz", "content": "...", "markers": [], "part": "checkpoint"},
        ]
    }
    out = _validate_sections(payload)
    assert len(out) == 7
    assert [s["part"] for s in out] == [
        "hook",
        "recall",
        "definition",
        "intuition",
        "visual",
        "extra",
        "checkpoint",
    ]


def test_validate_sections_rejects_invalid_part() -> None:
    """Unknown part values must be rejected by schema."""
    payload = {
        "sections": [
            {"section": "X", "content": "...", "markers": [], "part": "invalid_part_name"}
        ]
    }
    with pytest.raises(ValueError):
        _validate_sections(payload)


def test_validate_sections_backward_compat_missing_part() -> None:
    """Sections without a part field must default to 'extra' for backward compat."""
    payload = {"sections": [{"section": "Intro", "content": "Hello.", "markers": []}]}
    out = _validate_sections(payload)
    assert out[0]["part"] == "extra"


def test_salvage_sections_fills_default_part_when_missing() -> None:
    """_salvage_sections must add part='extra' when missing."""
    payload = {
        "sections": [
            {"section": "Intro", "content": "Hello.", "markers": []},
            {"section": "Quiz", "content": "Q1?", "markers": [], "part": "checkpoint"},
        ]
    }
    out = _salvage_sections(payload)
    assert len(out) == 2
    assert out[0]["part"] == "extra"
    assert out[1]["part"] == "checkpoint"


def test_salvage_sections_coerces_invalid_part_to_extra() -> None:
    """Salvage must tolerate invalid part values by coercing to 'extra' (best-effort recovery)."""
    payload = {
        "sections": [
            {"section": "X", "content": "...", "markers": [], "part": "not_a_real_part"}
        ]
    }
    out = _salvage_sections(payload)
    assert len(out) == 1
    assert out[0]["part"] == "extra"
