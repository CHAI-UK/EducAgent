"""
Build the Pearl (2009) Causality knowledge graph as a NetworkX DiGraph.

Node types : Section, Concept
Edge types  : NEXT_IN_SEQUENCE, COVERED_IN, ILLUSTRATES, SUBTOPIC_OF,
              RELATED_TO_SEE_ALSO, RELATED_TO_ALIAS, COMMONLY_CONFUSED,
              PREREQUISITE_OF, APPLIED_TO
"""

import json
import pickle
import re
import sys
from collections import defaultdict, Counter
from pathlib import Path

import networkx as nx

# Allow running from any directory
sys.path.insert(0, str(Path(__file__).parent))
from toc_parser import parse_toc, Section

INDEX_PATH  = Path(__file__).parent.parent / "assets/subject_index_parsed.json"
OUTPUT_DIR  = Path(__file__).parent / "output"
BOOK_CHAPTERS = 11

# ── Visual metadata ────────────────────────────────────────────────────────────

CHAPTER_COLORS = {
    1:  "#79c0ff",  # sky blue       — Introduction
    2:  "#56d364",  # green          — Inferred Causation
    3:  "#e3b341",  # amber          — Causal Diagrams
    4:  "#ff7b72",  # salmon         — Actions
    5:  "#d2a8ff",  # lavender       — Social Science / Economics
    6:  "#3fb950",  # lime           — Simpson's Paradox
    7:  "#ffa657",  # orange         — Counterfactuals
    8:  "#58a6ff",  # blue           — Imperfect Experiments
    9:  "#f78166",  # coral          — Probability of Causation
    10: "#a5d6ff",  # light blue     — The Actual Cause
    11: "#7ee787",  # light green    — Reflections
    0:  "#6e7681",  # gray           — unassigned
}

EDGE_META = {
    "NEXT_IN_SEQUENCE":    {"color": "#3d444d", "width": 0.8,  "dashes": [4, 4]},
    "COVERED_IN":          {"color": "#238636", "width": 1.0,  "dashes": False},
    "ILLUSTRATES":         {"color": "#2ea043", "width": 1.0,  "dashes": False},
    "SUBTOPIC_OF":         {"color": "#1f6feb", "width": 1.5,  "dashes": False},
    "RELATED_TO_SEE_ALSO": {"color": "#d29922", "width": 1.5,  "dashes": [6, 3]},
    "RELATED_TO_ALIAS":    {"color": "#8957e5", "width": 1.5,  "dashes": [3, 3]},
    "COMMONLY_CONFUSED":   {"color": "#da3633", "width": 2.0,  "dashes": False},
    "PREREQUISITE_OF":     {"color": "#f0883e", "width": 2.5,  "dashes": False},
    "APPLIED_TO":          {"color": "#1abc9c", "width": 1.2,  "dashes": [2, 4]},
}

# ── Curated knowledge ──────────────────────────────────────────────────────────
# Names below are lowercased/simplified; find_concept() does fuzzy slug matching.

PREREQUISITE_PAIRS = [
    ("probability theory",          "conditional independence"),
    ("probability theory",          "bayesian inference"),
    ("conditional independence",    "bayesian networks probabilistic"),
    ("conditional independence",    "graphoids"),
    ("bayesian networks probabilistic", "d separation"),
    ("bayesian networks probabilistic", "markov condition"),
    ("d separation",                "back door criterion"),
    ("d separation",                "model equivalence"),
    ("d separation",                "causal discovery"),
    ("back door criterion",         "confounding bias"),
    ("back door criterion",         "do calculus"),
    ("confounding bias",            "adjustment for covariates"),
    ("adjustment for covariates",   "propensity score"),
    ("structural equations",        "causal models"),
    ("structural equations",        "sem structural equation modeling"),
    ("causal models",               "counterfactuals"),
    ("causal models",               "causal effect"),
    ("functional models",           "counterfactuals"),
    ("causal effect",               "direct effects"),
    ("causal effect",               "indirect effects"),
    ("do calculus",                 "front door criterion"),
    ("identification",              "do calculus"),
    ("bayesian networks causal",    "identification"),
    ("counterfactuals",             "probability of causation"),
    ("counterfactuals",             "actual causation"),
    ("probability of causation",    "singular causes"),
    ("regression",                  "structural parameters"),
    ("instrumental variables",      "identification"),
]

