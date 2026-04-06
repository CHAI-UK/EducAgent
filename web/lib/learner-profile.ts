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
    { label: t("Machine Learning"), value: "machine_learning" },
    { label: t("Correlation vs causation"), value: "correlation_vs_causation" },
    { label: t("Confounding and controls"), value: "confounding_controls" },
    {
      label: t("DAGs / causal graphs"),
      value: "dags_causal_graphs",
    },
    { label: t("Experiments and A/B tests"), value: "experiments_ab_tests" },
    { label: t("Potential outcomes"), value: "potential_outcomes" },
    {
      label: t("Interventions / do-calculus"),
      value: "interventions_do_calculus",
    },
    { label: t("Counterfactuals"), value: "counterfactuals" },
    { label: t("None yet"), value: "none" },
  ];
}

export function getExpertiseLevelOptions(t: TFunction): Array<{
  label: string;
  value: LearnerProfileExpertiseLevel;
}> {
  return [
    { label: t("I'm new to causality"), value: "new_to_causality" },
    {
      label: t("I know correlation and confounding"),
      value: "knows_correlation_confounding",
    },
    { label: t("I can read DAGs"), value: "reads_dags" },
    {
      label: t("I've used causal inference methods"),
      value: "used_causal_methods",
    },
    {
      label: t("I'm comfortable with formal SCM / do-calculus ideas"),
      value: "comfortable_formal_scm",
    },
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

  const priorKnowledge = learnerProfile.prior_knowledge.reduce<
    LearnerProfilePriorKnowledge[]
  >((normalized, item) => {
    if (item === "none") {
      return ["none"];
    }
    if (normalized.includes("none") || normalized.includes(item)) {
      return normalized;
    }
    return [...normalized, item];
  }, []);

  return {
    background: learnerProfile.background ?? "",
    role: learnerProfile.role ?? "",
    prior_knowledge: priorKnowledge,
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
