"use client";

import { useState } from "react";
import { CheckCircle2, Circle, XCircle } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import { useTranslation } from "react-i18next";
import type { StudyQuizQuestion } from "@/content/study";
import { processLatexContent } from "@/lib/latex";

interface InteractiveQuizProps {
  questions: StudyQuizQuestion[];
}

function InlineMarkdown({ content }: { content: string }) {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm, remarkMath]}
      rehypePlugins={[rehypeKatex]}
      components={{
        p: ({ children }) => <>{children}</>,
        em: ({ children }) => <em>{children}</em>,
        strong: ({ children }) => <strong>{children}</strong>,
      }}
    >
      {processLatexContent(content)}
    </ReactMarkdown>
  );
}

export default function InteractiveQuiz({ questions }: InteractiveQuizProps) {
  const { t } = useTranslation();
  const [selectedAnswers, setSelectedAnswers] = useState<
    Record<string, string>
  >({});

  return (
    <section className="mt-6 rounded-xl border border-slate-200 bg-slate-50 p-5 dark:border-slate-700 dark:bg-slate-900">
      <div className="mb-5">
        <h3 className="text-lg font-semibold text-slate-900 dark:text-white">
          {t("Check Your Understanding")}
        </h3>
        <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">
          {t(
            "Select an answer. Correct answers show the explanation right away.",
          )}
        </p>
      </div>

      <div className="space-y-6">
        {questions.map((question, index) => {
          const selectedOptionId = selectedAnswers[question.id];
          const isCorrect = selectedOptionId === question.correctOptionId;
          const hasSelection = Boolean(selectedOptionId);

          return (
            <div
              key={question.id}
              className="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-800"
            >
              <p className="text-sm font-medium leading-relaxed text-slate-900 dark:text-white">
                {index + 1}. <InlineMarkdown content={question.prompt} />
              </p>

              <div className="mt-4 space-y-2">
                {question.options.map((option) => {
                  const isSelected = selectedOptionId === option.id;
                  const showCorrectState = isSelected && isCorrect;
                  const showWrongState =
                    isSelected && hasSelection && !isCorrect;

                  return (
                    <button
                      key={option.id}
                      type="button"
                      onClick={() =>
                        setSelectedAnswers((current) => ({
                          ...current,
                          [question.id]: option.id,
                        }))
                      }
                      className={`w-full rounded-lg border px-3 py-3 text-left transition-colors ${
                        showCorrectState
                          ? "border-emerald-300 bg-emerald-50 dark:border-emerald-700 dark:bg-emerald-900/20"
                          : showWrongState
                            ? "border-rose-300 bg-rose-50 dark:border-rose-700 dark:bg-rose-900/20"
                            : isSelected
                              ? "border-indigo-300 bg-indigo-50 dark:border-indigo-700 dark:bg-indigo-900/20"
                              : "border-slate-200 bg-white hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900 dark:hover:bg-slate-800"
                      }`}
                    >
                      <div className="flex items-start gap-3">
                        <span className="mt-0.5 shrink-0">
                          {showCorrectState ? (
                            <CheckCircle2 className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
                          ) : showWrongState ? (
                            <XCircle className="h-4 w-4 text-rose-600 dark:text-rose-400" />
                          ) : (
                            <Circle className="h-4 w-4 text-slate-400" />
                          )}
                        </span>
                        <span className="text-sm text-slate-800 dark:text-slate-100">
                          <span className="font-medium">{option.label}) </span>
                          <InlineMarkdown content={option.text} />
                        </span>
                      </div>
                    </button>
                  );
                })}
              </div>

              {hasSelection && !isCorrect ? (
                <div className="mt-3 rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700 dark:border-rose-800 dark:bg-rose-950/30 dark:text-rose-300">
                  {t("That's not correct. Try another option.")}
                </div>
              ) : null}

              {isCorrect ? (
                <div className="mt-3 rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-3 text-sm text-emerald-800 dark:border-emerald-800 dark:bg-emerald-950/30 dark:text-emerald-200">
                  <p className="font-medium">{t("Correct")}</p>
                  <div className="mt-1 leading-relaxed">
                    <InlineMarkdown content={question.explanation} />
                  </div>
                </div>
              ) : null}
            </div>
          );
        })}
      </div>
    </section>
  );
}
