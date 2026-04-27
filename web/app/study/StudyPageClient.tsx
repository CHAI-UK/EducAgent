"use client";

import { useEffect, useMemo, useRef } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { BookOpen, ChevronLeft, ChevronRight, Layers } from "lucide-react";
import { useTranslation } from "react-i18next";
import MarkdownRenderer from "@/components/common/MarkdownRenderer";
import type { StudyPath } from "@/content/study";
import InteractiveQuiz from "@/components/study/InteractiveQuiz";

interface StudyPageClientProps {
  studyPath: StudyPath;
}

export default function StudyPageClient({ studyPath }: StudyPageClientProps) {
  const { t } = useTranslation();
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const contentRef = useRef<HTMLElement | null>(null);

  const activeNodeId = searchParams.get("item") ?? "";
  const activeSectionId = searchParams.get("section") ?? "";
  const activeNode = useMemo(
    () =>
      studyPath.nodes.find((node) => node.id === activeNodeId) ??
      studyPath.nodes[0],
    [activeNodeId, studyPath.nodes],
  );

  const activeIndex = studyPath.nodes.findIndex(
    (node) => node.id === activeNode.id,
  );
  const previousNode =
    activeIndex > 0 ? studyPath.nodes[activeIndex - 1] : null;
  const nextNode =
    activeIndex >= 0 && activeIndex < studyPath.nodes.length - 1
      ? studyPath.nodes[activeIndex + 1]
      : null;
  const nodeGroups = useMemo(() => {
    const groups: Array<{
      id: string;
      title: string;
      nodes: typeof studyPath.nodes;
    }> = [];

    for (const node of studyPath.nodes) {
      const groupId = node.topic?.id ?? "study-sections";
      const groupTitle = node.topic?.title ?? t("Sections");
      const existingGroup = groups.find((group) => group.id === groupId);

      if (existingGroup) {
        existingGroup.nodes.push(node);
        continue;
      }

      groups.push({
        id: groupId,
        title: groupTitle,
        nodes: [node],
      });
    }

    return groups;
  }, [studyPath.nodes, t]);

  const openNode = (nodeId: string) => {
    const params = new URLSearchParams(searchParams.toString());
    params.set("item", nodeId);
    params.delete("section");
    router.push(`${pathname}?${params.toString()}`, { scroll: false });
  };

  const openConcept = (conceptId: string) => {
    const params = new URLSearchParams(searchParams.toString());
    params.set("concept", conceptId);
    params.delete("item");
    params.delete("section");
    router.push(`${pathname}?${params.toString()}`, { scroll: false });
  };

  const openSection = (nodeId: string, sectionId: string) => {
    const params = new URLSearchParams(searchParams.toString());
    params.set("item", nodeId);
    params.set("section", sectionId);
    router.push(`${pathname}?${params.toString()}`, { scroll: false });
  };

  useEffect(() => {
    contentRef.current?.scrollTo({ top: 0, behavior: "auto" });
  }, [activeNode.id]);

  useEffect(() => {
    if (!activeSectionId) {
      return;
    }

    const scrollToSection = () => {
      const contentElement = contentRef.current;
      const sectionElement = document.getElementById(activeSectionId);
      if (!contentElement || !sectionElement) {
        return;
      }

      const contentRect = contentElement.getBoundingClientRect();
      const sectionRect = sectionElement.getBoundingClientRect();
      const offsetWithinContent =
        sectionRect.top - contentRect.top + contentElement.scrollTop;

      contentElement.scrollTo({
        top: Math.max(offsetWithinContent - 16, 0),
        behavior: "smooth",
      });
    };

    const frameId = window.requestAnimationFrame(scrollToSection);
    return () => window.cancelAnimationFrame(frameId);
  }, [activeNode.id, activeSectionId]);

  useEffect(() => {
    const previousHtmlOverflow = document.documentElement.style.overflow;
    const previousBodyOverflow = document.body.style.overflow;

    document.documentElement.style.overflow = "hidden";
    document.body.style.overflow = "hidden";

    return () => {
      document.documentElement.style.overflow = previousHtmlOverflow;
      document.body.style.overflow = previousBodyOverflow;
    };
  }, []);

  return (
    <div className="h-[calc(100dvh-3rem)] overflow-hidden p-4">
      <div className="grid h-full min-h-0 grid-cols-1 gap-4 lg:grid-cols-[320px_minmax(0,1fr)]">
        <aside className="min-h-0 overflow-y-auto rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-800">
          <div className="mb-4">
            <h1 className="text-lg font-semibold text-slate-900 dark:text-white">
              {studyPath.title}
            </h1>
          </div>

          {studyPath.availableConcepts.length > 1 ? (
            <div className="mb-4">
              <div className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase text-slate-500 dark:text-slate-400">
                <Layers className="h-3.5 w-3.5" />
                {t("Concepts")}
              </div>
              <div className="space-y-1">
                {studyPath.availableConcepts.map((concept) => {
                  const isActive = studyPath.conceptId === concept.id;

                  return (
                    <button
                      key={concept.id}
                      type="button"
                      onClick={() => openConcept(concept.id)}
                      className={`w-full rounded-lg px-3 py-2 text-left text-sm transition-colors ${
                        isActive
                          ? "bg-slate-900 text-white dark:bg-white dark:text-slate-900"
                          : "text-slate-700 hover:bg-slate-100 dark:text-slate-200 dark:hover:bg-slate-700/60"
                      }`}
                    >
                      {concept.title}
                    </button>
                  );
                })}
              </div>
            </div>
          ) : null}

          <div className="space-y-4">
            {nodeGroups.map((group) => {
              const groupIsActive = group.nodes.some(
                (node) => activeNode.id === node.id,
              );

              return (
                <div key={group.id} className="space-y-1.5">
                  <div
                    className={`rounded-lg px-3 py-2 text-sm font-semibold ${
                      groupIsActive
                        ? "bg-slate-100 text-slate-950 dark:bg-slate-700/60 dark:text-white"
                        : "text-slate-700 dark:text-slate-200"
                    }`}
                  >
                    {group.title}
                  </div>

                  <div className="ml-3 space-y-1 border-l border-slate-200 pl-3 dark:border-slate-700">
                    {group.nodes.map((node) => {
                      const isActive = activeNode.id === node.id;

                      return (
                        <div key={node.id} className="space-y-1">
                          <button
                            type="button"
                            onClick={() => openNode(node.id)}
                            className={`w-full rounded-lg px-3 py-2 text-left transition-colors ${
                              isActive
                                ? "bg-indigo-50 text-indigo-900 dark:bg-indigo-900/30 dark:text-indigo-100"
                                : "text-slate-700 hover:bg-slate-100 dark:text-slate-200 dark:hover:bg-slate-700/60"
                            }`}
                          >
                            <p className="text-sm font-medium">{node.title}</p>
                          </button>

                          {node.subtopics?.length ? (
                            <div className="ml-3 space-y-1 border-l border-slate-200 pl-3 dark:border-slate-700">
                              {node.subtopics.map((subtopic) => {
                                const isActiveSection =
                                  isActive && activeSectionId === subtopic.id;

                                return (
                                  <button
                                    key={subtopic.id}
                                    type="button"
                                    onClick={() =>
                                      openSection(node.id, subtopic.id)
                                    }
                                    className={`w-full rounded-md px-2 py-1.5 text-left text-xs transition-colors ${
                                      isActiveSection
                                        ? "bg-slate-100 text-slate-900 dark:bg-slate-700/70 dark:text-white"
                                        : "text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-700/50"
                                    }`}
                                  >
                                    {subtopic.title}
                                  </button>
                                );
                              })}
                            </div>
                          ) : null}
                        </div>
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </div>
        </aside>

        <section
          ref={contentRef}
          className="min-h-0 overflow-y-auto rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-700 dark:bg-slate-800"
        >
          <div className="flex items-center gap-2 mb-2">
            <BookOpen className="w-5 h-5 text-indigo-500" />
            <h2 className="text-xl font-semibold text-slate-900 dark:text-white">
              {activeNode.title}
            </h2>
          </div>

          {activeNode.content ? (
            <div className="rounded-xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 p-5">
              <MarkdownRenderer content={activeNode.content} variant="prose" />
            </div>
          ) : null}

          {activeNode.quiz?.length ? (
            <InteractiveQuiz questions={activeNode.quiz} />
          ) : null}

          <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <button
              type="button"
              onClick={() => previousNode && openNode(previousNode.id)}
              disabled={!previousNode}
              className="inline-flex items-center justify-center gap-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 px-4 py-2 text-sm text-slate-700 dark:text-slate-200 disabled:cursor-not-allowed disabled:opacity-50"
            >
              <ChevronLeft className="h-4 w-4" />
              {t("Previous")}
            </button>
            <button
              type="button"
              onClick={() => nextNode && openNode(nextNode.id)}
              disabled={!nextNode}
              className="inline-flex items-center justify-center gap-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 px-4 py-2 text-sm text-slate-700 dark:text-slate-200 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {t("Next")}
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        </section>
      </div>
    </div>
  );
}
