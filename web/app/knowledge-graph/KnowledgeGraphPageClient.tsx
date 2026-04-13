"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { BookOpen, X } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import { useTranslation } from "react-i18next";
import type { StudyPath } from "@/content/study";
import { processLatexContent } from "@/lib/latex";

interface KnowledgeGraphPageClientProps {
  studyPath: StudyPath;
}

function ObjectiveMarkdown({ content }: { content: string }) {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm, remarkMath]}
      rehypePlugins={[rehypeKatex]}
      components={{
        p: ({ children }) => <>{children}</>,
      }}
    >
      {processLatexContent(content)}
    </ReactMarkdown>
  );
}

export default function KnowledgeGraphPageClient({
  studyPath,
}: KnowledgeGraphPageClientProps) {
  const { t } = useTranslation();
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(
    studyPath.nodes[0]?.id ?? null,
  );

  const selectedNode = useMemo(
    () => studyPath.nodes.find((node) => node.id === selectedNodeId) ?? null,
    [selectedNodeId, studyPath.nodes],
  );

  return (
    <div className="min-h-screen p-4">
      <div className="max-w-6xl mx-auto">
        <div className="mb-4 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-slate-900 dark:text-white">
              {t("Knowledge Graph")}
            </h1>
            <p className="text-sm text-slate-600 dark:text-slate-300 mt-1">
              {studyPath.title}
            </p>
          </div>
        </div>

        <section className="relative rounded-2xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-4 md:p-8 min-h-[420px]">
          <div className="relative flex flex-col md:flex-row gap-6">
            <div className="relative flex-1 flex flex-col items-center justify-center py-6">
              {studyPath.nodes.map((node, index) => (
                <div
                  key={node.id}
                  className="w-full flex flex-col items-center"
                >
                  <button
                    type="button"
                    onClick={() =>
                      setSelectedNodeId((prev) =>
                        prev === node.id ? null : node.id,
                      )
                    }
                    className={`rounded-2xl border p-4 md:p-5 shadow-sm text-left transition-colors ${
                      selectedNodeId === node.id
                        ? "border-blue-500 dark:border-blue-400 bg-blue-100 dark:bg-blue-900/40 ring-2 ring-blue-300/70 dark:ring-blue-500/70"
                        : "border-blue-200 dark:border-blue-700 bg-blue-50 dark:bg-blue-900/30 hover:bg-blue-100/70 dark:hover:bg-blue-900/40"
                    }`}
                    style={{ width: "min(100%, 360px)" }}
                    aria-pressed={selectedNodeId === node.id}
                  >
                    <div className="flex items-start gap-2">
                      <BookOpen className="w-4 h-4 mt-0.5 text-blue-600 dark:text-blue-300" />
                      <p className="text-sm md:text-base font-semibold text-slate-900 dark:text-white">
                        {node.title}
                      </p>
                    </div>
                  </button>

                  {index < studyPath.nodes.length - 1 && (
                    <div
                      aria-hidden
                      className="relative h-16 w-6 mt-4 flex items-start justify-center"
                    >
                      <div className="w-1 h-12 bg-blue-600 dark:bg-blue-400 rounded-full" />
                      <div className="absolute top-11 w-0 h-0 border-l-[7px] border-l-transparent border-r-[7px] border-r-transparent border-t-[10px] border-t-blue-600 dark:border-t-blue-400" />
                    </div>
                  )}
                </div>
              ))}
            </div>

            {selectedNode && (
              <aside className="w-full md:w-[360px] rounded-2xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900/40 p-4 md:p-5 self-start">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <h2 className="text-base font-semibold text-slate-900 dark:text-white">
                      {selectedNode.title}
                    </h2>
                  </div>
                  <button
                    type="button"
                    onClick={() => setSelectedNodeId(null)}
                    className="rounded-md p-1 text-slate-500 hover:bg-slate-200/80 dark:text-slate-300 dark:hover:bg-slate-700"
                    aria-label={t("Close panel")}
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>
                {selectedNode.learningObjectives?.length ? (
                  <div className="mt-4">
                    <p className="text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400">
                      {t("Learning objectives")}
                    </p>
                    <ul className="mt-2 space-y-2 text-sm text-slate-700 dark:text-slate-200">
                      {selectedNode.learningObjectives.map((objective) => (
                        <li key={objective} className="flex gap-2">
                          <span className="mt-1 shrink-0">•</span>
                          <span>
                            <ObjectiveMarkdown content={objective} />
                          </span>
                        </li>
                      ))}
                    </ul>
                  </div>
                ) : null}

                <Link
                  href={`/study?item=${encodeURIComponent(selectedNode.id)}`}
                  className="mt-5 inline-flex items-center rounded-lg border border-blue-200 dark:border-blue-700 bg-white dark:bg-slate-800 px-4 py-2 text-sm font-medium text-blue-700 dark:text-blue-300 hover:bg-blue-50 dark:hover:bg-slate-700"
                >
                  {t("Open in Study Mode")}
                </Link>
              </aside>
            )}
          </div>
        </section>
      </div>
    </div>
  );
}
