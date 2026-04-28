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

  // Clean up multiple consecutive newlines
  result = result.replace(/\n{3,}/g, "\n\n");

  return result;
}

function transformOutsidePattern(
  content: string,
  pattern: RegExp,
  transform: (segment: string) => string,
): string {
  let result = "";
  let cursor = 0;
  pattern.lastIndex = 0;

  let match: RegExpExecArray | null;
  while ((match = pattern.exec(content)) !== null) {
    result += transform(content.slice(cursor, match.index));
    result += match[0];
    cursor = match.index + match[0].length;
  }

  return result + transform(content.slice(cursor));
}

function unwrapInlineCodeMath(content: string): string {
  return transformOutsidePattern(content, /```[\s\S]*?```/g, (segment) =>
    segment.replace(/`(\${1,2}[^`\n]+?\${1,2})`/g, "$1"),
  );
}

function normalizeGraphNotationSegment(content: string): string {
  const withSymbolAliases = content.replace(
    /([A-Za-z])\s+\(([A-Z])\)/g,
    "$1 ($$$2$$)",
  );
  const graphToken = String.raw`(?:[A-Z][A-Za-z0-9_]*|[a-z][a-z0-9_]*_[A-Za-z0-9_]+)`;
  const graphPath = new RegExp(
    String.raw`(^|[^\w$])(${graphToken}(?:\s*(?:→|←|↔)\s*${graphToken})+)(?=$|[^\w$])`,
    "g",
  );

  return withSymbolAliases.replace(
    graphPath,
    (_match, prefix: string, expression: string) => {
      const latex = expression
        .replace(/\s*→\s*/g, " \\\\rightarrow ")
        .replace(/\s*←\s*/g, " \\\\leftarrow ")
        .replace(/\s*↔\s*/g, " \\\\leftrightarrow ");
      return `${prefix}$${latex}$`;
    },
  );
}

function normalizeGraphNotation(content: string): string {
  return transformOutsidePattern(
    content,
    /```[\s\S]*?```|`[^`\n]+`|\$\$[\s\S]*?\$\$|\$(?!\$)(?:\\.|[^$\n])+\$|!\[[^\]]*\]\([^)]+\)|\[(?:CONTEXT_IMAGE|PEDAGOGICAL_IMAGE|IMAGE):\s*[^\]]+\]/gi,
    normalizeGraphNotationSegment,
  );
}

function normalizeStandaloneDisplayMath(content: string): string {
  return content
    .split("\n")
    .map((line) => {
      const trimmed = line.trim();
      if (
        trimmed.length > 4 &&
        trimmed.startsWith("$$") &&
        trimmed.endsWith("$$") &&
        !trimmed.slice(2, -2).includes("$$")
      ) {
        const expression = trimmed.slice(2, -2).trim();
        return expression ? `$$\n${expression}\n$$` : line;
      }

      return line;
    })
    .join("\n");
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
  const normalizedTags = unwrapInlineCodeMath(str).replace(
    /\\tag\{([^}]+)\}/g,
    "\\qquad \\text{($1)}",
  );

  // Apply delimiter conversion
  return normalizeStandaloneDisplayMath(
    normalizeGraphNotation(
      convertLatexDelimiters(normalizeCaptionMath(normalizedTags)),
    ),
  );
}
