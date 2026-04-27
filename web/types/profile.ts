export type LearnerProfilePriorKnowledge =
  | "probability_statistics"
  | "machine_learning"
  | "correlation_vs_causation"
  | "confounding_controls"
  | "dags_causal_graphs"
  | "experiments_ab_tests"
  | "potential_outcomes"
  | "interventions_do_calculus"
  | "counterfactuals"
  | "none";

export type LearnerProfileExpertiseLevel =
  | "new_to_causality"
  | "knows_correlation_confounding"
  | "reads_dags"
  | "used_causal_methods"
  | "comfortable_formal_scm";

export interface LearnerProfile {
  id: string;
  background: string | null;
  role: string | null;
  prior_knowledge: LearnerProfilePriorKnowledge[];
  expertise_level: LearnerProfileExpertiseLevel | null;
  learning_goal: string | null;
  is_skipped: boolean;
  created_at: string;
  updated_at: string;
}

export type LearnerAdaptationProfileSig =
  | "computer_science_ml"
  | "radiologist"
  | "biologist"
  | "material"
  | "education";

export interface LearnerAdaptationContext {
  background_summary: string | null;
  role_summary: string | null;
  prior_knowledge: LearnerProfilePriorKnowledge[];
  expertise_level: LearnerProfileExpertiseLevel | null;
  learning_goal_summary: string | null;
  domain_framing: string | null;
}

export interface LearnerAdaptation {
  id: string;
  profile_sig: LearnerAdaptationProfileSig;
  adaptation_ctx: LearnerAdaptationContext;
  generated_at: string;
  source_profile_updated_at: string | null;
}

export interface Profile {
  id: string;
  email: string;
  username: string;
  first_name: string | null;
  last_name: string | null;
  institution: string | null;
  avatar_url: string | null;
  is_active: boolean;
  is_verified: boolean;
  is_superuser: boolean;
  created_at: string | null;
  updated_at: string | null;
  learner_profile: LearnerProfile | null;
  learner_adaptation: LearnerAdaptation | null;
}
