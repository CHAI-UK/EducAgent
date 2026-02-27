"use strict";
const pptxgen = require("pptxgenjs");
const pres = new pptxgen();
pres.layout = "LAYOUT_16x9";   // 10" × 5.625"
pres.title  = "EducAgent Update";
pres.author = "EducAgent Project";

// ── Palette ────────────────────────────────────────────────────────────────────
const C = {
  bg:     "0B1017",   // deep space
  card:   "0D1117",   // card bg (same family)
  card2:  "161B22",   // card fill
  border: "21262D",   // borders / dividers
  acc:    "58A6FF",   // space blue
  green:  "3FB950",   // success / done
  orange: "F0883E",   // action / next
  purple: "8957E5",   // prerequisite
  yellow: "D29922",   // see-also / edges
  red:    "DA3633",   // confused
  teal:   "1ABC9C",   // applied-to
  t1:     "E6EDF3",   // text primary
  t2:     "8B949E",   // text secondary
  t3:     "484F58",   // text dim
};

// ── Shared helpers ─────────────────────────────────────────────────────────────
const setBg = s => { s.background = { color: C.bg }; };

// Thin accent top & bottom bars (give each slide a colour identity)
function framSlide(slide, color) {
  slide.addShape(pres.shapes.RECTANGLE, { x:0, y:0,       w:10, h:0.055, fill:{color}, line:{color} });
  slide.addShape(pres.shapes.RECTANGLE, { x:0, y:5.57,    w:10, h:0.055, fill:{color}, line:{color} });
}

// Horizontal rule
function hr(slide, y, x=0.35, w=9.3) {
  slide.addShape(pres.shapes.LINE, { x, y, w, h:0, line:{color:C.border, width:0.5} });
}

// Vertical rule
function vr(slide, x, y=0.62, h=4.88) {
  slide.addShape(pres.shapes.LINE, { x, y, w:0, h, line:{color:C.border, width:0.5} });
}

// Card with optional left-accent bar
function card(slide, x, y, w, h, accentColor=null, opts={}) {
  slide.addShape(pres.shapes.RECTANGLE, {
    x, y, w, h,
    fill: { color: C.card2 },
    line: { color: C.border, width: 0.5 },
    shadow: { type:"outer", blur:6, offset:2, angle:135, color:"000000", opacity:0.25 },
    ...opts,
  });
  if (accentColor) {
    slide.addShape(pres.shapes.RECTANGLE, {
      x, y, w:0.05, h,
      fill:{ color:accentColor }, line:{ color:accentColor, width:0 },
    });
  }
}

// Numbered step pill  (small circle with number)
function numPill(slide, x, y, num, color) {
  slide.addShape(pres.shapes.OVAL, {
    x, y, w:0.28, h:0.28,
    fill:{ color }, line:{ color, width:0 },
  });
  slide.addText(String(num), {
    x, y, w:0.28, h:0.28,
    fontSize:8, bold:true, color:C.bg, align:"center", valign:"middle", margin:0,
  });
}

// Scattered ambient dots — gives each slide a "deep space" feeling
function ambientStars(slide) {
  const positions = [
    [8.8,0.9,1.2],[9.4,2.1,0.8],[9.2,3.8,1.5],[8.6,5.0,0.9],
    [0.1,1.4,1.0],[0.08,3.2,0.7],[0.12,4.7,1.3],
  ];
  for (const [px,py,op] of positions) {
    slide.addShape(pres.shapes.OVAL, {
      x:px, y:py, w:0.04, h:0.04,
      fill:{ color:"FFFFFF", transparency: Math.round(100 - op*50) },
      line:{ color:"FFFFFF", width:0 },
    });
  }
}


