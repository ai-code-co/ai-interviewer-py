-- AI Evaluations Table
-- Stores structured AI evaluation results for candidates

create table if not exists ai_evaluations (
  id uuid primary key default gen_random_uuid(),
  candidate_id uuid not null references candidates(id) on delete cascade,
  score integer not null check (score >= 0 and score <= 100),
  recommendation text not null check (recommendation in ('STRONG_MATCH', 'POTENTIAL_MATCH', 'WEAK_MATCH')),
  matched_skills text[] not null default '{}',
  missing_skills text[] not null default '{}',
  strengths text[] not null default '{}',
  weaknesses text[] not null default '{}',
  summary text not null,
  status text not null check (status in ('PENDING', 'COMPLETED', 'FAILED')) default 'PENDING',
  error_message text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (candidate_id)
);

create index if not exists idx_ai_evaluations_candidate_id
  on ai_evaluations(candidate_id);

create index if not exists idx_ai_evaluations_status
  on ai_evaluations(status);

-- Update timestamp trigger
create or replace function update_updated_at_column()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

create trigger update_ai_evaluations_updated_at
  before update on ai_evaluations
  for each row
  execute function update_updated_at_column();

