"""
Generate a self-contained interactive HTML knowledge graph for ECI (2017).

Extends the Pearl visualize.py with:
  - category nodes (diamond shape, larger, with ring outline)
  - ECI chapter labels & colors
  - 3-book subtitle

Run:   conda run -n edu python graph/eci_visualize.py
Output: graph/output/eci_graph.html
"""

import json
import sys
from collections import Counter
from pathlib import Path

import networkx as nx

sys.path.insert(0, str(Path(__file__).parent))
from eci_graph_builder import build_graph, save_graph, EDGE_META, CHAPTER_COLORS

OUTPUT_DIR  = Path(__file__).parent / "output"
OUTPUT_HTML = OUTPUT_DIR / "eci_graph.html"

# ── Edge type display config ───────────────────────────────────────────────────

EDGE_DISPLAY = {
    "PREREQUISITE_OF":     {"label": "Prerequisite Of",       "icon": "⬆", "default": True},
    "SUBTOPIC_OF":         {"label": "Subtopic Of",           "icon": "⤴", "default": True},
    "RELATED_TO_SEE_ALSO": {"label": "Related To (see also)", "icon": "↔", "default": True},
    "RELATED_TO_ALIAS":    {"label": "Alias / Same As",       "icon": "≡", "default": True},
    "COMMONLY_CONFUSED":   {"label": "Commonly Confused",     "icon": "⚡", "default": True},
    "APPLIED_TO":          {"label": "Applied To",            "icon": "◆", "default": True},
    "COVERED_IN":          {"label": "Covered In",            "icon": "⊂", "default": False},
    "ILLUSTRATES":         {"label": "Illustrates",           "icon": "⊃", "default": False},
    "NEXT_IN_SEQUENCE":    {"label": "Next in Sequence",      "icon": "→", "default": False},
}

VIEW_PRESETS = {
    "Curriculum":    ["NEXT_IN_SEQUENCE", "PREREQUISITE_OF"],
    "Concept Web":   ["SUBTOPIC_OF", "RELATED_TO_SEE_ALSO", "RELATED_TO_ALIAS",
                      "COMMONLY_CONFUSED", "PREREQUISITE_OF", "APPLIED_TO"],
    "Content Map":   ["COVERED_IN", "ILLUSTRATES"],
    "All":           list(EDGE_DISPLAY.keys()),
}

CHAPTER_LABELS = {
    1:  "Ch 1 — Statistical & Causal Models",
    2:  "Ch 2 — Assumptions for Causal Inference",
    3:  "Ch 3 — Cause-Effect Models",
    4:  "Ch 4 — Learning Cause-Effect Models",
    5:  "Ch 5 — Connections to ML, I",
    6:  "Ch 6 — Multivariate Causal Models",
    7:  "Ch 7 — Learning Multivariate Causal Models",
    8:  "Ch 8 — Connections to ML, II",
    9:  "Ch 9 — Hidden Variables",
    10: "Ch 10 — Time Series",
    11: "App A — Probability & Statistics",
    12: "App B — Causal Orderings",
    13: "App C — Proofs",
    0:  "Unassigned",
}

# ── vis.js data conversion ─────────────────────────────────────────────────────

