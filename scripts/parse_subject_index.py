"""
Parse the Subject Index from Pearl (2009) Causality using pdfplumber.
- Handles two-column layout by processing each column independently.
- Uses x-coordinate thresholding to distinguish top-level from sub-entries.
"""

import pdfplumber
import re
import json
from pathlib import Path
from collections import Counter

PDF_PATH = Path(__file__).parent.parent / "assets/Pearl_2009_Causality_sections/24_Subject_Index.pdf"
OUT_PATH = Path(__file__).parent.parent / "assets/subject_index_parsed.json"

# Right column actual content starts at ~240; left column overflow lands at ~185.
# Use 225 so the right crop starts cleanly after the overflow zone.
COLUMN_SPLIT_LEFT  = 225   # left  column: x  < this
COLUMN_SPLIT_RIGHT = 225   # right column: x >= this


# ── Page-reference parsing ─────────────────────────────────────────────────────

def parse_page_refs(refs_str: str) -> list[dict]:
    """Parse "12, 34–6, 78n, 130t" → list of structured dicts."""
    refs = []
    for part in [p.strip() for p in refs_str.split(",") if p.strip()]:
        # Range: e.g. "118–26", "354-5"
        m = re.match(r"^(\d+)\s*[–\-]\s*(\d+)([nft]?)$", part)
        if m:
            start, end_raw, suffix = int(m.group(1)), m.group(2), m.group(3)
            if int(end_raw) < start:
                n_miss = len(str(start)) - len(end_raw)
                end = int(str(start)[:n_miss] + end_raw)
            else:
                end = int(end_raw)
            refs.append({"pages": list(range(start, end + 1)), "suffix": suffix, "raw": part})
            continue
        # Single: e.g. "20", "205n", "186f"
        m = re.fullmatch(r"(\d+)([nft]?)", part)
        if m:
            refs.append({"pages": [int(m.group(1))], "suffix": m.group(2), "raw": part})
    return refs


def split_term_refs(text: str):
    """
    Split "foo bar, 12, 34–6, 78n" → ("foo bar", "12, 34–6, 78n").
    Returns (text, "") when no page refs are found.
    """
    parts = text.split(",")
    split_at = len(parts)
    for i in range(len(parts) - 1, 0, -1):
        token = parts[i].strip()
        if re.fullmatch(r"\d+[–\-]?\d*[nft]?", token):
            split_at = i
        else:
            break
    if split_at == len(parts):
        return text.strip(), ""
    return ",".join(parts[:split_at]).strip(), ",".join(parts[split_at:]).strip()


# ── Column-line extraction ─────────────────────────────────────────────────────

def extract_column_lines(page, x_min: float, x_max: float) -> list[dict]:
    """Extract lines from a column defined by [x_min, x_max], sorted by y."""
    cropped = page.crop((x_min, 0, x_max, page.height))
    words = cropped.extract_words(x_tolerance=4, y_tolerance=3)
    if not words:
        return []

    line_map: dict[float, list] = {}
    for w in words:
        y_key = round(w["top"] / 2) * 2
        line_map.setdefault(y_key, []).append(w)

    lines = []
    for y, ws in sorted(line_map.items()):
        ws_sorted = sorted(ws, key=lambda w: w["x0"])
        text = " ".join(w["text"] for w in ws_sorted).strip()
        x0 = ws_sorted[0]["x0"]
        if text:
            lines.append({"text": text, "x0": x0, "y": y})
    return lines


def filter_noise(lines: list[dict]) -> list[dict]:
    """Remove page headers/footers and stray number-only overflow tokens."""
    clean = []
    for l in lines:
        t = l["text"].strip()
        if (
            t.isdigit()
            or re.fullmatch(r"\d+\s+Subject Index", t)
            or re.fullmatch(r"Subject Index\s+\d+", t)
            or t == "Subject Index"
            # Stray overflow: pure page-ref tokens with no alphabetic content
            # e.g. "223–5", "3", "7" that leaked in from the other column
            or (re.fullmatch(r"[\d\s,–\-nft]+", t) and not re.search(r"[a-zA-Z]", t))
        ):
            continue
        clean.append(l)
    return clean


