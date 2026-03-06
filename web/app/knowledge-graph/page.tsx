"use client";

import Link from "next/link";
import { STUDY_CHAPTERS } from "@/content/study";
import type { StudyItem } from "@/content/study";
import { BookOpen, X } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";

interface SubtopicItem {
  id: string;
  title: string;
  depth: number;
}

export default function KnowledgeGraphPage() {
  const { t } = useTranslation();
  const [selectedChapterId, setSelectedChapterId] = useState<string | null>(
    null,
  );

  const getSubtopics = (item: StudyItem, depth = 0): SubtopicItem[] => {
    if (!item.children?.length) {
      return [];
    }

    return item.children.flatMap((child) => [
      { id: child.id, title: child.title, depth },
      ...getSubtopics(child, depth + 1),
    ]);
  };

  const chapterNodes = STUDY_CHAPTERS.filter((item) => item.level === "chapter").map(
    (chapter, index) => ({
      id: chapter.id,
      title: chapter.title,
      subtitle: `Chapter ${index + 1}`,
      subtopics: getSubtopics(chapter),
    }),
  );
  const selectedChapter = chapterNodes.find((node) => node.id === selectedChapterId);

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
          <div className="relative flex flex-col md:flex-row gap-6">
            <div className="relative flex-1 flex flex-col items-center justify-center py-6">
              {chapterNodes.map((node, index) => (
                <div key={node.id} className="w-full flex flex-col items-center">
                  <button
                    type="button"
                    onClick={() =>
                      setSelectedChapterId((prev) => (prev === node.id ? null : node.id))
                    }
                    className={`rounded-2xl border p-4 md:p-5 shadow-sm text-left transition-colors ${
                      selectedChapterId === node.id
                        ? "border-blue-500 dark:border-blue-400 bg-blue-100 dark:bg-blue-900/40 ring-2 ring-blue-300/70 dark:ring-blue-500/70"
                        : "border-blue-200 dark:border-blue-700 bg-blue-50 dark:bg-blue-900/30 hover:bg-blue-100/70 dark:hover:bg-blue-900/40"
                    }`}
                    style={{ width: "min(100%, 320px)" }}
                    aria-pressed={selectedChapterId === node.id}
                  >
                    <p className="text-xs uppercase tracking-wide text-blue-700 dark:text-blue-200">
                      {node.subtitle}
                    </p>
                    <div className="mt-2 flex items-start gap-2">
                      <BookOpen className="w-4 h-4 mt-0.5 text-blue-600 dark:text-blue-300" />
                      <p className="text-sm md:text-base font-semibold text-slate-900 dark:text-white">
                        {node.title}
                      </p>
                    </div>
                  </button>

                  {index < chapterNodes.length - 1 && (
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

            {selectedChapter && (
              <aside className="w-full md:w-[360px] rounded-2xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900/40 p-4 md:p-5 self-start">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-xs uppercase tracking-wide text-slate-600 dark:text-slate-300">
                      {selectedChapter.subtitle}
                    </p>
                    <h2 className="mt-1 text-base font-semibold text-slate-900 dark:text-white">
                      {selectedChapter.title}
                    </h2>
                  </div>
                  <button
                    type="button"
                    onClick={() => setSelectedChapterId(null)}
                    className="rounded-md p-1 text-slate-500 hover:bg-slate-200/80 dark:text-slate-300 dark:hover:bg-slate-700"
                    aria-label={t("Close panel")}
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>
                {selectedChapter.subtopics.length > 0 ? (
                  <ul className="mt-2 space-y-2">
                    {selectedChapter.subtopics.map((subtopic) => (
                      <li
                        key={subtopic.id}
                        className="flex items-start gap-2 text-sm text-slate-700 dark:text-slate-200"
                        style={{ marginLeft: `${subtopic.depth * 16}px` }}
                      >
                        <span className="mt-1 shrink-0">
                          {subtopic.depth === 0 ? "•" : "◦"}
                        </span>
                        <Link
                          href={`/study?item=${encodeURIComponent(subtopic.id)}`}
                          className="block min-w-0 rounded-md border border-transparent px-1.5 py-0.5 leading-relaxed text-slate-600 dark:text-slate-300 hover:bg-white dark:hover:bg-slate-700 hover:text-blue-600 dark:hover:text-blue-400 hover:shadow-sm hover:border-slate-100 dark:hover:border-slate-600 transition-all duration-200"
                        >
                          {subtopic.title}
                        </Link>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
                    {t("No subtopics available")}
                  </p>
                )}
              </aside>
            )}
          </div>
        </section>
      </div>
    </div>
  );
}
