"""
Concept Stars — Slipways-inspired concept map for Pearl (2009) Causality.

Each concept is a star floating in space.
  · Star size  ∝ degree (total connections)
  · Star glow  ∝ page-reference count
  · Click a star → it centres on screen, reveals connections as glowing lines
  · Sidebar shows connections grouped by edge type with toggle filters
  · Search box with fuzzy-match dropdown

Run:    conda run -n edu python graph/concept_stars.py
Output: graph/output/concept_stars.html   (open directly in browser, no server needed)
"""

import json
import pickle
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

GRAPH_PKL   = Path(__file__).parent / "output" / "graph.pkl"
OUTPUT_HTML = Path(__file__).parent / "output" / "concept_stars.html"

CONCEPT_EDGE_TYPES = {
    "SUBTOPIC_OF", "PREREQUISITE_OF",
    "RELATED_TO_SEE_ALSO", "RELATED_TO_ALIAS",
    "COMMONLY_CONFUSED", "APPLIED_TO",
}


# ── Data extraction ────────────────────────────────────────────────────────────

def build_data() -> dict:
    import networkx as nx
    G: nx.DiGraph = pickle.load(open(GRAPH_PKL, "rb"))

    concept_ids = {n for n, d in G.nodes(data=True) if d.get("type") == "concept"}

    nodes = [
        {
            "id":      nid,
            "label":   d.get("label", nid),
            "color":   d.get("color", "#6e7681"),
            "chapter": d.get("chapter", 0),
            "pages":   len(d.get("page_refs", [])),
        }
        for nid, d in G.nodes(data=True)
        if d.get("type") == "concept"
    ]

    links = [
        {
            "source":    u,
            "target":    v,
            "edge_type": d.get("edge_type", ""),
            "color":     d.get("color", "#888"),
            "dashes":    d.get("dashes", False),
        }
        for u, v, d in G.edges(data=True)
        if u in concept_ids and v in concept_ids
        and d.get("edge_type", "") in CONCEPT_EDGE_TYPES
    ]

    return {"nodes": nodes, "links": links}


# ── HTML template (raw string — no f-string processing, safe JS curly braces) ──

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Concept Stars — Pearl (2009) Causality</title>
<style>
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html, body {
  width: 100vw; height: 100vh; overflow: hidden;
  background: #010409;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif;
  color: #e6edf3;
}

/* ── Canvas ── */
#canvas {
  position: fixed; top: 0; left: 0;
  width: 100vw; height: 100vh;
  cursor: grab;
}
#canvas:active { cursor: grabbing; }

/* ── HUD ── */
#hud-title {
  position: fixed; top: 18px; left: 22px;
  font-size: 11px; font-weight: 700; letter-spacing: 1.2px;
  text-transform: uppercase; color: #58a6ff; opacity: 0.75;
  pointer-events: none; z-index: 10;
}
#hud-stats {
  position: fixed; top: 36px; left: 22px;
  font-size: 10px; color: #484f58; letter-spacing: 0.3px;
  pointer-events: none; z-index: 10;
}
#hud-stats span { color: #6e7681; }
#hud-hint {
  position: fixed; bottom: 16px; left: 50%; transform: translateX(-50%);
  font-size: 10px; color: #21262d; letter-spacing: 0.5px;
  pointer-events: none; z-index: 10;
  transition: color 0.5s;
}
body:hover #hud-hint { color: #30363d; }