def graph_to_vis(G: nx.DiGraph) -> tuple[list, list]:
    nodes = []
    for nid, data in G.nodes(data=True):
        node_type = data.get("type", "concept")
        shape     = data.get("shape", "dot")
        size      = data.get("size", 10)
        color     = data.get("color", "#6e7681")
        label     = data.get("short_label") or data.get("label", nid)
        chapter   = data.get("chapter", 0)

        # Category nodes get a lighter fill with stronger border
        if node_type == "category":
            color_obj = {
                "background": color + "33",   # 20% opacity fill
                "border":     color,
                "highlight":  {"background": "#ffffff", "border": color},
                "hover":      {"background": color + "55", "border": color},
            }
            border_width = 2.5
        elif node_type == "section":
            color_obj = {
                "background": color,
                "border":     color,
                "highlight":  {"background": "#ffffff", "border": "#ffffff"},
                "hover":      {"background": color, "border": "#ffffff"},
            }
            border_width = 1.5
        else:
            color_obj = {
                "background": color,
                "border":     color,
                "highlight":  {"background": "#ffffff", "border": "#ffffff"},
                "hover":      {"background": color, "border": "#ffffff"},
            }
            border_width = 1.5

        nodes.append({
            "id":          nid,
            "label":       label,
            "title":       data.get("tooltip", data.get("label", nid)),
            "shape":       shape,
            "size":        size,
            "color":       color_obj,
            "borderWidth": border_width,
            "font":        {"color": "#e6edf3", "size": 11},
            "chapter":     chapter,
            "node_type":   node_type,
            "_full_label": data.get("label", nid),
        })

    edges = []
    for i, (src, tgt, data) in enumerate(G.edges(data=True)):
        etype  = data.get("edge_type", "UNKNOWN")
        color  = data.get("color", "#555")
        width  = data.get("width", 1.0)
        dashes = data.get("dashes", False)

        edges.append({
            "id":        f"e{i}",
            "from":      src,
            "to":        tgt,
            "edge_type": etype,
            "color":     {"color": color, "highlight": "#ffffff", "hover": "#ffffff",
                          "opacity": 0.85},
            "width":     width,
            "dashes":    dashes,
            "arrows":    "to" if etype not in
                         ("COMMONLY_CONFUSED", "RELATED_TO_SEE_ALSO", "RELATED_TO_ALIAS")
                         else "",
            "smooth":    {"type": "continuous", "roundness": 0.3},
            "hidden":    not EDGE_DISPLAY.get(etype, {}).get("default", False),
        })

    return nodes, edges


# ── HTML component builders ────────────────────────────────────────────────────

def build_toggle_html(edge_counts: dict) -> str:
    rows = []
    for etype, disp in EDGE_DISPLAY.items():
        ec      = EDGE_META[etype]["color"]
        checked = "checked" if disp["default"] else ""
        count   = edge_counts.get(etype, 0)
        rows.append(f"""
        <label class="edge-row" data-type="{etype}">
          <span class="swatch" style="background:{ec}"></span>
          <span class="edge-label">{disp['icon']} {disp['label']}</span>
          <span class="edge-count">{count}</span>
          <div class="toggle-wrap">
            <input type="checkbox" id="tog_{etype}" data-type="{etype}" {checked}
                   onchange="onToggle(this)">
            <span class="slider" style="--ac:{ec}"></span>
          </div>
        </label>""")
    return "\n".join(rows)


def build_chapter_options() -> str:
    opts = ['<option value="0">All chapters</option>']
    for ch, label in CHAPTER_LABELS.items():
        if ch == 0:
            continue
        color = CHAPTER_COLORS.get(ch, "#aaa")
        opts.append(f'<option value="{ch}" data-color="{color}">{label}</option>')
    return "\n".join(opts)


def build_legend_html() -> str:
    items = [
        '<div class="legend-row">'
        '<span class="lg-box" style="background:#6e7681;border-radius:3px;'
        'width:14px;height:10px"></span><span>Section</span></div>',
        '<div class="legend-row">'
        '<span class="lg-diamond"></span><span>Category</span></div>',
    ]
    for ch in range(1, 14):
        color = CHAPTER_COLORS.get(ch, "#6e7681")
        label = CHAPTER_LABELS.get(ch, f"Ch {ch}")
        short = label.split(" — ")[0] if " — " in label else label
        items.append(
            f'<div class="legend-row">'
            f'<span class="lg-dot" style="background:{color}"></span>'
            f'<span>{short}</span></div>'
        )
    return "\n".join(items)


# ── Full HTML generation ───────────────────────────────────────────────────────

