-- Allow INSERT (Crucial for saving the first time)
create policy "Allow insert access for all"
on public.ai_interview_evaluations for insert
with check (true);

-- Allow UPDATE (Crucial for 'upsert' to work)
create policy "Allow update access for all"
on public.ai_interview_evaluations for update
using (true);