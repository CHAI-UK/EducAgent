"use client";

import React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import rehypeRaw from "rehype-raw";
import "katex/dist/katex.min.css";
import Mermaid from "@/components/Mermaid";
import { processLatexContent } from "@/lib/latex";

interface MarkdownRendererProps {
  content: string;
  className?: string;
  variant?: "default" | "compact" | "prose";
}

function slugifyHeading(value: string) {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

function textFromChildren(children: React.ReactNode): string {
  return React.Children.toArray(children)
    .map((child) => {
      if (typeof child === "string" || typeof child === "number") {
        return String(child);
      }

      if (React.isValidElement<{ children?: React.ReactNode }>(child)) {
        return textFromChildren(child.props.children);
      }

      return "";
    })
    .join("")
    .trim();
}

/**
 * Shared MarkdownRenderer component with KaTeX support and consistent table styling
 */
export default function MarkdownRenderer({
  content,
  className = "",
  variant = "default",
}: MarkdownRendererProps) {
  const paragraphComponents = {
    p: ({ node, children, ...props }: any) => {
      const childArray = React.Children.toArray(children);
      const firstChild = childArray[0] as React.ReactElement<{
        children?: React.ReactNode;
      }>;
      const isCaptionParagraph =
        childArray.length === 1 &&
        React.isValidElement(firstChild) &&
        firstChild.type === "em";

      if (isCaptionParagraph) {
        return (
          <p
            className="mt-2 text-sm italic leading-6 text-slate-500 dark:text-slate-400"
            {...props}
          >
            {children}
          </p>
        );
      }

      return <p {...props}>{children}</p>;
    },
  };

  // Table components with consistent styling
  const tableComponents = {
    table: ({ node, ...props }: any) => (
      <div
        className={`overflow-x-auto rounded-lg border border-slate-200 dark:border-slate-700 shadow-sm ${
          variant === "compact" ? "my-2" : "my-4"
        }`}
      >
        <table
          className="min-w-full divide-y divide-slate-200 dark:divide-slate-700 text-sm"
          {...props}
        />
      </div>
    ),
    thead: ({ node, ...props }: any) => (
      <thead className="bg-slate-50 dark:bg-slate-800" {...props} />
    ),
    th: ({ node, ...props }: any) => (
      <th
        className={`text-left font-semibold text-slate-700 dark:text-slate-300 whitespace-nowrap border-b border-slate-200 dark:border-slate-700 ${
          variant === "compact" ? "px-2 py-1.5" : "px-3 py-2"
        }`}
        {...props}
      />
    ),
    tbody: ({ node, ...props }: any) => (
      <tbody
        className="divide-y divide-slate-100 dark:divide-slate-700 bg-white dark:bg-slate-900"
        {...props}
      />
    ),
    td: ({ node, ...props }: any) => (
      <td
        className={`text-slate-600 dark:text-slate-400 border-b border-slate-100 dark:border-slate-700 ${
          variant === "compact" ? "px-2 py-1.5" : "px-3 py-2"
        }`}
        {...props}
      />
    ),
    tr: ({ node, ...props }: any) => (
      <tr
        className="hover:bg-slate-50/50 dark:hover:bg-slate-800/50 transition-colors"
        {...props}
      />
    ),
  };

  // Code block styling
  const codeComponents = {
    code: ({
      node,
      inline,
      className: codeClassName,
      children,
      ...props
    }: any) => {
      const match = /language-(\w+)/.exec(codeClassName || "");
      const language = match ? match[1] : "";

      if (language === "mermaid") {
        const chartCode = String(children).replace(/\n$/, "");
        return <Mermaid chart={chartCode} />;
      }

      if (inline) {
        return (
          <code
            className="px-1.5 py-0.5 bg-slate-100 dark:bg-slate-800 text-slate-800 dark:text-slate-200 rounded text-sm font-mono"
            {...props}
          >
            {children}
          </code>
        );
      }
      return (
        <code
          className={`block p-3 bg-slate-900 dark:bg-slate-950 text-slate-100 rounded-lg overflow-x-auto text-sm font-mono ${codeClassName || ""}`}
          {...props}
        >
          {children}
        </code>
      );
    },
    pre: ({ node, children, ...props }: any) => {
      const child = React.Children.toArray(children)[0] as React.ReactElement<{
        className?: string;
      }>;

      if (child?.props?.className?.includes("language-mermaid")) {
        return <>{children}</>;
      }

      return (
        <pre className="my-4" {...props}>
          {children}
        </pre>
      );
    },
  };

  const mediaComponents = {
    img: ({ node, alt, src, ...props }: any) =>
      typeof src === "string" ? (
        // eslint-disable-next-line @next/next/no-img-element -- Markdown-driven study assets can have mismatched extensions/metadata
        <img
          src={src}
          alt={alt || ""}
          className="my-4 h-auto w-full rounded-lg border border-slate-200 dark:border-slate-700 shadow-sm"
          loading="lazy"
          {...props}
        />
      ) : null,
  };

  const headingComponents = {
    h3: ({ node, children, ...props }: any) => {
      const headingText = textFromChildren(children);
      const headingId = slugifyHeading(headingText);

      return (
        <h3 id={headingId} {...props}>
          {children}
        </h3>
      );
    },
  };

  const proseClasses =
    variant === "prose"
      ? "prose prose-slate dark:prose-invert prose-headings:font-bold prose-h1:text-2xl prose-h2:text-xl max-w-none"
      : "prose prose-sm max-w-none";

  return (
    <div className={`${proseClasses} ${className}`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm, remarkMath]}
        rehypePlugins={[rehypeRaw, rehypeKatex]}
        components={{
          ...paragraphComponents,
          ...tableComponents,
          ...codeComponents,
          ...mediaComponents,
          ...headingComponents,
        }}
      >
        {processLatexContent(content)}
      </ReactMarkdown>
    </div>
  );
}