def infer_sub_threshold(lines: list[dict], col_x_min: float) -> float:
    """
    Find the x0 boundary between top-level entries (smaller x0) and
    sub-entries (larger x0) within a single column.
    Ignores lines that appear near the column's left edge (overflow artifacts).
    """
    # Filter out any lines with x0 suspiciously close to the column boundary
    interior = [l for l in lines if l["x0"] > col_x_min + 5]
    if not interior:
        interior = lines

    buckets = Counter(round(l["x0"] / 5) * 5 for l in interior)
    top_buckets = sorted(b[0] for b in buckets.most_common(3))

    if len(top_buckets) >= 2:
        # Threshold = midpoint of the two smallest (most-common) x0 clusters
        return (top_buckets[0] + top_buckets[1]) / 2
    return top_buckets[0] + 10


# ── "See also" normalisation ───────────────────────────────────────────────────

def normalise_see_also(lines: list[dict]) -> list[dict]:
    """
    In the PDF, italic text causes adjacent words to merge without spaces.
    "see also intervention" often comes out as two tokens: "see" + "alsointervention".
    This pass merges them back.
    """
    result = []
    i = 0
    while i < len(lines):
        line = lines[i]
        t = line["text"]

        # Case 1: line is exactly "see" – next line is "also<word>"
        if t.lower() == "see" and i + 1 < len(lines):
            nxt = lines[i + 1]["text"]
            m = re.match(r"^also([A-Za-z].*)$", nxt, re.IGNORECASE)
            if m:
                merged_text = "see also " + m.group(1)
                result.append({**line, "text": merged_text})
                i += 2
                continue

        # Case 2: line itself starts with "also<word>" (merged at extraction)
        m = re.match(r"^also([A-Za-z].*)$", t, re.IGNORECASE)
        if m:
            # Attach to previous entry as see-also; represent as a see-also line
            result.append({**line, "text": "see also " + m.group(1)})
            i += 1
            continue

        result.append(line)
        i += 1
    return result


# ── Index parsing ──────────────────────────────────────────────────────────────

SEE_ALSO_RE = re.compile(r"^see also\s+(.+)$", re.IGNORECASE)


def parse_column_lines(lines: list[dict], sub_threshold: float) -> list[dict]:
    """Parse lines from a single column into structured index entries."""
    entries = []
    current_parent: str | None = None

    for line in lines:
        text = line["text"].strip()
        x0 = line["x0"]
        if not text:
            continue

        is_sub = x0 > sub_threshold

        # "see also" → cross-reference on most recent entry
        m = SEE_ALSO_RE.match(text)
        if m:
            targets = [t.strip() for t in re.split(r"[;,]", m.group(1)) if t.strip()]
            if entries:
                entries[-1]["see_also"].extend(targets)
            continue

        term, refs_str = split_term_refs(text)
        page_refs = parse_page_refs(refs_str) if refs_str else []
        is_header = not refs_str

        if is_sub and current_parent:
            concept = f"{current_parent}, {term}"
            parent = current_parent
        else:
            concept = term
            parent = None
            current_parent = term

        entries.append({
            "concept": concept,
            "parent": parent,
            "term": term,
            "page_refs": page_refs,
            "see_also": [],
            "is_header": is_header,
        })

    return entries


def parse_index(pdf_path: Path) -> list[dict]:
    all_entries = []
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            for col_x_min, col_x_max in [
                (0,                  COLUMN_SPLIT_LEFT),
                (COLUMN_SPLIT_RIGHT, page.width),
            ]:
                lines = extract_column_lines(page, col_x_min, col_x_max)
                lines = filter_noise(lines)
                lines = normalise_see_also(lines)
                if not lines:
                    continue
                threshold = infer_sub_threshold(lines, col_x_min)
                entries = parse_column_lines(lines, threshold)
                for e in entries:
                    e["source_pdf_page"] = page_num
                all_entries.extend(entries)
    return all_entries


# ── Main ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print(f"Parsing: {PDF_PATH}\n")
    entries = parse_index(PDF_PATH)

    print(f"Total entries: {len(entries)}\n")
    print("=== All entries ===")
    prev_parent = None
    for e in entries:
        indent = "    " if e["parent"] else ""
        refs = ", ".join(r["raw"] for r in e["page_refs"]) or "(header)"
        see = f"  →see also: {e['see_also']}" if e["see_also"] else ""
        if e["parent"] != prev_parent and not e["parent"]:
            print()  # blank line between top-level groups
        print(f"{indent}[{e['concept']}]  {refs}{see}")
        prev_parent = e["parent"]

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(entries, f, indent=2)
    print(f"\nSaved {len(entries)} entries → {OUT_PATH}")
