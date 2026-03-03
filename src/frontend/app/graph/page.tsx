'use client'

import { useCallback, useEffect, useRef, useState } from 'react'
import dynamic from 'next/dynamic'
import {
  fetchEgoGraph,
  searchConcepts,
  type EgoGraphResponse,
  type GraphNode,
  type SearchResult,
} from '@/lib/api'

// Dynamic imports — both components use window/canvas and must skip SSR
const EgoGraph    = dynamic(() => import('@/components/EgoGraph'),    { ssr: false })
const ExplainPanel = dynamic(() => import('@/components/ExplainPanel'), { ssr: false })

export default function GraphPage() {
  const [searchQuery,    setSearchQuery]    = useState('')
  const [searchResults,  setSearchResults]  = useState<SearchResult[]>([])
  const [showDropdown,   setShowDropdown]   = useState(false)
  const [egoGraph,       setEgoGraph]       = useState<EgoGraphResponse | null>(null)
  const [activeNodeId,   setActiveNodeId]   = useState<string | null>(null)
  const [isPanelOpen,    setIsPanelOpen]    = useState(false)
  const [isLoading,      setIsLoading]      = useState(false)
  const [loadError,      setLoadError]      = useState<string | null>(null)
  const [searchError,    setSearchError]    = useState<string | null>(null)

  const debounceRef    = useRef<ReturnType<typeof setTimeout> | null>(null)
  const searchAreaRef  = useRef<HTMLDivElement>(null)
  const graphFetchRef  = useRef<AbortController | null>(null)

  // Debounced search — errors are shown, not swallowed
  const handleSearchChange = useCallback((q: string) => {
    setSearchQuery(q)
    setSearchError(null)
    if (debounceRef.current) clearTimeout(debounceRef.current)
    if (q.trim().length < 2) {
      setSearchResults([])
      setShowDropdown(false)
      return
    }
    debounceRef.current = setTimeout(async () => {
      try {
        const results = await searchConcepts(q, 8)
        setSearchResults(results)
        setShowDropdown(results.length > 0)
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : String(e)
        setSearchError(`Search failed: ${msg}`)
        setSearchResults([])
        setShowDropdown(false)
      }
    }, 250)
  }, [])

  // Select from dropdown → load ego graph
  const handleSelectConcept = useCallback(async (result: SearchResult) => {
    setShowDropdown(false)
    setSearchQuery(result.name)
    setIsLoading(true)
    setLoadError(null)
    setIsPanelOpen(false)
    setActiveNodeId(null)
    // Cancel any in-flight graph fetch before starting a new one
    if (graphFetchRef.current) graphFetchRef.current.abort()
    const controller = new AbortController()
    graphFetchRef.current = controller
    try {
      const graph = await fetchEgoGraph(result.concept_id, controller.signal)
      setEgoGraph(graph)
    } catch (e: unknown) {
      if ((e as Error).name === 'AbortError') return
      const msg = e instanceof Error ? e.message : String(e)
      setLoadError(msg === '404' ? 'Concept not found.' : 'Failed to load graph.')
    } finally {
      setIsLoading(false)
    }
  }, [])

  // Click a concept node:
  //   center node  → open explain panel (already loaded)
  //   neighbor node → fetch its ego graph, then open panel
  const handleNodeClick = useCallback(async (node: GraphNode) => {
    if (egoGraph && node.id === egoGraph.center.id) {
      setActiveNodeId(node.id)
      setIsPanelOpen(true)
      return
    }
    setIsLoading(true)
    setLoadError(null)
    setIsPanelOpen(false)
    setActiveNodeId(null)
    setSearchQuery(node.name)
    // Cancel any in-flight graph fetch before starting a new one
    if (graphFetchRef.current) graphFetchRef.current.abort()
    const controller = new AbortController()
    graphFetchRef.current = controller
    try {
      const graph = await fetchEgoGraph(node.id, controller.signal)
      setEgoGraph(graph)
      setActiveNodeId(node.id)
      setIsPanelOpen(true)
    } catch (e: unknown) {
      if ((e as Error).name === 'AbortError') return
      const msg = e instanceof Error ? e.message : String(e)
      setLoadError(msg === '404' ? 'Concept not found.' : 'Failed to load graph.')
    } finally {
      setIsLoading(false)
    }
  }, [egoGraph])

  const handleClosePanel = useCallback(() => {
    setIsPanelOpen(false)
    setActiveNodeId(null)
  }, [])

  // Close dropdown when clicking outside the search area
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (searchAreaRef.current && searchAreaRef.current.contains(e.target as Node)) return
      setShowDropdown(false)
    }
    document.addEventListener('click', handler)
    return () => document.removeEventListener('click', handler)
  }, [])

  const activeNode = egoGraph?.nodes.find(n => n.id === activeNodeId) ?? null

  return (
    <main className="graph-page">
      {/* Page header */}
      <div className="page-header">
        <div className="page-tag">
          <span className="page-tag-dot" />
          <span className="page-tag-text">Knowledge Graph</span>
        </div>
        <h1 className="page-title">
          Concept<br />
          Explorer
        </h1>
        <p className="page-desc">
          Search for a concept to see its causal neighbourhood.
          Click any gold node to stream an AI explanation sourced from the textbook.
        </p>
      </div>

      {/* Search */}
      <div className="graph-search-area" ref={searchAreaRef}>
        <div className="search-bar">
          <span className="search-prefix">concept:</span>
          <input
            className="search-input"
            type="text"
            value={searchQuery}
            onChange={e => handleSearchChange(e.target.value)}
            placeholder="e.g. d-separation, backdoor criterion…"
            autoComplete="off"
          />
        </div>

        {showDropdown && searchResults.length > 0 && (
          <ul className="search-results">
            {searchResults.map(r => (
              <li
                key={r.concept_id}
                className="search-result-item"
                onClick={() => handleSelectConcept(r)}
              >
                <span className="search-result-name">{r.name}</span>
                <span className="search-result-meta">Ch.{r.chapter}</span>
              </li>
            ))}
          </ul>
        )}
      </div>

      {searchError && <p className="graph-status graph-error">{searchError}</p>}
      {loadError   && <p className="graph-status graph-error">{loadError}</p>}
      {isLoading  && <p className="graph-status">Loading graph…</p>}

      {!egoGraph && !isLoading && !loadError && (
        <p className="graph-status graph-hint">
          Search above to explore the ECI knowledge graph — 189 concepts, 332 relationships.
        </p>
      )}

      {/* Graph canvas + panel */}
      {egoGraph && (
        <div className={`graph-container${isPanelOpen ? ' panel-open' : ''}`}>
          <EgoGraph
            data={{ nodes: egoGraph.nodes, edges: egoGraph.edges }}
            centerId={egoGraph.center.id}
            onNodeClick={handleNodeClick}
            selectedNodeId={activeNodeId}
          />
        </div>
      )}

      {isPanelOpen && activeNode && (
        <ExplainPanel
          conceptId={activeNode.id}
          conceptName={activeNode.name}
          onClose={handleClosePanel}
        />
      )}
    </main>
  )
}
