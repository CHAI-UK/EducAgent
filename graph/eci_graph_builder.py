"""
Build the Elements of Causal Inference (ECI, 2017) knowledge graph.

Node types:
  section  — TOC sections (box)
  concept  — Index concepts (dot)
  category — Umbrella grouping nodes, e.g. "graph", "entropy" (diamond)

Edge types:
  NEXT_IN_SEQUENCE, COVERED_IN, ILLUSTRATES, SUBTOPIC_OF,
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

sys.path.insert(0, str(Path(__file__).parent))
from eci_toc_parser import parse_toc, Section

INDEX_PATH = (
    Path(__file__).parent.parent
    / "assets/ElementsOfCausalInference_sections/markdowns/18_Index/18_Index.mmd"
)
OUTPUT_DIR = Path(__file__).parent / "output"

# ── Visual metadata ────────────────────────────────────────────────────────────

CHAPTER_COLORS = {
    1:  "#79c0ff",  # sky blue       — Statistical & Causal Models
    2:  "#56d364",  # green          — Assumptions for Causal Inference
    3:  "#e3b341",  # amber          — Cause-Effect Models
    4:  "#ff7b72",  # salmon         — Learning Cause-Effect Models
    5:  "#d2a8ff",  # lavender       — Connections to ML, I
    6:  "#3fb950",  # lime           — Multivariate Causal Models
    7:  "#ffa657",  # orange         — Learning Multivariate Causal Models
    8:  "#58a6ff",  # blue           — Connections to ML, II
    9:  "#f78166",  # coral          — Hidden Variables
    10: "#a5d6ff",  # light blue     — Time Series
    11: "#7ee787",  # light green    — Appendix A
    12: "#8b949e",  # gray-blue      — Appendix B
    13: "#6e7681",  # gray           — Appendix C
    0:  "#6e7681",  # gray           — unassigned
}

EDGE_META = {
    "NEXT_IN_SEQUENCE":    {"color": "#3d444d", "width": 0.8,  "dashes": [4, 4]},
    "COVERED_IN":          {"color": "#238636", "width": 1.0,  "dashes": False},
    "SUBTOPIC_OF":         {"color": "#1f6feb", "width": 1.5,  "dashes": False},
    "RELATED_TO_SEE_ALSO": {"color": "#d29922", "width": 1.5,  "dashes": [6, 3]},
    "RELATED_TO_ALIAS":    {"color": "#8957e5", "width": 1.5,  "dashes": [3, 3]},
    "COMMONLY_CONFUSED":   {"color": "#da3633", "width": 2.0,  "dashes": False},
    "PREREQUISITE_OF":     {"color": "#f0883e", "width": 2.5,  "dashes": False},
    "APPLIED_TO":          {"color": "#1abc9c", "width": 1.2,  "dashes": [2, 4]},
}

# ── Index parsing ──────────────────────────────────────────────────────────────

# Two-column PDF extraction artifacts (merged lines → expand to separate entries)
LINE_CORRECTIONS: dict[str, list[str]] = {
    "DCM, see dynamic causal modeling descendant, see graph": [
        "DCM, see dynamic causal modeling",
        "descendant, see graph",
    ],
    "SCM, see structural causal model selection bias, 104": [
        "SCM, see structural causal model",
        "selection bias, 104",
    ],
    "SEM, see structural equation model semi-supervised learning, 71": [
        "SEM, see structural equation model",
        "semi-supervised learning, 71",
    ],
    # Truncated 'see' target (column break cut off the last word)
    "ICA, see independent component": [
        "ICA, see independent component analysis",
    ],
}

# Canonical full name for sub-entries: (parent_lower, sub_term_lower) → name
SUB_ENTRY_NAMES: dict[tuple[str, str], str] = {
    # entropy
    ("entropy", "shannon entropy"):     "Shannon Entropy",
    ("entropy", "transfer entropy"):    "Transfer Entropy",
    # graph — some sub-entries already carry the acronym in parentheses
    ("graph", "collider"):                                         "Collider",
    ("graph", "d-separation"):                                     "D-Separation",
    ("graph", "descendant"):                                       "Descendant",
    ("graph", "directed acyclic graph (dag)"):                     "Directed Acyclic Graph (DAG)",
    ("graph", "induced path graph (ipg)"):                         "Induced Path Graph (IPG)",
    ("graph", "maximal ancestral graph (mag)"):                    "Maximal Ancestral Graph (MAG)",
    ("graph", "parent"):                                           "Parent",
    ("graph", "partially ancestral graph (pag)"):                  "Partially Ancestral Graph (PAG)",
    ("graph", "partially directed acyclic graph (pdag)"):          "Partially Directed Acyclic Graph (PDAG)",
    ("graph", "partially oriented induced path graph (poipg)"):    "Partially Oriented Induced Path Graph (POIPG)",
    ("graph", "path"):                                             "Path",
    ("graph", "v-structure"):                                      "V-Structure",
    ("graph", "y-structure"):                                      "Y-Structure",
    # independence
    ("independence", "causal mechanisms"):             "Independence of Causal Mechanisms",
    ("independence", "generic viewpoint assumption"):  "Generic Viewpoint Assumption",
    ("independence", "noises"):                        "Independence of Noises",
    ("independence", "objects"):                       "Independence of Objects",
    ("independence", "random variables"):              "Independence of Random Variables",
    ("independence", "structure from motion"):         "Structure from Motion",
    # invariance / invariant
    ("invariance", "simon's criterion"):  "Simon's Criterion",
    ("invariant",  "causal prediction"):  "Invariant Causal Prediction",
    ("invariant",  "conditionals"):       "Invariant Conditionals",
    ("invariant",  "mechanisms"):         "Invariant Mechanisms",
    # mechanism — "invariant" sub-entry maps to same name → pages merge on build
    ("mechanism",  "independent"):        "Independent Mechanisms",
    ("mechanism",  "invariant"):          "Invariant Mechanisms",
    # noises
    ("noises",     "independent"):        "Independent Noises",
    # regression
    ("regression", "half-sibling"):       "Half-Sibling Regression",
    # sufficiency
    ("sufficiency", "causal sufficiency"):          "Causal Sufficiency",
    ("sufficiency", "interventional sufficiency"):  "Interventional Sufficiency",
    # time series
    ("time series", "full time graph"):  "Full Time Graph",
    ("time series", "summary graph"):    "Summary Graph",
    # variable
    ("variable", "endogenous"):  "Endogenous Variable",
    ("variable", "exogenous"):   "Exogenous Variable",
}

# Acronym merges: (ACRONYM, full_name_lower)
# The canonical node is renamed  "Title Case Full Name (ACRONYM)"
ACRONYM_PAIRS: list[tuple[str, str]] = [
    ("ACE",    "average causal effect"),
    ("ANM",    "additive noise model"),
    ("BIC",    "bayesian information criterion"),
    ("CAM",    "causal additive model"),
    ("DCM",    "dynamic causal modeling"),
    ("fMRI",   "functional magnetic resonance imaging"),
    ("GES",    "greedy equivalence search"),
    ("GIES",   "greedy interventional equivalence search"),
    ("ICA",    "independent component analysis"),
    ("ILP",    "integer linear programming"),
    ("LiNGAM", "linear non-gaussian acyclic model"),
    ("NP",     "nondeterministic polynomial time"),
    ("RESIT",  "regression with subsequent independence test"),
    ("SCM",    "structural causal model"),
    ("SIC",    "spectral independence criterion"),
]

# Alias-only merges (add as alias, no rename): (alias_lower, canonical_lower)
ALIAS_ONLY: list[tuple[str, str]] = [
    ("bd score",  "bayesian dirichlet score"),
    ("bde score", "bayesian dirichlet equivalence score"),
]

# Synonym absorptions: synonym_lower → canonical_lower (synonym disappears as a node)
SYNONYM_MAP: dict[str, str] = {
    "causal discovery":          "causal learning",
    "structure learning":        "causal learning",
    "causal effect":             "total causal effect",
    "confounder":                "common cause",
    "structural equation model": "structural causal model",
}

# Pure alphabetical redirects that point to a category but whose concept is
# already captured as a sub-entry — discard after sub-entry processing.
REDUNDANT_REDIRECTS: set[str] = {
    # graph sub-entries
    "collider", "d-separation", "descendant", "directed acyclic graph",
    "induced path graph", "maximal ancestral graph", "parent",
    "partially ancestral graph", "partially directed acyclic graph",
    "partially oriented induced path graph", "path", "v-structure", "y-structure",
    # graph sub-entry acronyms
    "dag", "ipg", "mag", "pag", "pdag", "poipg",
    # sufficiency sub-entries
    "causal sufficiency", "interventional sufficiency",
    # entropy sub-entries
    "transfer entropy",
}

# ── Curated knowledge ──────────────────────────────────────────────────────────

PREREQUISITE_PAIRS: list[tuple[str, str]] = [
    # Probability → everything
    ("random variable",                   "structural causal model (scm)"),
    ("conditional independence",          "d-separation"),
    ("conditional independence",          "causal markov condition"),
    # Graph theory foundations
    ("directed acyclic graph (dag)",      "d-separation"),
    ("directed acyclic graph (dag)",      "structural causal model (scm)"),
    ("d-separation",                      "causal markov condition"),
    ("causal markov condition",           "faithfulness"),
    ("causal markov condition",           "causal minimality"),
    ("markov property",                   "causal markov condition"),
    ("markov equivalence",                "pc algorithm"),
    # Identification
    ("d-separation",                      "backdoor criterion"),
    ("backdoor criterion",                "adjustment"),
    ("backdoor criterion",                "propensity score matching"),
    # Cause-effect models
    ("structural causal model (scm)",     "interventions"),
    ("structural causal model (scm)",     "counterfactuals"),
    ("structural causal model (scm)",     "potential outcomes"),
    ("structural causal model (scm)",     "total causal effect (ace)"),
    ("additive noise model (anm)",        "causal learning"),
    ("linear non-gaussian acyclic model (lingam)", "independent component analysis (ica)"),
    # Learning algorithms
    ("faithfulness",                      "causal learning"),
    ("kolmogorov complexity",             "additive noise model (anm)"),
    ("markov equivalence",                "greedy equivalence search (ges)"),
    ("causal learning",                   "pc algorithm"),
    ("causal learning",                   "ges"),
    ("causal learning",                   "greedy equivalence search (ges)"),
    # Hidden variables
    ("directed acyclic graph (dag)",      "maximal ancestral graph (mag)"),
    ("maximal ancestral graph (mag)",     "fci algorithm"),
    ("instrumental variable",             "total causal effect (ace)"),
    # Time series
    ("structural causal model (scm)",     "granger causality"),
    ("granger causality",                 "transfer entropy"),
]

COMMONLY_CONFUSED_PAIRS: list[tuple[str, str]] = [
    ("granger causality",               "total causal effect (ace)"),
    ("markov condition",                "causal markov condition"),
    ("structural causal model (scm)",   "structural equation model"),   # SEM is subsumed
    ("counterfactuals",                 "potential outcomes"),           # different formalisms
    ("d-separation",                    "conditional independence"),
    ("common cause",                    "collider"),                     # opposite roles
    ("faithfulness",                    "markov property"),
    ("adjustment",                      "inverse probability weighting"),
]

SEE_ALSO_PAIRS: list[tuple[str, str]] = [
    ("granger causality",                           "transfer entropy"),
    ("pc algorithm",                                "fci algorithm"),
    ("greedy equivalence search (ges)",             "greedy interventional equivalence search (gies)"),
    ("backdoor criterion",                          "propensity score matching"),
    ("instrumental variable",                       "potential outcomes"),
    ("causal additive model (cam)",                 "additive noise model (anm)"),
    ("bayesian information criterion (bic)",        "bayesian dirichlet score"),
    ("simpson's paradox",                           "common cause"),
    ("invariant causal prediction",                 "causal learning"),
    ("half-sibling regression",                     "inverse probability weighting"),
    ("independence of causal mechanisms",           "independent mechanisms"),
    ("invariant mechanisms",                        "mechanism"),
    ("independence of noises",                      "independent noises"),
]

ALIAS_PAIRS: list[tuple[str, str]] = [
    # These pairs were absorbed as synonyms but we want a cross-edge reminder
    # (concept was merged so we add edges between aliases and canonical)
]

# ── Helpers ────────────────────────────────────────────────────────────────────

def slugify(name: str) -> str:
    name = name.replace("'", "").replace("\u2019", "")
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def most_specific_section(page: int, sections: list[Section]) -> Section | None:
    candidates = [s for s in sections if s.start_page <= page <= s.end_page]
    return max(candidates, key=lambda s: s.depth) if candidates else None


def find_concept(name: str, G: nx.DiGraph) -> str | None:
    """Find concept/category node by approximate slug matching."""
    target = slugify(name)
    if target in G and G.nodes[target].get("type") in ("concept", "category"):
        return target
    for nid, data in G.nodes(data=True):
        if data.get("type") not in ("concept", "category"):
            continue
        if target in nid or nid in target:
            return nid
    return None


def add_edge(G: nx.DiGraph, src: str, tgt: str, etype: str) -> None:
    if src not in G or tgt not in G or src == tgt:
        return
    meta = EDGE_META[etype]
    G.add_edge(src, tgt,
               edge_type=etype,
               color=meta["color"],
               width=meta["width"],
               dashes=meta["dashes"])


# ── Index parsing ──────────────────────────────────────────────────────────────

def _title_case(s: str) -> str:
    """Minimal title-case preserving known initialisms."""
    LOWERS = {"of", "and", "to", "in", "for", "a", "an", "the", "with", "by", "from"}
    words = s.split()
    return " ".join(
        w.capitalize() if (i == 0 or w.lower() not in LOWERS) else w.lower()
        for i, w in enumerate(words)
    )


def _parse_pages(s: str) -> list[int]:
    """Expand '48, 50–52, 208' → sorted unique list of ints."""
    pages: list[int] = []
    for part in re.split(r",\s*", s.strip()):
        part = part.strip()
        m = re.match(r"^(\d+)\s*[–\-]\s*(\d+)$", part)
        if m:
            pages.extend(range(int(m.group(1)), int(m.group(2)) + 1))
        elif re.match(r"^\d+$", part):
            pages.append(int(part))
    return sorted(set(pages))


def _parse_entry_line(line: str) -> tuple[str, list[int], list[str]]:
    """Return (concept_name, pages, see_refs) for one raw index line."""
    line = line.strip()

    # Extract ', see X' (must have a space before 'see' to avoid false matches)
    see_refs: list[str] = []
    see_m = re.search(r",\s+see\s+(.+)$", line, re.IGNORECASE)
    if see_m:
        see_refs = [s.strip() for s in re.split(r"\s+and\s+", see_m.group(1))]
        line = line[:see_m.start()].strip()

    # Split on commas; trailing numeric parts are page refs
    parts = [p.strip() for p in line.split(",")]
    page_re = re.compile(r"^\d+(?:\s*[–\-]\s*\d+)?$")
    boundary = len(parts) - 1
    for i in range(len(parts) - 1, -1, -1):
        if not page_re.match(parts[i]):
            boundary = i
            break

    concept  = ", ".join(parts[: boundary + 1]).strip()
    page_str = ", ".join(parts[boundary + 1 :]).strip()
    pages    = _parse_pages(page_str) if page_str else []
    return concept, pages, see_refs


def parse_eci_index(path: Path = INDEX_PATH) -> list[dict]:
    """
    Parse the ECI subject index .mmd into a list of entry dicts.

    Each dict:
      concept   : str        — canonical display name
      aliases   : list[str]  — alternative names / acronyms
      pages     : list[int]  — all page references
      node_type : str        — "concept" | "category"
      parent    : str|None   — parent concept name (for SUBTOPIC_OF edge)
      see_refs  : list[str]  — cross-reference targets
    """
    lines = path.read_text().splitlines()

    # ── Pre-process: expand two-column merge artifacts ─────────────────────────
    expanded: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped in LINE_CORRECTIONS:
            indent = " " * (len(line) - len(line.lstrip()))
            for fix in LINE_CORRECTIONS[stripped]:
                expanded.append(indent + fix)
        else:
            expanded.append(line)

    # ── Parse lines into (is_sub, parent_text, concept, pages, see_refs) ───────
    RawRow = tuple[bool, str | None, str, list[int], list[str]]
    raw: list[RawRow] = []
    current_parent: str | None = None

    for line in expanded:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "<---" in stripped:
            current_parent = None   # reset context at page-split markers
            continue

        is_sub  = line.startswith("    ") and not line.startswith("        ")
        concept, pages, see_refs = _parse_entry_line(stripped)
        if not concept:
            continue

        raw.append((is_sub, current_parent if is_sub else None, concept, pages, see_refs))

        # Update parent context for next lines (top-level entries only)
        if not is_sub:
            current_parent = concept

    # ── Identify which top-level entries have sub-entries (→ category nodes) ───
    has_sub: set[str] = {parent.lower() for is_sub, parent, *_ in raw if is_sub and parent}

    # ── Build entry dict ───────────────────────────────────────────────────────
    entries: dict[str, dict] = {}   # key = lowercased canonical name

    for is_sub, parent, concept_raw, pages, see_refs in raw:
        if is_sub and parent:
            key_sub = SUB_ENTRY_NAMES.get((parent.lower(), concept_raw.lower()), concept_raw)
            full_name = key_sub
            parent_name = parent
        else:
            full_name   = concept_raw
            parent_name = None

        is_cat = (not is_sub
                  and not pages
                  and full_name.lower() in has_sub)
        node_type = "category" if is_cat else "concept"
        key = full_name.lower()

        if key in entries:
            # Merge duplicate entries (e.g. "Invariant Mechanisms" from two parents,
            # or alphabetical redirect + sub-entry for the same concept)
            entries[key]["pages"] = sorted(set(entries[key]["pages"] + pages))
            entries[key]["see_refs"] = list(dict.fromkeys(entries[key]["see_refs"] + see_refs))
            # Promote parent: if the existing entry has no parent (came from an
            # alphabetical redirect) but the new one does (from a sub-entry), set it.
            if entries[key]["parent"] is None and parent_name is not None:
                entries[key]["parent"] = parent_name
            # Also promote node_type: sub-entries are never categories
            if is_sub:
                entries[key]["node_type"] = "concept"
        else:
            entries[key] = {
                "concept":   full_name,
                "aliases":   [],
                "pages":     pages,
                "node_type": node_type,
                "parent":    parent_name,
                "see_refs":  see_refs,
            }

    # ── Acronym merges: rename full form to "Title Case Name (ACRONYM)" ────────
    for acronym, full_lower in ACRONYM_PAIRS:
        canonical = _find_entry_fuzzy(full_lower, entries)
        if canonical is None:
            continue
        old_key = next(k for k, v in entries.items() if v is canonical)
        # Add acronym as alias
        if acronym not in canonical["aliases"]:
            canonical["aliases"].append(acronym)
        # Rename: title-case the base name and append (ACRONYM)
        base = canonical["concept"]
        if f"({acronym})" not in base:
            canonical["concept"] = _title_case(base) + f" ({acronym})"
        # Remove acronym-only stub entry
        entries.pop(acronym.lower(), None)
        # Re-key under new lowercase canonical name
        new_key = canonical["concept"].lower()
        if new_key != old_key:
            entries[new_key] = entries.pop(old_key)

    # ── Alias-only merges (BD score, BDe score) ────────────────────────────────
    for alias_lower, canonical_lower in ALIAS_ONLY:
        canonical = _find_entry_fuzzy(canonical_lower, entries)
        if canonical and alias_lower not in canonical["aliases"]:
            canonical["aliases"].append(alias_lower)
        entries.pop(alias_lower, None)

    # ── Synonym absorptions ────────────────────────────────────────────────────
    # Keep synonyms as lightweight alias nodes; RELATED_TO_ALIAS edge added in
    # build_graph step 6.  Clear see_refs so step 5 doesn't add a spurious
    # RELATED_TO_SEE_ALSO on top of the alias edge.
    for synonym_lower, target_lower in SYNONYM_MAP.items():
        canonical = _find_entry_fuzzy(target_lower, entries)
        if canonical and synonym_lower not in canonical["aliases"]:
            canonical["aliases"].append(synonym_lower)
        if synonym_lower in entries:
            entries[synonym_lower]["see_refs"] = []
        # (no longer removing the synonym node)

    # ── Discard redundant alphabetical redirects ──────────────────────────────
    # These point to a category but the concept already exists as a sub-entry.
    to_remove = [
        key for key, e in entries.items()
        if (e["node_type"] == "concept"
            and not e["pages"]
            and e["see_refs"]
            and e["concept"].lower() in REDUNDANT_REDIRECTS)
    ]
    for key in to_remove:
        entries.pop(key, None)

    # ── Special case: non-descendant (redirect with no sub-entry counterpart) ──
    if "non-descendant" not in entries and "non_descendant" not in entries:
        entries["non-descendant"] = {
            "concept": "Non-Descendant",
            "aliases": [],
            "pages":   [],
            "node_type": "concept",
            "parent":  "graph",
            "see_refs": [],
        }

    return list(entries.values())


def _find_entry_fuzzy(name_lower: str, entries: dict[str, dict]) -> dict | None:
    """Find an entry dict by lowercased name, with partial-match fallback."""
    if name_lower in entries:
        return entries[name_lower]
    for key, entry in entries.items():
        if name_lower in key or key in name_lower:
            return entry
    return None


# ── Graph builder ──────────────────────────────────────────────────────────────

def build_graph() -> nx.DiGraph:
    G        = nx.DiGraph()
    sections = parse_toc()
    entries  = parse_eci_index()

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
                   tooltip=(f"§{sec.section_id}: {sec.title}\n"
                            f"pp. {sec.start_page}–{sec.end_page}"),
                   chapter=sec.chapter,
                   depth=sec.depth,
                   start_page=sec.start_page,
                   end_page=sec.end_page,
                   color=CHAPTER_COLORS.get(sec.chapter, CHAPTER_COLORS[0]),
                   shape="box",
                   size=14 + max(0, (1 - sec.depth)) * 10)

    # Linear TOC sequence edges
    for a, b in zip(sec_node_ids, sec_node_ids[1:]):
        add_edge(G, a, b, "NEXT_IN_SEQUENCE")

    # ── 2. Concept / category nodes ────────────────────────────────────────────
    concept_pages: dict[str, list[int]] = defaultdict(list)
    concept_meta:  dict[str, dict]      = {}

    for entry in entries:
        cid = slugify(entry["concept"])
        concept_pages[cid].extend(entry["pages"])
        concept_meta[cid] = entry

    # Assign earliest chapter to each concept
    concept_chapter: dict[str, int] = {}
    for cid, pages in concept_pages.items():
        chaps = []
        for p in sorted(set(pages)):
            sec = most_specific_section(p, sections)
            if sec:
                chaps.append(sec.chapter)
        concept_chapter[cid] = min(chaps) if chaps else 0

    for cid, meta in concept_meta.items():
        pages_sorted = sorted(set(concept_pages[cid]))
        ch           = concept_chapter.get(cid, 0)
        node_type    = meta["node_type"]   # "concept" | "category"
        page_str     = ", ".join(str(p) for p in pages_sorted[:12])
        if len(pages_sorted) > 12:
            page_str += "…"

        aliases_str = ""
        if meta["aliases"]:
            aliases_str = "\nAlso known as: " + ", ".join(meta["aliases"])

        # Shape: section=box, concept=dot, category=diamond
        shape = "diamond" if node_type == "category" else "dot"
        # Size: category nodes slightly larger; concept size scales with page count
        if node_type == "category":
            size = 20
        else:
            size = 7 + min(len(pages_sorted) * 0.9, 18)

        G.add_node(cid,
                   type=node_type,
                   label=meta["concept"],
                   short_label=meta["concept"] if (len(pages_sorted) >= 2
                                                   or node_type == "category") else "",
                   tooltip=(f"{meta['concept']}{aliases_str}\n"
                            f"Pages: {page_str if page_str else '—'}"),
                   chapter=ch,
                   color=CHAPTER_COLORS.get(ch, CHAPTER_COLORS[0]),
                   shape=shape,
                   size=size,
                   page_refs=pages_sorted)

    # ── 3. COVERED_IN  (concept → section, one direction only) ─────────────────
    # ILLUSTRATES (section→concept) was the exact inverse — dropped as redundant.
    for cid, pages in concept_pages.items():
        if cid not in G:
            continue
        seen: set[str] = set()
        for p in sorted(set(pages)):
            sec = most_specific_section(p, sections)
            if sec:
                sid = f"sec_{slugify(sec.section_id)}"
                if sid not in seen:
                    seen.add(sid)
                    add_edge(G, cid, sid, "COVERED_IN")

    # ── 4. SUBTOPIC_OF ─────────────────────────────────────────────────────────
    for entry in entries:
        if not entry.get("parent"):
            continue
        child_id  = slugify(entry["concept"])
        parent_id = find_concept(entry["parent"], G)
        if parent_id:
            add_edge(G, child_id, parent_id, "SUBTOPIC_OF")

    # ── 5. RELATED_TO_SEE_ALSO ─────────────────────────────────────────────────
    for entry in entries:
        src_id = slugify(entry["concept"])
        for ref in entry.get("see_refs", []):
            tgt_id = find_concept(ref, G)
            if tgt_id and not G.has_edge(src_id, tgt_id):
                add_edge(G, src_id, tgt_id, "RELATED_TO_SEE_ALSO")

    for a_name, b_name in SEE_ALSO_PAIRS:
        aid = find_concept(a_name, G)
        bid = find_concept(b_name, G)
        if aid and bid:
            add_edge(G, aid, bid, "RELATED_TO_SEE_ALSO")
            add_edge(G, bid, aid, "RELATED_TO_SEE_ALSO")

    # ── 6. RELATED_TO_ALIAS ────────────────────────────────────────────────────
    # (a) Synonym nodes ↔ their canonical (bidirectional: clicking either node
    #     surfaces the other as an alias)
    for synonym_lower, target_lower in SYNONYM_MAP.items():
        aid = find_concept(synonym_lower, G)
        bid = find_concept(target_lower, G)
        if aid and bid:
            add_edge(G, aid, bid, "RELATED_TO_ALIAS")
            add_edge(G, bid, aid, "RELATED_TO_ALIAS")

    # (b) Near-duplicate sub-entry pairs
    extra_alias = [
        ("invariant mechanisms", "independent mechanisms"),
        ("independence of noises", "independent noises"),
        ("independence of causal mechanisms", "independent mechanisms"),
    ]
    for a_name, b_name in extra_alias:
        aid = find_concept(a_name, G)
        bid = find_concept(b_name, G)
        if aid and bid:
            add_edge(G, aid, bid, "RELATED_TO_ALIAS")
            add_edge(G, bid, aid, "RELATED_TO_ALIAS")

    # ── 7. COMMONLY_CONFUSED ───────────────────────────────────────────────────
    for a_name, b_name in COMMONLY_CONFUSED_PAIRS:
        aid = find_concept(a_name, G)
        bid = find_concept(b_name, G)
        if aid and bid:
            add_edge(G, aid, bid, "COMMONLY_CONFUSED")
            add_edge(G, bid, aid, "COMMONLY_CONFUSED")

    # ── 8. PREREQUISITE_OF ─────────────────────────────────────────────────────
    for a_name, b_name in PREREQUISITE_PAIRS:
        aid = find_concept(a_name, G)
        bid = find_concept(b_name, G)
        if aid and bid:
            add_edge(G, aid, bid, "PREREQUISITE_OF")

    return G


# ── Save / report ──────────────────────────────────────────────────────────────

def save_graph(G: nx.DiGraph, out_dir: Path = OUTPUT_DIR) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    with open(out_dir / "eci_graph.pkl", "wb") as f:
        pickle.dump(G, f)

    from networkx.readwrite import json_graph
    with open(out_dir / "eci_graph.json", "w") as f:
        json.dump(json_graph.node_link_data(G), f, indent=2, default=str)

    n = G.number_of_nodes()
    e = G.number_of_edges()
    print(f"\nGraph: {n} nodes, {e} edges")

    type_counts = Counter(d.get("edge_type", "?") for _, _, d in G.edges(data=True))
    for etype in sorted(EDGE_META.keys()):
        print(f"  {etype:<28} {type_counts.get(etype, 0):>5}")

    # Node type breakdown
    nt_counts = Counter(d.get("type") for _, d in G.nodes(data=True))
    print(f"\nNode types:")
    for nt, cnt in sorted(nt_counts.items()):
        print(f"  {nt:<12} {cnt:>4}")


if __name__ == "__main__":
    G = build_graph()
    save_graph(G)
    print(f"\nSaved to {OUTPUT_DIR}/")