// ═══════════════════════════════════════════════════════════════════════════════
// SLIDE 1 — Project Summary
// ═══════════════════════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  setBg(s); framSlide(s, C.acc); ambientStars(s);

  // Wordmark
  s.addText([
    { text:"EDUC", options:{ bold:true, color:C.acc } },
    { text:"AGENT", options:{ bold:true, color:C.t1 } },
  ], { x:0.35, y:0.13, w:4, h:0.44, fontSize:26, charSpacing:6, margin:0 });

  s.addText("Project Update  ·  Theme Meeting  ·  Feb 2026", {
    x:0.35, y:0.55, w:6, h:0.22, fontSize:9, color:C.t3, charSpacing:1.5, margin:0,
  });

  s.addText("Feb 2026", { x:8.9, y:0.22, w:0.75, h:0.2, fontSize:9, color:C.t3, align:"right", margin:0 });

  hr(s, 0.82);

  // ── Left: What is EducAgent? ──────────────────────────────
  s.addText("What is EducAgent?", {
    x:0.35, y:0.92, w:5.5, h:0.28, fontSize:13, bold:true, color:C.acc, margin:0,
  });

  const vision = [
    { text:"An AI tutor for Pearl's Causality (2009) — answering questions like \"what do I need to know before the back-door criterion?\"", options:{ bullet:true, color:C.t1, fontSize:10.5, breakLine:true, paraSpaceAfter:8 } },
    { text:"Powered by a GraphRAG architecture — the agent reasons over a structured knowledge graph, not just raw text chunks", options:{ bullet:true, color:C.t1, fontSize:10.5, breakLine:true, paraSpaceAfter:8 } },
    { text:"Adapts explanations to the learner's background: statistician, ML engineer, economist, or clinician", options:{ bullet:true, color:C.t1, fontSize:10.5, breakLine:true, paraSpaceAfter:8 } },
    { text:"Foundation: a causality concept graph extracted from the book's TOC and Subject Index — built this cycle", options:{ bullet:true, color:C.t2, fontSize:10, breakLine:true } },
  ];
  s.addText(vision, { x:0.35, y:1.24, w:5.35, h:2.0, margin:0, valign:"top" });

  // After Feb plan
  s.addText("Plan After Feb:", {
    x:0.35, y:3.3, w:5.35, h:0.24, fontSize:10.5, bold:true, color:C.orange, margin:0,
  });
  s.addText([
    { text:"Deliver a working prototype that can:", options:{ color:C.t2, fontSize:10, breakLine:true, paraSpaceAfter:4 } },
    { text:"(1) answer prerequisite questions via graph traversal", options:{ bullet:true, indentLevel:1, color:C.t1, fontSize:10, breakLine:true, paraSpaceAfter:3 } },
    { text:"(2) retrieve relevant section content (RAG)", options:{ bullet:true, indentLevel:1, color:C.t1, fontSize:10, breakLine:true, paraSpaceAfter:3 } },
    { text:"(3) tailor explanations to a user-defined background profile", options:{ bullet:true, indentLevel:1, color:C.t1, fontSize:10 } },
  ], { x:0.35, y:3.56, w:5.35, h:1.2, margin:0, valign:"top" });

  // ── Vertical divider ──────────────────────────────────────
  vr(s, 5.95, 0.92, 3.9);

  // ── Right: Progress + Agreed Actions ─────────────────────
  s.addText("Progress This Cycle", {
    x:6.1, y:0.92, w:3.55, h:0.28, fontSize:13, bold:true, color:C.t1, margin:0,
  });

  const progress = [
    { label:"Knowledge graph spec & schema",                     done:true  },
    { label:"TOC parser → 240 Section nodes",                    done:true  },
    { label:"Subject Index parser → 613 Concept nodes",          done:true  },
    { label:"9 edge types, curated relations (>50 pairs)",       done:true  },
    { label:"D3.js 'Slipways Universe' visualisation (uni.html)",done:true  },
  ];

  progress.forEach(({ label, done }, i) => {
    const y = 1.27 + i * 0.34;
    s.addShape(pres.shapes.OVAL, {
      x:6.1, y:y+0.06, w:0.13, h:0.13,
      fill:{ color: done ? C.green : C.border },
      line:{ color: done ? C.green : C.border, width:0 },
    });
    s.addText(label, {
      x:6.32, y, w:3.35, h:0.28,
      fontSize:9.5, color: done ? C.t1 : C.t2, margin:0,
    });
  });

  s.addText("Agreed Actions", {
    x:6.1, y:3.08, w:3.55, h:0.26, fontSize:11, bold:true, color:C.orange, margin:0,
  });
  const agreed = [
    "Build concept knowledge graph  ✓",
    "Build interactive visualisation  ✓",
    "Define next-phase scope (see Slide 3)",
  ];
  agreed.forEach((a, i) => {
    s.addText("→  " + a, {
      x:6.1, y:3.36 + i*0.3, w:3.55, h:0.26,
      fontSize:9.5, color: i < 2 ? C.green : C.t2, margin:0,
    });
  });

  // ── Bottom stat strip ─────────────────────────────────────
  s.addShape(pres.shapes.RECTANGLE, {
    x:0, y:4.78, w:10, h:0.78, fill:{color:C.card2}, line:{color:C.border, width:0.5},
  });

  const stats = [
    { val:"853",   label:"Total Nodes",     color:C.acc    },
    { val:"3,533", label:"Total Edges",     color:C.green  },
    { val:"613",   label:"Concept Stars",   color:C.purple },
    { val:"240",   label:"TOC Sections",    color:C.yellow },
    { val:"9",     label:"Edge Types",      color:C.orange },
  ];
  stats.forEach(({ val, label, color }, i) => {
    const x = 0.15 + i * 1.96;
    s.addText(val,   { x, y:4.83, w:1.9, h:0.34, fontSize:22, bold:true, color, align:"center", margin:0 });
    s.addText(label, { x, y:5.16, w:1.9, h:0.18, fontSize:7.5, color:C.t3, align:"center", charSpacing:0.8, margin:0 });
  });
}


