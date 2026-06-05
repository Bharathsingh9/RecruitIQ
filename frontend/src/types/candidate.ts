export interface Candidate {
  id: number;
  name: string;
  email: string | null;
  phone: string | null;
  resume_score: number; // JD match score %
  overall_resume_score?: number; // Weighted resume score
  grade?: string;
  experience_years: number;
  education_score: number;
  certifications: number;
  prediction: string; // 'Shortlist' | 'Needs Review' | 'Reject'
  confidence?: number;
  rank_score?: number;
  matched_skills: string[];
  missing_skills: string[];
  created_at: string;
  rank?: number;
  filtered_rank?: number;
}

export interface Evaluation {
  id: number;
  candidate_id: number;
  question: string;
  answer: string;
  score: number;
  technical_depth: number;
  communication: number;
  completeness: number;
  strengths: string[];
  improvements: string[];
  created_at: string;
}

export interface KPIStats {
  total: number;
  shortlisted: number;
  needs_review: number;
  rejected: number;
  average_score: number;
}

export interface SkillStats {
  skill: string;
  count: number;
}

export interface ScoreBucket {
  range: string;
  count: number;
}

export interface ExperienceScorePlot {
  name: string;
  experience: number;
  score: number;
  prediction: string;
}

export interface AnalyticsResponse {
  kpis: KPIStats;
  prediction_distribution: { name: string; value: number }[];
  top_skills: SkillStats[];
  top_missing_skills: SkillStats[];
  score_distribution: ScoreBucket[];
  experience_vs_score: ExperienceScorePlot[];
}