def generate_html(G: nx.DiGraph) -> str:
    nodes_vis, edges_vis = graph_to_vis(G)
    n_nodes = len(nodes_vis)
    n_edges = len(edges_vis)

    edge_counts  = Counter(e["edge_type"] for e in edges_vis)
    nodes_json   = json.dumps(nodes_vis,  separators=(",", ":"))
    edges_json   = json.dumps(edges_vis,  separators=(",", ":"))
    presets_json = json.dumps(VIEW_PRESETS, separators=(",", ":"))
    toggles_html = build_toggle_html(edge_counts)
    chapter_opts = build_chapter_options()
    legend_html  = build_legend_html()

    vis_options = json.dumps({
        "physics": {
            "enabled": True,
            "solver": "barnesHut",
            "barnesHut": {
                "gravitationalConstant": -4500,
                "centralGravity": 0.25,
                "springLength": 115,
                "springConstant": 0.04,
                "damping": 0.15,
                "avoidOverlap": 0.15,
            },
            "stabilization": {
                "enabled": True,
                "iterations": 350,
                "updateInterval": 30,
                "fit": True,
            },
            "minVelocity": 0.5,
        },
        "edges": {
            "smooth": {"enabled": True, "type": "continuous", "roundness": 0.3},
            "selectionWidth": 3,
        },
        "nodes": {
            "borderWidth": 1.5,
            "borderWidthSelected": 3,
            "shadow": False,
        },
        "interaction": {
            "hover": True,
            "tooltipDelay": 80,
            "hideEdgesOnDrag": True,
            "multiselect": False,
            "navigationButtons": False,
            "keyboard": {"enabled": True, "bindToWindow": False},
        },
        "layout": {"improvedLayout": True},
    }, separators=(",", ":"))

    el_labels_json = json.dumps({k: v["label"] for k, v in EDGE_DISPLAY.items()})
    ch_labels_json = json.dumps({str(k): v for k, v in CHAPTER_LABELS.items()})

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Elements of Causal Inference — Knowledge Graph</title>
<script src="https://unpkg.com/vis-network@9.1.9/standalone/umd/vis-network.min.js"></script>
<style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",system-ui,sans-serif;
  background:#0a0e1a;color:#e6edf3;overflow:hidden;height:100vh;display:flex}}

/* ── Sidebar ── */
#sidebar{{
  width:272px;min-width:272px;height:100vh;
  background:#0d1117;border-right:1px solid #21262d;
  display:flex;flex-direction:column;overflow:hidden;z-index:10;
  box-shadow:4px 0 20px rgba(0,0,0,0.5);
}}
#sidebar-header{{padding:18px 16px 14px;border-bottom:1px solid #21262d;flex-shrink:0}}
#sidebar-header .title{{font-size:13px;font-weight:700;color:#58a6ff;
  letter-spacing:0.5px;text-transform:uppercase}}