// ═══════════════════════════════════════════════════════════════════════════════
// SLIDE 2 — Results
// ═══════════════════════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  setBg(s); framSlide(s, C.green); ambientStars(s);

  s.addText("Results: Concept Graph + Slipways Universe", {
    x:0.35, y:0.12, w:9.3, h:0.38, fontSize:18, bold:true, color:C.t1, margin:0,
  });
  hr(s, 0.55);

  // ── Left: Build pipeline ──────────────────────────────────
  s.addText("HOW THE GRAPH WAS BUILT", {
    x:0.35, y:0.63, w:4.6, h:0.22, fontSize:9, bold:true, color:C.t3, charSpacing:1.5, margin:0,
  });

  const steps = [
    { num:1, color:C.acc,    title:"Parse TOC → Section Nodes",
      body:"240 sections (11 chapters, depth 0–2). Each node has chapter, page range, and hierarchy. Linked by NEXT_IN_SEQUENCE edges." },
    { num:2, color:C.green,  title:"Parse Subject Index → Concept Nodes",
      body:"613 concepts from the 6-page index. Includes page refs, parent/child entries, 'see also' links, and 'of X' sub-entries." },
    { num:3, color:C.purple, title:"Connect Concepts ↔ Sections + Concepts",
      body:"COVERED_IN (concept → section, via pages). Curated PREREQUISITE_OF (28 pairs), ALIAS (9), COMMONLY_CONFUSED (10), SEE_ALSO (13)." },
    { num:4, color:C.orange, title:"Export & Visualise",
      body:"NetworkX DiGraph → .pkl + .json. Visualised with D3.js force simulation as the 'Slipways Universe' (uni.html)." },
  ];

  steps.forEach(({ num, color, title, body }, i) => {
    const y = 0.92 + i * 1.12;
    card(s, 0.35, y, 4.6, 0.98, color);
    numPill(s, 0.5, y + 0.08, num, color);
    s.addText(title, {
      x:0.9, y:y+0.07, w:3.95, h:0.26,
      fontSize:10, bold:true, color:C.t1, margin:0,
    });
    s.addText(body, {
      x:0.52, y:y+0.38, w:4.32, h:0.55,
      fontSize:8.5, color:C.t2, margin:0,
    });
  });

  // ── Divider ───────────────────────────────────────────────
  vr(s, 5.22, 0.63, 4.72);

  // ── Right: Visualisation ──────────────────────────────────
  s.addText("THE SLIPWAYS UNIVERSE (uni.html)", {
    x:5.37, y:0.63, w:4.28, h:0.22, fontSize:9, bold:true, color:C.t3, charSpacing:1.5, margin:0,
  });

  // Screenshot placeholder
  s.addShape(pres.shapes.RECTANGLE, {
    x:5.37, y:0.92, w:4.28, h:2.72,
    fill:{ color:"080D18" }, line:{ color:C.acc, width:1 },
  });
  // Decorative inner dots (fake stars)
  [
    [5.7,1.2],[6.2,1.8],[6.9,1.4],[7.5,2.1],[8.1,1.6],[8.7,2.4],
    [5.9,2.5],[7.0,2.8],[7.8,2.2],[9.0,1.9],[6.5,3.3],[8.4,3.1],
  ].forEach(([px, py]) => {
    s.addShape(pres.shapes.OVAL, {
      x:px, y:py, w:0.05, h:0.05,
      fill:{ color:"4A7AB5" }, line:{ color:"4A7AB5", width:0 },
    });
  });
  s.addText("[ Insert screenshot / demo video ]", {
    x:5.37, y:0.92, w:4.28, h:2.72,
    fontSize:11, color:"2A5080", align:"center", valign:"middle", margin:0, bold:true,
  });
  s.addText("uni.html", {
    x:5.37, y:3.44, w:4.28, h:0.18,
    fontSize:8, color:"2A5080", align:"center", margin:0,
  });

  // Feature list
  const features = [
    { icon:"★", col:C.acc,    text:"613 stars = concepts  ·  size ∝ connections, colour = chapter" },
    { icon:"◎", col:"4A9EFF", text:"Nebulas = book sections (TOC hierarchy, dashed ring style)" },
    { icon:"↝", col:C.yellow, text:"Animated particle flows trace connection type (6 edge types)" },
    { icon:"⌕", col:C.green,  text:"Search + entity & edge-type filters in HUD panel" },
    { icon:"⟳", col:C.t2,     text:"Lazy-load architecture — activate full 853-node graph on demand" },
  ];

  features.forEach(({ icon, col, text }, i) => {
    s.addText([
      { text: icon + "  ", options:{ bold:true, color:col } },
      { text,               options:{ color:C.t2 } },
    ], {
      x:5.37, y:3.68 + i*0.36, w:4.28, h:0.32,
      fontSize:9.5, margin:0, valign:"middle",
    });
  });
}


