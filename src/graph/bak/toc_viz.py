"""
Generate a beautiful collapsible radial mind-map of the Pearl (2009) TOC.

Layout  : D3.js radial tree — root at centre, 11 chapters radiate outward
Interact: click to expand/collapse · zoom/pan · hover tooltip
Output  : graph/output/toc_tree.html  (self-contained, no server needed)

Run: conda run -n edu python graph/toc_viz.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from toc_parser import parse_toc, Section
from graph_builder import CHAPTER_COLORS

OUTPUT_HTML = Path(__file__).parent / "output" / "toc_tree.html"

CHAPTER_LABELS = {
    1:  "Introduction",
    2:  "Inferred Causation",
    3:  "Causal Diagrams",
    4:  "Actions & Plans",
    5:  "Structural Models",
    6:  "Simpson's Paradox",
    7:  "Counterfactuals",
    8:  "Imperfect Experiments",
    9:  "Probability of Causation",
    10: "The Actual Cause",
    11: "Reflections",
}

# ── Build hierarchical tree dict ────────────────────────────────────────────────

def build_tree(sections: list[Section]) -> dict:
    root = {
        "id":       "root",
        "name":     "Pearl (2009)",
        "subtitle": "Causality",
        "type":     "root",
        "chapter":  0,
        "pages":    "1–460",
        "depth":    -1,
        "children": [],
    }
    node_map: dict[str, dict] = {"": root}

    for sec in sections:
        short_name = (
            CHAPTER_LABELS.get(sec.section_id_int, sec.title)
            if sec.depth == 0 else sec.title
        )
        node = {
            "id":       sec.section_id,
            "name":     short_name,
            "full":     f"§{sec.section_id}  {sec.title}",
            "type":     ["chapter", "section", "subsection"][min(sec.depth, 2)],
            "chapter":  sec.chapter,
            "pages":    f"{sec.start_page}–{sec.end_page}",
            "depth":    sec.depth,
            "children": [],
        }
        node_map[sec.section_id] = node
        parent = node_map.get(sec.parent_id, root)
        parent["children"].append(node)

    return root


# patch Section with a helper property
_orig_parse = parse_toc

def parse_toc_patched():
    secs = _orig_parse()
    for s in secs:
        s.section_id_int = int(s.section_id.split(".")[0])
    return secs


# ── HTML generation ─────────────────────────────────────────────────────────────

def generate_html(tree: dict, n_chapters: int, n_sections: int, n_subsections: int) -> str:
    tree_json   = json.dumps(tree, separators=(",", ":"))
    colors_json = json.dumps(CHAPTER_COLORS, separators=(",", ":"))

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Pearl (2009) — TOC Mind Map</title>
<script src="https://d3js.org/d3.v7.min.js"></script>
<style>
/* ── Base ─────────────────────────────────────────────────────────────────── */
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
html, body {{
  width: 100%; height: 100%; overflow: hidden;
  background: #0a0e1a;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif;
  color: #e6edf3;
}}

/* ── SVG ──────────────────────────────────────────────────────────────────── */
svg {{ width: 100vw; height: 100vh; cursor: grab; }}
svg:active {{ cursor: grabbing; }}

.link {{
  fill: none;
  stroke-linecap: round;
  transition: opacity .2s;
}}
.link:hover {{ opacity: 1 !important; }}

.node circle, .node rect {{
  stroke-width: 2px;
  cursor: pointer;
  transition: filter .15s, stroke-width .15s;
}}
.node:hover circle,
.node:hover rect {{
  filter: brightness(1.35) drop-shadow(0 0 6px currentColor);
  stroke-width: 2.5px;
}}

.node-label {{
  pointer-events: none;
  dominant-baseline: middle;
  font-weight: 500;
  letter-spacing: 0.2px;
  transition: opacity .2s;
}}

/* collapsed indicator pulse */
@keyframes pulse {{
  0%,100% {{ r: 4px; opacity:.6; }}
  50%      {{ r: 6px; opacity:.9; }}
}}
.has-children circle.dot {{ animation: pulse 2s ease-in-out infinite; }}

/* ── Controls ─────────────────────────────────────────────────────────────── */
#controls {{
  position: fixed; top: 16px; right: 16px;
  display: flex; flex-direction: column; gap: 6px;
  z-index: 20;
}}
.ctrl-btn {{
  background: rgba(22,27,34,0.92);
  border: 1px solid #30363d;
  border-radius: 7px;
  color: #8b949e;
  font-size: 11px; font-weight: 600;
  padding: 7px 12px;
  cursor: pointer;
  backdrop-filter: blur(8px);
  transition: border-color .15s, color .15s;
  letter-spacing: 0.4px;
  text-align: left;
}}
.ctrl-btn:hover {{ border-color: #58a6ff; color: #58a6ff; }}

/* ── Stats bar ────────────────────────────────────────────────────────────── */
#stats {{
  position: fixed; bottom: 16px; left: 50%;
  transform: translateX(-50%);
  display: flex; gap: 10px;
  z-index: 20;
}}
.stat-pill {{
  background: rgba(13,17,23,0.88);
  border: 1px solid #21262d;
  border-radius: 20px;
  padding: 4px 14px;
  font-size: 11px; color: #8b949e;
  font-weight: 600; letter-spacing: 0.3px;
  backdrop-filter: blur(6px);
}}
.stat-pill span {{ color: #e6edf3; }}

/* ── Tooltip ──────────────────────────────────────────────────────────────── */
#tooltip {{
  position: fixed;
  background: rgba(13,17,23,0.96);
  border: 1px solid #30363d;
  border-radius: 9px;
  padding: 11px 15px;
  font-size: 12px;
  pointer-events: none;
  z-index: 30;
  max-width: 280px;
  opacity: 0;
  transition: opacity .15s;
  backdrop-filter: blur(10px);
  box-shadow: 0 8px 32px rgba(0,0,0,0.5);
}}
#tooltip.show {{ opacity: 1; }}
#tooltip .tt-title {{
  font-weight: 600; font-size: 13px;
  color: #e6edf3; margin-bottom: 5px;
  line-height: 1.3;
}}
#tooltip .tt-row {{
  color: #8b949e; font-size: 11px;
  margin-top: 3px; line-height: 1.5;
}}
#tooltip .tt-row span {{ color: #c9d1d9; }}

/* ── Breadcrumb ───────────────────────────────────────────────────────────── */
#breadcrumb {{
  position: fixed; top: 16px; left: 16px;
  font-size: 11px; color: #484f58;
  z-index: 20; max-width: 420px;
  line-height: 1.8; letter-spacing: 0.2px;
}}
#breadcrumb span {{ color: #8b949e; }}
#breadcrumb .sep {{ margin: 0 5px; color: #30363d; }}
</style>
</head>
<body>

<svg id="svg"></svg>

<!-- Controls -->
<div id="controls">
  <button class="ctrl-btn" onclick="resetView()">⌂ Reset view</button>
  <button class="ctrl-btn" onclick="expandAll()">⊞ Expand all</button>
  <button class="ctrl-btn" onclick="collapseAll()">⊟ Collapse all</button>
</div>

<!-- Stats -->
<div id="stats">
  <div class="stat-pill"><span>{n_chapters}</span> chapters</div>
  <div class="stat-pill"><span>{n_sections}</span> sections</div>
  <div class="stat-pill"><span>{n_subsections}</span> subsections</div>
</div>

<!-- Tooltip -->
<div id="tooltip">
  <div class="tt-title" id="tt-title"></div>
  <div class="tt-row" id="tt-pages"></div>
  <div class="tt-row" id="tt-children"></div>
</div>

<!-- Breadcrumb -->
<div id="breadcrumb"></div>

<script>
// ── Data ───────────────────────────────────────────────────────────────────────
const RAW_TREE   = /** TREE_PLACEHOLDER **/;
const CH_COLORS  = /** COLORS_PLACEHOLDER **/;

const nodeColor = d => {{
  if (d.data.type === 'root') return '#58a6ff';
  const c = CH_COLORS[String(d.data.chapter)] || '#6e7681';
  if (d.data.type === 'chapter')    return c;
  if (d.data.type === 'section')    return c + 'cc';   // 80% opacity hex
  return c + '88';                                      // 53%
}};

const linkColor = d => {{
  const ch = d.target.data.chapter;
  return CH_COLORS[String(ch)] || '#444';
}};

// ── Layout ─────────────────────────────────────────────────────────────────────
const W = window.innerWidth, H = window.innerHeight;
const CX = W / 2, CY = H / 2;
const BASE_R = Math.min(CX, CY) * 0.88;

const tree = d3.tree()
  .size([2 * Math.PI, BASE_R])
  .separation((a, b) => (a.parent === b.parent ? 1 : 2) / a.depth);

// ── SVG setup ──────────────────────────────────────────────────────────────────
const svg = d3.select('#svg');

// Subtle radial gradient background
const defs = svg.append('defs');
const grad = defs.append('radialGradient').attr('id','bg-grad')
  .attr('cx','50%').attr('cy','50%').attr('r','70%');
grad.append('stop').attr('offset','0%')  .attr('stop-color','#0d1220');
grad.append('stop').attr('offset','100%').attr('stop-color','#050810');
svg.append('rect').attr('width','100%').attr('height','100%').attr('fill','url(#bg-grad)');

// Zoom group
const g = svg.append('g').attr('transform', `translate(${{CX}},${{CY}})`);

const zoom = d3.zoom()
  .scaleExtent([0.15, 4])
  .on('zoom', e => g.attr('transform', e.transform.translate(CX, CY)));
svg.call(zoom);

// ── Tree state ─────────────────────────────────────────────────────────────────
let root, linkSel, nodeSel;
let nodeId = 0;

function buildRoot(data) {{
  root = d3.hierarchy(data, d => d.children);
  root.x0 = 0; root.y0 = 0;
  // Collapse sections and below initially
  root.descendants().forEach(d => {{
    d.id = ++nodeId;
    if (d.depth >= 1) collapse(d);   // hide sections/subsections on load
  }});
}}

function collapse(d) {{
  if (d.children) {{
    d._children = d.children;
    d._children.forEach(collapse);
    d.children = null;
  }}
}}

function expand(d) {{
  if (d._children) {{
    d.children = d._children;
    d._children = null;
  }}
}}

// ── Draw / update ──────────────────────────────────────────────────────────────
function update(source, duration = 600) {{
  tree(root);

  const nodes = root.descendants();
  const links = root.links();

  // ── Links ──────────────────────────────────────────────────────────────────
  const link = g.selectAll('path.link')
    .data(links, d => d.target.id);

  const linkEnter = link.enter().append('path')
    .attr('class', 'link')
    .attr('d', () => {{
      const o = radialPoint(source.x0 ?? source.x, source.y0 ?? source.y);
      return straight(o, o);
    }})
    .attr('stroke', linkColor)
    .attr('stroke-width', d => [1.8, 1.2, 0.7][Math.min(d.target.data.depth, 2)])
    .attr('opacity', d => [0.55, 0.40, 0.28][Math.min(d.target.data.depth, 2)]);

  linkEnter.merge(link).transition().duration(duration).ease(d3.easeCubicInOut)
    .attr('d', d => linkRadial(d));

  link.exit().transition().duration(duration).ease(d3.easeCubicInOut)
    .attr('d', () => {{
      const o = radialPoint(source.x, source.y);
      return straight(o, o);
    }})
    .remove();

  // ── Nodes ──────────────────────────────────────────────────────────────────
  const node = g.selectAll('g.node')
    .data(nodes, d => d.id);

  const nodeEnter = node.enter().append('g')
    .attr('class', d => 'node ' + (d._children ? 'has-children' : ''))
    .attr('transform', () => `translate(${{radialPoint(source.x0 ?? source.x, source.y0 ?? source.y).join(',')}})`)
    .attr('opacity', 0)
    .on('click', (event, d) => {{ event.stopPropagation(); toggleNode(d); }})
    .on('mouseenter', showTooltip)
    .on('mousemove',  moveTooltip)
    .on('mouseleave', hideTooltip);

  // Root: special pill shape
  nodeEnter.filter(d => d.data.type === 'root')
    .append('rect')
    .attr('x', -48).attr('y', -22).attr('width', 96).attr('height', 44)
    .attr('rx', 14)
    .attr('fill', '#0d2044')
    .attr('stroke', '#58a6ff')
    .attr('stroke-width', 2);

  nodeEnter.filter(d => d.data.type === 'root')
    .append('text').attr('class','node-label')
    .attr('text-anchor','middle').attr('dy','-5px')
    .attr('fill','#79c0ff').attr('font-size','12px').attr('font-weight','700')
    .text(d => d.data.name);

  nodeEnter.filter(d => d.data.type === 'root')
    .append('text').attr('class','node-label')
    .attr('text-anchor','middle').attr('dy','10px')
    .attr('fill','#8b949e').attr('font-size','10px')
    .text(d => d.data.subtitle);

  // Chapter nodes: circle with number
  const chEnter = nodeEnter.filter(d => d.data.type === 'chapter');
  chEnter.append('circle')
    .attr('r', 18)
    .attr('fill', d => CH_COLORS[String(d.data.chapter)] || '#6e7681')
    .attr('fill-opacity', 0.18)
    .attr('stroke', d => CH_COLORS[String(d.data.chapter)] || '#6e7681');

  chEnter.append('text').attr('class','node-label')
    .attr('text-anchor','middle').attr('dy','-2px')
    .attr('fill', d => CH_COLORS[String(d.data.chapter)])
    .attr('font-size','11px').attr('font-weight','700')
    .text(d => d.data.id);

  // Chapter label (outside ring)
  chEnter.append('text').attr('class','node-label ch-label')
    .attr('fill', d => CH_COLORS[String(d.data.chapter)])
    .attr('font-size','11.5px').attr('font-weight','600')
    .text(d => d.data.name);

  // Section nodes: smaller circle
  const secEnter = nodeEnter.filter(d => d.data.type === 'section');
  secEnter.append('circle')
    .attr('r', 6)
    .attr('fill', d => CH_COLORS[String(d.data.chapter)] || '#6e7681')
    .attr('fill-opacity', 0.25)
    .attr('stroke', d => CH_COLORS[String(d.data.chapter)] || '#6e7681');

  secEnter.append('text').attr('class','node-label sec-label')
    .attr('fill', d => CH_COLORS[String(d.data.chapter)])
    .attr('font-size','10.5px')
    .text(d => d.data.name.length > 32 ? d.data.name.slice(0,30)+'…' : d.data.name);

  // Subsection nodes: tiny dot
  const subEnter = nodeEnter.filter(d => d.data.type === 'subsection');
  subEnter.append('circle')
    .attr('r', 3.5)
    .attr('fill', d => CH_COLORS[String(d.data.chapter)] || '#6e7681')
    .attr('fill-opacity', 0.5)
    .attr('stroke', d => CH_COLORS[String(d.data.chapter)] || '#6e7681')
    .attr('stroke-opacity', 0.6);

  subEnter.append('text').attr('class','node-label sub-label')
    .attr('fill', '#8b949e')
    .attr('font-size','9.5px')
    .text(d => d.data.name.length > 36 ? d.data.name.slice(0,34)+'…' : d.data.name);

  // Collapsed-children pulse dot
  nodeEnter.filter(d => d.data.type !== 'root')
    .append('circle').attr('class','dot')
    .attr('r', 0).attr('fill','white').attr('opacity',0);

  // Merge enter + update
  const nodeUpdate = nodeEnter.merge(node);

  nodeUpdate.transition().duration(duration).ease(d3.easeCubicInOut)
    .attr('transform', d => `translate(${{radialPoint(d.x, d.y).join(',')}})`)
    .attr('opacity', 1);

  // Update class (has-children)
  nodeUpdate.attr('class', d => 'node ' + (d._children ? 'has-children' : ''));

  // Pulse dot visibility
  nodeUpdate.select('circle.dot')
    .transition().duration(duration)
    .attr('r', d => d._children ? 4 : 0)
    .attr('opacity', d => d._children ? 0.6 : 0);

  // Position labels (radial aware)
  nodeUpdate.select('.ch-label')
    .attr('text-anchor', d => d.x < Math.PI ? 'start' : 'end')
    .attr('transform', d => {{
      const flip = d.x >= Math.PI;
      return `translate(${{flip ? -26 : 26}},4) rotate(${{flip ? 180 : 0}})`;
    }});

  nodeUpdate.select('.sec-label')
    .attr('text-anchor', d => d.x < Math.PI ? 'start' : 'end')
    .attr('transform', d => {{
      const flip = d.x >= Math.PI;
      return `translate(${{flip ? -10 : 10}},0) rotate(${{flip ? 180 : 0}})`;
    }});

  nodeUpdate.select('.sub-label')
    .attr('text-anchor', d => d.x < Math.PI ? 'start' : 'end')
    .attr('transform', d => {{
      const flip = d.x >= Math.PI;
      return `translate(${{flip ? -7 : 7}},0) rotate(${{flip ? 180 : 0}})`;
    }});

  // Exit
  const nodeExit = node.exit().transition().duration(duration).ease(d3.easeCubicInOut)
    .attr('transform', () => `translate(${{radialPoint(source.x, source.y).join(',')}})`)
    .attr('opacity', 0).remove();

  // Save positions for next transition origin
  nodes.forEach(d => {{ d.x0 = d.x; d.y0 = d.y; }});
}}

// ── Geometry helpers ────────────────────────────────────────────────────────────
function radialPoint(angle, radius) {{
  return [radius * Math.cos(angle - Math.PI / 2), radius * Math.sin(angle - Math.PI / 2)];
}}

function straight(a, b) {{
  return `M${{a[0]}},${{a[1]}}L${{b[0]}},${{b[1]}}`;
}}

function linkRadial(d) {{
  const s = radialPoint(d.source.x, d.source.y);
  const t = radialPoint(d.target.x, d.target.y);
  const mx = (s[0] + t[0]) / 2, my = (s[1] + t[1]) / 2;
  const dist = Math.sqrt((t[0]-s[0])**2 + (t[1]-s[1])**2);
  const bulge = Math.min(dist * 0.35, 60);
  const perp = [-((t[1]-s[1])/dist)*bulge, ((t[0]-s[0])/dist)*bulge];
  return `M${{s[0]}},${{s[1]}} Q${{mx+perp[0]}},${{my+perp[1]}} ${{t[0]}},${{t[1]}}`;
}}

// ── Interactions ────────────────────────────────────────────────────────────────
function toggleNode(d) {{
  if (d.data.type === 'root') return;
  if (d.children) {{
    d._children = d.children;
    d.children = null;
  }} else if (d._children) {{
    d.children = d._children;
    d._children = null;
  }}
  updateBreadcrumb(d);
  update(d);
}}

function resetView() {{
  svg.transition().duration(500).call(
    zoom.transform,
    d3.zoomIdentity.translate(CX, CY).scale(1)
  );
}}

function expandAll() {{
  root.descendants().forEach(d => {{
    if (d._children) {{ d.children = d._children; d._children = null; }}
  }});
  update(root, 800);
}}

function collapseAll() {{
  root.descendants().forEach(d => {{
    if (d.depth >= 1 && d.children) {{
      d._children = d.children; d.children = null;
    }}
  }});
  update(root, 800);
}}

// ── Tooltip ─────────────────────────────────────────────────────────────────────
function showTooltip(event, d) {{
  const tt = document.getElementById('tooltip');
  document.getElementById('tt-title').textContent = d.data.full || d.data.name;
  document.getElementById('tt-pages').innerHTML =
    `Pages: <span>${{d.data.pages}}</span>`;
  const nc = (d.children || d._children || []).length;
  document.getElementById('tt-children').innerHTML = nc > 0
    ? `Sub-items: <span>${{nc}}</span>  ${{d.children ? '(expanded)' : '(collapsed)'}}`
    : '';
  tt.classList.add('show');
  moveTooltip(event);
}}

function moveTooltip(event) {{
  const tt = document.getElementById('tooltip');
  const x = event.clientX + 16, y = event.clientY - 10;
  tt.style.left = (x + tt.offsetWidth > window.innerWidth ? x - tt.offsetWidth - 32 : x) + 'px';
  tt.style.top  = (y + tt.offsetHeight > window.innerHeight ? y - tt.offsetHeight : y) + 'px';
}}

function hideTooltip() {{
  document.getElementById('tooltip').classList.remove('show');
}}

// ── Breadcrumb ───────────────────────────────────────────────────────────────────
function updateBreadcrumb(d) {{
  const path = d.ancestors().reverse();
  const bc = document.getElementById('breadcrumb');
  bc.innerHTML = path.map((n, i) =>
    i === 0 ? `<span>${{n.data.name}}</span>` :
    `<span class="sep">›</span><span>${{n.data.name}}</span>`
  ).join('');
}}

// ── Init ─────────────────────────────────────────────────────────────────────────
buildRoot(RAW_TREE);
update(root, 0);
// Fit initial view with a slight zoom-out
svg.call(zoom.transform, d3.zoomIdentity.translate(CX, CY).scale(0.72));
</script>
</body>
</html>""" \
    .replace("/** TREE_PLACEHOLDER **/",   tree_json) \
    .replace("/** COLORS_PLACEHOLDER **/", colors_json)


# ── Main ────────────────────────────────────────────────────────────────────────

def main() -> None:
    sections = parse_toc_patched()

    n_chapters    = sum(1 for s in sections if s.depth == 0)
    n_sections    = sum(1 for s in sections if s.depth == 1)
    n_subsections = sum(1 for s in sections if s.depth == 2)

    tree = build_tree(sections)
    html = generate_html(tree, n_chapters, n_sections, n_subsections)

    OUTPUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_HTML.write_text(html, encoding="utf-8")

    print(f"TOC tree saved → {OUTPUT_HTML}")
    print(f"Chapters: {n_chapters} · Sections: {n_sections} · Subsections: {n_subsections}")
    print(f"Open: file://{OUTPUT_HTML.resolve()}")


if __name__ == "__main__":
    main()
