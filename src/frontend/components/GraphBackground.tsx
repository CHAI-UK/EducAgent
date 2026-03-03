/**
 * Decorative animated SVG causal graph — fixed full-viewport background.
 * Nodes and directed edges breathe and appear on load, evoking the ECI knowledge graph.
 * Pure CSS animations; no runtime JS after mount.
 */

// Positions in a 0-100 × 0-100 coordinate space (percentages of viewport)
const NODES = [
  { id: 'n0',  cx:  8,  cy: 14, r: 1.0 },
  { id: 'n1',  cx: 26,  cy:  5, r: 0.7 },
  { id: 'n2',  cx: 50,  cy: 10, r: 1.3 },
  { id: 'n3',  cx: 72,  cy:  4, r: 0.8 },
  { id: 'n4',  cx: 90,  cy: 16, r: 1.0 },
  { id: 'n5',  cx: 14,  cy: 32, r: 0.9 },
  { id: 'n6',  cx: 36,  cy: 26, r: 1.2 },
  { id: 'n7',  cx: 60,  cy: 22, r: 0.7 },
  { id: 'n8',  cx: 82,  cy: 36, r: 1.0 },
  { id: 'n9',  cx:  4,  cy: 52, r: 0.8 },
  { id: 'n10', cx: 26,  cy: 48, r: 1.3 },
  { id: 'n11', cx: 50,  cy: 44, r: 0.9 },
  { id: 'n12', cx: 72,  cy: 54, r: 1.1 },
  { id: 'n13', cx: 94,  cy: 50, r: 0.7 },
  { id: 'n14', cx: 16,  cy: 68, r: 1.0 },
  { id: 'n15', cx: 40,  cy: 72, r: 0.8 },
  { id: 'n16', cx: 62,  cy: 68, r: 1.2 },
  { id: 'n17', cx: 86,  cy: 74, r: 0.9 },
  { id: 'n18', cx: 28,  cy: 88, r: 0.7 },
  { id: 'n19', cx: 55,  cy: 92, r: 1.0 },
  { id: 'n20', cx: 78,  cy: 90, r: 0.8 },
]

const EDGES: [string, string][] = [
  ['n0', 'n1'], ['n1', 'n2'], ['n2', 'n3'], ['n3', 'n4'],
  ['n0', 'n5'], ['n1', 'n6'], ['n2', 'n7'], ['n4', 'n8'],
  ['n5', 'n6'], ['n6', 'n7'], ['n7', 'n8'],
  ['n5', 'n9'], ['n6', 'n10'], ['n7', 'n11'], ['n8', 'n12'], ['n8', 'n13'],
  ['n9', 'n10'], ['n10', 'n11'], ['n11', 'n12'], ['n12', 'n13'],
  ['n9', 'n14'], ['n10', 'n15'], ['n11', 'n16'], ['n12', 'n17'],
  ['n14', 'n15'], ['n15', 'n16'], ['n16', 'n17'],
  ['n14', 'n18'], ['n15', 'n18'], ['n16', 'n19'], ['n17', 'n20'],
  ['n18', 'n19'], ['n19', 'n20'],
  // Long-range "causal" links
  ['n2', 'n11'], ['n6', 'n15'], ['n10', 'n18'], ['n3', 'n12'],
]

const nodeMap = Object.fromEntries(NODES.map(n => [n.id, n]))

export default function GraphBackground() {
  return (
    <svg
      className="graph-bg"
      viewBox="0 0 100 100"
      preserveAspectRatio="xMidYMid slice"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      <defs>
        {/* Tiny arrowhead marker */}
        <marker
          id="arr"
          markerWidth="4"
          markerHeight="4"
          refX="3.5"
          refY="2"
          orient="auto"
        >
          <polygon points="0 0, 4 2, 0 4" fill="rgba(40,90,180,0.4)" />
        </marker>

        {/* Radial gradient for node glow */}
        <radialGradient id="node-glow-grad" cx="50%" cy="50%" r="50%">
          <stop offset="0%"   stopColor="#4a8fff" stopOpacity="0.4" />
          <stop offset="100%" stopColor="#4a8fff" stopOpacity="0" />
        </radialGradient>
      </defs>

      {/* Edges */}
      <g>
        {EDGES.map(([from, to], i) => {
          const a = nodeMap[from]
          const b = nodeMap[to]
          if (!a || !b) return null
          const delay = `${(i * 0.08).toFixed(2)}s`
          return (
            <line
              key={`e-${i}`}
              x1={a.cx}
              y1={a.cy}
              x2={b.cx}
              y2={b.cy}
              className="graph-edge"
              style={{ animationDelay: delay }}
              markerEnd="url(#arr)"
            />
          )
        })}
      </g>

      {/* Glow halos (rendered behind node dots) */}
      <g>
        {NODES.map((node, i) => (
          <circle
            key={`g-${node.id}`}
            cx={node.cx}
            cy={node.cy}
            r={node.r * 2.5}
            className="graph-node-glow"
            style={{ animationDelay: `${(i * 0.15).toFixed(2)}s` }}
          />
        ))}
      </g>

      {/* Node dots */}
      <g>
        {NODES.map((node, i) => (
          <circle
            key={node.id}
            cx={node.cx}
            cy={node.cy}
            r={node.r}
            className="graph-node"
            style={{ animationDelay: `${(i * 0.15).toFixed(2)}s` }}
          />
        ))}
      </g>
    </svg>
  )
}
