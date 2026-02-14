-- Bootstrap schema snapshot.
-- For incremental changes, use versioned files in app/tidb/migrations/
-- and apply with: python migrate.py up

CREATE TABLE IF NOT EXISTS jobs (
  id VARCHAR(36) PRIMARY KEY,
  title TEXT NOT NULL,
  description TEXT NULL,
  status ENUM('open', 'closed') NOT NULL DEFAULT 'open',
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
);

CREATE TABLE IF NOT EXISTS application_tokens (
  id VARCHAR(36) PRIMARY KEY,
  token VARCHAR(255) NOT NULL UNIQUE,
  email VARCHAR(255) NOT NULL,
  issued_by VARCHAR(36) NULL,
  status ENUM('PENDING', 'USED', 'EXPIRED') NOT NULL DEFAULT 'PENDING',
  expires_at DATETIME(6) NOT NULL,
  used_at DATETIME(6) NULL,
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  INDEX idx_application_tokens_email (email)
);

CREATE TABLE IF NOT EXISTS candidates (
  id VARCHAR(36) PRIMARY KEY,
  job_id VARCHAR(36) NOT NULL,
  name VARCHAR(255) NOT NULL,
  email VARCHAR(255) NOT NULL,
  phone VARCHAR(50) NULL,
  status ENUM('PENDING', 'APPROVED', 'REJECTED') NOT NULL DEFAULT 'PENDING',
  status_updated_at DATETIME(6) NULL,
  status_updated_by VARCHAR(36) NULL,
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  UNIQUE KEY uq_candidates_email_job (email, job_id),
  INDEX idx_candidates_status (status),
  CONSTRAINT fk_candidates_job FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS candidate_documents (
  id VARCHAR(36) PRIMARY KEY,
  candidate_id VARCHAR(36) NOT NULL,
  storage_bucket VARCHAR(100) NOT NULL,
  storage_path TEXT NOT NULL,
  file_hash CHAR(64) NOT NULL,
  uploaded_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  INDEX idx_candidate_documents_candidate_id (candidate_id),
  CONSTRAINT fk_candidate_documents_candidate FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS ai_evaluations (
  id VARCHAR(36) PRIMARY KEY,
  candidate_id VARCHAR(36) NOT NULL,
  score INT NOT NULL,
  recommendation ENUM('STRONG_MATCH', 'POTENTIAL_MATCH', 'WEAK_MATCH') NOT NULL,
  matched_skills JSON NULL,
  missing_skills JSON NULL,
  strengths JSON NULL,
  weaknesses JSON NULL,
  summary TEXT NOT NULL,
  status ENUM('PENDING', 'COMPLETED', 'FAILED') NOT NULL DEFAULT 'PENDING',
  error_message TEXT NULL,
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  UNIQUE KEY uq_ai_evaluations_candidate_id (candidate_id),
  INDEX idx_ai_evaluations_status (status),
  CONSTRAINT fk_ai_evaluations_candidate FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS interview_questions (
  id VARCHAR(36) PRIMARY KEY,
  job_id VARCHAR(36) NOT NULL,
  question_text TEXT NOT NULL,
  expected_keywords JSON NULL,
  question_order INT NOT NULL,
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  INDEX idx_interview_questions_job_order (job_id, question_order),
  CONSTRAINT fk_interview_questions_job FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS interview_sessions (
  id VARCHAR(36) PRIMARY KEY,
  candidate_id VARCHAR(36) NOT NULL,
  job_id VARCHAR(36) NOT NULL,
  access_token VARCHAR(255) NULL UNIQUE,
  status ENUM('PENDING', 'IN_PROGRESS', 'COMPLETED') NOT NULL DEFAULT 'PENDING',
  last_question_id VARCHAR(36) NULL,
  duration TEXT NULL,
  transcript_url TEXT NULL,
  completed_at DATETIME(6) NULL,
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  INDEX idx_interview_sessions_candidate (candidate_id),
  INDEX idx_interview_sessions_job (job_id),
  CONSTRAINT fk_interview_sessions_candidate FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE CASCADE,
  CONSTRAINT fk_interview_sessions_job FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS interview_responses (
  id VARCHAR(36) PRIMARY KEY,
  session_id VARCHAR(36) NOT NULL,
  question_id VARCHAR(36) NOT NULL,
  answer_text LONGTEXT NULL,
  answer_audio_url TEXT NULL,
  answer_video_url TEXT NULL,
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  INDEX idx_interview_responses_session (session_id),
  CONSTRAINT fk_interview_responses_session FOREIGN KEY (session_id) REFERENCES interview_sessions(id) ON DELETE CASCADE,
  CONSTRAINT fk_interview_responses_question FOREIGN KEY (question_id) REFERENCES interview_questions(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS ai_interview_evaluations (
  id VARCHAR(36) PRIMARY KEY,
  session_id VARCHAR(36) NOT NULL UNIQUE,
  score INT NULL,
  recommendation VARCHAR(50) NULL,
  summary TEXT NULL,
  matched_skills JSON NULL,
  missing_skills JSON NULL,
  strengths JSON NULL,
  areas_for_improvement JSON NULL,
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  CONSTRAINT fk_ai_interview_evaluations_session FOREIGN KEY (session_id) REFERENCES interview_sessions(id) ON DELETE CASCADE
);
