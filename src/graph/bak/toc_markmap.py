"""
Generate a Markmap mind-map of the Pearl (2009) Table of Contents.

markmap handles all layout, folding, zoom, and pan — we just supply markdown.

Features
  · colorFreezeLevel 2 → each chapter branch has a consistent colour
  · Section nodes show page ranges as inline code spans
  · Chapters start collapsed; click to expand
  · Dark theme via CSS overrides on markmap's SVG output

Run:    conda run -n edu python graph/toc_markmap.py
Output: graph/output/toc_markmap.html  (self-contained, open in any browser)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from toc_parser import parse_toc, Section
from graph_builder import CHAPTER_COLORS

OUTPUT_HTML = Path(__file__).parent / "output" / "toc_markmap.html"

CHAPTER_SHORT = {
    1:  "Introduction to Probabilities, Graphs & Causal Models",
    2:  "A Theory of Inferred Causation",
    3:  "Causal Diagrams & Identification of Causal Effects",
    4:  "Actions, Plans & Direct Effects",
    5:  "Causality & Structural Models in Social Science",
    6:  "Simpson's Paradox, Confounding & Collapsibility",
    7:  "The Logic of Structure-Based Counterfactuals",
    8:  "Imperfect Experiments",
    9:  "Probability of Causation",
    10: "The Actual Cause",
    11: "Reflections, Elaborations & Discussions",
}


# ── Markdown builder ────────────────────────────────────────────────────────────

def build_markdown(sections: list[Section]) -> str:
    lines: list[str] = ["# Pearl (2009) — Causality"]

    for sec in sections:
        hashes = "#" * (sec.depth + 2)   # depth 0 → ##, 1 → ###, 2 → ####
        pages  = (f"`p. {sec.start_page}`" if sec.start_page == sec.end_page
                  else f"`pp. {sec.start_page}–{sec.end_page}`")

        if sec.depth == 0:
            # Chapter: full title, no page range (spans too many pages to be useful)
            title = CHAPTER_SHORT.get(sec.chapter, sec.title)
            lines.append(f"{hashes} **Ch. {sec.section_id}** — {title}")
        else:
            lines.append(f"{hashes} **{sec.section_id}** {sec.title}  {pages}")

    return "\n".join(lines)


# ── HTML template ────────────────────────────────────────────────────────────────

def generate_html(markdown: str, n_ch: int, n_sec: int, n_sub: int) -> str:

    # YAML colour list — one entry per chapter, in order 1–11
    yaml_colors = "\n".join(
        f'    - "{CHAPTER_COLORS[ch]}"' for ch in range(1, 12)
    )

    frontmatter = f"""\
---
markmap:
  colorFreezeLevel: 2
  maxWidth: 380
  initialExpandLevel: 1
  zoom: true
  pan: true
  spacingHorizontal: 100
  spacingVertical: 6
  paddingX: 14
  colors:
{yaml_colors}
---"""

    full_md = frontmatter + "\n\n" + markdown

    # Escape backticks inside the <script type="text/template"> block —
    # they're fine in a non-JS template block, no escaping needed.

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Pearl (2009) — Causality Mind Map</title>

<!-- markmap autoloader bundles d3 + markmap-lib + markmap-view -->
<script src="https://cdn.jsdelivr.net/npm/markmap-autoloader@0.16"></script>

<style>
/* ── Reset ──────────────────────────────────────────────────────────────── */
*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
html, body {{
  width: 100vw; height: 100vh; overflow: hidden;
  background: #0d1117;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif;
  color: #e6edf3;
}}

/* ── Markmap dark-theme overrides ───────────────────────────────────────── */
/* The autoloader renders an <svg class="markmap"> inside our div */
svg.markmap {{
  background: #0d1117 !important;
  width:  100vw !important;
  height: 100vh !important;
}}

/* All text inside nodes */
.markmap-foreign,
.markmap-foreign div,
.markmap-foreign span,
.markmap-foreign p {{
  color: #c9d1d9 !important;
  line-height: 1.5 !important;
}}

/* Bold section IDs */
.markmap-foreign strong {{ color: #e6edf3 !important; font-weight: 700 !important; }}

/* Page-range code spans */
.markmap-foreign code {{
  color: #8b949e !important;
  background: rgba(139,148,158,0.12) !important;
  border-radius: 4px !important;
  padding: 1px 6px !important;
  font-size: 0.80em !important;
  font-family: ui-monospace, "SF Mono", "Fira Code", monospace !important;
  letter-spacing: 0.2px !important;
}}

/* Node circle: semi-transparent fill, coloured stroke */
.markmap-node > circle {{
  fill-opacity: 0.08 !important;
  stroke-width: 1.8px !important;
  transition: r 0.15s ease !important;
}}
.markmap-node:hover > circle {{ fill-opacity: 0.18 !important; }}

/* Connector paths */
.markmap-link {{ stroke-opacity: 0.40 !important; }}

/* Fold indicator triangle */
.markmap-fold {{ fill-opacity: 0.6 !important; }}

/* ── HUD overlays ───────────────────────────────────────────────────────── */
#hud-title {{
  position: fixed; top: 18px; left: 22px;
  font-size: 11px; font-weight: 700; letter-spacing: 1px;
  text-transform: uppercase; color: #58a6ff; opacity: 0.75;
  pointer-events: none; z-index: 10;
}}
#hud-stats {{
  position: fixed; top: 38px; left: 22px;
  font-size: 10px; color: #484f58; letter-spacing: 0.3px;
  pointer-events: none; z-index: 10;
}}
#hud-stats span {{ color: #6e7681; }}
#hud-hint {{
  position: fixed; bottom: 16px; left: 50%; transform: translateX(-50%);
  font-size: 10px; color: #30363d; letter-spacing: 0.6px;
  pointer-events: none; z-index: 10;
}}
</style>
</head>
<body>

<!-- HUD labels -->
<div id="hud-title">Causality · Table of Contents</div>
<div id="hud-stats">
  <span>{n_ch}</span> chapters &nbsp;·&nbsp;
  <span>{n_sec}</span> sections &nbsp;·&nbsp;
  <span>{n_sub}</span> subsections
</div>
<div id="hud-hint">click node to fold / unfold &nbsp;·&nbsp; scroll to zoom &nbsp;·&nbsp; drag to pan</div>

<!-- markmap renders into this div (autoloader detects it automatically) -->
<div class="markmap" style="width:100vw;height:100vh;">
<script type="text/template">
{full_md}
</script>
</div>

</body>
</html>"""


# ── Main ─────────────────────────────────────────────────────────────────────────

def main() -> None:
    sections  = parse_toc()
    n_ch  = sum(1 for s in sections if s.depth == 0)
    n_sec = sum(1 for s in sections if s.depth == 1)
    n_sub = sum(1 for s in sections if s.depth == 2)

    md   = build_markdown(sections)
    html = generate_html(md, n_ch, n_sec, n_sub)

    OUTPUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_HTML.write_text(html, encoding="utf-8")

    print(f"Saved  → {OUTPUT_HTML}")
    print(f"Nodes  : {n_ch} chapters · {n_sec} sections · {n_sub} subsections")
    print(f"Open   : file://{OUTPUT_HTML.resolve()}")


if __name__ == "__main__":
    main()
