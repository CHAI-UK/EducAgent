"""
Audit subject_index_parsed.json for duplicate/redundant concept entries.

Outputs three sections:
  1. Definition sub-entries  — metadata, not real concepts
  2. Symmetric index pairs   — (A, B) and (B, A) both indexed
  3. High-Jaccard pairs      — concepts sharing >= 50% of their pages

Run:
    conda run -n edu python graph/audit_duplicates.py
    conda run -n edu python graph/audit_duplicates.py --threshold 0.4
"""

import json
import re
import sys
from collections import defaultdict
from itertools import combinations
from pathlib import Path

INDEX_PATH = Path(__file__).parent.parent / "assets/subject_index_parsed.json"

THRESHOLD = float(sys.argv[sys.argv.index("--threshold") + 1]) if "--threshold" in sys.argv else 0.5


def slugify(name: str) -> str:
    name = name.replace("'", "").replace("\u2019", "")
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def jaccard(a: set, b: set) -> float:
    union = a | b
    return len(a & b) / len(union) if union else 0.0


def main() -> None:
    data = json.loads(INDEX_PATH.read_text())
    print(f"Loaded {len(data)} index entries\n")

    # ── 1. Definition sub-entries ─────────────────────────────────────────────
    DEF_RE = re.compile(
        r"^(definition|definitions|definition of|definitions of|"
        r"general definition|operational definition|hierarchy of definitions|"
        r"counterfactual and graphical definitions)$",
        re.I,
    )
    def_entries = [e for e in data if DEF_RE.match(e.get("term", "").strip())]

    print(f"{'='*60}")
    print(f"1. DEFINITION SUB-ENTRIES  ({len(def_entries)} found)")
    print(f"{'='*60}")
    print("These point to where a concept is *defined*, not new concepts.")
    print("Recommendation: drop as nodes; store pages as 'definition_pages' on parent.\n")
    for e in sorted(def_entries, key=lambda x: x["parent"] or ""):
        pages = sorted({p for r in e["page_refs"] for p in r["pages"]})
        print(f"  parent={e['parent']!r:40s}  term={e['term']!r:30s}  pages={pages}")

    # ── Build page sets per concept ───────────────────────────────────────────
    concept_pages: dict[str, tuple[str, set[int]]] = {}
    for e in data:
        cid = slugify(e["concept"])
        pages = {p for r in e["page_refs"] for p in r["pages"]}
        # Merge pages if slug collision (shouldn't happen but guard)
        if cid in concept_pages:
            _, existing = concept_pages[cid]
            concept_pages[cid] = (e["concept"], existing | pages)
        else:
            concept_pages[cid] = (e["concept"], pages)

    # ── 2. Symmetric index pairs ──────────────────────────────────────────────
    sym_candidates: dict[tuple, list] = defaultdict(list)
    for e in data:
        c = e["concept"]
        if "," in c:
            parts = [p.strip() for p in c.split(",", 1)]
            key = tuple(sorted(p.lower() for p in parts))
            sym_candidates[key].append(e)

    sym_pairs = [(k, v) for k, v in sym_candidates.items() if len(v) >= 2]

    print(f"\n{'='*60}")
    print(f"2. SYMMETRIC INDEX PAIRS  ({len(sym_pairs)} found)")
    print(f"{'='*60}")
    print("Index entries of the form 'A, B' and 'B, A' — likely the same concept.\n")

    for key, entries in sorted(sym_pairs, key=lambda kv: -jaccard(
        {p for r in kv[1][0]["page_refs"] for p in r["pages"]},
        {p for r in kv[1][1]["page_refs"] for p in r["pages"]},
    )):
        names = [e["concept"] for e in entries]
        page_sets = [{p for r in e["page_refs"] for p in r["pages"]} for e in entries]
        j = jaccard(page_sets[0], page_sets[1])
        verdict = ("MERGE (strong)"   if j >= 0.5 else
                   "REVIEW (partial)" if j > 0.0 else
                   "DIFFERENT? (no overlap)")
        print(f"  [{verdict}]  Jaccard={j:.2f}")
        for name, ps in zip(names, page_sets):
            print(f"    {name!r:50s}  pages={sorted(ps)}")
        print()

    # ── 3. High-Jaccard pairs ─────────────────────────────────────────────────
    # Only consider concepts with >= 2 pages (single-page entries are too noisy)
    eligible = [
        (cid, name, pages)
        for cid, (name, pages) in concept_pages.items()
        if len(pages) >= 2
    ]
    eligible.sort(key=lambda x: x[1])

    hits = []
    for (cid1, name1, p1), (cid2, name2, p2) in combinations(eligible, 2):
        j = jaccard(p1, p2)
        if j >= THRESHOLD:
            hits.append((j, name1, name2, sorted(p1), sorted(p2)))
    hits.sort(reverse=True)

    # Exclude symmetric pairs already shown above (by name-key)
    sym_names: set[frozenset] = set()
    for _, entries in sym_pairs:
        sym_names.add(frozenset(e["concept"] for e in entries))
    novel_hits = [(j, n1, n2, p1, p2) for j, n1, n2, p1, p2 in hits
                  if frozenset([n1, n2]) not in sym_names]

    print(f"\n{'='*60}")
    print(f"3. HIGH-JACCARD PAIRS  (threshold={THRESHOLD:.1f}, {len(novel_hits)} found, excluding symmetric pairs)")
    print(f"{'='*60}")
    print("Concepts sharing >= threshold% of their pages — potential coreferences.\n")

    for j, name1, name2, pages1, pages2 in novel_hits:
        shared = sorted(set(pages1) & set(pages2))
        print(f"  Jaccard={j:.2f}  shared={shared}")
        print(f"    A: {name1!r:55s}  all={pages1}")
        print(f"    B: {name2!r:55s}  all={pages2}")
        print()

    print(f"Summary: {len(def_entries)} definition entries, "
          f"{len(sym_pairs)} symmetric pairs, "
          f"{len(novel_hits)} high-Jaccard pairs (threshold={THRESHOLD:.1f})")


if __name__ == "__main__":
    main()
