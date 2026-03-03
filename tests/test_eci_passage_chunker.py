"""Tests for graph.eci_passage_chunker (T2.2a-f)."""
import textwrap
from pathlib import Path

import pytest

from graph.eci_passage_chunker import (
    PassageChunk,
    _extract_section_heading,
    _get_tail_words,
    _is_embed_empty,
    _resolve_images,
    chunk_section,
    parse_toc_start_pages,
)


# ── parse_toc_start_pages ─────────────────────────────────────────────────────

def test_toc_parse_chapter_start_pages(tmp_path):
    """T2.2a — TOC parser extracts correct chapter start pages."""
    toc_content = textwrap.dedent("""\
        ## Contents
        1 Statistical and Causal Models 1
        1.1 Probability Theory 1
        2 Assumptions for Causal Inference 15
        3 Cause-Effect Models 33
        Appendix A Some Probability 213
        Appendix B Causal Orderings 221
        Appendix C Proofs 225
    """)
    toc = tmp_path / "01_TOC.mmd"
    toc.write_text(toc_content)

    pages = parse_toc_start_pages(toc)
    assert pages[1] == 1
    assert pages[2] == 15
    assert pages[3] == 33
    assert pages[11] == 213
    assert pages[12] == 221
    assert pages[13] == 225


def test_toc_parse_missing_file_returns_fallback(tmp_path):
    """T2.2a — missing TOC file falls back to hardcoded values."""
    pages = parse_toc_start_pages(tmp_path / "nonexistent.mmd")
    assert pages[1] == 1
    assert pages[6] == 81


# ── _get_tail_words ───────────────────────────────────────────────────────────

def test_get_tail_words_fewer_than_n():
    text = "hello world"
    assert _get_tail_words(text, 80) == "hello world"


def test_get_tail_words_exact_n():
    words = ["word"] * 100
    text = " ".join(words)
    tail = _get_tail_words(text, 80)
    assert len(tail.split()) == 80


# ── _resolve_images ───────────────────────────────────────────────────────────

def test_resolve_images_absolute_path():
    """T2.2e — content gets absolute image path."""
    text = "![](images/fig1.png)"
    content, _ = _resolve_images(text, "05_Ch02_AssumptionsForCausalInference")
    assert "assets/ElementsOfCausalInference_sections/markdowns" in content
    assert "05_Ch02_AssumptionsForCausalInference/images/fig1.png" in content


def test_resolve_images_embed_uses_caption():
    """T2.2e — content_for_embed replaces image tag + caption line."""
    text = "![alt](images/fig1.png)\nFigure 2.1: Some caption text"
    _, embed = _resolve_images(text, "05_Ch02_AssumptionsForCausalInference")
    assert "[Figure: Figure 2.1: Some caption text]" in embed
    assert "images/" not in embed


def test_resolve_images_embed_no_caption():
    """T2.2e — image with no following caption becomes [Figure]."""
    text = "Some text\n![](images/fig.jpg)\nNext paragraph"
    _, embed = _resolve_images(text, "05_Ch02")
    assert "[Figure]" in embed


# ── _is_embed_empty ───────────────────────────────────────────────────────────

def test_is_embed_empty_only_figures():
    assert _is_embed_empty("[Figure]\n[Figure: caption]") is True


def test_is_embed_empty_with_text():
    assert _is_embed_empty("[Figure]\nSome real text") is False


def test_is_embed_empty_blank():
    assert _is_embed_empty("   ") is True


# ── chunk_section ─────────────────────────────────────────────────────────────

def _make_mmd(tmp_path: Path, content: str, dir_name: str = "04_Ch01_Test") -> Path:
    chapter_dir = tmp_path / dir_name
    chapter_dir.mkdir(parents=True, exist_ok=True)
    f = chapter_dir / f"{dir_name}.mmd"
    f.write_text(content)
    return f


def test_chunk_section_page_nums(tmp_path):
    """T2.2b — page_num values are taken from the split markers."""
    mmd = _make_mmd(tmp_path, textwrap.dedent("""\
        Intro text on first page.
        <--- Page Split 2 --->
        Content on page two.
        <--- Page Split 3 --->
        Content on page three.
    """))
    chunks = chunk_section(mmd, chapter=1, chapter_start_page=1)
    page_nums = [c.page_num for c in chunks]
    assert 2 in page_nums
    assert 3 in page_nums


def test_chunk_section_heading_extraction(tmp_path):
    """T2.2c — section_heading is extracted from ## heading in segment."""
    mmd = _make_mmd(tmp_path, textwrap.dedent("""\
        ## Introduction
        Some content here.
        <--- Page Split 2 --->
        ## Second Section
        More content.
    """))
    chunks = chunk_section(mmd, chapter=1, chapter_start_page=1)
    headings = [c.section_heading for c in chunks]
    assert "Second Section" in headings


def test_chunk_section_prefix_overlap(tmp_path):
    """T2.2d — second chunk starts with tail words from the first segment."""
    words = " ".join([f"word{i}" for i in range(100)])
    mmd = _make_mmd(tmp_path, f"{words}\n<--- Page Split 5 --->\nNew content here.")
    chunks = chunk_section(mmd, chapter=1, chapter_start_page=4, overlap_words=10)
    assert len(chunks) >= 2
    # The second chunk's content_for_embed should contain the last 10 words of previous page
    last_10 = " ".join([f"word{i}" for i in range(90, 100)])
    assert last_10 in chunks[1].content_for_embed


def test_chunk_section_skips_image_only_pages(tmp_path):
    """T2.2f — a page with only images (no prefix from prior page) is skipped.

    The first page has only an image so there is no prefix overlap.  Its
    content_for_embed resolves to a bare [Figure] token and _is_embed_empty
    must return True, causing chunk_section to drop it.
    """
    mmd = _make_mmd(tmp_path, textwrap.dedent("""\
        ![](images/only_image.jpg)
        <--- Page Split 2 --->
        Some real text on second page.
    """))
    chunks = chunk_section(mmd, chapter=1, chapter_start_page=1)
    # chapter_start_page=1 is image-only with no prior prefix → should be skipped
    page_nums = [c.page_num for c in chunks]
    assert 1 not in page_nums
    assert 2 in page_nums


def test_chunk_section_returns_passagechunk_instances(tmp_path):
    """T2.2b — each item is a PassageChunk with required fields."""
    mmd = _make_mmd(tmp_path, "Hello world.\n<--- Page Split 10 --->\nMore text here.")
    chunks = chunk_section(mmd, chapter=3, chapter_start_page=33)
    for c in chunks:
        assert isinstance(c, PassageChunk)
        assert c.chapter == 3
        assert isinstance(c.page_num, int)
        assert isinstance(c.content, str)
        assert isinstance(c.content_for_embed, str)