#sidebar-header .subtitle{{font-size:11px;color:#8b949e;margin-top:3px}}
.stats-pills{{display:flex;gap:6px;margin-top:10px;flex-wrap:wrap}}
.pill{{background:#161b22;border:1px solid #30363d;border-radius:20px;
  padding:3px 10px;font-size:10px;color:#8b949e;font-weight:600;letter-spacing:0.3px}}
.pill span{{color:#e6edf3}}

/* ── Search ── */
.section-wrap{{padding:10px 12px;border-bottom:1px solid #21262d;flex-shrink:0}}
.section-label{{font-size:9px;font-weight:700;color:#484f58;letter-spacing:1.2px;
  text-transform:uppercase;margin-bottom:6px}}
#search{{width:100%;background:#161b22;border:1px solid #30363d;border-radius:6px;
  color:#e6edf3;padding:7px 10px;font-size:12px;outline:none;transition:border-color .15s}}
#search:focus{{border-color:#58a6ff}}
#search::placeholder{{color:#484f58}}
#search-count{{font-size:10px;color:#8b949e;margin-top:4px;min-height:14px}}

/* ── Presets ── */
.preset-grid{{display:grid;grid-template-columns:1fr 1fr;gap:5px;margin-top:2px}}
.preset-btn{{background:#161b22;border:1px solid #30363d;border-radius:6px;
  color:#8b949e;font-size:10px;font-weight:600;padding:6px 4px;
  cursor:pointer;transition:all .15s;text-align:center;letter-spacing:0.3px}}
.preset-btn:hover{{background:#1c2128;border-color:#58a6ff;color:#58a6ff}}
.preset-btn.active{{background:#1f3a5a;border-color:#58a6ff;color:#58a6ff}}

/* ── Edge toggles ── */
#toggle-scroll{{flex:1;overflow-y:auto;padding:8px 0;
  scrollbar-width:thin;scrollbar-color:#30363d transparent}}
#toggle-scroll::-webkit-scrollbar{{width:4px}}
#toggle-scroll::-webkit-scrollbar-thumb{{background:#30363d;border-radius:2px}}
.edge-row{{display:flex;align-items:center;gap:7px;padding:6px 12px;
  cursor:pointer;transition:background .1s}}
.edge-row:hover{{background:#161b22}}
.swatch{{width:10px;height:10px;border-radius:50%;flex-shrink:0}}
.edge-label{{flex:1;font-size:11px;color:#c9d1d9}}
.edge-count{{font-size:9px;color:#484f58;min-width:28px;text-align:right}}
.toggle-wrap{{position:relative;width:32px;height:17px;flex-shrink:0}}
.toggle-wrap input{{opacity:0;width:0;height:0;position:absolute}}
.slider{{position:absolute;inset:0;background:#21262d;border-radius:17px;
  cursor:pointer;transition:background .2s}}
.slider::before{{content:"";position:absolute;height:11px;width:11px;left:3px;bottom:3px;
  background:#484f58;border-radius:50%;transition:.2s}}
input:checked + .slider{{background:var(--ac,#58a6ff)}}
input:checked + .slider::before{{transform:translateX(15px);background:#fff}}

/* ── Chapter filter ── */
#chapter-sel{{width:100%;background:#161b22;border:1px solid #30363d;
  border-radius:6px;color:#c9d1d9;padding:6px 8px;font-size:11px;
  outline:none;cursor:pointer}}
#chapter-sel:focus{{border-color:#58a6ff}}

/* ── Legend ── */
.legend-grid{{display:flex;flex-wrap:wrap;gap:4px;margin-top:4px}}
.legend-row{{display:flex;align-items:center;gap:5px;font-size:10px;
  color:#8b949e;width:calc(50% - 2px)}}
.lg-dot{{width:8px;height:8px;border-radius:50%;flex-shrink:0}}
.lg-box{{flex-shrink:0}}
.lg-diamond{{
  width:9px;height:9px;border:1.5px solid #8b949e;
  transform:rotate(45deg);flex-shrink:0;background:transparent
}}

/* ── Network ── */
#net-wrap{{flex:1;position:relative;overflow:hidden}}
#mynetwork{{width:100%;height:100%}}

/* ── Loading ── */
#loading{{position:absolute;inset:0;background:rgba(10,14,26,0.9);
  display:flex;flex-direction:column;align-items:center;justify-content:center;
  z-index:20;transition:opacity .5s}}
#loading.done{{opacity:0;pointer-events:none}}
.spinner{{width:36px;height:36px;border:3px solid #21262d;
  border-top-color:#58a6ff;border-radius:50%;
  animation:spin .8s linear infinite;margin-bottom:14px}}
@keyframes spin{{to{{transform:rotate(360deg)}}}}
#loading p{{font-size:12px;color:#8b949e}}
#progress-bar{{width:200px;height:3px;background:#21262d;border-radius:3px;
  margin-top:10px;overflow:hidden}}
#progress-fill{{width:0%;height:100%;background:#58a6ff;transition:width .1s;border-radius:3px}}

/* ── Info panel ── */
#info-panel{{
  position:absolute;bottom:16px;right:16px;width:260px;
  background:rgba(13,17,23,0.95);border:1px solid #30363d;border-radius:10px;
  padding:14px;font-size:11px;
  transform:translateY(120%);transition:transform .2s cubic-bezier(.4,0,.2,1);
  backdrop-filter:blur(8px);z-index:15;
  max-height:50vh;overflow-y:auto;
  scrollbar-width:thin;scrollbar-color:#30363d transparent
}}
#info-panel.show{{transform:translateY(0)}}
#info-panel h3{{font-size:13px;color:#e6edf3;font-weight:600;margin-bottom:8px;line-height:1.3}}
.info-meta{{color:#8b949e;margin-bottom:8px;line-height:1.6}}
.info-section-title{{font-size:9px;font-weight:700;color:#484f58;
  text-transform:uppercase;letter-spacing:1px;margin:8px 0 4px}}
.info-edge-group{{margin-bottom:6px}}
.info-chip{{display:inline-block;background:#161b22;border-radius:4px;
  padding:2px 6px;margin:2px 2px 0 0;font-size:10px;color:#c9d1d9;
  border:1px solid #30363d;cursor:pointer;transition:border-color .1s}}
.info-chip:hover{{border-color:#58a6ff;color:#58a6ff}}
#info-close{{position:absolute;top:10px;right:10px;background:none;border:none;
  color:#484f58;cursor:pointer;font-size:14px;padding:2px 5px;transition:color .1s}}
#info-close:hover{{color:#e6edf3}}

/* ── Physics toggle ── */
#physics-btn{{
  position:absolute;top:12px;right:12px;
  background:#161b22;border:1px solid #30363d;border-radius:6px;
  color:#8b949e;font-size:10px;font-weight:600;padding:5px 10px;
  cursor:pointer;z-index:10;transition:all .15s;letter-spacing:0.3px}}
#physics-btn:hover{{border-color:#58a6ff;color:#58a6ff}}

/* ── Node type legend badge ── */
.nt-badge{{
  display:inline-block;padding:1px 6px;border-radius:3px;
  font-size:9px;font-weight:700;letter-spacing:0.4px;
  text-transform:uppercase;margin-left:5px;vertical-align:middle
}}
.nt-category{{background:#1f3a5a;color:#58a6ff;border:1px solid #1f6feb}}
.nt-concept{{background:#161b22;color:#8b949e;border:1px solid #30363d}}
.nt-section{{background:#1a1f2a;color:#6e7681;border:1px solid #21262d}}
</style>
</head>
<body>

<div id="sidebar">
  <div id="sidebar-header">
    <div class="title">ECI Knowledge Graph</div>
    <div class="subtitle">Peters, Janzing & Schölkopf (2017)</div>
    <div class="stats-pills">
      <div class="pill"><span id="stat-nodes">{n_nodes}</span> nodes</div>
      <div class="pill"><span id="stat-edges">{n_edges}</span> edges</div>
      <div class="pill" id="stat-selected" style="display:none">
        <span id="sel-count">0</span> selected
      </div>
    </div>
  </div>

  <div class="section-wrap">
    <div class="section-label">Search</div>
    <input id="search" type="text" placeholder="Find a concept…" autocomplete="off">
    <div id="search-count"></div>
  </div>

  <div class="section-wrap">
    <div class="section-label">View Preset</div>
    <div class="preset-grid">
      <button class="preset-btn" onclick="setPreset('Curriculum')">Curriculum</button>
      <button class="preset-btn" onclick="setPreset('Concept Web')">Concept Web</button>
      <button class="preset-btn" onclick="setPreset('Content Map')">Content Map</button>
      <button class="preset-btn active" id="preset-All" onclick="setPreset('All')">All</button>
    </div>
  </div>

  <div class="section-wrap" style="padding-bottom:6px">
    <div class="section-label">Edge Types</div>
  </div>
  <div id="toggle-scroll">
    {toggles_html}
  </div>

  <div class="section-wrap" style="border-top:1px solid #21262d">
    <div class="section-label">Chapter Filter</div>
    <select id="chapter-sel" onchange="filterChapter(this.value)">
      {chapter_opts}
    </select>
  </div>

  <div class="section-wrap">
    <div class="section-label">Node Legend</div>
    <div class="legend-grid">
      {legend_html}
    </div>
  </div>
</div>

<div id="net-wrap">
  <div id="mynetwork"></div>

  <div id="loading">
    <div class="spinner"></div>
    <p>Stabilizing graph…</p>
    <div id="progress-bar"><div id="progress-fill"></div></div>
  </div>

  <button id="physics-btn" onclick="togglePhysics()" style="display:none">⏸ Pause physics</button>

  <div id="info-panel">
    <button id="info-close" onclick="closeInfo()">✕</button>
    <h3 id="info-title"></h3>
    <div class="info-meta" id="info-meta"></div>
    <div id="info-edges"></div>
  </div>
</div>

<script>
const RAW_NODES = /** NODES_PLACEHOLDER **/;
const RAW_EDGES = /** EDGES_PLACEHOLDER **/;
const PRESETS   = /** PRESETS_PLACEHOLDER **/;

const nodes = new vis.DataSet(RAW_NODES);
const edges = new vis.DataSet(RAW_EDGES);

const container = document.getElementById('mynetwork');
const network   = new vis.Network(container, {{nodes, edges}}, /** OPTIONS_PLACEHOLDER **/);

let physicsOn = true;
network.on('stabilizationProgress', p => {{
  document.getElementById('progress-fill').style.width = (p.iterations/p.total*100)+'%';
}});
network.on('stabilizationIterationsDone', () => {{
  network.setOptions({{physics:{{enabled:false}}}});
  physicsOn = false;
  const ld = document.getElementById('loading');
  ld.classList.add('done');
  setTimeout(()=>ld.remove(), 600);
  const pb = document.getElementById('physics-btn');
  pb.style.display = 'block';
  pb.textContent = '▶ Resume physics';
}});
network.on('stabilized', () => {{
  document.getElementById('loading').classList.add('done');
}});

function togglePhysics() {{
  physicsOn = !physicsOn;
  network.setOptions({{physics:{{enabled:physicsOn}}}});
  document.getElementById('physics-btn').textContent =
    physicsOn ? '⏸ Pause physics' : '▶ Resume physics';
}}

// Edge type index
const edgesByType = {{}};
RAW_EDGES.forEach(e => {{
  if (!edgesByType[e.edge_type]) edgesByType[e.edge_type] = [];
  edgesByType[e.edge_type].push(e.id);
}});

function onToggle(cb) {{
  const type = cb.dataset.type;
  const hide = !cb.checked;
  edges.update((edgesByType[type]||[]).map(id=>({{id,hidden:hide}})));
  clearPresetActive();
}}

function setPreset(name) {{
  const active = PRESETS[name] || [];
  document.querySelectorAll('.toggle-wrap input').forEach(cb => {{
    const t = cb.dataset.type;
    const on = active.includes(t);
    cb.checked = on;
    edges.update((edgesByType[t]||[]).map(id=>({{id,hidden:!on}})));
  }});
  clearPresetActive();
  const btn = document.getElementById('preset-'+name.replace(' ','_'));
  if(btn) btn.classList.add('active');
}}

function clearPresetActive() {{
  document.querySelectorAll('.preset-btn').forEach(b=>b.classList.remove('active'));
}}

let searchTimer;
document.getElementById('search').addEventListener('input', function() {{
  clearTimeout(searchTimer);
  searchTimer = setTimeout(()=>doSearch(this.value.trim()), 150);
}});

function doSearch(q) {{
  const cnt = document.getElementById('search-count');
  if (!q) {{
    nodes.update(RAW_NODES.map(n=>({{id:n.id,opacity:1}})));
    cnt.textContent = '';
    return;
  }}
  const lq = q.toLowerCase();
  let hits = 0;
  const updates = RAW_NODES.map(n => {{
    const match = (n._full_label||n.label).toLowerCase().includes(lq);
    if(match) hits++;
    return {{id:n.id,opacity:match?1:0.08}};
  }});
  nodes.update(updates);
  cnt.textContent = hits+' match'+(hits!==1?'es':'');
  const first = RAW_NODES.find(n=>(n._full_label||n.label).toLowerCase().includes(lq));
  if(first) network.focus(first.id,{{scale:1.2,animation:{{duration:400,easingFunction:'easeInOutQuad'}}}});
}}

function filterChapter(ch) {{
  const val = parseInt(ch);
  if (val===0) {{ nodes.update(RAW_NODES.map(n=>({{id:n.id,opacity:1}}))); return; }}
  nodes.update(RAW_NODES.map(n=>({{id:n.id,opacity:n.chapter===val?1:0.06}})));
}}

const _EL = {el_labels_json};
const _CL = {ch_labels_json};

function showInfo(nodeId) {{
  const ndata = nodes.get(nodeId);
  if(!ndata) return;
  document.getElementById('info-title').textContent = ndata._full_label||ndata.label;

  const chLabel = _CL[String(ndata.chapter)]||'';
  const ntMap = {{'section':'Section','concept':'Concept','category':'Category'}};
  const ntLabel = ntMap[ndata.node_type]||ndata.node_type||'';
  const badge = ndata.node_type==='category'
    ? '<span class="nt-badge nt-category">Category</span>'
    : (ndata.node_type==='section'
      ? '<span class="nt-badge nt-section">Section</span>'
      : '<span class="nt-badge nt-concept">Concept</span>');
  document.getElementById('info-meta').innerHTML =
    badge + (chLabel ? ' <span style="color:#8b949e">· '+chLabel+'</span>' : '');

  const connEdgeIds = network.getConnectedEdges(nodeId);
  const connEdges   = edges.get(connEdgeIds);
  const byType = {{}};
  connEdges.forEach(e => {{
    if(!byType[e.edge_type]) byType[e.edge_type] = [];
    const otherId = e.from===nodeId?e.to:e.from;
    const other   = nodes.get(otherId);
    const dir     = e.from===nodeId?'→':'←';
    byType[e.edge_type].push({{id:otherId,label:(other?._full_label||other?.label||otherId),dir}});
  }});

  let html = '';
  Object.entries(byType).forEach(([etype,peers]) => {{
    const label = _EL[etype]||etype;
    html += `<div class="info-section-title">${{label}}</div><div class="info-edge-group">`;
    peers.slice(0,8).forEach(p => {{
      html += `<span class="info-chip" onclick="selectNode('${{p.id}}')">${{p.dir}} ${{p.label}}</span>`;
    }});
    if(peers.length>8) html += `<span class="info-chip">+${{peers.length-8}} more</span>`;
    html += '</div>';
  }});
  if(!html) html='<div class="info-meta">No visible connections.</div>';
  document.getElementById('info-edges').innerHTML = html;

  document.getElementById('info-panel').classList.add('show');
}}

function closeInfo() {{
  document.getElementById('info-panel').classList.remove('show');
  network.unselectAll();
}}

function selectNode(id) {{
  network.selectNodes([id]);
  network.focus(id,{{scale:1.4,animation:{{duration:400,easingFunction:'easeInOutQuad'}}}});
  showInfo(id);
}}

network.on('click', params => {{
  if(params.nodes.length>0) showInfo(params.nodes[0]);
  else closeInfo();
}});

network.on('selectNode', p => {{
  document.getElementById('stat-selected').style.display='';
  document.getElementById('sel-count').textContent=p.nodes.length;
}});
network.on('deselectNode', () => {{
  document.getElementById('stat-selected').style.display='none';
}});
</script>
</body>
</html>""" \
    .replace("/** NODES_PLACEHOLDER **/",   nodes_json) \
    .replace("/** EDGES_PLACEHOLDER **/",   edges_json) \
    .replace("/** PRESETS_PLACEHOLDER **/", presets_json) \
    .replace("/** OPTIONS_PLACEHOLDER **/", vis_options)


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    print("Building ECI graph…")
    G = build_graph()
    save_graph(G)

    print("Generating HTML…")
    html = generate_html(G)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_HTML.write_text(html, encoding="utf-8")
    print(f"\nVisualization saved → {OUTPUT_HTML}")
    print(f"Open in browser:  file://{OUTPUT_HTML.resolve()}")


if __name__ == "__main__":
    main()
