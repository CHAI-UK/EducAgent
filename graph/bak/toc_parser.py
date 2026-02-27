"""
Parse the Table of Contents markdown into Section nodes with page ranges.
"""

import re
from dataclasses import dataclass
from pathlib import Path

TOC_PATH = (
    Path(__file__).parent.parent
    / "assets/Pearl_2009_Causality_sections/markdowns/07_Contents/07_Contents.mmd"
)
BOOK_LAST_PAGE = 460

SECTION_RE = re.compile(r"^(\d+(?:\.\d+)*)\s+(.+?)\s+(\d+)\s*$")


@dataclass
class Section:
    section_id: str   # e.g. "1.2.3"
    title: str
    chapter: int
    depth: int        # 0 = chapter, 1 = section, 2 = subsection
    start_page: int
    end_page: int
    parent_id: str    # "" for chapter-level


def parse_toc(path: Path = TOC_PATH) -> list[Section]:
    raw: list[Section] = []

    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "<---" in line or "Powered by" in line:
            continue
        m = SECTION_RE.match(line)
        if not m:
            continue

        sid   = m.group(1)
        title = m.group(2).strip()
        page  = int(m.group(3))
        parts = sid.split(".")
        depth = len(parts) - 1

        raw.append(Section(
            section_id=sid,
            title=title,
            chapter=int(parts[0]),
            depth=depth,
            start_page=page,
            end_page=0,
            parent_id=".".join(parts[:-1]) if depth > 0 else "",
        ))

    # Second pass: end_page = start of next section at same or shallower depth - 1
    for i, sec in enumerate(raw):
        sec.end_page = BOOK_LAST_PAGE
        for j in range(i + 1, len(raw)):
            if raw[j].depth <= sec.depth:
                sec.end_page = max(sec.start_page, raw[j].start_page - 1)
                break

    return raw


if __name__ == "__main__":
    sections = parse_toc()
    print(f"Parsed {len(sections)} sections")
    for s in sections[:15]:
        print(f"  {s.section_id:<12} ch={s.chapter} p{s.start_page:>3}–{s.end_page:<3}  {s.title[:55]}")
