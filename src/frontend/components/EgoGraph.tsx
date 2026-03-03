'use client'

/**
 * EgoGraph — renders the 1-hop neighbourhood of a concept using react-force-graph-2d.
 *
 * Must be dynamically imported with ssr:false because react-force-graph-2d
 * accesses window/document at module load time. The parent page.tsx handles
 * the dynamic() call; this component is always rendered client-side only.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import ForceGraph2D from 'react-force-graph-2d'
import type { GraphEdge, GraphNode } from '@/lib/api'

// ── Internal types for react-force-graph-2d ──────────────────────────────────

interface FGNode extends Record<string, unknown> {
  id: string
  name: string
  node_type: string
  chapter?: number
  // Simulation coords added by d3 at runtime:
  x?: number
  y?: number
}

interface FGLink extends Record<string, unknown> {
  source: string | FGNode
  target: string | FGNode
  edge_type: string
}

// ── Props ─────────────────────────────────────────────────────────────────────

export interface EgoGraphProps {
  data: { nodes: GraphNode[]; edges: GraphEdge[] }
  centerId: string
  onNodeClick: (node: GraphNode) => void
  selectedNodeId: string | null
}

// ── Component ─────────────────────────────────────────────────────────────────

export default function EgoGraph({
  data,
  centerId,
  onNodeClick,
  selectedNodeId,
}: EgoGraphProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 })

  // Measure container; resize canvas when the container changes size
  // (this handles the panel-open width transition automatically)
  useEffect(() => {
    if (!containerRef.current) return
    const obs = new ResizeObserver(entries => {
      const { width, height } = entries[0].contentRect
      setDimensions({ width: Math.floor(width), height: Math.floor(height) })
    })
    obs.observe(containerRef.current)
    return () => obs.disconnect()
  }, [])

  // react-force-graph-2d mutates node objects in place to add x/y/vx/vy.
  // Always pass cloned objects so React state is never mutated.
  const graphData = useMemo(() => ({
    nodes: data.nodes.map(n => ({ ...n })) as FGNode[],
    links: data.edges.map(e => ({ ...e })) as FGLink[],
  }), [data])

  // Custom canvas node painter
  const nodeCanvasObject = useCallback(
    (node: FGNode, ctx: CanvasRenderingContext2D, globalScale: number) => {
      const isCenter   = node.id === centerId
      const isSelected = node.id === selectedNodeId
      const isConcept  = node.node_type === 'Concept'
      const isSection  = node.node_type === 'Section'

      const r = isCenter ? 10 : isConcept ? 7 : 5

      // Fill
      ctx.beginPath()
      ctx.arc(node.x!, node.y!, r, 0, 2 * Math.PI)
      ctx.fillStyle = isCenter
        ? '#dfc07a'   // --gold-bright
        : isConcept
          ? '#c9a95f' // --gold
          : isSection
            ? '#4a8fff' // --blue
            : '#6e7681'  // category / dim
      ctx.fill()

      // Selected ring
      if (isSelected) {
        ctx.beginPath()
        ctx.arc(node.x!, node.y!, r + 3, 0, 2 * Math.PI)
        ctx.strokeStyle = '#dfc07a'
        ctx.lineWidth = 1.5 / globalScale
        ctx.stroke()
      }

      // Label — show at sufficient zoom, always for center/selected
      if (globalScale >= 1.2 || isCenter || isSelected) {
        const fontSize = Math.max(3, (isCenter ? 5 : 4) / globalScale * 2)
        ctx.font = `${fontSize}px "JetBrains Mono", monospace`
        ctx.fillStyle = isCenter ? '#dfc07a' : '#e4e0d2'
        ctx.textAlign = 'center'
        ctx.textBaseline = 'top'
        ctx.fillText(
          node.name.length > 22 ? node.name.slice(0, 20) + '…' : node.name,
          node.x!,
          node.y! + r + 2,
        )
      }
    },
    [centerId, selectedNodeId],
  )

  const handleNodeClick = useCallback(
    (node: FGNode) => {
      // Only concept nodes have AI explanations
      if (node.node_type === 'Concept') {
        onNodeClick(node as unknown as GraphNode)
      }
    },
    [onNodeClick],
  )

  const linkColor = useCallback((link: FGLink) => {
    switch (link.edge_type as string) {
      case 'PREREQUISITE_OF':     return 'rgba(201,169,95,0.6)'
      case 'COVERED_IN':          return 'rgba(74,143,255,0.4)'
      case 'COMMONLY_CONFUSED':   return 'rgba(255,100,100,0.5)'
      case 'RELATED_TO_SEE_ALSO': return 'rgba(100,180,100,0.5)'
      default:                    return 'rgba(40,80,180,0.3)'
    }
  }, [])

  return (
    <div ref={containerRef} className="ego-graph-container">
      <ForceGraph2D
        graphData={graphData}
        width={dimensions.width}
        height={dimensions.height}
        backgroundColor="#06060e"
        nodeCanvasObject={nodeCanvasObject}
        nodeCanvasObjectMode={() => 'replace'}
        onNodeClick={handleNodeClick}
        linkColor={linkColor}
        linkWidth={1.5}
        linkDirectionalArrowLength={5}
        linkDirectionalArrowRelPos={1}
        enableNodeDrag
        enableZoomInteraction
        cooldownTicks={120}
        d3AlphaDecay={0.03}
        d3VelocityDecay={0.3}
      />
    </div>
  )
}
