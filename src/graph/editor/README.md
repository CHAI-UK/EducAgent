# ECI Graph Editor

A browser-based editor for the ECI (Elements of Causal Inference) concept knowledge graph.
Lets contributors visually explore, edit, and export `eci_graph.json` without touching JSON by hand.

## Quick Start

```bash
# From the project root
uvicorn server:app --reload --port 8765
```

Then open **http://localhost:8765** in your browser.

> **Requires:** `fastapi`, `uvicorn` — both available in the `edu` conda environment.

---

## Interface Overview

```
┌──────────────────────────────────────────────────────────────┐
│ TOOLBAR  [Search…]  N-HOP ±  +Add Node  ⇄Merge  ↓Save  ⬇Export │
├────────────────────┬─────────────────────────────────────────┤
│  NODE EXPLORER     │  GRAPH CANVAS                           │
│  ─────────────     │                                         │
│  [filter text]     │   (D3 force-directed graph)             │
│  [type ▾]          │                                         │
│  • concept nodes   │   [Node Info Panel]  top-right          │
│  § section nodes   │   [Legend]           bottom-left        │
│  ◆ category nodes  │                                         │
└────────────────────┴─────────────────────────────────────────┘
```

### Left Panel — Node Explorer
- **Filter box**: type to search by label or ID
- **Type dropdown**: filter to Concept / Section / Category only
- Click any row to select that node and display its ego-graph on the canvas

### Toolbar Search (top bar)
- Type to search across all nodes; use **↑ ↓** to navigate results, **Enter** to select
- Selecting a node centers it on the canvas

### N-Hop Control
- Controls how many hops away from the selected node are shown
- **N=1** (default): only directly connected neighbors
- **N=2**: neighbors-of-neighbors too; up to **N=5**
- Use the **−/+** buttons or type directly

### Node Info Panel (top-right of canvas)
Appears when a node is selected. Shows label, type, ID, chapter, in/out edge counts, and quick-action buttons: **Edit**, **+ Edge**, **Delete**.

---

## Operations

### Node Operations
| Action | How |
|---|---|
| Select node | Click list row, or use toolbar search |
| Navigate to neighbor | Click any neighbor node in the graph |
| Edit label / type | Right-click node → *Edit node*, or Info Panel → *Edit* |
| Add edge from node | Right-click node → *Add edge from this* |
| Add edge to node | Right-click node → *Add edge to this* |
| Delete node | Right-click node → *Delete node*, or Info Panel → *Delete* |
| Add new node | Toolbar **+ Add Node** button |
| Merge two nodes | Toolbar **⇄ Merge** button |
| Drag node | Click and drag any node to reposition |

### Edge Operations
| Action | How |
|---|---|
| Change edge type | Click the edge line → *Change edge type* |
| Delete edge | Click the edge line → *Delete edge* |
| Hover edge | Highlights and shows full opacity |

### Merge Nodes
Opens a dialog to pick **Node A** (kept) and **Node B** (removed).
All edges attached to B are reattached to A; self-loops and duplicate edges are automatically removed.

---

## Saving & Exporting

| Button | Effect |
|---|---|
| **↓ Save** | Overwrites `src/graph/output/eci_graph.json` on the server |
| **⬇ Export** | Downloads `eci_graph_edited.json` to your local machine |
| **Ctrl+S** | Same as Save |

A small orange dot on the Save button indicates unsaved changes.
Closing the tab with unsaved changes triggers a browser confirmation prompt.

---

## Node Search in Modals
All node-selection dropdowns (Add Edge, Merge) include a **filter input** above the list.
Type to narrow down the 189+ nodes — the select list updates live.

---

## Keyboard Shortcuts

| Key | Action |
|---|---|
| `Ctrl+S` | Save graph |
| `Escape` | Close modal / context menu / search dropdown |
| `↑ / ↓` | Navigate toolbar search results |
| `Enter` | Confirm toolbar search selection |

---

## Graph Format

The editor reads and writes `src/graph/output/eci_graph.json` which follows this schema:

```jsonc
{
  "directed": true,
  "multigraph": false,
  "graph": {},
  "nodes": [
    {
      "id": "backdoor_criterion",   // unique slug (never changed by editor)
      "type": "concept",            // "concept" | "section" | "category"
      "label": "Backdoor Criterion",
      "short_label": "Backdoor Criterion",
      "chapter": 4,
      "color": "#3fb950",           // preserved as-is
      "shape": "dot",               // preserved as-is
      "size": 10,                   // preserved as-is
      "page_refs": [88, 91]
    }
  ],
  "edges": [
    {
      "source": "backdoor_criterion",
      "target": "d_separation",
      "edge_type": "PREREQUISITE_OF",  // see edge types below
      "color": "#ff6b6b",
      "width": 1.5,
      "dashes": false
    }
  ]
}
```

### Node Types
| Type | Color | Meaning |
|---|---|---|
| `concept` | Teal | A causal inference concept |
| `section` | Violet | A book section (§1, §2.3, …) |
| `category` | Amber | A high-level topic cluster |

### Edge Types
| Type | Color | Meaning |
|---|---|---|
| `PREREQUISITE_OF` | Red | A must be understood before B |
| `COVERED_IN` | Teal | Concept covered in that section |
| `NEXT_IN_SEQUENCE` | Blue | Sequential ordering of sections |
| `SUBTOPIC_OF` | Purple | A is a subtopic of B |
| `RELATED_TO_SEE_ALSO` | Yellow | Related, worth reading together |
| `RELATED_TO_ALIAS` | Green | Same concept, different name |
| `COMMONLY_CONFUSED` | Orange | Frequently confused with each other |

---

## File Structure

```
src/graph/editor/
├── server.py      # FastAPI backend (load/save JSON, serve static files)
├── index.html     # Complete single-page application (D3.js, vanilla JS/CSS)
└── README.md      # This file

src/graph/output/
└── eci_graph.json # Source of truth — edited in-place by Save
```

---

## Contributing Workflow

1. Start the server: `conda run -n edu uvicorn server:app --reload --port 8765`
2. Open http://localhost:8765
3. Use the **Node Explorer** or search bar to find the concept you want to edit
4. Right-click nodes/edges to modify; use **+ Add Node** for new entries
5. Click **↓ Save** (or `Ctrl+S`) when done — this updates `eci_graph.json` directly
6. Optionally use **⬇ Export** to download a local backup copy

> **Tip:** Start with N=1 to keep the graph readable. Increase to N=2 when you need
> to see broader context around a node.
