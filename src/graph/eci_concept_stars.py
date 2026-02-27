"""
ECI Concept Stars — generate eci_uni.html from the ECI knowledge graph.

Reads eci_graph.pkl (built by eci_graph_builder.py) and produces a
self-contained D3 visualization based on uni.html with three node kinds:

  concept  — small glowing star
  section  — dashed-ring nebula
  category — large red/orange sun, with corona rays; sub-concepts orbit it

Run:    conda run -n edu python graph/eci_concept_stars.py
Output: graph/output/eci_uni.html  (open directly in browser, no server needed)
"""

import json
import pickle
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

GRAPH_PKL   = Path(__file__).parent / "output" / "eci_graph.pkl"
OUTPUT_HTML = Path(__file__).parent / "output" / "eci_uni.html"


# ── Data extraction ─────────────────────────────────────────────────────────

def build_data() -> dict:
    import networkx as nx
    G: nx.DiGraph = pickle.load(open(GRAPH_PKL, "rb"))

    nodes = []
    for nid, d in G.nodes(data=True):
        node = dict(d)
        node["id"] = nid
        nodes.append(node)

    links = []
    for u, v, d in G.edges(data=True):
        link = dict(d)
        link["source"] = u
        link["target"] = v
        links.append(link)

    return {"nodes": nodes, "links": links}


