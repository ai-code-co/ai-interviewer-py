------------------------------------------------
-- Convert skill-related columns to JSONB
------------------------------------------------

alter table ai_evaluations
  alter column matched_skills
    drop default,
  alter column matched_skills
    type jsonb
    using to_jsonb(matched_skills),
  alter column matched_skills
    set default '[]'::jsonb;

alter table ai_evaluations
  alter column missing_skills
    drop default,
  alter column missing_skills
    type jsonb
    using to_jsonb(missing_skills),
  alter column missing_skills
    set default '[]'::jsonb;

alter table ai_evaluations
  alter column strengths
    drop default,
  alter column strengths
    type jsonb
    using to_jsonb(strengths),
  alter column strengths
    set default '[]'::jsonb;

alter table ai_evaluations
  alter column weaknesses
    drop default,
  alter column weaknesses
    type jsonb
    using to_jsonb(weaknesses),
  alter column weaknesses
    set default '[]'::jsonb;
