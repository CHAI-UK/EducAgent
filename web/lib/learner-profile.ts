import {
  LearnerProfile,
  LearnerProfileExpertiseLevel,
  LearnerProfilePriorKnowledge,
} from "@/types/profile";
import { TFunction } from "i18next";

export interface LearnerProfileFormState {
  background: string;
  role: string;
  prior_knowledge: LearnerProfilePriorKnowledge[];
  expertise_level: LearnerProfileExpertiseLevel | "";
  learning_goal: string;
}

export function getPriorKnowledgeOptions(t: TFunction): Array<{
  label: string;
  value: LearnerProfilePriorKnowledge;
}> {
  return [
    {
      label: t("Probability/Statistics"),
      value: "probability_statistics",
    },
    { label: t("Linear Regression"), value: "linear_regression" },
    { label: t("Machine Learning"), value: "machine_learning" },
    { label: t("Bayesian Reasoning"), value: "bayesian_reasoning" },
    {
      label: t("Epidemiology/Study Design"),
      value: "epidemiology_study_design",
    },
    { label: t("DAGs/Graphical Models"), value: "dags_graphical_models" },
    { label: t("None"), value: "none" },
  ];
}

export function getExpertiseLevelOptions(t: TFunction): Array<{
  label: string;
  value: LearnerProfileExpertiseLevel;
}> {
  return [
    { label: t("Beginner"), value: "beginner" },
    { label: t("Moderate"), value: "moderate" },
    { label: t("Expert"), value: "expert" },
  ];
}

export function buildLearnerProfileForm(
  learnerProfile: LearnerProfile | null,
): LearnerProfileFormState {
  if (!learnerProfile || learnerProfile.is_skipped) {
    return {
      background: "",
      role: "",
      prior_knowledge: [],
      expertise_level: "",
      learning_goal: "",
    };
  }

  return {
    background: learnerProfile.background ?? "",
    role: learnerProfile.role ?? "",
    prior_knowledge: learnerProfile.prior_knowledge,
    expertise_level: learnerProfile.expertise_level ?? "",
    learning_goal: learnerProfile.learning_goal ?? "",
  };
}

export function togglePriorKnowledge(
  current: LearnerProfilePriorKnowledge[],
  value: LearnerProfilePriorKnowledge,
): LearnerProfilePriorKnowledge[] {
  if (value === "none") {
    return current.includes("none") ? [] : ["none"];
  }

  const withoutNone = current.filter((item) => item !== "none");
  if (withoutNone.includes(value)) {
    return withoutNone.filter((item) => item !== value);
  }

  return [...withoutNone, value];
}

export function toLearnerProfilePayload(form: LearnerProfileFormState) {
  return {
    background: form.background.trim() || null,
    role: form.role.trim() || null,
    prior_knowledge: form.prior_knowledge,
    expertise_level: form.expertise_level || null,
    learning_goal: form.learning_goal.trim() || null,
  };
}
