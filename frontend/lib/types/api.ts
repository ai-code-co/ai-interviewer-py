export interface Job {
  id: string
  title: string
  description: string | null
  status: "open" | "closed"
  created_at: string
}

export interface CandidateWithJob {
  id: string
  name: string
  email: string
  phone: string | null
  created_at: string
  job: {
    id: string
    title: string
    description: string | null
  }
}



export interface AIEvaluation {
  score: number
  recommendation: "STRONG_MATCH" | "POTENTIAL_MATCH" | "WEAK_MATCH"
  matched_skills: Record<string, string> | string[]
  missing_skills: Record<string, string> | string[]
  strengths: Record<string, string> | string[]
  weaknesses: Record<string, string> | string[]
  summary: string
  status: "PENDING" | "COMPLETED" | "FAILED"
  created_at?: string
  updated_at?: string
  error_message?: string
}

// Helper interfaces for better readability
export interface SkillDetail {
  skill: string;
  reason: string;
}

export interface AssessmentPoint {
  header: string;
  detail: string;
}

export interface InterviewEvaluation {
  id?: string;
  session_id?: string;
  score: number;
  recommendation:"STRONG_MATCH" | "POTENTIAL_MATCH" | "WEAK_MATCH";
  summary: string;
  matched_skills: SkillDetail[];
  missing_skills: SkillDetail[];
  strengths: AssessmentPoint[];
  areas_for_improvement: AssessmentPoint[];
  created_at?: string;
}

export interface CandidateDetail extends CandidateWithJob {
  status?: "PENDING" | "APPROVED" | "REJECTED"
  status_updated_at?: string | null
  status_updated_by?: string | null
  documents: {
    id: string
    storage_bucket: string
    storage_path: string
    file_hash: string
    uploaded_at: string
    url?: string | null
  }[]
  evaluation?: AIEvaluation
  // ADD THIS NEW FIELD:
  interview?: {
    id: string
    status: string
    video_url?: string
    transcript_url?: string
    started_at: string
    completed_at?: string
  }
  ai_interview_report?: InterviewEvaluation

}

export interface InvitedCandidate {
  id: string
  email: string
  status: "PENDING" | "USED" | "EXPIRED"
  created_at: string
  expires_at: string
  used_at: string | null
  has_applied: boolean
}

