/**
 * Utility functions for LaTeX processing
 *
 * remark-math only supports $...$ and $$...$$ delimiters by default.
 * Many LLMs output LaTeX using \(...\) and \[...\] delimiters.
 * This utility converts between formats.
 */

/**
 * Convert LaTeX delimiters from \(...\) and \[...\] to $...$ and $$...$$
 * This makes the content compatible with remark-math for ReactMarkdown rendering.
 *
 * @param content - The content containing LaTeX with \(...\) or \[...\] delimiters
 * @returns Content with $...$ and $$...$$ delimiters
 */
export function convertLatexDelimiters(content: string): string {
  if (!content) return content;

  let result = content;

  // Convert \[...\] to $$...$$ (block math)
  // Use a regex that handles multiline content
  // Note: In JSON strings, \[ becomes \\[ which in JS becomes \[
  result = result.replace(/\\\[([\s\S]*?)\\\]/g, "\n$$\n$1\n$$\n");

  // Convert \(...\) to $...$ (inline math)
  // Be careful not to match escaped parentheses in other contexts
  result = result.replace(/\\\(([\s\S]*?)\\\)/g, " $$$1$$ ");

  // Also handle cases where LaTeX is directly in the text without proper delimiters
  // e.g., standalone \lim, \frac, etc. that should be wrapped
  // This is a common issue with LLM outputs

  // Clean up multiple consecutive newlines
  result = result.replace(/\n{3,}/g, "\n\n");

  return result;
}

function normalizeCaptionMath(content: string): string {
  const lines = content.split("\n");

  return lines
    .map((line) => {
      const trimmed = line.trim();
      if (!trimmed.startsWith("*") || !trimmed.endsWith("*")) {
        return line;
      }

      const segments = line.split(/(\$[^$]+\$)/g);
      const normalized = segments
        .map((segment) => {
          if (segment.startsWith("$") && segment.endsWith("$")) {
            return segment;
          }

          return segment.replace(
            /\b([A-Za-z])_([A-Za-z0-9]+)(\s*=\s*[-+]?\d+(?:\.\d+)?)?/g,
            (_match, symbol: string, subscript: string, suffix = "") =>
              `$${symbol}_${subscript}${suffix.replace(/\s+/g, "")}$`,
          );
        })
        .join("");

      return normalized;
    })
    .join("\n");
}

/**
 * Process content for ReactMarkdown rendering with proper LaTeX support
 * This is a convenience wrapper that applies all necessary transformations.
 *
 * @param content - The raw content to process
 * @returns Processed content ready for ReactMarkdown with remark-math
 */
export function processLatexContent(content: string): string {
  if (!content) return "";

  // Convert to string if not already
  const str = String(content);

  // Rewrite unsupported equation tags into visible text labels before parsing.
  const normalizedTags = str.replace(
    /\\tag\{([^}]+)\}/g,
    "\\qquad \\text{($1)}",
  );

  // Apply delimiter conversion
  return convertLatexDelimiters(normalizeCaptionMath(normalizedTags));
}