COMMONLY_CONFUSED_PAIRS = [
    ("confounders",         "collider"),
    ("simpsons paradox",    "confounding bias"),
    ("causal effect",       "correlation"),
    ("d separation",        "conditional independence"),
    ("counterfactuals",     "probability"),
    ("direct effects",      "indirect effects"),
    ("exogeneity",          "ignorability"),
    ("structural equations", "regression"),
    ("intervention",        "conditioning"),
    ("causal discovery",    "causal inference"),
]

ALIAS_PAIRS = [
    ("concomitants",             "covariates"),
    ("mediation",                "indirect effects"),
    ("neyman rubin model",       "potential outcome framework"),
    ("superexogeneity",          "exogeneity"),
    ("dag isomorph",             "stability"),
    ("latent structure",         "semi markovian models"),
    ("set operator",             "do calculus"),
    ("standardize",              "adjustment for covariates"),
]

SEE_ALSO_PAIRS = [
    ("actions",                  "intervention"),
    ("actual causation",         "singular causes"),
    ("adjustment for covariates", "confounding bias"),
    ("confounding bias",         "exogeneity"),
    ("confounding bias",         "ignorability"),
    ("faithfulness",             "stability"),
    ("sem structural equation modeling", "structural equations"),
    ("screening off",            "conditional independence"),
    ("semi markovian models",    "latent structure"),
    ("total effect",             "causal effect"),
    ("singular causes",          "actual causation"),
    ("suppressor effect",        "simpsons paradox"),
    ("treatment time varying",   "intervention"),
]

# ── Index entry corrections (PDF parsing artifacts) ────────────────────────────
# Cross-checked against assets/.../24_Subject_Index.mmd (ground truth).
#
# Root causes:
#   1. Digit-prefix leak  — a trailing page number from one PDF line bled onto
#      the start of the next, producing "146 Markovian", "0 coherence", etc.
#   2. Page refs in name  — split_term_refs stopped early on trailing commas,
#      leaving refs inside the concept string: "Bayesian networks,causal".
#   3. See-also merge     — italic "see also" text printed without spaces in
#      the PDF, producing "concomitants,seecovariates".
#   4. OCR errors         — "do calculus" → "docalculus", "v-structure" → "y-structure".
#   5. Sub-entry promoted — "preference of" is a sub-entry of "causal models"
#      in the index but was classified as a top-level entry.

# Concepts to drop entirely (no corresponding entry in the ground-truth index).
# Children whose parent appears here are also dropped automatically.
_DROP_CONCEPTS: set[str] = {
    "146 Markovian",                               # page 146 leaked before sub-entry
    "62 causal",                                   # page 62 leaked artifact
    "2 testing for",                               # page 2 leaked artifact
    "5 and background knowledge",                  # Bayesian method sub-entries misrouted
    "s, and back-door criterion",                  # "s" from "ignorability" clipped
    "preference of",                               # sub-entry of causal models, mis-promoted
    "–72,356–7, operational definition",           # page-range prefix artifact
    "82,200, structural theory,seecausation,structural",  # compound artifact
    "structural interpretation of",               # orphaned sub-entry of potential-outcome framework
}