/* ── Search ── */
#search-wrap {
  position: fixed; top: 16px; right: 22px;
  z-index: 20; width: 230px;
}
#search-input {
  width: 100%;
  background: rgba(22,27,34,0.88);
  border: 1px solid #30363d;
  color: #c9d1d9; padding: 7px 14px;
  border-radius: 20px;
  font-size: 12px; outline: none; letter-spacing: 0.3px;
  backdrop-filter: blur(12px);
  transition: border-color 0.2s, background 0.2s;
}
#search-input:focus {
  border-color: #388bfd;
  background: rgba(22,27,34,0.97);
}
#search-input::placeholder { color: #484f58; }
#search-dropdown {
  position: absolute; top: calc(100% + 6px); left: 0; right: 0;
  background: rgba(13,17,23,0.97);
  border: 1px solid #30363d;
  border-radius: 10px; overflow: hidden;
  display: none;
  backdrop-filter: blur(12px);
  box-shadow: 0 8px 32px rgba(0,0,0,0.6);
}
.search-item {
  padding: 8px 14px; font-size: 12px; cursor: pointer;
  color: #c9d1d9; letter-spacing: 0.2px;
  display: flex; justify-content: space-between; align-items: center;
  border-bottom: 1px solid #161b22;
  transition: background 0.1s;
}
.search-item:last-child { border-bottom: none; }
.search-item:hover, .search-item.active { background: #161b22; color: #58a6ff; }
.search-item .deg { color: #484f58; font-size: 10px; }

/* ── Sidebar ── */
#sidebar {
  position: fixed; left: 0; top: 0; bottom: 0;
  width: 268px;
  background: rgba(10,14,20,0.94);
  border-right: 1px solid #21262d;
  backdrop-filter: blur(16px);
  transform: translateX(-268px);
  transition: transform 0.35s cubic-bezier(0.4, 0, 0.2, 1);
  z-index: 15;
  display: flex; flex-direction: column;
  overflow: hidden;
}
#sidebar.open { transform: translateX(0); }

#sb-header {
  padding: 16px 18px 14px;
  border-bottom: 1px solid #21262d;
  flex-shrink: 0;
}
#sb-close {
  float: right; margin-top: 1px;
  width: 20px; height: 20px; border-radius: 50%;
  background: #21262d; border: none; color: #6e7681;
  cursor: pointer; font-size: 13px; line-height: 20px; text-align: center;
  transition: background 0.15s, color 0.15s;
}
#sb-close:hover { background: #30363d; color: #e6edf3; }
#sb-name {
  font-size: 14px; font-weight: 700; color: #e6edf3;
  margin-right: 28px; line-height: 1.4; word-break: break-word;
}
#sb-meta {
  display: flex; gap: 16px; margin-top: 10px;
}
.meta-chip { display: flex; flex-direction: column; gap: 1px; }
.meta-chip .val { font-size: 17px; font-weight: 700; color: #c9d1d9; }
.meta-chip .key {
  text-transform: uppercase; letter-spacing: 0.7px;
  font-size: 9px; color: #484f58;
}

#sb-toggles {
  padding: 12px 18px;
  border-bottom: 1px solid #21262d;
  flex-shrink: 0;
}
.section-label {
  font-size: 9px; text-transform: uppercase; letter-spacing: 0.8px;
  color: #484f58; margin-bottom: 8px;
}
.edge-toggle {
  display: flex; align-items: center; gap: 8px;
  padding: 4px 0; cursor: pointer; user-select: none;
}
.edge-toggle input[type="checkbox"] { display: none; }
.t-dot {
  width: 8px; height: 8px; border-radius: 50%;
  flex-shrink: 0; transition: opacity 0.2s;
}
.t-text { font-size: 11px; color: #6e7681; transition: color 0.2s; }
.edge-toggle:has(input:checked) .t-text { color: #c9d1d9; }
.edge-toggle:has(input:not(:checked)) .t-dot { opacity: 0.18; }

#sb-neighbors {
  flex: 1; overflow-y: auto; padding: 8px 0 16px;
}
#sb-neighbors::-webkit-scrollbar { width: 3px; }
#sb-neighbors::-webkit-scrollbar-track { background: transparent; }
#sb-neighbors::-webkit-scrollbar-thumb { background: #30363d; border-radius: 2px; }
.nb-group {
  padding: 8px 18px 2px;
  font-size: 9px; text-transform: uppercase; letter-spacing: 0.8px;
  font-weight: 600;
}
.nb-item {
  padding: 5px 18px;
  font-size: 12px; color: #6e7681;
  cursor: pointer;
  display: flex; align-items: center; gap: 7px;
  transition: color 0.12s, background 0.12s;
}
.nb-item:hover { background: rgba(56,139,253,0.06); color: #58a6ff; }
.nb-dot { width: 6px; height: 6px; border-radius: 50%; flex-shrink: 0; }

/* ── Tooltip ── */
#tooltip {
  position: fixed; pointer-events: none;
  background: rgba(13,17,23,0.95);
  border: 1px solid #30363d; border-radius: 8px;
  padding: 8px 12px; font-size: 12px;
  display: none; z-index: 40;
  backdrop-filter: blur(8px);
  max-width: 220px; line-height: 1.5;
  box-shadow: 0 4px 16px rgba(0,0,0,0.5);
}
#tooltip strong { color: #e6edf3; display: block; }
#tooltip .dim { color: #6e7681; font-size: 10px; }

/* ── Animations ── */
@keyframes twinkle {
  0%, 100% { opacity: 0.80; }
  50%       { opacity: 1.00; }
}
@keyframes pulse-ring {
  0%, 100% { opacity: 0.4; }
  50%       { opacity: 0.85; }
}
@keyframes flow-dash {
  to { stroke-dashoffset: -28; }
}
.star-body {
  animation: twinkle var(--td, 3s) var(--dl, 0s) ease-in-out infinite;
}
.star-ring-sel {
  animation: pulse-ring 1.6s ease-in-out infinite;
}
.edge-flow {
  animation: flow-dash 1.1s linear infinite;
}
</style>
</head>
<body>

<!-- HUD -->
<div id="hud-title">Concept Stars &middot; Causality</div>
<div id="hud-stats">
  <span id="stat-n">–</span> concepts &nbsp;·&nbsp;
  <span id="stat-e">–</span> connections shown
</div>
<div id="hud-hint">
  click a star to explore &nbsp;·&nbsp; scroll to zoom &nbsp;·&nbsp; drag to pan
</div>

<!-- Search -->
<div id="search-wrap">
  <input id="search-input" type="text" placeholder="Search concepts…"
         autocomplete="off" spellcheck="false">
  <div id="search-dropdown"></div>
</div>

<!-- Sidebar -->
<div id="sidebar">
  <div id="sb-header">
    <button id="sb-close" title="Close (Esc)">×</button>
    <div id="sb-name">—</div>
    <div id="sb-meta">
      <div class="meta-chip">
        <span class="val" id="sb-degree">0</span>
        <span class="key">Links</span>
      </div>
      <div class="meta-chip">
        <span class="val" id="sb-pages">0</span>
        <span class="key">Pages</span>
      </div>
      <div class="meta-chip">
        <span class="val" id="sb-chapter">—</span>
        <span class="key">Ch.</span>
      </div>
    </div>
  </div>
  <div id="sb-toggles">
    <div class="section-label">Edge types</div>
    <div id="toggle-list"></div>
  </div>
  <div id="sb-neighbors"></div>
</div>

<!-- Canvas -->
<svg id="canvas"></svg>

<!-- Tooltip -->
<div id="tooltip"></div>

<script src="https://d3js.org/d3.v7.min.js"></script>
<script>
"use strict";

// ── Embedded graph data ────────────────────────────────────────────────────
const GRAPH_DATA = __GRAPH_DATA__;

// ── Edge metadata ──────────────────────────────────────────────────────────
const EDGE_META = {
  "PREREQUISITE_OF":     { label: "Prerequisite Of",   color: "#f0883e", icon: "→" },
  "SUBTOPIC_OF":         { label: "Subtopic Of",        color: "#388bfd", icon: "↳" },
  "RELATED_TO_SEE_ALSO": { label: "See Also",           color: "#d29922", icon: "↔" },
  "RELATED_TO_ALIAS":    { label: "Alias / Same As",    color: "#8957e5", icon: "≈" },
  "COMMONLY_CONFUSED":   { label: "Commonly Confused",  color: "#da3633", icon: "⚡" },
  "APPLIED_TO":          { label: "Applied To",         color: "#1abc9c", icon: "⊂" },
};

// ── State ──────────────────────────────────────────────────────────────────
let selectedId   = null;
const visibleTypes = new Set(Object.keys(EDGE_META));

// ── SVG + zoom setup ───────────────────────────────────────────────────────
const W = window.innerWidth, H = window.innerHeight;
const svg = d3.select("#canvas").attr("width", W).attr("height", H);

// Background: deep-space radial gradient
const bgDefs = svg.append("defs");
const bgGrad = bgDefs.append("radialGradient")
  .attr("id", "bg-grad").attr("cx", "50%").attr("cy", "50%").attr("r", "65%");
bgGrad.append("stop").attr("offset", "0%").attr("stop-color", "#050d1e");
bgGrad.append("stop").attr("offset", "100%").attr("stop-color", "#010409");
svg.append("rect").attr("width", W).attr("height", H).attr("fill", "url(#bg-grad)");

// SVG filters
const defs = svg.select("defs");

// Star glow filter
const sf = defs.append("filter").attr("id", "star-glow")
  .attr("x", "-250%").attr("y", "-250%").attr("width", "600%").attr("height", "600%");
sf.append("feGaussianBlur").attr("stdDeviation", "6").attr("result", "blur");
const sm = sf.append("feMerge");
sm.append("feMergeNode").attr("in", "blur");
sm.append("feMergeNode").attr("in", "SourceGraphic");

// Line glow filter
const lf = defs.append("filter").attr("id", "line-glow")
  .attr("x", "-80%").attr("y", "-80%").attr("width", "260%").attr("height", "260%");
lf.append("feGaussianBlur").attr("stdDeviation", "3").attr("result", "blur");
const lm = lf.append("feMerge");
lm.append("feMergeNode").attr("in", "blur");
lm.append("feMergeNode").attr("in", "SourceGraphic");

// World container (receives zoom transforms)
const world = svg.append("g").attr("id", "world");

// Zoom / pan
const zoom = d3.zoom()
  .scaleExtent([0.05, 14])
  .on("zoom", e => world.attr("transform", e.transform));
svg.call(zoom);
// Start view centred on world origin
svg.call(zoom.transform, d3.zoomIdentity.translate(W / 2, H / 2));

// Click on blank space → deselect
svg.on("click", () => { if (selectedId) deselect(); });

// ── Ambient star field (decorative background dots) ────────────────────────
const bgStars = d3.range(500).map(() => ({
  x: (Math.random() - 0.5) * W * 5,
  y: (Math.random() - 0.5) * H * 5,
  r: Math.random() < 0.82 ? 0.4 : (Math.random() < 0.6 ? 0.8 : 1.3),
  o: 0.08 + Math.random() * 0.28,
}));
world.append("g").attr("id", "bg-stars")
  .selectAll("circle").data(bgStars).enter().append("circle")
  .attr("cx", d => d.x).attr("cy", d => d.y)
  .attr("r",  d => d.r).attr("fill", "white").attr("opacity", d => d.o);

// ── Data: nodes & links ────────────────────────────────────────────────────
const nodes = GRAPH_DATA.nodes.map(n => ({ ...n }));
const links = GRAPH_DATA.links.map(l => ({ ...l }));

// Compute degree
const degMap = {};
nodes.forEach(n => { degMap[n.id] = 0; });
links.forEach(l => {
  degMap[l.source] = (degMap[l.source] || 0) + 1;
  degMap[l.target] = (degMap[l.target] || 0) + 1;
});
nodes.forEach(n => {
  n.degree = degMap[n.id] || 0;
  // radius 4–20 px based on degree
  n.radius = 4 + Math.pow(n.degree, 0.55) * 2.4;
});

const nodeById = new Map(nodes.map(n => [n.id, n]));

// Adjacency index  id → [{edgeType, neighborId, color, dashes, dir}]
const adj = new Map(nodes.map(n => [n.id, []]));
links.forEach(l => {
  adj.get(l.source)?.push({ edgeType: l.edge_type, neighborId: l.target, color: l.color, dashes: l.dashes, dir: "out" });
  adj.get(l.target)?.push({ edgeType: l.edge_type, neighborId: l.source, color: l.color, dashes: l.dashes, dir: "in"  });
});

// ── Force simulation ───────────────────────────────────────────────────────
const sim = d3.forceSimulation(nodes)
  .force("charge",  d3.forceManyBody().strength(d => -(55 + d.radius * 9)).theta(0.88))
  .force("center",  d3.forceCenter(0, 0).strength(0.018))
  .force("collide", d3.forceCollide(d => d.radius + 7).strength(0.75).iterations(2))
  .alphaDecay(0.0008)
  .velocityDecay(0.36)
  .on("tick", ticked);

// When simulation naturally stops, give it a gentle nudge so stars keep drifting
sim.on("end", () => sim.alphaTarget(0.04).restart());

// ── Layers ─────────────────────────────────────────────────────────────────
const linkLayer = world.append("g").attr("id", "links");
const nodeLayer = world.append("g").attr("id", "nodes");

// ── Draw concept stars ─────────────────────────────────────────────────────
const nodeEl = nodeLayer.selectAll(".concept")
  .data(nodes).enter().append("g")
  .attr("class", "concept")
  .style("cursor", "pointer")
  .on("click",     onNodeClick)
  .on("mouseover", onHover)
  .on("mouseout",  onHoverOut);

// Outer halo (very large, very soft)
nodeEl.append("circle").attr("class", "star-halo")
  .attr("r", d => d.radius * 4.5)
  .attr("fill", d => d.color)
  .attr("opacity", 0.05)
  .attr("pointer-events", "none")
  .attr("filter", "url(#star-glow)");

// Mid glow
nodeEl.append("circle").attr("class", "star-glow")
  .attr("r", d => d.radius * 2.2)
  .attr("fill", d => d.color)
  .attr("opacity", 0.11)
  .attr("pointer-events", "none");

// Main disc (twinkling)
nodeEl.append("circle").attr("class", "star-body")
  .attr("r", d => d.radius)
  .attr("fill", d => d.color)
  .attr("pointer-events", "all");

// Bright hot core
nodeEl.append("circle").attr("class", "star-core")
  .attr("r", d => Math.max(1.2, d.radius * 0.28))
  .attr("fill", "white")
  .attr("opacity", 0.88)
  .attr("pointer-events", "none");

// Selection ring (hidden until selected)
nodeEl.append("circle").attr("class", "star-ring")
  .attr("r", d => d.radius + 8)
  .attr("fill", "none")
  .attr("stroke", d => d.color)
  .attr("stroke-width", 1.4)
  .attr("opacity", 0)
  .attr("pointer-events", "none");

// Randomise twinkle timing per star (using char codes so it's deterministic)
nodeEl
  .style("--td", d => `${2.4 + (d.id.length % 28) * 0.13}s`)
  .style("--dl", d => `${((d.id.charCodeAt(0) || 0) % 38) * 0.09}s`);

// ── Tick handler ──────────────────────────────────────────────────────────
function ticked() {
  nodeEl.attr("transform", d => `translate(${d.x},${d.y})`);
  // Edge lines track node positions via data references (src/tgt are node objs)
  linkLayer.selectAll(".el-glow, .el-main")
    .attr("x1", d => d.src.x).attr("y1", d => d.src.y)
    .attr("x2", d => d.tgt.x).attr("y2", d => d.tgt.y);
}

// ── Stats ──────────────────────────────────────────────────────────────────
document.getElementById("stat-n").textContent = nodes.length;
document.getElementById("stat-e").textContent = links.length;

// ── Tooltip ────────────────────────────────────────────────────────────────
const tip = document.getElementById("tooltip");

function onHover(event, d) {
  tip.style.display = "block";
  tip.style.left = (event.clientX + 18) + "px";
  tip.style.top  = (event.clientY - 12) + "px";
  tip.innerHTML =
    `<strong>${d.label}</strong>` +
    `<span class="dim">${d.degree} connections · ${d.pages} page ref${d.pages !== 1 ? "s" : ""}</span>`;
  if (selectedId !== d.id)
    d3.select(this).select(".star-halo").attr("opacity", 0.20);
}
function onHoverOut(event, d) {
  tip.style.display = "none";
  if (selectedId !== d.id)
    d3.select(this).select(".star-halo").attr("opacity", 0.05);
}

// ── Selection ──────────────────────────────────────────────────────────────
function onNodeClick(event, d) {
  event.stopPropagation();
  selectedId === d.id ? deselect() : selectNode(d);
}

function selectNode(d) {
  selectedId = d.id;

  const conns   = getVisibleConns(d.id);
  const connIds = new Set([d.id, ...conns.map(a => a.neighborId)]);

  // Dim unconnected
  nodeEl.attr("opacity", n => connIds.has(n.id) ? 1 : 0.035);

  // Halos
  nodeEl.selectAll(".star-halo").attr("opacity", function() {
    const nd = d3.select(this.parentNode).datum();
    return nd.id === d.id ? 0.38 : (connIds.has(nd.id) ? 0.10 : 0.01);
  });

  // Pulsing ring on selected
  nodeEl.selectAll(".star-ring")
    .attr("opacity",     nd => nd.id === d.id ? 0.7  : 0)
    .attr("class",       nd => nd.id === d.id ? "star-ring star-ring-sel" : "star-ring");

  drawEdges(d, conns);
  zoomTo(d);
  showSidebar(d, conns);
}

function deselect() {
  selectedId = null;
  nodeEl.attr("opacity", 1);
  nodeEl.selectAll(".star-halo").attr("opacity", 0.05);
  nodeEl.selectAll(".star-ring").attr("opacity", 0).attr("class", "star-ring");
  linkLayer.selectAll(".el-glow, .el-main").remove();
  hideSidebar();
}

function getVisibleConns(id) {
  return (adj.get(id) || []).filter(a => visibleTypes.has(a.edgeType));
}

// ── Zoom to a node ─────────────────────────────────────────────────────────
function zoomTo(d) {
  const sbW   = 268;                        // sidebar width
  const cx    = sbW + (W - sbW) / 2;       // centre of remaining canvas
  const scale = Math.min(4.0, Math.max(1.8, 9 / Math.sqrt(d.degree + 1)));
  svg.transition().duration(780).ease(d3.easeCubicInOut)
    .call(zoom.transform,
      d3.zoomIdentity
        .translate(cx - d.x * scale, H / 2 - d.y * scale)
        .scale(scale));
}

// ── Edge drawing ───────────────────────────────────────────────────────────
function drawEdges(d, conns) {
  linkLayer.selectAll(".el-glow, .el-main").remove();

  const edgeData = conns.map(a => ({
    src:      nodeById.get(d.id),
    tgt:      nodeById.get(a.neighborId),
    edgeType: a.edgeType,
    color:    a.color || EDGE_META[a.edgeType]?.color || "#888",
    dashes:   a.dashes,
  })).filter(e => e.src && e.tgt);

  if (!edgeData.length) return;

  // Glow layer (wide + blurred)
  linkLayer.selectAll(".el-glow").data(edgeData).enter().append("line")
    .attr("class", "el-glow")
    .attr("x1", e => e.src.x).attr("y1", e => e.src.y)
    .attr("x2", e => e.tgt.x).attr("y2", e => e.tgt.y)
    .attr("stroke", e => e.color)
    .attr("stroke-width", 6)
    .attr("opacity", 0)
    .attr("filter", "url(#line-glow)")
    .transition().duration(280)
    .attr("opacity", 0.18);

  // Main line (crisp, optionally animated dashes)
  linkLayer.selectAll(".el-main").data(edgeData).enter().append("line")
    .attr("class", e => "el-main" + (Array.isArray(e.dashes) ? " edge-flow" : ""))
    .attr("x1", e => e.src.x).attr("y1", e => e.src.y)
    .attr("x2", e => e.tgt.x).attr("y2", e => e.tgt.y)
    .attr("stroke", e => e.color)
    .attr("stroke-width", 1.6)
    .attr("stroke-dasharray", e => Array.isArray(e.dashes) ? e.dashes.join(",") : null)
    .attr("opacity", 0)
    .transition().duration(280)
    .attr("opacity", 0.88);
}

function refreshEdges() {
  if (!selectedId) return;
  const d = nodeById.get(selectedId);
  if (!d) return;
  const conns   = getVisibleConns(d.id);
  const connIds = new Set([d.id, ...conns.map(a => a.neighborId)]);
  nodeEl.attr("opacity", n => connIds.has(n.id) ? 1 : 0.035);
  drawEdges(d, conns);
  refreshNeighborList(d, conns);
}

// ── Sidebar ────────────────────────────────────────────────────────────────
const sidebar = document.getElementById("sidebar");
document.getElementById("sb-close").onclick = deselect;

// Build edge-type toggles once
const toggleList = document.getElementById("toggle-list");
Object.entries(EDGE_META).forEach(([etype, meta]) => {
  const lbl = document.createElement("label");
  lbl.className = "edge-toggle";
  lbl.innerHTML =
    `<input type="checkbox" checked data-etype="${etype}">` +
    `<span class="t-dot" style="background:${meta.color}"></span>` +
    `<span class="t-text">${meta.icon} ${meta.label}</span>`;
  lbl.querySelector("input").onchange = function() {
    this.checked ? visibleTypes.add(etype) : visibleTypes.delete(etype);
    refreshEdges();
  };
  toggleList.appendChild(lbl);
});

function showSidebar(d, conns) {
  document.getElementById("sb-name").textContent    = d.label;
  document.getElementById("sb-degree").textContent  = d.degree;
  document.getElementById("sb-pages").textContent   = d.pages;
  document.getElementById("sb-chapter").textContent = d.chapter || "–";
  refreshNeighborList(d, conns);
  sidebar.classList.add("open");
}
function hideSidebar() { sidebar.classList.remove("open"); }

function refreshNeighborList(d, conns) {
  const nb = document.getElementById("sb-neighbors");
  nb.innerHTML = "";

  // Group by edge type
  const groups = {};
  conns.forEach(a => {
    (groups[a.edgeType] = groups[a.edgeType] || []).push(a);
  });

  if (!Object.keys(groups).length) {
    nb.innerHTML = `<div style="padding:14px 18px;font-size:11px;color:#484f58;">
      No connections with current filters.</div>`;
    return;
  }

  Object.entries(groups).forEach(([etype, items]) => {
    const meta = EDGE_META[etype] || { label: etype, color: "#888", icon: "•" };
    const gh = document.createElement("div");
    gh.className = "nb-group";
    gh.style.color = meta.color;
    gh.textContent = `${meta.icon}  ${meta.label}`;
    nb.appendChild(gh);

    items.forEach(a => {
      const nd = nodeById.get(a.neighborId);
      if (!nd) return;
      const el = document.createElement("div");
      el.className = "nb-item";
      el.innerHTML = `<span class="nb-dot" style="background:${nd.color}"></span>${nd.label}`;
      el.onclick = () => selectNode(nd);
      nb.appendChild(el);
    });
  });
}

// ── Search ─────────────────────────────────────────────────────────────────
const searchInput = document.getElementById("search-input");
const searchDrop  = document.getElementById("search-dropdown");
let dropItems     = [];
let activeIdx     = -1;

searchInput.addEventListener("input", () => {
  const q = searchInput.value.trim().toLowerCase();
  searchDrop.style.display = "none";
  activeIdx = -1;
  if (q.length < 1) return;

  dropItems = nodes
    .filter(n => n.label.toLowerCase().includes(q))
    .sort((a, b) => {
      const aStarts = a.label.toLowerCase().startsWith(q) ? 0 : 1;
      const bStarts = b.label.toLowerCase().startsWith(q) ? 0 : 1;
      return aStarts - bStarts || a.label.length - b.label.length;
    })
    .slice(0, 12);

  if (!dropItems.length) return;
  searchDrop.innerHTML = dropItems.map((n, i) =>
    `<div class="search-item" data-idx="${i}" data-id="${n.id}">
       <span>${n.label}</span>
       <span class="deg">${n.degree}</span>
     </div>`
  ).join("");
  searchDrop.style.display = "block";
});

searchDrop.addEventListener("click", e => {
  const item = e.target.closest(".search-item");
  if (!item) return;
  const nd = nodeById.get(item.dataset.id);
  if (!nd) return;
  searchInput.value = nd.label;
  searchDrop.style.display = "none";
  selectNode(nd);
});

// Keyboard nav in dropdown
searchInput.addEventListener("keydown", e => {
  const items = searchDrop.querySelectorAll(".search-item");
  if (e.key === "Escape") { searchDrop.style.display = "none"; searchInput.blur(); return; }
  if (!items.length) return;
  if (e.key === "ArrowDown") {
    e.preventDefault();
    activeIdx = (activeIdx + 1) % items.length;
    items.forEach((el, i) => el.classList.toggle("active", i === activeIdx));
  } else if (e.key === "ArrowUp") {
    e.preventDefault();
    activeIdx = (activeIdx - 1 + items.length) % items.length;
    items.forEach((el, i) => el.classList.toggle("active", i === activeIdx));
  } else if (e.key === "Enter" && activeIdx >= 0) {
    const nd = nodeById.get(dropItems[activeIdx].id);
    if (nd) { searchInput.value = nd.label; searchDrop.style.display = "none"; selectNode(nd); }
  }
});

document.addEventListener("click", e => {
  if (!document.getElementById("search-wrap").contains(e.target))
    searchDrop.style.display = "none";
});

// Escape also deselects
document.addEventListener("keydown", e => {
  if (e.key === "Escape" && selectedId) deselect();
});
</script>
</body>
</html>"""


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    data = build_data()
    n_concepts = len(data["nodes"])
    n_edges    = len(data["links"])

    html = HTML.replace("__GRAPH_DATA__", json.dumps(data))

    OUTPUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_HTML.write_text(html, encoding="utf-8")

    print(f"Saved    → {OUTPUT_HTML}")
    print(f"Concepts : {n_concepts}")
    print(f"Edges    : {n_edges}  (concept-concept only)")
    print(f"Open     : file://{OUTPUT_HTML.resolve()}")


if __name__ == "__main__":
    main()
