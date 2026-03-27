"use client";

import { Fragment, useEffect, useMemo, useState } from "react";
import { Loader2, Pencil } from "lucide-react";
import { useTranslation } from "react-i18next";

import { apiFetch } from "@/lib/api";
import {
  buildLearnerProfileForm,
  getExpertiseLevelOptions,
  getPriorKnowledgeOptions,
  LearnerProfileFormState,
  togglePriorKnowledge,
  toLearnerProfilePayload,
} from "@/lib/learner-profile";
import { Profile } from "@/types/profile";

function StepShell({
  step,
  stepLabels,
  t,
  children,
}: {
  step: number;
  stepLabels: string[];
  t: (key: string) => string;
  children: React.ReactNode;
}) {
  return (
    <div className="rounded-3xl border border-slate-200 bg-white p-8 shadow-sm dark:border-slate-700 dark:bg-slate-800">
      <div className="mb-8">
        <div className="mb-4 flex items-center justify-between gap-4">
          <div>
            <p className="text-sm font-medium uppercase tracking-[0.18em] text-blue-600 dark:text-blue-300">
              {t("Learner profile setup")}
            </p>
            <h1 className="mt-2 text-3xl font-semibold text-slate-950 dark:text-slate-50">
              {t("Tell us how you learn best")}
            </h1>
          </div>
        </div>

        <div className="mb-2 px-2">
          <div className="flex items-start">
            {stepLabels.map((label, index) => {
              const isComplete = index < step;
              const isCurrent = index === step;

              return (
                <Fragment key={label}>
                  <div className="flex w-24 shrink-0 flex-col items-center text-center">
                    <div
                      className={`z-10 flex h-10 w-10 items-center justify-center rounded-full border-2 text-sm font-semibold transition-colors ${
                        isComplete
                          ? "border-blue-600 bg-blue-600 text-white dark:border-blue-400 dark:bg-blue-500"
                          : isCurrent
                            ? "border-blue-600 bg-white text-blue-600 dark:border-blue-400 dark:bg-slate-800 dark:text-blue-300"
                            : "border-slate-400 bg-white text-slate-500 dark:border-slate-500 dark:bg-slate-800 dark:text-slate-400"
                      }`}
                    >
                      {isComplete ? (
                        <span className="text-lg font-bold leading-none">
                          ✓
                        </span>
                      ) : isCurrent ? (
                        <Pencil className="h-4 w-4" />
                      ) : (
                        index + 1
                      )}
                    </div>
                    <span
                      className={`mt-3 text-[13px] font-medium leading-5 ${
                        isComplete || isCurrent
                          ? "text-blue-600 dark:text-blue-300"
                          : "text-slate-500 dark:text-slate-400"
                      }`}
                    >
                      {label}
                    </span>
                  </div>

                  {index < stepLabels.length - 1 && (
                    <div
                      className={`mt-5 h-px flex-1 ${
                        index < step
                          ? "bg-blue-600 dark:bg-blue-400"
                          : "bg-slate-200 dark:bg-slate-700"
                      }`}
                    />
                  )}
                </Fragment>
              );
            })}
          </div>
        </div>
      </div>

      {children}
    </div>
  );
}

