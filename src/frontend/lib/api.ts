/**
 * Typed fetch helpers for the EducAgent FastAPI backend.
 * Base URL is controlled by NEXT_PUBLIC_API_URL (defaults to localhost:8000).
 */

export const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

// ---- Types ----------------------------------------------------------------

export interface HealthResponse {
  status: string
  neo4j: string
  graph: Record<string, unknown>
}

export interface Concept {
  concept_id: string
  name: string
  chapter: number
  difficulty: number
}

export interface SearchResult {
  concept_id: string
  name: string
  chapter: number
  score: number
}

// ── Graph types ──────────────────────────────────────────────────────────────

export interface GraphNode {
  id: string
  node_type: string        // "Concept" | "Section" | "Category"
  name: string
  chapter?: number
  page_refs?: number[]
}

export interface GraphEdge {
  source: string
  target: string
  edge_type: string
}

export interface EgoGraphResponse {
  center: GraphNode
  nodes: GraphNode[]
  edges: GraphEdge[]
}

// ---- Helpers ---------------------------------------------------------------

async function apiFetch<T>(url: string, signal?: AbortSignal): Promise<T> {
  const res = await fetch(url, signal ? { signal } : undefined)
  if (!res.ok) throw new Error(String(res.status))
  return res.json() as Promise<T>
}

// ---- Endpoints -------------------------------------------------------------

export function fetchHealth(): Promise<HealthResponse> {
  return apiFetch<HealthResponse>(`${API_BASE}/health`)
}

export function fetchPrerequisites(conceptId: string): Promise<Concept[]> {
  return apiFetch<Concept[]>(
    `${API_BASE}/api/v1/concepts/${conceptId}/prerequisites`,
  )
}

export function searchConcepts(
  q: string,
  limit = 10,
): Promise<SearchResult[]> {
  return apiFetch<SearchResult[]>(
    `${API_BASE}/api/v1/concepts/search?q=${encodeURIComponent(q)}&limit=${limit}`,
  )
}

export function fetchEgoGraph(conceptId: string, signal?: AbortSignal): Promise<EgoGraphResponse> {
  return apiFetch<EgoGraphResponse>(
    `${API_BASE}/api/v1/graph/ego/${encodeURIComponent(conceptId)}`,
    signal,
  )
}