# ── HTML template ────────────────────────────────────────────────────────────

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ECI Concept Universe — Elements of Causal Inference (2017)</title>
<script src="https://d3js.org/d3.v7.min.js"></script>
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: "Segoe UI", system-ui, sans-serif;
    background: radial-gradient(circle at center, #0b101a 0%, #020408 100%);
    color: #e6edf3;
    overflow: hidden;
    height: 100vh;
    display: flex;
  }
  svg { width: 100vw; height: 100vh; position: absolute; top: 0; left: 0; z-index: 1; }

  /* ── Star / node visuals ─── */
  .node text {
    font-size: 12px; font-weight: 500; fill: #c9d1d9; letter-spacing: 1px;
    text-shadow: 0 0 8px rgba(0,0,0,0.8), 0 0 15px rgba(0,0,0,1);
    pointer-events: none; opacity: 0;
    transition: opacity 0.4s ease, transform 0.4s ease; transform: translateY(5px);
  }
  .node:hover text, .node.active text, .node.neighbor text { opacity: 1; transform: translateY(0); }
  .node.dimmed { opacity: 0.12; transition: opacity 0.5s; }
  .node { transition: opacity 0.5s; cursor: pointer; }

  /* Concept star */
  .star-core  { fill: #ffffff; transition: r 0.3s; }
  .star-halo  { transition: r 0.3s, opacity 0.3s; opacity: 0.6; }
  .star-flare { stroke: #ffffff; stroke-width: 1; opacity: 0.3;
                transition: opacity 0.3s, stroke-width 0.3s; }

  /* Section nebula */
  .nebula-core  { fill: #0b101a; stroke: rgba(88,166,255,0.4); stroke-width: 1.5;
                  stroke-dasharray: 4,4; transition: r 0.3s; }
  .nebula-halo  { fill: #1f6feb; opacity: 0.05; transition: r 0.3s, opacity 0.3s; }
  .node.active  .nebula-halo { opacity: 0.2; }
  .node.active  .nebula-core { stroke: #00f0ff; stroke-width: 2; }

  /* Category sun */
  .sun-core   { transition: r 0.3s; }
  .sun-corona { opacity: 0.08; transition: r 0.3s, opacity 0.3s; }
  .sun-rays   { opacity: 0.35; transition: opacity 0.3s, stroke-width 0.3s; }
  .node:hover .sun-corona, .node.active .sun-corona { opacity: 0.28; }
  .node:hover .sun-rays,   .node.active .sun-rays   { opacity: 0.7; stroke-width: 2; }

  /* Shared hover */
  .node:hover .star-halo,  .node.active .star-halo  { opacity: 0.9; }
  .node:hover .star-flare, .node.active .star-flare { opacity: 0.7; stroke-width: 1.5; }

  /* ── Links ── */
  .link-group { opacity: 0; transition: opacity 0.5s ease; pointer-events: none; }
  .link-group.active { opacity: 1; }
  .link-base { stroke-opacity: 0.2; transition: stroke-width 0.3s; }
  .link-particles {
    stroke-opacity: 0.9; stroke-linecap: round;
    stroke-dasharray: 4,30;
    animation: flowParticles 1.5s linear infinite;
  }
  @keyframes flowParticles { from { stroke-dashoffset: 34; } to { stroke-dashoffset: 0; } }

  /* ── HUD panel ── */
  #hud-panel {
    position: absolute; top: 20px; left: 20px; width: 270px;
    background: rgba(10,14,23,0.4); border: 1px solid rgba(88,166,255,0.2);
    border-radius: 8px; backdrop-filter: blur(8px); z-index: 10;
    padding: 16px; box-shadow: 0 4px 30px rgba(0,0,0,0.5);
  }
  .hud-title {
    font-size: 11px; font-weight: 700; color: #58a6ff;
    margin-bottom: 6px; letter-spacing: 2px; text-transform: uppercase;
  }
  #universe-stats { font-size: 10px; color: #39ff14; margin-bottom: 12px; font-family: monospace; }
  .hud-divider { height: 1px; background: rgba(88,166,255,0.2); margin: 12px 0; }
  .filter-row  { display: flex; align-items: center; margin-bottom: 10px; font-size: 12px; cursor: pointer; }
  .filter-color { width: 10px; height: 10px; border-radius: 50%; margin-right: 12px; flex-shrink: 0; }
  .hud-btn {
    background: rgba(88,166,255,0.1); border: 1px solid #58a6ff;
    color: #58a6ff; padding: 8px 12px; border-radius: 4px;
    font-size: 11px; font-weight: bold; cursor: pointer; width: 100%;
    text-transform: uppercase; letter-spacing: 1px; transition: all 0.2s; margin-top: 5px;
  }
  .hud-btn:hover { background: #58a6ff; color: #fff; box-shadow: 0 0 15px rgba(88,166,255,0.4); }
  .hud-btn:disabled { background: rgba(255,255,255,0.05); border-color: rgba(255,255,255,0.2); color: #888; cursor: not-allowed; box-shadow: none; }

  /* ── Search ── */
  #search-container {
    position: absolute; top: 20px; left: 50%; transform: translateX(-50%);
    z-index: 10; width: 400px;
  }
  #search-input {
    width: 100%; padding: 12px 20px; border-radius: 30px;
    background: rgba(10,14,23,0.6); border: 1px solid rgba(88,166,255,0.3);
    color: white; font-size: 14px; outline: none;
    backdrop-filter: blur(8px); box-shadow: 0 4px 20px rgba(0,0,0,0.5); transition: all 0.3s;
  }
  #search-input:focus { border-color: #58a6ff; background: rgba(10,14,23,0.9); box-shadow: 0 0 15px rgba(88,166,255,0.3); }
  #dropdown {
    position: absolute; top: 55px; left: 0; width: 100%;
    background: rgba(10,14,23,0.95); border: 1px solid rgba(88,166,255,0.2);
    border-radius: 12px; max-height: 300px; overflow-y: auto;
    display: none; backdrop-filter: blur(10px); padding: 8px 0;
  }
  .dropdown-item {
    padding: 10px 20px; cursor: pointer; font-size: 13px; color: #c9d1d9;
    display: flex; justify-content: space-between; align-items: center;
    border-bottom: 1px solid rgba(255,255,255,0.05);
  }
  .dropdown-item:last-child { border-bottom: none; }
  .dropdown-item:hover { background: rgba(88,166,255,0.2); color: #fff; }
  .item-mass { font-size: 10px; color: #58a6ff; font-family: monospace; background: rgba(88,166,255,0.1); padding: 2px 6px; border-radius: 4px; }

  /* ── Info panel ── */
  #info-panel {
    position: absolute; top: 20px; right: 20px; width: 300px;
    background: rgba(10,14,23,0.6); border: 1px solid rgba(88,166,255,0.2);
    border-radius: 8px; backdrop-filter: blur(10px); z-index: 10;
    padding: 24px; box-shadow: 0 8px 32px rgba(0,0,0,0.5);
    opacity: 0; pointer-events: none; transition: opacity 0.4s, transform 0.4s; transform: translateX(20px);
  }
  #info-panel.show { opacity: 1; pointer-events: auto; transform: translateX(0); }
  #info-title { font-size: 18px; font-weight: 300; margin-bottom: 8px; color: #fff; letter-spacing: 1px; }
  #info-desc { font-size: 12px; color: #8b949e; line-height: 1.6; margin-bottom: 16px; max-height: 300px; overflow-y: auto; }
  .close-btn { position: absolute; top: 15px; right: 15px; cursor: pointer; color: #8b949e; font-size: 16px; }
  .close-btn:hover { color: #fff; }
</style>
</head>
<body>

<div id="hud-panel">
  <div class="hud-title">ECI Universe &nbsp;·&nbsp; Causal Inference 2017</div>
  <div id="universe-stats">Nodes: 0 / 0</div>

  <div style="font-size:11px;color:#8b949e;margin-bottom:8px;">Entity types:</div>
  <label class="filter-row">
    <input type="checkbox" id="toggle-concepts" style="margin-right:10px;accent-color:#58a6ff" checked>
    <div class="filter-color" style="background:#58a6ff;box-shadow:0 0 10px #58a6ff"></div>
    <span>Concepts (Stars)</span>
  </label>
  <label class="filter-row">
    <input type="checkbox" id="toggle-categories" style="margin-right:10px;accent-color:#ff6b35" checked>
    <div class="filter-color" style="background:#ff6b35;box-shadow:0 0 10px #ff6b35;border-radius:2px"></div>
    <span>Categories (Suns)</span>
  </label>
  <label class="filter-row">
    <input type="checkbox" id="toggle-sections" style="margin-right:10px;accent-color:#1f6feb" checked>
    <div class="filter-color" style="background:transparent;border:2px dashed #1f6feb;"></div>
    <span>Sections (Nebulas)</span>
  </label>

  <div class="hud-divider"></div>
  <div style="font-size:11px;color:#8b949e;margin-bottom:8px;">Active edge routes:</div>
  <div id="filter-container"></div>

  <div class="hud-divider"></div>
  <button id="btn-load-all" class="hud-btn">Load Full Universe</button>
</div>

<div id="search-container">
  <input type="text" id="search-input" placeholder="Scan the cosmos for concepts…" autocomplete="off">
  <div id="dropdown"></div>
</div>

<div id="info-panel">
  <div class="close-btn" onclick="resetUniverse()">✕</div>
  <div id="info-title">Concept</div>
  <div id="info-desc"></div>
</div>

<svg id="universe"></svg>

<script>
// ── Embedded graph data ───────────────────────────────────────────────────
const GRAPH_DATA = __GRAPH_DATA__;

// ── Core state ────────────────────────────────────────────────────────────
const width = window.innerWidth;
const height = window.innerHeight;

let masterNodes = [];
let masterLinks = [];
let visibleNodes = [];
let visibleLinks = [];

let activatedNodeIds = new Set();
let nodeTypesVisible = { concept: true, category: true, section: true };

let edgeColors = {};
let nodeDegree = {};
let selectedNodeId = null;
let activeFilters = new Set();
const INITIAL_NODES_COUNT = 60;

const svg = d3.select("#universe").attr("viewBox", [0, 0, width, height]);
const container = svg.append("g");
let linkGroup, nodeGroup, simulation;

// Ambient star field
const bgStars = svg.insert("g", ":first-child").attr("class", "bg-stars");
for (let i = 0; i < 250; i++) {
  bgStars.append("circle")
    .attr("cx", Math.random() * width).attr("cy", Math.random() * height)
    .attr("r", Math.random() * 1.5).attr("fill", "#fff").attr("opacity", Math.random() * 0.5 + 0.05);
}

const zoom = d3.zoom().scaleExtent([0.05, 5]).on("zoom", e => {
  container.attr("transform", e.transform);
  bgStars.attr("transform", `translate(${e.transform.x * 0.1},${e.transform.y * 0.1}) scale(${1 + (e.transform.k - 1) * 0.1})`);
});
svg.call(zoom);

// ── Data processing ───────────────────────────────────────────────────────
function processData(data) {
  const rawNodes = data.nodes || [];
  rawNodes.forEach(n => {
    n.isSection  = n.type === "section";
    n.isCategory = n.type === "category";
  });
  const nodeIds = new Set(rawNodes.map(n => n.id));

  const rawLinks = data.links || data.edges || [];
  const validLinks = rawLinks.filter(l => nodeIds.has(l.source) && nodeIds.has(l.target));

  validLinks.forEach(l => {
    const eType = l.edge_type || "UNKNOWN";
    l.type = eType;
    if (!edgeColors[eType]) edgeColors[eType] = l.color || "#00f0ff";
  });

  rawNodes.forEach(n => { nodeDegree[n.id] = 0; });
  validLinks.forEach(l => {
    nodeDegree[l.source]++;
    nodeDegree[l.target]++;
  });

  masterNodes = rawNodes.map(d => {
    const degree = nodeDegree[d.id] || 0;
    let radius, haloColor, displayColor;

    if (d.isSection) {
      radius     = Math.max(15, Math.min(40, 10 + degree * 0.5));
      haloColor  = "#1a2333";
      displayColor = d.color || "#1f6feb";
    } else if (d.isCategory) {
      radius     = Math.max(22, Math.min(42, 20 + Math.sqrt(degree) * 5));
      haloColor  = "#ff6b35";
      displayColor = "#ff6b35";
    } else {
      radius     = Math.max(3, Math.min(15, 2 + degree * 0.8));
      haloColor  = degree > 8 ? "#00f0ff" : degree > 3 ? "#b026ff" : "#58a6ff";
      displayColor = d.color || "#58a6ff";
    }

    return {
      ...d,
      label:        d.short_label || d.label || d.id,
      desc:         d.tooltip || d.desc || "No description.",
      radius,
      haloColor,
      displayColor,
    };
  });

  masterLinks = validLinks.map(d => ({ ...d }));

  // Seed initial high-degree nodes
  const sorted = [...masterNodes].sort((a, b) => (nodeDegree[b.id] || 0) - (nodeDegree[a.id] || 0));
  sorted.slice(0, INITIAL_NODES_COUNT).forEach(n => {
    n.x = width  / 2 + (Math.random() - 0.5) * width  * 0.5;
    n.y = height / 2 + (Math.random() - 0.5) * height * 0.5;
    activatedNodeIds.add(n.id);
  });

  initUniverse();
}

// ── Refresh visible set ───────────────────────────────────────────────────
function refreshVisibleData() {
  visibleNodes = masterNodes.filter(n => {
    if (!activatedNodeIds.has(n.id))  return false;
    if (n.isSection  && !nodeTypesVisible.section)  return false;
    if (n.isCategory && !nodeTypesVisible.category) return false;
    if (!n.isSection && !n.isCategory && !nodeTypesVisible.concept) return false;
    return true;
  });

  const vIds = new Set(visibleNodes.map(n => n.id));
  visibleLinks = masterLinks
    .filter(l => {
      const sid = l.source.id || l.source;
      const tid = l.target.id || l.target;
      return vIds.has(sid) && vIds.has(tid);
    })
    .map(l => ({ ...l }));

  updateRender();
}

// ── Initialise simulation & UI ────────────────────────────────────────────
function initUniverse() {
  const defs = svg.append("defs");

  // Per-edge-type glow filters
  Object.entries(edgeColors).forEach(([type, color]) => {
    const safeId = "glow-" + btoa(unescape(encodeURIComponent(type))).replace(/[^a-zA-Z0-9]/g, "");
    const f = defs.append("filter").attr("id", safeId)
      .attr("x", "-50%").attr("y", "-50%").attr("width", "200%").attr("height", "200%");
    f.append("feGaussianBlur").attr("stdDeviation", "2").attr("result", "blur1");
    f.append("feGaussianBlur").attr("stdDeviation", "6").attr("result", "blur2").attr("in", "SourceGraphic");
    const m = f.append("feMerge");
    m.append("feMergeNode").attr("in", "blur2");
    m.append("feMergeNode").attr("in", "blur1");
    m.append("feMergeNode").attr("in", "SourceGraphic");
  });

  // Star glow
  const sf = defs.append("filter").attr("id", "star-glow")
    .attr("x", "-50%").attr("y", "-50%").attr("width", "200%").attr("height", "200%");
  sf.append("feGaussianBlur").attr("stdDeviation", "4").attr("result", "blur");
  const sm = sf.append("feMerge");
  sm.append("feMergeNode").attr("in", "blur");
  sm.append("feMergeNode").attr("in", "SourceGraphic");

  // Sun glow (stronger)
  const sunf = defs.append("filter").attr("id", "sun-glow")
    .attr("x", "-80%").attr("y", "-80%").attr("width", "360%").attr("height", "360%");
  sunf.append("feGaussianBlur").attr("stdDeviation", "9").attr("result", "blur");
  const sunm = sunf.append("feMerge");
  sunm.append("feMergeNode").attr("in", "blur");
  sunm.append("feMergeNode").attr("in", "SourceGraphic");

  linkGroup = container.append("g").attr("class", "links");
  nodeGroup = container.append("g").attr("class", "nodes");

  simulation = d3.forceSimulation()
    .force("link", d3.forceLink().id(d => d.id).distance(d => {
      if (d.type === "SUBTOPIC_OF")  return 70;
      if (d.type === "COVERED_IN" || d.type === "ILLUSTRATES") return 200;
      if (d.type === "NEXT_IN_SEQUENCE") return 140;
      return 130;
    }))
    .force("charge", d3.forceManyBody().strength(d =>
      d.isSection ? -700 : d.isCategory ? -1200 : -280
    ))
    .force("center", d3.forceCenter(width / 2, height / 2).strength(0.04))
    .force("collide", d3.forceCollide().radius(d => d.radius + (d.isCategory ? 30 : 15)))
    .velocityDecay(0.42)
    .alphaDecay(0.01);

  simulation.on("tick", () => {
    linkGroup.selectAll(".link-group").selectAll("line")
      .attr("x1", d => d.source.x).attr("y1", d => d.source.y)
      .attr("x2", d => d.target.x).attr("y2", d => d.target.y);
    nodeGroup.selectAll(".node").attr("transform", d => `translate(${d.x},${d.y})`);
  });

  // Entity filter handlers
  const handleEntityFilter = () => {
    if (selectedNodeId) {
      const n = masterNodes.find(n => n.id === selectedNodeId);
      const vis = n.isSection  ? nodeTypesVisible.section
                : n.isCategory ? nodeTypesVisible.category
                : nodeTypesVisible.concept;
      if (vis) expandAndFocusNode(selectedNodeId);
      else { resetUniverse(); refreshVisibleData(); }
    } else {
      refreshVisibleData();
    }
  };

  document.getElementById("toggle-concepts").addEventListener("change", e => {
    nodeTypesVisible.concept = e.target.checked; handleEntityFilter();
  });
  document.getElementById("toggle-categories").addEventListener("change", e => {
    nodeTypesVisible.category = e.target.checked; handleEntityFilter();
  });
  document.getElementById("toggle-sections").addEventListener("change", e => {
    nodeTypesVisible.section = e.target.checked; handleEntityFilter();
  });

  // Load-all button
  document.getElementById("btn-load-all").addEventListener("click", function() {
    masterNodes.forEach(n => {
      if (!activatedNodeIds.has(n.id)) {
        n.x = (Math.random() - 0.5) * width  * 3;
        n.y = (Math.random() - 0.5) * height * 3;
        activatedNodeIds.add(n.id);
      }
    });
    this.innerText = "ALL SYSTEMS ONLINE";
    this.disabled = true;
    if (selectedNodeId) expandAndFocusNode(selectedNodeId);
    else refreshVisibleData();
  });

  // Edge-type filter UI
  const filterContainer = document.getElementById("filter-container");
  filterContainer.innerHTML = "";
  Object.entries(edgeColors).forEach(([type, color]) => {
    activeFilters.add(type);
    const row = document.createElement("label");
    row.className = "filter-row";
    row.innerHTML =
      `<input type="checkbox" style="margin-right:10px;accent-color:${color}" value="${type}" checked>` +
      `<div class="filter-color" style="background:${color};box-shadow:0 0 8px ${color}"></div>` +
      `<span>${type.replace(/_/g, " ")}</span>`;
    filterContainer.appendChild(row);
    row.querySelector("input").addEventListener("change", e => {
      if (e.target.checked) activeFilters.add(type); else activeFilters.delete(type);
      if (selectedNodeId) expandAndFocusNode(selectedNodeId); else refreshVisibleData();
    });
  });

  // Search
  const searchInput = document.getElementById("search-input");
  const dropdown    = document.getElementById("dropdown");
  searchInput.addEventListener("input", function() {
    const val = this.value.toLowerCase().trim();
    dropdown.innerHTML = "";
    if (!val) { dropdown.style.display = "none"; return; }
    const terms = val.split(" ").filter(t => t.length > 0);
    const hits = masterNodes.map(n => {
      const lbl = (n.label || "").toLowerCase();
      let score = 0;
      if (lbl === val)          score = 1000;
      else if (lbl.startsWith(val)) score = 800;
      else if (lbl.includes(val))   score = 500;
      else if (terms.length > 1 && terms.every(t => lbl.includes(t))) score = 100;
      if (score > 0) score += (nodeDegree[n.id] || 0) * 0.5;
      return { n, score };
    }).filter(x => x.score > 0).sort((a, b) => b.score - a.score).map(x => x.n);
    if (!hits.length) { dropdown.style.display = "none"; return; }
    dropdown.style.display = "block";
    hits.slice(0, 15).forEach(n => {
      const el = document.createElement("div");
      el.className = "dropdown-item";
      const icon = n.isCategory ? "☀ " : n.isSection ? "◎ " : "✦ ";
      el.innerHTML = `<span>${icon}${n.label}</span><span class="item-mass">Links: ${nodeDegree[n.id] || 0}</span>`;
      el.onclick = () => {
        searchInput.value = n.label;
        dropdown.style.display = "none";
        expandAndFocusNode(n.id);
      };
      dropdown.appendChild(el);
    });
  });

  svg.on("click", e => {
    if (e.target.tagName === "svg" && selectedNodeId) resetUniverse();
  });

  refreshVisibleData();
}

// ── D3 render pipeline ────────────────────────────────────────────────────
function updateRender() {
  document.getElementById("universe-stats").innerText =
    `Explored: ${activatedNodeIds.size} / Total: ${masterNodes.length}`;

  // Links
  linkGroup.selectAll(".link-group")
    .data(visibleLinks, d => {
      const s = d.source.id || d.source, t = d.target.id || d.target;
      return s + "-" + t;
    })
    .join(
      enter => {
        const g = enter.append("g").attr("class", "link-group")
          .attr("id", d => `link-${d.source.id || d.source}-${d.target.id || d.target}`);
        g.append("line").attr("class", "link-base")
          .attr("stroke", d => edgeColors[d.type]).attr("stroke-width", 1.5)
          .attr("filter", d => `url(#glow-${btoa(unescape(encodeURIComponent(d.type))).replace(/[^a-zA-Z0-9]/g, "")})`);
        g.append("line").attr("class", "link-particles")
          .attr("stroke", "#ffffff").attr("stroke-width", 1.5)
          .attr("filter", d => `url(#glow-${btoa(unescape(encodeURIComponent(d.type))).replace(/[^a-zA-Z0-9]/g, "")})`);
        return g;
      },
      update => update,
      exit   => exit.remove()
    );

  // Nodes
  nodeGroup.selectAll(".node")
    .data(visibleNodes, d => d.id)
    .join(
      enter => {
        const g = enter.append("g").attr("class", "node")
          .call(dragBehavior(simulation))
          .on("click",     (ev, d) => expandAndFocusNode(d.id))
          .on("mouseover", handleMouseOver)
          .on("mouseout",  handleMouseOut);

        // ── Category sun ──
        g.filter(d => d.isCategory)
          .append("circle").attr("class", "sun-corona")
          .attr("r", d => d.radius * 2.5)
          .attr("fill", "#ff6b35")
          .attr("filter", "url(#sun-glow)");

        g.filter(d => d.isCategory)
          .append("path").attr("class", "sun-rays")
          .attr("d", d => {
            const s = d.radius * 2.0;
            const s2 = s * 0.72;
            return `M-${s},0 L${s},0 M0,-${s} L0,${s} M-${s2},-${s2} L${s2},${s2} M${s2},-${s2} L-${s2},${s2}`;
          })
          .attr("stroke", "#ff6b35")
          .attr("stroke-width", 1.8)
          .attr("fill", "none")
          .attr("filter", "url(#sun-glow)");

        // ── Concept star flares ──
        g.filter(d => !d.isSection && !d.isCategory)
          .append("path").attr("class", "star-flare")
          .attr("d", d => { const s = d.radius * 2.5; return `M-${s},0 L${s},0 M0,-${s} L0,${s}`; })
          .attr("filter", "url(#star-glow)");

        // ── Halo for all types ──
        g.append("circle")
          .attr("class", d => d.isSection ? "nebula-halo" : d.isCategory ? "sun-corona" : "star-halo")
          .attr("r", d => d.isSection ? d.radius * 1.5 : d.isCategory ? d.radius * 1.8 : d.radius + 3)
          .attr("fill", d => d.isSection ? "#1f6feb" : d.haloColor)
          .attr("filter", d => d.isSection ? "" : "url(#star-glow)");

        // ── Core circle ──
        g.append("circle")
          .attr("class", d => d.isSection ? "nebula-core" : d.isCategory ? "sun-core" : "star-core")
          .attr("r", d => d.radius)
          .style("fill", d => d.isCategory ? "#ff6b35" : null);

        // ── Label ──
        g.append("text")
          .attr("dx", d => d.radius + 12)
          .attr("dy", 4)
          .style("fill", d => d.isSection ? "#58a6ff" : d.isCategory ? "#ffd0a0" : "#c9d1d9")
          .style("text-transform", d => d.isSection ? "uppercase" : "none")
          .style("letter-spacing", d => d.isSection ? "2px" : d.isCategory ? "1.5px" : "1px")
          .style("font-weight", d => d.isCategory ? "600" : "500")
          .text(d => d.label);

        return g;
      },
      update => update,
      exit   => exit.remove()
    );

  simulation.nodes(visibleNodes);
  simulation.force("link").links(visibleLinks);
  simulation.alpha(0.15).restart();
}

// ── Explore & focus ───────────────────────────────────────────────────────
function expandAndFocusNode(nodeId) {
  if (selectedNodeId && selectedNodeId !== nodeId) {
    const old = masterNodes.find(n => n.id === selectedNodeId);
    if (old) { old.fx = null; old.fy = null; }
  }
  selectedNodeId = nodeId;
  const target = masterNodes.find(n => n.id === nodeId);

  if (!activatedNodeIds.has(nodeId)) {
    target.x = width / 2; target.y = height / 2;
    activatedNodeIds.add(nodeId);
  }

  const neighborIds = new Set();
  const linksToAdd  = [];
  masterLinks.forEach(l => {
    const sid = l.source.id || l.source;
    const tid = l.target.id || l.target;
    if (activeFilters.has(l.type)) {
      if (sid === nodeId) { neighborIds.add(tid); linksToAdd.push(l); }
      if (tid === nodeId) { neighborIds.add(sid); linksToAdd.push(l); }
    }
  });

  neighborIds.forEach(nid => {
    if (!activatedNodeIds.has(nid)) {
      const nn = masterNodes.find(n => n.id === nid);
      const radius = 60 + Math.random() * 200;
      const angle  = Math.random() * Math.PI * 2;
      nn.x = (target.x || width  / 2) + Math.cos(angle) * radius;
      nn.y = (target.y || height / 2) + Math.sin(angle) * radius;
      activatedNodeIds.add(nid);
    }
  });

  refreshVisibleData();

  target.fx = target.x || width  / 2;
  target.fy = target.y || height / 2;

  const connEdgeIds = new Set(linksToAdd.map(l => `link-${l.source.id || l.source}-${l.target.id || l.target}`));
  d3.selectAll(".node").classed("dimmed",   d => d.id !== nodeId && !neighborIds.has(d.id));
  d3.selectAll(".node").classed("active",   d => d.id === nodeId);
  d3.selectAll(".node").classed("neighbor", d => neighborIds.has(d.id));
  d3.selectAll(".link-group").classed("active", false)
    .filter(function() { return connEdgeIds.has(d3.select(this).attr("id")); })
    .classed("active", true);

  const icon = target.isCategory ? "☀ Category" : target.isSection ? "◎ Section" : "✦ Concept";
  const accentColor = target.isCategory ? "#ff6b35" : target.isSection ? "#58a6ff" : "#8b949e";
  document.getElementById("info-title").innerText = target.label;
  document.getElementById("info-desc").innerHTML =
    `<span style="color:${accentColor}">${icon} · Mass: ${nodeDegree[nodeId]}</span><br><br>${target.desc}`;
  document.getElementById("info-panel").classList.add("show");

  svg.transition().duration(1000).call(
    zoom.transform,
    d3.zoomIdentity.translate(width / 2, height / 2).scale(1.2)
      .translate(-(target.x || width / 2), -(target.y || height / 2))
  );
}

// ── Reset ─────────────────────────────────────────────────────────────────
function resetUniverse() {
  if (selectedNodeId) {
    const old = masterNodes.find(n => n.id === selectedNodeId);
    if (old) { old.fx = null; old.fy = null; }
  }
  selectedNodeId = null;
  document.getElementById("info-panel").classList.remove("show");
  d3.selectAll(".node").classed("dimmed", false).classed("active", false).classed("neighbor", false);
  d3.selectAll(".star-halo, .nebula-halo")
    .attr("r", d => d.isSection ? d.radius * 1.5 : d.isCategory ? d.radius * 1.8 : d.radius + 3);
  d3.selectAll(".link-group").classed("active", false);
}

// ── Hover ─────────────────────────────────────────────────────────────────
function handleMouseOver(event, d) {
  if (selectedNodeId && selectedNodeId !== d.id) return;
  d3.select(this).select(".star-halo, .nebula-halo")
    .attr("r", d.isSection ? d.radius * 1.8 : d.isCategory ? d.radius * 2.2 : d.radius + 6);
}
function handleMouseOut(event, d) {
  if (selectedNodeId) return;
  d3.select(this).select(".star-halo, .nebula-halo")
    .attr("r", d.isSection ? d.radius * 1.5 : d.isCategory ? d.radius * 1.8 : d.radius + 3);
}

// ── Drag ──────────────────────────────────────────────────────────────────
function dragBehavior(sim) {
  return d3.drag()
    .on("start", (ev, d) => { if (!ev.active) sim.alphaTarget(0.1).restart(); d.fx = d.x; d.fy = d.y; })
    .on("drag",  (ev, d) => { d.fx = ev.x; d.fy = ev.y; })
    .on("end",   (ev, d) => {
      if (!ev.active) sim.alphaTarget(0);
      if (d.id !== selectedNodeId) { d.fx = null; d.fy = null; }
    });
}

// ── Boot ──────────────────────────────────────────────────────────────────
processData(GRAPH_DATA);
</script>
</body>
</html>"""


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    data   = build_data()
    n_all  = len(data["nodes"])
    n_links = len(data["links"])

    by_type = {}
    for n in data["nodes"]:
        t = n.get("type", "?")
        by_type[t] = by_type.get(t, 0) + 1

    html = HTML.replace("__GRAPH_DATA__", json.dumps(data))

    OUTPUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_HTML.write_text(html, encoding="utf-8")

    print(f"Saved    → {OUTPUT_HTML}")
    print(f"Nodes    : {n_all}  {by_type}")
    print(f"Links    : {n_links}")
    print(f"Open     : file://{OUTPUT_HTML.resolve()}")


if __name__ == "__main__":
    main()
