/**
 * Re-exports the Vercel AI SDK SSE streaming utilities with local type aliases.
 * Import from here rather than from 'ai' directly so the abstraction boundary
 * makes future SDK upgrades a single-file change.
 */

export { readStreamableValue, createStreamableValue } from 'ai/rsc'
export type { StreamableValue } from 'ai/rsc'