export default function LearnerOnboardingPage() {
  const { t } = useTranslation();
  const [profile, setProfile] = useState<Profile | null>(null);
  const [form, setForm] = useState<LearnerProfileFormState | null>(null);
  const [step, setStep] = useState(0);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const stepLabels = useMemo(
    () => [
      t("Background"),
      t("Role"),
      t("Prior knowledge"),
      t("Expertise level"),
      t("Learning goal"),
    ],
    [t],
  );
  const priorKnowledgeOptions = useMemo(() => getPriorKnowledgeOptions(t), [t]);
  const expertiseLevelOptions = useMemo(() => getExpertiseLevelOptions(t), [t]);

  useEffect(() => {
    let mounted = true;

    apiFetch("/api/v1/profile")
      .then(async (response) => {
        if (!response.ok) {
          throw new Error(t("Failed to load profile"));
        }
        return response.json();
      })
      .then((data: Profile) => {
        if (!mounted) return;
        if (data.learner_profile) {
          window.location.href = "/";
          return;
        }
        setProfile(data);
        setForm(buildLearnerProfileForm(null));
      })
      .catch(() => {
        if (!mounted) return;
        setError(t("We couldn't load your profile setup right now."));
      })
      .finally(() => {
        if (mounted) setLoading(false);
      });

    return () => {
      mounted = false;
    };
  }, [t]);

  const canGoBack = step > 0;
  const isLastStep = step === stepLabels.length - 1;
  const nextButtonLabel = isLastStep ? t("Finish") : t("Next Step");
  const title = useMemo(
    () => profile?.first_name || profile?.username || t("there"),
    [profile, t],
  );

  const updateForm = <K extends keyof LearnerProfileFormState>(
    field: K,
    value: LearnerProfileFormState[K],
  ) => {
    setForm((prev) => (prev ? { ...prev, [field]: value } : prev));
    setError(null);
  };

  const handleNext = async () => {
    if (!form) return;
    if (!isLastStep) {
      setStep((current) => Math.min(current + 1, stepLabels.length - 1));
      return;
    }

    setSaving(true);
    setError(null);

    try {
      const response = await apiFetch("/api/v1/profile/learner", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(toLearnerProfilePayload(form)),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        throw new Error(
          errorData?.detail || t("Failed to save learner profile"),
        );
      }

      const data = (await response.json()) as Profile;
      window.dispatchEvent(
        new CustomEvent("profile-updated", { detail: data }),
      );
      window.location.href = "/";
    } catch (saveError) {
      setError(
        saveError instanceof Error
          ? saveError.message
          : t("Failed to save learner profile"),
      );
    } finally {
      setSaving(false);
    }
  };

  const handleSkip = async () => {
    setSaving(true);
    setError(null);

    try {
      const response = await apiFetch("/api/v1/profile/learner/skip", {
        method: "POST",
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        throw new Error(errorData?.detail || t("Failed to skip setup"));
      }

      const data = (await response.json()) as Profile;
      window.dispatchEvent(
        new CustomEvent("profile-updated", { detail: data }),
      );
      window.location.href = "/";
    } catch (skipError) {
      setError(
        skipError instanceof Error
          ? skipError.message
          : t("Failed to skip setup"),
      );
    } finally {
      setSaving(false);
    }
  };

  if (loading || !form) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50 dark:bg-slate-900">
        <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 px-4 py-10 dark:bg-slate-900">
      <div className="mx-auto max-w-4xl">
        <StepShell step={step} stepLabels={stepLabels} t={t}>
          <div className="min-h-[180px]">
            {step === 0 && (
              <label className="grid gap-3 text-sm font-medium text-slate-700 dark:text-slate-200">
                {t("Background")}
                <textarea
                  value={form.background}
                  onChange={(event) =>
                    updateForm("background", event.target.value)
                  }
                  rows={6}
                  className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-slate-900 outline-none transition focus:border-blue-400 focus:bg-white focus:ring-2 focus:ring-blue-100 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100 dark:focus:border-blue-500 dark:focus:bg-slate-950 dark:focus:ring-blue-950/60"
                  placeholder={t(
                    "Share your background, training, or discipline.",
                  )}
                />
              </label>
            )}

            {step === 1 && (
              <label className="grid gap-3 text-sm font-medium text-slate-700 dark:text-slate-200">
                {t("Role")}
                <textarea
                  value={form.role}
                  onChange={(event) => updateForm("role", event.target.value)}
                  rows={6}
                  className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-slate-900 outline-none transition focus:border-blue-400 focus:bg-white focus:ring-2 focus:ring-blue-100 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100 dark:focus:border-blue-500 dark:focus:bg-slate-950 dark:focus:ring-blue-950/60"
                  placeholder={t("What best describes your current role?")}
                />
              </label>
            )}

            {step === 2 && (
              <div>
                <p className="mb-4 text-sm font-medium text-slate-700 dark:text-slate-200">
                  {t("Prior knowledge")}
                </p>
                <div className="grid gap-3 sm:grid-cols-2">
                  {priorKnowledgeOptions.map((option) => {
                    const checked = form.prior_knowledge.includes(option.value);
                    return (
                      <label
                        key={option.value}
                        className={`flex cursor-pointer items-center gap-3 rounded-2xl border px-4 py-4 text-sm transition ${
                          checked
                            ? "border-blue-300 bg-blue-50 text-blue-900 dark:border-blue-700 dark:bg-blue-950/30 dark:text-blue-100"
                            : "border-slate-200 bg-slate-50 text-slate-700 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200"
                        }`}
                      >
                        <input
                          type="checkbox"
                          className="h-4 w-4 rounded border-slate-300"
                          checked={checked}
                          onChange={() =>
                            updateForm(
                              "prior_knowledge",
                              togglePriorKnowledge(
                                form.prior_knowledge,
                                option.value,
                              ),
                            )
                          }
                        />
                        <span>{option.label}</span>
                      </label>
                    );
                  })}
                </div>
              </div>
            )}

            {step === 3 && (
              <div>
                <p className="mb-4 text-sm font-medium text-slate-700 dark:text-slate-200">
                  {t("Expertise level")}
                </p>
                <div className="grid gap-3 sm:grid-cols-3">
                  {expertiseLevelOptions.map((option) => {
                    const checked = form.expertise_level === option.value;
                    return (
                      <label
                        key={option.value}
                        className={`flex cursor-pointer items-center gap-3 rounded-2xl border px-4 py-4 text-sm transition ${
                          checked
                            ? "border-blue-300 bg-blue-50 text-blue-900 dark:border-blue-700 dark:bg-blue-950/30 dark:text-blue-100"
                            : "border-slate-200 bg-slate-50 text-slate-700 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200"
                        }`}
                      >
                        <input
                          type="radio"
                          name="expertise_level"
                          checked={checked}
                          onChange={() =>
                            updateForm("expertise_level", option.value)
                          }
                        />
                        <span>{option.label}</span>
                      </label>
                    );
                  })}
                </div>
              </div>
            )}

            {step === 4 && (
              <label className="grid gap-3 text-sm font-medium text-slate-700 dark:text-slate-200">
                {t("Learning goal")}
                <textarea
                  value={form.learning_goal}
                  onChange={(event) =>
                    updateForm("learning_goal", event.target.value)
                  }
                  rows={6}
                  className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-slate-900 outline-none transition focus:border-blue-400 focus:bg-white focus:ring-2 focus:ring-blue-100 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100 dark:focus:border-blue-500 dark:focus:bg-slate-950 dark:focus:ring-blue-950/60"
                  placeholder={t(
                    "What do you want to get better at with EducAgent?",
                  )}
                />
              </label>
            )}
          </div>

          {error && (
            <div className="mt-6 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-900/60 dark:bg-red-950/30 dark:text-red-300">
              {error}
            </div>
          )}

          <div className="mt-8 flex flex-col gap-3 border-t border-slate-200 pt-6 sm:flex-row sm:items-center sm:justify-between dark:border-slate-700">
            <button
              type="button"
              onClick={handleSkip}
              disabled={saving}
              className="inline-flex items-center justify-center rounded-xl border border-slate-200 px-4 py-3 text-sm font-medium text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60 dark:border-slate-600 dark:text-slate-200 dark:hover:bg-slate-700"
            >
              {t("Skip for now")}
            </button>

            <div className="flex gap-3">
              <button
                type="button"
                onClick={() => setStep((current) => Math.max(current - 1, 0))}
                disabled={!canGoBack || saving}
                className="inline-flex items-center justify-center rounded-xl border border-slate-200 px-4 py-3 text-sm font-medium text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60 dark:border-slate-600 dark:text-slate-200 dark:hover:bg-slate-700"
              >
                {t("Previous")}
              </button>
              <button
                type="button"
                onClick={handleNext}
                disabled={saving}
                className="inline-flex min-w-[120px] items-center justify-center rounded-xl bg-blue-600 px-5 py-3 text-sm font-medium text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-blue-300"
              >
                {saving ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  nextButtonLabel
                )}
              </button>
            </div>
          </div>
        </StepShell>
      </div>
    </div>
  );
}