# Rename map: exact JSON concept string → canonical name from the .mmd.
_CONCEPT_RENAMES: dict[str, str] = {
    # OCR / whitespace errors
    "docalculus":               "do calculus",
    "y-structure":              "v-structure",
    # Digit-prefix leaks — strip the spurious leading number
    "0 coherence":              "coherence",
    "63 temporal information":  "temporal information",
    "98 causal theory":         "causal theory",
    # Page refs embedded in concept name (split_term_refs stopped early)
    "Bayes conditionalization,73,109,112,":           "Bayes conditionalization",
    "Bayesian networks,causal":                       "Bayesian networks, causal",
    "Bayesian networks,probabilistic":                "Bayesian networks, probabilistic",
    "ETT (effect of treatment on the treated),269–70,": "ETT (effect of treatment on the treated)",
    "instrumental variables,90,153,168,247–8,":       "instrumental variables",
    "quantum mechanics and causation,26,62,220,":     "quantum mechanics and causation",
    "randomized experiments,33,259,332,340,388,":     "randomized experiments",
    "temporal bias,of statistical associations,59,":  "temporal bias, of statistical associations",
    "treatment,time varying":                         "treatment, time varying",
    "homomorphy,in imaging":                          "homomorphy, in imaging",
    "world,causal":                                   "world, causal",
    "submodel,causal":                                "submodel, causal",
    # Page-range prefix artifacts where the real concept should be kept
    "–70, identifying models":                        "identifying models",
    # Page refs embedded in sub-entry concept names
    "error terms, counterfactual interpretation,214–15,244n,": "error terms, counterfactual interpretation",
    # See-also text merged into concept name
    "concomitants,seecovariates":      "concomitants",
    "DAG isomorph,seestability":       "DAG isomorph",
    "superexogeneity,seeexogeneily":   "superexogeneity",
    "set(·) operator,see do(·) operator": "set(·) operator",
}


def preprocess_index_entries(entries: list[dict]) -> list[dict]:
    """
    Remove and rename parsing artifacts in the raw subject index JSON
    before building the graph.  All corrections are cross-checked against
    the ground-truth markdown in 24_Subject_Index.mmd.
    """
    # Track concepts that must be dropped (including cascaded children)
    drop_set: set[str] = set(_DROP_CONCEPTS)

    # First pass: also mark children of dropped parents
    for e in entries:
        if e.get("parent") in drop_set:
            drop_set.add(e["concept"])

    # Also treat entries whose concept starts with digit(s) + space as drop/rename
    # candidates if not already handled by _CONCEPT_RENAMES.
    digit_prefix_re = re.compile(r"^\d+\s+([A-Za-z].*)$")

    result: list[dict] = []
    for e in entries:
        concept = e["concept"]
        parent  = e.get("parent")

        # Drop explicit artifacts and cascaded children
        if concept in drop_set or parent in drop_set:
            continue

        # Apply explicit rename
        if concept in _CONCEPT_RENAMES:
            e = dict(e)
            e["concept"] = _CONCEPT_RENAMES[concept]
            concept = e["concept"]

        # Rename parent if it was renamed
        if parent in _CONCEPT_RENAMES:
            e = dict(e)
            e["parent"] = _CONCEPT_RENAMES[parent]
            parent = e["parent"]

        # Strip residual digit-prefix leaks not covered by _CONCEPT_RENAMES
        m = digit_prefix_re.match(concept)
        if m:
            e = dict(e)
            e["concept"] = m.group(1)
            concept = e["concept"]

        result.append(e)

    n_dropped = len(entries) - len(result)
    if n_dropped:
        print(f"  [preprocess] dropped/renamed {n_dropped} artifact entries")

    return result


# ── Helpers ────────────────────────────────────────────────────────────────────

def slugify(name: str) -> str:
    name = name.replace("'", "").replace("\u2019", "")  # strip apostrophes
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def most_specific_section(page: int, sections: list[Section]) -> Section | None:
    """Return the deepest (most specific) section covering this page."""
    candidates = [s for s in sections if s.start_page <= page <= s.end_page]
    return max(candidates, key=lambda s: s.depth) if candidates else None


