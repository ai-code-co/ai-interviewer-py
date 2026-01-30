------------------------------------------------
-- Function: Auto-create profile on user signup
------------------------------------------------
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer
as $$
begin
  insert into public.profiles (
    id,
    full_name,
    email
  )
  values (
    new.id,
    null,        -- full_name initially NULL
    new.email
  );

  return new;
end;
$$;

------------------------------------------------
-- Trigger: Runs after insert on auth.users
------------------------------------------------
drop trigger if exists on_auth_user_created on auth.users;

create trigger on_auth_user_created
after insert on auth.users
for each row
execute function public.handle_new_user();
