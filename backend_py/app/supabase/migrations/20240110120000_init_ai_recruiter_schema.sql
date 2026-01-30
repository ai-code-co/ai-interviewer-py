-- Enable UUID generation
create extension if not exists "pgcrypto";

------------------------------------------------
-- JOBS
------------------------------------------------
create table if not exists jobs (
  id uuid primary key default gen_random_uuid(),
  title text not null,
  description text,
  status text not null
    check (status in ('open', 'closed')) default 'open',
  created_at timestamptz not null default now()
);

------------------------------------------------
-- PROFILES (extends auth.users)
------------------------------------------------
create table if not exists profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  full_name text,
  email text,
  created_at timestamptz not null default now()
);

------------------------------------------------
-- APPLICATION TOKENS
------------------------------------------------
create table if not exists application_tokens (
  id uuid primary key default gen_random_uuid(),
  token text not null unique,
  email text not null,
  issued_by uuid not null references auth.users(id) on delete restrict,
  status text not null
    check (status in ('PENDING', 'USED', 'EXPIRED')) default 'PENDING',
  expires_at timestamptz not null,
  used_at timestamptz,
  created_at timestamptz not null default now()
);

create index if not exists idx_application_tokens_token
  on application_tokens(token);

create index if not exists idx_application_tokens_email
  on application_tokens(email);

------------------------------------------------
-- CANDIDATES
------------------------------------------------
create table if not exists candidates (
  id uuid primary key default gen_random_uuid(),
  job_id uuid not null references jobs(id) on delete restrict,
  name text not null,
  email text not null,
  phone text,
  created_at timestamptz not null default now(),
  unique (email, job_id)
);

------------------------------------------------
-- CANDIDATE DOCUMENTS
------------------------------------------------
create table if not exists candidate_documents (
  id uuid primary key default gen_random_uuid(),
  candidate_id uuid not null references candidates(id) on delete cascade,
  storage_bucket text not null,
  storage_path text not null,
  file_hash char(64) not null,
  uploaded_at timestamptz not null default now()
);

create index if not exists idx_candidate_documents_candidate_id
  on candidate_documents(candidate_id);
