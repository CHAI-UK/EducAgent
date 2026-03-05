"use client";

import { BookOpen } from "lucide-react";
import { useTranslation } from "react-i18next";

const chapterNodes = [
  {
    id: "ch-1",
    title: "Statistical and Causal Modes",
    subtitle: "Chapter 1",
  },
  {
    id: "ch-2",
    title: "Assumptions for Causal Inference",
    subtitle: "Chapter 2",
  },
];

export default function KnowledgeGraphPage() {
  const { t } = useTranslation();

  return (
    <div className="min-h-screen p-4">
      <div className="max-w-6xl mx-auto">
        <div className="mb-4 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-slate-900 dark:text-white">
              {t("Knowledge Graph")}
            </h1>
            <p className="text-sm text-slate-600 dark:text-slate-300 mt-1">
              {t("Learning path connections between chapters")}
            </p>
          </div>
        </div>

        <section className="relative rounded-2xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-4 md:p-8 min-h-[420px]">
          <div className="relative flex flex-col h-full items-center justify-center py-6">
            {chapterNodes.map((node, index) => (
              <div key={node.id} className="w-full flex flex-col items-center">
                <div
                  className="rounded-2xl border border-indigo-200 dark:border-indigo-700 bg-indigo-50 dark:bg-indigo-900/30 p-4 md:p-5 shadow-sm"
                  style={{ width: "min(100%, 320px)" }}
                >
                  <p className="text-xs uppercase tracking-wide text-indigo-700 dark:text-indigo-200">
                    {node.subtitle}
                  </p>
                  <div className="mt-2 flex items-start gap-2">
                    <BookOpen className="w-4 h-4 mt-0.5 text-indigo-600 dark:text-indigo-300" />
                    <p className="text-sm md:text-base font-semibold text-slate-900 dark:text-white">
                      {node.title}
                    </p>
                  </div>
                </div>

                {index < chapterNodes.length - 1 && (
                  <div
                    aria-hidden
                    className="relative h-16 w-6 mt-4 flex items-start justify-center"
                  >
                    <div className="w-1 h-12 bg-indigo-600 dark:bg-indigo-400 rounded-full" />
                    <div className="absolute top-11 w-0 h-0 border-l-[7px] border-l-transparent border-r-[7px] border-r-transparent border-t-[10px] border-t-indigo-600 dark:border-t-indigo-400" />
                  </div>
                )}
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
