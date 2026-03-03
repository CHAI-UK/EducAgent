"""ECI textbook markdown chunker.

Splits per-chapter .mmd files on page-split markers, applies 80-word prefix
overlap between adjacent pages, and resolves image paths to absolute form for
frontend rendering while substituting figure captions for the embedding API.
"""
import re
from dataclasses import dataclass
from pathlib import Path

# ── Regex patterns ────────────────────────────────────────────────────────────

PAGE_SPLIT_RE = re.compile(r"<--- Page Split (\d+) --->")
IMG_RE = re.compile(r"!\[([^\]]*)\]\(images/([^)]+)\)")
CAPTION_RE = re.compile(r"^(Figure\s[\d.]+[:\s].+)$")

# ── Chapter directory → chapter int (hardcoded; do NOT parse dynamically) ────

CHAPTER_DIRS: dict[str, int] = {
    "04_Ch01_StatisticalAndCausalModels": 1,
    "05_Ch02_AssumptionsForCausalInference": 2,
    "06_Ch03_CauseEffectModels": 3,
    "07_Ch04_LearningCauseEffectModels": 4,
    "08_Ch05_ConnectionsToMachineLearning_I": 5,
    "09_Ch06_MultivariateCausalModels": 6,
    "10_Ch07_LearningMultivariateCausalModels": 7,
    "11_Ch08_ConnectionsToMachineLearning_II": 8,
    "12_Ch09_HiddenVariables": 9,
    "13_Ch10_TimeSeries": 10,
    "14_AppA_SomeProbabilityAndStatistics": 11,
    "15_AppB_CausalOrderingsAdjacencyMatrices": 12,
    "16_AppC_Proofs": 13,
}

# Fallback chapter start pages derived from 01_TOC.mmd
_TOC_FALLBACK: dict[int, int] = {
    1: 1, 2: 15, 3: 33, 4: 43, 5: 71, 6: 81, 7: 135,
    8: 157, 9: 171, 10: 197, 11: 213, 12: 221, 13: 225,
}


# ── Data model ────────────────────────────────────────────────────────────────

@dataclass
class PassageChunk:
    chapter: int
    page_num: int
    section_heading: str
    content: str            # full markdown; image tags resolved to absolute paths
    content_for_embed: str  # sent to embedding API; image tags → [Figure: caption]


# ── Helpers ───────────────────────────────────────────────────────────────────

def parse_toc_start_pages(toc_path: Path) -> dict[int, int]:
    """Parse 01_TOC.mmd → {chapter_num: start_page}.

    Falls back to hardcoded _TOC_FALLBACK for any missing chapters so callers
    never need to handle errors.
    """
    SECTION_RE = re.compile(r"^(\d+)(?:\.\d+)?\s+.+?\s+(\d+)\s*$")
    APPENDIX_CH_RE = re.compile(r"^Appendix\s+([A-C])\s+.+?\s+(\d+)\s*$")
    appendix_map = {"A": 11, "B": 12, "C": 13}
    result: dict[int, int] = {}

    try:
        for line in toc_path.read_text(encoding="utf-8").splitlines():
            m = SECTION_RE.match(line.strip())
            if m:
                ch, pg = int(m.group(1)), int(m.group(2))
                if ch not in result:   # first hit = chapter-level entry
                    result[ch] = pg
                continue
            m2 = APPENDIX_CH_RE.match(line.strip())
            if m2:
                result[appendix_map[m2.group(1)]] = int(m2.group(2))
    except Exception:
        pass

    for ch, pg in _TOC_FALLBACK.items():
        result.setdefault(ch, pg)

    return result


def _get_tail_words(text: str, n: int = 80) -> str:
    """Return the last n whitespace-split words of text joined by spaces."""
    words = text.split()
    return " ".join(words[-n:]) if len(words) > n else " ".join(words)


def _extract_section_heading(raw_text: str) -> str:
    """Return the nearest ## heading found in raw_text (scanning from end)."""
    for line in reversed(raw_text.splitlines()):
        stripped = line.strip()
        if stripped.startswith("## "):
            return stripped[3:].strip()
    return ""