def find_concept(name: str, G: nx.DiGraph) -> str | None:
    """Find a concept node by approximate slug match."""
    target = slugify(name)
    if target in G and G.nodes[target].get("type") == "concept":
        return target
    # Substring fallback: target is contained in node id or vice versa
    for nid, data in G.nodes(data=True):
        if data.get("type") != "concept":
            continue
        if target in nid or nid in target:
            return nid
    return None


def add_edge(G: nx.DiGraph, src: str, tgt: str, etype: str) -> None:
    """Add a directed edge with visual metadata; skip if nodes missing."""
    if src not in G or tgt not in G or src == tgt:
        return
    meta = EDGE_META[etype]
    G.add_edge(src, tgt,
               edge_type=etype,
               color=meta["color"],
               width=meta["width"],
               dashes=meta["dashes"])


# ── Graph builder ──────────────────────────────────────────────────────────────

def build_graph() -> nx.DiGraph:
    G = nx.DiGraph()
    sections = parse_toc()
    index_entries = preprocess_index_entries(json.loads(INDEX_PATH.read_text()))

    # ── 1. Section nodes ───────────────────────────────────────────────────────
    sec_node_ids: list[str] = []
    for sec in sections:
        nid = f"sec_{slugify(sec.section_id)}"
        sec_node_ids.append(nid)
        G.add_node(nid,
                   type="section",
                   section_id=sec.section_id,
                   label=f"§{sec.section_id} {sec.title}",
                   short_label=sec.title if sec.depth <= 1 else "",
                   tooltip=f"§{sec.section_id}: {sec.title}\npp. {sec.start_page}–{sec.end_page}",
                   chapter=sec.chapter,
                   depth=sec.depth,
                   start_page=sec.start_page,
                   end_page=sec.end_page,
                   color=CHAPTER_COLORS.get(sec.chapter, CHAPTER_COLORS[0]),
                   shape="box",
                   size=14 + max(0, (2 - sec.depth)) * 5)

    # NEXT_IN_SEQUENCE (linear TOC order)
    for a, b in zip(sec_node_ids, sec_node_ids[1:]):
        add_edge(G, a, b, "NEXT_IN_SEQUENCE")

    # ── 2. Concept nodes ───────────────────────────────────────────────────────
    concept_pages: dict[str, set[int]] = defaultdict(set)
    concept_meta:  dict[str, dict]     = {}

    for entry in index_entries:
        cid = slugify(entry["concept"])
        for ref in entry["page_refs"]:
            concept_pages[cid].update(ref["pages"])
        concept_meta[cid] = {
            "name":      entry["concept"],
            "parent":    entry.get("parent"),
            "term":      entry.get("term", ""),
            "is_header": entry.get("is_header", False),
            "see_also":  entry.get("see_also", []),
        }

    # Assign each concept to its earliest chapter
    concept_chapter: dict[str, int] = {}
    for cid, pages in concept_pages.items():
        chaps = []
        for p in sorted(pages):
            sec = most_specific_section(p, sections)
            if sec:
                chaps.append(sec.chapter)
        concept_chapter[cid] = min(chaps) if chaps else 0

    for cid, meta in concept_meta.items():
        pages_sorted = sorted(concept_pages[cid])
        ch = concept_chapter.get(cid, 0)
        page_str = ", ".join(str(p) for p in pages_sorted[:12])
        if len(pages_sorted) > 12:
            page_str += "…"

        G.add_node(cid,
                   type="concept",
                   label=meta["name"],
                   short_label=meta["name"] if len(pages_sorted) >= 2 else "",
                   tooltip=f"{meta['name']}\nPages: {page_str}",
                   chapter=ch,
                   color=CHAPTER_COLORS.get(ch, CHAPTER_COLORS[0]),
                   shape="dot",
                   size=7 + min(len(pages_sorted) * 0.9, 18),
                   page_refs=pages_sorted)

    # ── 3. COVERED_IN + ILLUSTRATES ───────────────────────────────────────────
    for cid, pages in concept_pages.items():
        if cid not in G:
            continue
        seen: set[str] = set()
        for p in pages:
            sec = most_specific_section(p, sections)
            if sec:
                sid = f"sec_{slugify(sec.section_id)}"
                if sid not in seen:
                    seen.add(sid)
                    add_edge(G, cid, sid, "COVERED_IN")
                    add_edge(G, sid, cid, "ILLUSTRATES")

    # ── 4. SUBTOPIC_OF ────────────────────────────────────────────────────────
    for entry in index_entries:
        if not entry.get("parent"):
            continue
        child_id  = slugify(entry["concept"])
        parent_id = slugify(entry["parent"])
        add_edge(G, child_id, parent_id, "SUBTOPIC_OF")

    # ── 5. APPLIED_TO  ("of <concept>" sub-entries) ───────────────────────────
    of_re = re.compile(r"^of\s+(.+)$", re.IGNORECASE)
    for entry in index_entries:
        if not entry.get("parent"):
            continue
        m = of_re.match(entry.get("term", ""))
        if not m:
            continue
        ref_name = m.group(1).strip()
        child_id = slugify(entry["concept"])
        ref_id   = find_concept(ref_name, G)
        if ref_id:
            add_edge(G, child_id, ref_id, "APPLIED_TO")

    # ── 6. RELATED_TO_SEE_ALSO  (parsed + hardcoded) ─────────────────────────
    for entry in index_entries:
        src_id = slugify(entry["concept"])
        for sa in entry.get("see_also", []):
            tgt_id = find_concept(sa, G)
            if tgt_id:
                add_edge(G, src_id, tgt_id, "RELATED_TO_SEE_ALSO")

    for a_name, b_name in SEE_ALSO_PAIRS:
        aid = find_concept(a_name, G)
        bid = find_concept(b_name, G)
        if aid and bid:
            add_edge(G, aid, bid, "RELATED_TO_SEE_ALSO")
            add_edge(G, bid, aid, "RELATED_TO_SEE_ALSO")

    # ── 7. RELATED_TO_ALIAS ───────────────────────────────────────────────────
    for a_name, b_name in ALIAS_PAIRS:
        aid = find_concept(a_name, G)
        bid = find_concept(b_name, G)
        if aid and bid:
            add_edge(G, aid, bid, "RELATED_TO_ALIAS")
            add_edge(G, bid, aid, "RELATED_TO_ALIAS")

    # ── 8. COMMONLY_CONFUSED ─────────────────────────────────────────────────
    for a_name, b_name in COMMONLY_CONFUSED_PAIRS:
        aid = find_concept(a_name, G)
        bid = find_concept(b_name, G)
        if aid and bid:
            add_edge(G, aid, bid, "COMMONLY_CONFUSED")
            add_edge(G, bid, aid, "COMMONLY_CONFUSED")

    # ── 9. PREREQUISITE_OF ────────────────────────────────────────────────────
    for a_name, b_name in PREREQUISITE_PAIRS:
        aid = find_concept(a_name, G)
        bid = find_concept(b_name, G)
        if aid and bid:
            add_edge(G, aid, bid, "PREREQUISITE_OF")

    return G


# ── Save / report ──────────────────────────────────────────────────────────────

def save_graph(G: nx.DiGraph, out_dir: Path = OUTPUT_DIR) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "graph.pkl", "wb") as f:
        pickle.dump(G, f)

    from networkx.readwrite import json_graph
    with open(out_dir / "graph.json", "w") as f:
        json.dump(json_graph.node_link_data(G), f, indent=2, default=str)

    n = G.number_of_nodes()
    e = G.number_of_edges()
    print(f"\nGraph: {n} nodes, {e} edges")

    type_counts = Counter(d.get("edge_type", "?") for _, _, d in G.edges(data=True))
    for etype in sorted(EDGE_META.keys()):
        print(f"  {etype:<28} {type_counts.get(etype, 0):>5}")


if __name__ == "__main__":
    G = build_graph()
    save_graph(G)
    print(f"\nSaved to {OUTPUT_DIR}/")
