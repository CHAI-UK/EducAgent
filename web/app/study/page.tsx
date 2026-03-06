"use client";

import { Suspense, useMemo, useState } from "react";
import { BookOpen, ChevronRight, ChevronDown } from "lucide-react";
import { useSearchParams } from "next/navigation";
import { useTranslation } from "react-i18next";
import MarkdownRenderer from "@/components/common/MarkdownRenderer";
import { STUDY_CHAPTERS, type StudyItem } from "@/content/study";

function flattenItems(items: StudyItem[]): StudyItem[] {
  return items.flatMap((item) => [
    item,
    ...(item.children ? flattenItems(item.children) : []),
  ]);
}

function findPathToItem(items: StudyItem[], targetId: string): StudyItem[] | null {
  for (const item of items) {
    if (item.id === targetId) {
      return [item];
    }
    if (item.children?.length) {
      const childPath = findPathToItem(item.children, targetId);
      if (childPath) {
        return [item, ...childPath];
      }
    }
  }
  return null;
}

function StudyPageContent() {
  const { t } = useTranslation();
  const searchParams = useSearchParams();
  const requestedItemId = searchParams.get("item") ?? "";
  const allItems = useMemo(() => flattenItems(STUDY_CHAPTERS), []);
  const requestedPath = useMemo(
    () =>
      requestedItemId
        ? findPathToItem(STUDY_CHAPTERS, requestedItemId)
        : null,
    [requestedItemId],
  );

  const [expandedChapterId, setExpandedChapterId] = useState<string>(
    requestedPath?.[0]?.id ?? STUDY_CHAPTERS[0].id,
  );
  const [activeItemId, setActiveItemId] = useState<string>(
    requestedPath?.[requestedPath.length - 1]?.id ?? STUDY_CHAPTERS[0].id,
  );
  const [expandedSectionIds, setExpandedSectionIds] = useState<string[]>(
    requestedPath && requestedPath.length >= 3 ? [requestedPath[1].id] : [],
  );

  const activeItem = useMemo(
    () =>
      allItems.find((item) => item.id === activeItemId) ?? STUDY_CHAPTERS[0],
    [activeItemId, allItems],
  );
  const hasRenderableContent = activeItem.content.trim().length > 0;
  const hasChildren = Boolean(activeItem.children?.length);

  return (
    <div className="h-screen p-4">
      <div className="h-full grid grid-cols-1 lg:grid-cols-[320px_minmax(0,1fr)] gap-4">
        <aside className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl p-4 overflow-y-auto">
          <div className="mb-4">
            <h1 className="text-lg font-semibold text-slate-900 dark:text-white">
              {t("Study Mode")}
            </h1>
            <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
              {t("Causality Learning Path")}
            </p>
          </div>

          <div className="space-y-2">
            {STUDY_CHAPTERS.map((chapter) => {
              const isExpanded = expandedChapterId === chapter.id;

              return (
                <div key={chapter.id} className="rounded-xl border border-slate-200 dark:border-slate-700 overflow-hidden">
                  <button
                    type="button"
                    onClick={() => {
                      setActiveItemId(chapter.id);
                      setExpandedChapterId((prev) =>
                        prev === chapter.id ? "" : chapter.id,
                      );
                    }}
                    className="w-full flex items-start gap-2 text-left p-3 bg-slate-50 dark:bg-slate-900 hover:bg-slate-100 dark:hover:bg-slate-700/60 transition-colors"
                  >
                    {isExpanded ? (
                      <ChevronDown className="w-4 h-4 mt-0.5 text-slate-500" />
                    ) : (
                      <ChevronRight className="w-4 h-4 mt-0.5 text-slate-500" />
                    )}
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-slate-900 dark:text-white">
                        {chapter.title}
                      </p>
                    </div>
                  </button>

                  {isExpanded && (
                    <div className="p-2 bg-white dark:bg-slate-800 space-y-1">
                      {chapter.children?.map((section) => {
                        const isActiveSection = activeItem.id === section.id;
                        const isSectionExpanded = expandedSectionIds.includes(
                          section.id,
                        );

                        return (
                          <div key={section.id} className="space-y-1">
                            <button
                              type="button"
                              onClick={() => {
                                setActiveItemId(section.id);
                                setExpandedSectionIds((prev) =>
                                  prev.includes(section.id)
                                    ? prev.filter((id) => id !== section.id)
                                    : [...prev, section.id],
                                );
                              }}
                              className={`w-full text-left rounded-lg px-3 py-2 border transition-colors ${
                                isActiveSection
                                  ? "bg-indigo-50 dark:bg-indigo-900/30 border-indigo-200 dark:border-indigo-700"
                                  : "bg-slate-50 dark:bg-slate-900 border-slate-200 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-700/60"
                              }`}
                            >
                              <div className="flex items-start gap-2">
                                {section.children?.length ? (
                                  isSectionExpanded ? (
                                    <ChevronDown className="w-3.5 h-3.5 mt-0.5 text-slate-500" />
                                  ) : (
                                    <ChevronRight className="w-3.5 h-3.5 mt-0.5 text-slate-500" />
                                  )
                                ) : null}
                                <p className="text-xs font-medium text-slate-900 dark:text-white">
                                  {section.title}
                                </p>
                              </div>
                            </button>

                            {isSectionExpanded &&
                              section.children?.map((subsection) => {
                              const isActiveSubsection =
                                activeItem.id === subsection.id;

                              return (
                                <button
                                  key={subsection.id}
                                  type="button"
                                  onClick={() => setActiveItemId(subsection.id)}
                                  className={`ml-4 w-[calc(100%-1rem)] text-left rounded-lg px-3 py-2 border transition-colors ${
                                    isActiveSubsection
                                      ? "bg-indigo-50 dark:bg-indigo-900/30 border-indigo-200 dark:border-indigo-700"
                                      : "bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-700/60"
                                  }`}
                                >
                                  <p className="text-xs text-slate-800 dark:text-slate-100">
                                    {subsection.title}
                                  </p>
                                </button>
                              );
                            })}
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </aside>

        <section className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl p-6 overflow-y-auto">
          <div className="flex items-center gap-2 mb-2">
            <BookOpen className="w-5 h-5 text-indigo-500" />
            <h2 className="text-xl font-semibold text-slate-900 dark:text-white">
              {activeItem.title}
            </h2>
          </div>

          {hasRenderableContent ? (
            <div className="rounded-xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 p-5">
              <MarkdownRenderer content={activeItem.content} variant="prose" />
            </div>
          ) : hasChildren ? (
            <div className="rounded-xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 p-5">
              <p className="text-sm text-slate-700 dark:text-slate-300 mb-4">
                {t("This topic is an overview. Select a subtopic below to continue.")}
              </p>
              <div className="space-y-2">
                {activeItem.children?.map((child) => (
                  <button
                    key={child.id}
                    type="button"
                    onClick={() => setActiveItemId(child.id)}
                    className="w-full text-left rounded-lg px-3 py-2 border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
                  >
                    <p className="text-sm font-medium text-slate-900 dark:text-white">
                      {child.title}
                    </p>
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="rounded-xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 p-5">
              <p className="text-sm text-slate-700 dark:text-slate-300">
                {t("Content will be added soon.")}
              </p>
            </div>
          )}

        </section>
      </div>
    </div>
  );
}

export default function StudyPage() {
  return (
    <Suspense fallback={<div className="h-screen p-4" />}>
      <StudyPageContent />
    </Suspense>
  );
}