// ═══════════════════════════════════════════════════════════════════════════════
// SLIDE 3 — Discussion & Next Actions
// ═══════════════════════════════════════════════════════════════════════════════
{
  const s = pres.addSlide();
  setBg(s); framSlide(s, C.orange); ambientStars(s);

  s.addText("Questions to Discuss  ·  Proposed Actions", {
    x:0.35, y:0.12, w:9.3, h:0.38, fontSize:18, bold:true, color:C.t1, margin:0,
  });
  hr(s, 0.55);

  // ── Left: Questions ───────────────────────────────────────
  s.addText("OPEN QUESTIONS", {
    x:0.35, y:0.63, w:4.6, h:0.22, fontSize:9, bold:true, color:C.t3, charSpacing:1.5, margin:0,
  });

  const questions = [
    { color:C.acc,
      q:"How to scale PREREQUISITE_OF edges?",
      d:"28 pairs are manually curated. Should we use an LLM to evaluate all ~37,000 concept pairs and extract edges automatically? What's the quality threshold?" },
    { color:C.purple,
      q:"What's the delivery scope post-Feb?",
      d:"Full adaptive tutor interface, or a demonstrable GraphRAG + student model prototype? What concrete output is expected by the next theme meeting?" },
    { color:C.green,
      q:"Student model: self-report vs quiz-inferred?",
      d:"Onboarding quiz that asks background questions, or adaptive inference as the student interacts? Which fits the timeline and evaluation criteria?" },
    { color:C.yellow,
      q:"Tech stack: stay on NetworkX or migrate to Neo4j?",
      d:"NetworkX is fast for prototyping. Neo4j enables Cypher queries and graph algorithms at scale. Worth migrating now, or prototype first?" },
  ];

  questions.forEach(({ color, q, d }, i) => {
    const y = 0.92 + i * 1.12;
    card(s, 0.35, y, 4.6, 1.0, color);
    s.addText(q, {
      x:0.52, y:y+0.08, w:4.28, h:0.26, fontSize:10, bold:true, color:C.t1, margin:0,
    });
    s.addText(d, {
      x:0.52, y:y+0.37, w:4.32, h:0.57, fontSize:8.5, color:C.t2, margin:0,
    });
  });

  // ── Divider ───────────────────────────────────────────────
  vr(s, 5.22, 0.63, 4.72);

  // ── Right: Actions ────────────────────────────────────────
  s.addText("BY NEXT THEME MEETING", {
    x:5.37, y:0.63, w:4.28, h:0.22, fontSize:9, bold:true, color:C.t3, charSpacing:1.5, margin:0,
  });

  const actions = [
    { color:C.purple, tag:"Graph",
      label:"LLM prerequisite edge extraction",
      d:"Prompt design + run on top 50 concept pairs. Manual spot-check of quality before bulk expansion." },
    { color:C.acc,    tag:"RAG",
      label:"RAG pipeline prototype",
      d:"Qdrant collection per chapter, embeddings at subsection granularity, test retrieval on sample questions." },
    { color:C.green,  tag:"Model",
      label:"Student profiling spec",
      d:"Define fields (background, role, mastery per concept) and onboarding flow. No implementation yet — design doc." },
    { color:C.yellow, tag:"Demo",
      label:"Demo recording of uni.html",
      d:"Screen-capture walkthrough of the Slipways visualisation for supervisor / CHAI group sharing." },
    { color:C.orange, tag:"Plan",
      label:"Agree March milestone",
      d:"Confirm with supervisor: what is the concrete deliverable for next theme meeting? Set measurable criteria." },
  ];

  actions.forEach(({ color, tag, label, d }, i) => {
    const y = 0.92 + i * 0.9;
    card(s, 5.37, y, 4.28, 0.78, color);

    // Tag chip (simple rect, avoids rounded-rect accent issue)
    s.addShape(pres.shapes.RECTANGLE, {
      x:9.2, y:y+0.08, w:0.38, h:0.18,
      fill:{ color, transparency:65 }, line:{ color, width:0.3 },
    });
    s.addText(tag, {
      x:9.2, y:y+0.08, w:0.38, h:0.18,
      fontSize:6, bold:true, color, align:"center", valign:"middle", margin:0,
    });

    s.addText(label, {
      x:5.54, y:y+0.06, w:3.56, h:0.26, fontSize:10, bold:true, color:C.t1, margin:0,
    });
    s.addText(d, {
      x:5.54, y:y+0.34, w:4.0, h:0.38, fontSize:8.5, color:C.t2, margin:0,
    });
  });
}


// ── Write ──────────────────────────────────────────────────────────────────────
pres.writeFile({ fileName: "EducAgent_Update.pptx" })
  .then(() => console.log("Done → EducAgent_Update.pptx"));
