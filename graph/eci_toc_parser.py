"""
Parse the Elements of Causal Inference (2017) Table of Contents.

Handles:
  - Numbered chapters 1–10 with up to 2 depth levels
  - Appendices A, B, C (treated as chapters 11, 12, 13)
"""

import re
from dataclasses import dataclass
from pathlib import Path

TOC_PATH = (
    Path(__file__).parent.parent
    / "assets/ElementsOfCausalInference_sections/markdowns/01_TOC/01_TOC.mmd"
)
BOOK_LAST_PAGE = 266

_APPENDIX_CHAPTER = {"A": 11, "B": 12, "C": 13}

SECTION_RE  = re.compile(r"^(\d+(?:\.\d+)*)\s+(.+?)\s+(\d+)\s*$")
APPENDIX_RE = re.compile(r"^(?:Appendix\s+)?([ABC])(?:\.(\d+))?\s+(.+?)\s+(\d+)\s*$")


@dataclass
class Section:
    section_id: str    # "1", "1.1", "A", "A.1", …
    title: str
    chapter: int       # 1–10 for chapters; 11–13 for appendices A–C
    depth: int         # 0 = chapter/appendix root, 1 = section
    start_page: int
    end_page: int
    parent_id: str     # "" for top-level, else e.g. "1" or "A"


def parse_toc(path: Path = TOC_PATH) -> list[Section]:
    raw: list[Section] = []

    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "<---" in line:
            continue

        # Numeric chapters / sections
        m = SECTION_RE.match(line)
        if m:
            sid   = m.group(1)
            title = m.group(2).strip()
            page  = int(m.group(3))
            parts = sid.split(".")
            depth = len(parts) - 1
            raw.append(Section(
                section_id=sid, title=title,
                chapter=int(parts[0]), depth=depth,
                start_page=page, end_page=0,
                parent_id=".".join(parts[:-1]) if depth > 0 else "",
            ))
            continue

        # Appendix entries: "Appendix A …" or "A.1 …"
        m = APPENDIX_RE.match(line)
        if m:
            letter = m.group(1)
            sub    = m.group(2)          # e.g. "1" for A.1, None for "Appendix A"
            title  = m.group(3).strip()
            page   = int(m.group(4))
            ch     = _APPENDIX_CHAPTER[letter]
            sid    = f"{letter}.{sub}" if sub else letter
            depth  = 1 if sub else 0
            raw.append(Section(
                section_id=sid, title=title,
                chapter=ch, depth=depth,
                start_page=page, end_page=0,
                parent_id=letter if sub else "",
            ))

    # end_page = start of next section at same or shallower depth − 1
    for i, sec in enumerate(raw):
        sec.end_page = BOOK_LAST_PAGE
        for j in range(i + 1, len(raw)):
            if raw[j].depth <= sec.depth:
                sec.end_page = max(sec.start_page, raw[j].start_page - 1)
                break

    return raw


if __name__ == "__main__":
    secs = parse_toc()
    print(f"Parsed {len(secs)} sections")
    for s in secs:
        print(f"  {s.section_id:<6} ch={s.chapter} p{s.start_page:>3}–{s.end_page:<3}  {s.title[:60]}")
