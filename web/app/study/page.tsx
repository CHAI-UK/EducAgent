"use client";

import { useMemo, useState } from "react";
import { BookOpen, CheckCircle2 } from "lucide-react";
import { useTranslation } from "react-i18next";

interface Topic {
  id: string;
  title: string;
  objective: string;
  duration: string;
  content: string[];
}

const TOPICS: Topic[] = [
  {
    id: "foundations",
    title: "1. Foundations of Causality",
    objective: "Understand why correlation is not causation.",
    duration: "10 min",
    content: [
      "Causality studies what happens when we intervene in a system, not just when we observe it.",
      "A correlation can appear because of a common cause, selection bias, or pure coincidence.",
      "Your first mental model should be: if I force X to change, what happens to Y?",
    ],
  },
  {
    id: "dags",
    title: "2. Causal Graphs (DAGs)",
    objective: "Represent assumptions using directed acyclic graphs.",
    duration: "12 min",
    content: [
      "A causal graph encodes assumptions about how variables influence one another.",
      "Edges indicate direct causal influence. Missing edges indicate no direct influence.",
      "Acyclic means no feedback loops in the same time slice.",
    ],
  },
  {
    id: "confounding",
    title: "3. Confounding and Backdoor Paths",
    objective: "Detect and block confounding bias.",
    duration: "14 min",
    content: [
      "A confounder is a common cause of treatment and outcome.",
      "Backdoor paths create spurious associations between treatment and outcome.",
      "To estimate causal effect, control for an appropriate adjustment set.",
    ],
  },
  {
    id: "interventions",
    title: "4. Interventions and do-Operator",
    objective: "Differentiate observing from intervening.",
    duration: "15 min",
    content: [
      "P(Y | X = x) is observational; P(Y | do(X = x)) is interventional.",
      "The do-operator removes incoming edges into X and models external assignment.",
      "This lets us answer policy questions such as: what if we set treatment to 1?",
    ],
  },
  {
    id: "counterfactuals",
    title: "5. Counterfactual Reasoning",
    objective: "Reason about what would have happened under alternate actions.",
    duration: "16 min",
    content: [
      "Counterfactuals ask about alternate worlds for the same unit.",
      "Example: would this student have passed if they had studied two more hours?",
      "They are central to fairness analysis, root-cause diagnosis, and personalized decisions.",
    ],
  },
];

export default function StudyPage() {
  const { t } = useTranslation();
  const [activeTopicId, setActiveTopicId] = useState<string>(TOPICS[0].id);

  const activeTopic = useMemo(
    () => TOPICS.find((topic) => topic.id === activeTopicId) ?? TOPICS[0],
    [activeTopicId],
  );

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
            {TOPICS.map((topic) => {
              const isActive = topic.id === activeTopic.id;
              return (
                <button
                  key={topic.id}
                  type="button"
                  onClick={() => setActiveTopicId(topic.id)}
                  className={`w-full text-left rounded-xl p-3 border transition-colors ${
                    isActive
                      ? "bg-indigo-50 dark:bg-indigo-900/30 border-indigo-200 dark:border-indigo-700"
                      : "bg-slate-50 dark:bg-slate-900 border-slate-200 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-700/60"
                  }`}
                >
                  <p className="text-sm font-medium text-slate-900 dark:text-white">
                    {topic.title}
                  </p>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                    {topic.duration}
                  </p>
                </button>
              );
            })}
          </div>
        </aside>

        <section className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl p-6 overflow-y-auto">
          <div className="flex items-center gap-2 mb-2">
            <BookOpen className="w-5 h-5 text-indigo-500" />
            <h2 className="text-xl font-semibold text-slate-900 dark:text-white">
              {activeTopic.title}
            </h2>
          </div>

          <p className="text-sm text-slate-600 dark:text-slate-300 mb-6">
            {activeTopic.objective}
          </p>

          <div className="space-y-4">
            {activeTopic.content.map((paragraph, index) => (
              <div
                key={`${activeTopic.id}-${index}`}
                className="p-4 rounded-xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700"
              >
                <p className="text-sm leading-6 text-slate-700 dark:text-slate-200">
                  {paragraph}
                </p>
              </div>
            ))}
          </div>

          <div className="mt-8 p-4 rounded-xl border border-emerald-200 dark:border-emerald-800 bg-emerald-50 dark:bg-emerald-900/20">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
              <p className="text-sm font-medium text-emerald-800 dark:text-emerald-300">
                {t("AI-generated lesson content will be plugged into this panel next.")}
              </p>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