def _resolve_images(text: str, dir_name: str) -> tuple[str, str]:
    """Return (content, content_for_embed) with image tags transformed.

    content:
        ![alt](images/X.jpg)  →  ![alt](assets/.../dir_name/images/X.jpg)

    content_for_embed:
        ![alt](images/X.jpg)          →  [Figure]
        ![alt](images/X.jpg)          →  [Figure: Figure 1.1: caption text]
        + "Figure 1.1: caption text"
    """
    abs_prefix = (
        "assets/ElementsOfCausalInference_sections"
        f"/markdowns/{dir_name}/images/"
    )

    # content: rewrite relative path to absolute
    content = IMG_RE.sub(
        lambda m: f"![{m.group(1)}]({abs_prefix}{m.group(2)})", text
    )

    # content_for_embed: replace image tag + optional caption line
    lines = text.splitlines()
    result: list[str] = []
    skip_next = False
    for i, line in enumerate(lines):
        if skip_next:
            skip_next = False
            continue
        m = IMG_RE.match(line.strip())
        if m:
            next_line = lines[i + 1].strip() if i + 1 < len(lines) else ""
            cap_m = CAPTION_RE.match(next_line)
            if cap_m:
                result.append(f"[Figure: {cap_m.group(1)}]")
                skip_next = True
            else:
                result.append("[Figure]")
        else:
            result.append(line)
    content_for_embed = "\n".join(result)

    return content, content_for_embed


def _is_embed_empty(content_for_embed: str) -> bool:
    """True if the embed text is blank or contains only [Figure...] tokens."""
    stripped = re.sub(r"\[Figure[^\]]*\]", "", content_for_embed)
    return not stripped.strip()


# ── Public API ────────────────────────────────────────────────────────────────

def chunk_section(
    mmd_path: Path,
    chapter: int,
    chapter_start_page: int,
    overlap_words: int = 80,
) -> list[PassageChunk]:
    """Chunk one .mmd file into PassageChunk objects with prefix overlap."""
    raw = mmd_path.read_text(encoding="utf-8")
    dir_name = mmd_path.parent.name

    # PAGE_SPLIT_RE.split produces: [pre, N, text, N, text, ...]
    parts = PAGE_SPLIT_RE.split(raw)
    segments: list[tuple[int, str]] = [(chapter_start_page, parts[0])]
    for i in range(1, len(parts), 2):
        try:
            page_num = int(parts[i])
            seg_text = parts[i + 1] if i + 1 < len(parts) else ""
        except (ValueError, IndexError):
            continue
        segments.append((page_num, seg_text))

    chunks: list[PassageChunk] = []
    for idx, (page_num, seg_text) in enumerate(segments):
        # Prefix overlap: prepend tail of the previous segment's raw text
        if idx > 0:
            prev_tail = _get_tail_words(segments[idx - 1][1], overlap_words)
            seg_with_prefix = prev_tail + "\n\n" + seg_text
        else:
            seg_with_prefix = seg_text

        # section_heading from raw segment (before prefix injection)
        section_heading = _extract_section_heading(seg_text)
        content, content_for_embed = _resolve_images(seg_with_prefix, dir_name)

        if _is_embed_empty(content_for_embed):
            continue

        chunks.append(PassageChunk(
            chapter=chapter,
            page_num=page_num,
            section_heading=section_heading,
            content=content,
            content_for_embed=content_for_embed,
        ))

    return chunks


def chunk_all_sections(
    markdowns_root: Path,
    toc_path: Path,
) -> list[PassageChunk]:
    """Chunk all chapter/appendix .mmd files and return combined list."""
    start_pages = parse_toc_start_pages(toc_path)
    all_chunks: list[PassageChunk] = []

    for dir_name, chapter in CHAPTER_DIRS.items():
        chapter_dir = markdowns_root / dir_name
        if not chapter_dir.is_dir():
            continue
        mmd_files = list(chapter_dir.glob("*.mmd"))
        if not mmd_files:
            continue
        chunks = chunk_section(
            mmd_path=mmd_files[0],
            chapter=chapter,
            chapter_start_page=start_pages.get(chapter, 1),
        )
        all_chunks.extend(chunks)

    return all_chunks


if __name__ == "__main__":
    root = Path(__file__).parent.parent.parent
    markdowns = root / "assets" / "ElementsOfCausalInference_sections" / "markdowns"
    toc = markdowns / "01_TOC" / "01_TOC.mmd"

    chunks = chunk_all_sections(markdowns, toc)
    print(f"Total chunks: {len(chunks)}")
    if chunks:
        s = chunks[0]
        print(f"\nSample (ch={s.chapter}, page={s.page_num}, heading={s.section_heading!r})")
        print(f"  content[:200]:           {s.content[:200]!r}")
        print(f"  content_for_embed[:200]: {s.content_for_embed[:200]!r}")
