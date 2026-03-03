'use client'

/**
 * ExplainPanel — slide-over drawer that streams an AI explanation for a concept.
 *
 * SSE is consumed with fetch + ReadableStream.getReader() — no Vercel AI SDK
 * needed (readStreamableValue is for RSC Server Actions, not plain SSE).
 *
 * SSE protocol from POST /api/v1/explain:
 *   data: <token>\n\n          — streamed text tokens
 *   event: sources\n
 *   data: <JSON array>\n\n     — passage metadata after stream ends
 *   data: [DONE]\n\n           — sentinel
 */

import { useEffect, useRef, useState } from 'react'
import katex from 'katex'
import 'katex/dist/katex.min.css'
import { API_BASE } from '@/lib/api'

// ── Math rendering ────────────────────────────────────────────────────────────
// Splits raw text on \( ... \) (inline) and \[ ... \] (display) LaTeX delimiters.
// Incomplete delimiters (e.g. while streaming) are left as plain text.
function renderMath(raw: string): React.ReactNode[] {
  const parts: React.ReactNode[] = []
  let last = 0
  let key = 0
  const regex = /\\\(([\s\S]*?)\\\)|\\\[([\s\S]*?)\\\]/g
  let match: RegExpExecArray | null

  while ((match = regex.exec(raw)) !== null) {
    if (match.index > last) {
      parts.push(<span key={key++}>{raw.slice(last, match.index)}</span>)
    }
    const isDisplay = match[2] !== undefined
    const math = isDisplay ? match[2] : match[1]
    try {
      const html = katex.renderToString(math, { displayMode: isDisplay, throwOnError: false })
      parts.push(<span key={key++} dangerouslySetInnerHTML={{ __html: html }} />)
    } catch {
      parts.push(<span key={key++}>{match[0]}</span>)
    }
    last = match.index + match[0].length
  }
  if (last < raw.length) parts.push(<span key={key++}>{raw.slice(last)}</span>)
  return parts
}

interface SourcePassage {
  page_num: number
  chapter: number
  section_heading: string
  score: number
  snippet: string
}

export interface ExplainPanelProps {
  conceptId: string
  conceptName: string
  onClose: () => void
}

export default function ExplainPanel({
  conceptId,
  conceptName,
  onClose,
}: ExplainPanelProps) {
  const [text, setText]             = useState('')
  const [sources, setSources]       = useState<SourcePassage[]>([])
  const [isStreaming, setIsStreaming] = useState(true)
  const [error, setError]           = useState<string | null>(null)
  const abortRef = useRef<AbortController | null>(null)

  // Close on Escape
  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [onClose])

  // Stream explanation whenever conceptId changes
  useEffect(() => {
    setText('')
    setSources([])
    setIsStreaming(true)
    setError(null)

    const controller = new AbortController()
    abortRef.current = controller

    async function stream() {
      try {
        const res = await fetch(`${API_BASE}/api/v1/explain`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ concept_id: conceptId, top_k: 5 }),
          signal: controller.signal,
        })
        if (!res.ok) {
          setError(`${res.status}: ${await res.text()}`)
          setIsStreaming(false)
          return
        }

        const reader = res.body!.getReader()
        const decoder = new TextDecoder()
        let buffer = ''
        let currentEvent = 'message'

        while (true) {
          const { done, value } = await reader.read()
          if (done) break

          buffer += decoder.decode(value, { stream: true })
          // Process complete SSE lines; hold back the incomplete trailing line
          const lines = buffer.split('\n')
          buffer = lines.pop()!

          for (const line of lines) {
            if (line.startsWith('event: ')) {
              currentEvent = line.slice(7).trim()
            } else if (line.startsWith('data: ')) {
              const payload = line.slice(6)
              if (payload === '[DONE]') {
                setIsStreaming(false)
              } else if (currentEvent === 'sources') {
                try { setSources(JSON.parse(payload)) } catch { /* ignore */ }
                currentEvent = 'message'
              } else if (currentEvent === 'error') {
                try {
                  const errData = JSON.parse(payload)
                  setError(errData.detail || 'AI explanation failed.')
                } catch {
                  setError('AI explanation failed.')
                }
                currentEvent = 'message'
              } else {
                setText(prev => prev + payload)
              }
            }
          }
        }
      } catch (err: unknown) {
        if ((err as Error).name !== 'AbortError') {
          setError('Failed to load explanation.')
        }
      } finally {
        setIsStreaming(false)
      }
    }

    stream()
    return () => controller.abort()
  }, [conceptId])

  return (
    <div
      className="explain-panel explain-panel-open"
      role="dialog"
      aria-label={`Explanation: ${conceptName}`}
    >
      {/* Header */}
      <div className="explain-panel-header">
        <div className="explain-panel-title">
          <span className="explain-panel-tag">◈ concept</span>
          <h2 className="explain-panel-concept-name">{conceptName}</h2>
        </div>
        <button
          className="explain-panel-close"
          onClick={onClose}
          aria-label="Close"
        >
          ✕
        </button>
      </div>

      {/* Scrollable explanation text */}
      <div className="explain-panel-body">
        {error && <p className="explain-panel-error">{error}</p>}
        <div className="explain-panel-text">
          {renderMath(text)}
          {isStreaming && <span className="explain-cursor">▋</span>}
        </div>
      </div>

      {/* Sources — always expanded */}
      {sources.length > 0 && (
        <div className="explain-sources">
          <p className="explain-sources-label">
            ◈ {sources.length} source passage{sources.length !== 1 ? 's' : ''}
          </p>
          <ul className="explain-sources-list">
            {sources.map((s, i) => (
              <li key={i} className="explain-source-item">
                <div className="explain-source-loc">
                  <span>Ch.{s.chapter}</span>
                  <span className="explain-source-loc-divider">·</span>
                  <span>p.{s.page_num}</span>
                  <span className="explain-source-loc-divider">·</span>
                  <span>{(s.score * 100).toFixed(1)}% match</span>
                </div>
                {s.section_heading && (
                  <div className="explain-source-heading">{s.section_heading}</div>
                )}
                {s.snippet && (
                  <div className="explain-source-snippet">{s.snippet}</div>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
