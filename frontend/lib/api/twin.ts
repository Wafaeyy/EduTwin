export type TwinProfile = {
  full_name: string;
  email: string;
  university: string;
  fied_of_study: string;
  education_stage: string;
  current_year: number | null;
};

export type TwinGoal = {
  goal_id: string;
  title: string;
  description: string;
  priority: string;
  status: string;
  progress: number;
  target_completion_date: string | null;
};

export type TwinSkill = {
  skill_id: string;
  name: string;
  description: string | null;
  skill_level: number;
  confidence: number;
  last_updated: string;
};

export type TwinInterest = {
  interest_id: string;
  topic: string;
  description: string | null;
  affinity: number;
  confidence: number;
  last_updated: string;
};

export type TwinKnowledge = {
  knowledge_id: string;
  title: string;
  description: string | null;
  mastery: number;
  confidence: number;
  last_updated: string;
};

export type TwinPreference = {
  preference_id: string;
  dimension: string;
  context: string;
  affinities: Record<string, number>;
  last_updated: string;
};

export type StudentTwin = {
  twin_id: string;
  profile: TwinProfile;
  goals: TwinGoal[];
  preferences: TwinPreference[];
  knowledge: TwinKnowledge[];
  skills: TwinSkill[];
  interests: TwinInterest[];
  created_at: string;
  last_updated: string;
};

const API_BASE_URL = "http://127.0.0.1:8000";

export async function getTwin(): Promise<StudentTwin> {
  const response = await fetch(
    `${API_BASE_URL}/twin`
  );

  if (!response.ok) {
    throw new Error("Failed to load Digital Twin.");
  }

  return response.json();
}