create table public.ai_interview_evaluations (
  id uuid default gen_random_uuid() primary key,
  session_id uuid references public.interview_sessions(id) on delete cascade not null unique,
  score integer,
  recommendation text,
  summary text,
  matched_skills jsonb, -- Stores the array of skill objects
  missing_skills jsonb, -- Stores the array of skill objects
  strengths jsonb,      -- Stores the array of strength objects
  areas_for_improvement jsonb, -- Stores the array of improvement objects
  created_at timestamptz default now()
);

-- Optional: Enable Row Level Security (RLS)
alter table public.ai_interview_evaluations enable row level security;

-- Optional: Policy to allow read access (adjust based on your auth needs)
create policy "Allow read access to all users"
on public.ai_interview_evaluations for select
using (true);