export type LearnerProfilePriorKnowledge =
  | "probability_statistics"
  | "linear_regression"
  | "machine_learning"
  | "bayesian_reasoning"
  | "epidemiology_study_design"
  | "dags_graphical_models"
  | "none";

export type LearnerProfileExpertiseLevel = "beginner" | "moderate" | "expert";

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
}
