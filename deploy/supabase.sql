-- Execute no SQL Editor do seu projeto Supabase Free.
-- Não adicione documentos, senhas ou chaves service_role neste arquivo.
create table if not exists public.pericia_cases (
  user_id uuid primary key references auth.users(id) on delete cascade,
  state jsonb not null,
  documents jsonb not null default '[]'::jsonb,
  tree jsonb not null default '[]'::jsonb,
  updated_at timestamptz not null default now()
);
alter table public.pericia_cases enable row level security;
revoke all on public.pericia_cases from anon;
grant select, insert, update on public.pericia_cases to authenticated;
drop policy if exists "pericia_owner" on public.pericia_cases;
create policy "pericia_owner" on public.pericia_cases to authenticated
  using ((select auth.uid()) = user_id)
  with check ((select auth.uid()) = user_id);

insert into storage.buckets (id, name, public, file_size_limit)
values ('pericia-private', 'pericia-private', false, 52428800)
on conflict (id) do update set public = false;
drop policy if exists "pericia_files_owner" on storage.objects;
create policy "pericia_files_owner" on storage.objects for all to authenticated
  using (bucket_id = 'pericia-private' and (storage.foldername(name))[1] = (select auth.uid())::text)
  with check (bucket_id = 'pericia-private' and (storage.foldername(name))[1] = (select auth.uid())::text);

-- Cada alteração bloqueia somente a linha do usuário durante a transação.
-- Campos de tarefas e quesitos são mesclados sobre a versão mais recente.
create or replace function public.pericia_update(kind text, item_id integer, fields jsonb)
returns jsonb language plpgsql security invoker set search_path = public as $$
declare
  result jsonb;
  items jsonb;
  allowed text[];
  entry jsonb;
  found_item boolean := false;
  description text;
begin
  if auth.uid() is null then raise exception 'Autenticação necessária'; end if;
  if kind not in ('notes', 'tasks', 'questions') or fields is null or jsonb_typeof(fields) <> 'object'
    then raise exception 'Dados inválidos'; end if;
  if exists (select 1 from jsonb_each(fields) where jsonb_typeof(value) <> 'string')
    then raise exception 'Valores inválidos'; end if;
  select state into result from public.pericia_cases where user_id = auth.uid() for update;
  if result is null then raise exception 'Importe o pacote privado'; end if;
  if kind = 'notes' then
    if fields <> jsonb_build_object('notes', fields->'notes') or not (fields ? 'notes')
      then raise exception 'Anotação inválida'; end if;
    result := jsonb_set(result, '{notes}', fields->'notes');
    description := 'Anotações gerais atualizadas';
  else
    allowed := case when kind = 'tasks' then array['status','due','notes','owner'] else array['answer','evidence'] end;
    if exists (select 1 from jsonb_object_keys(fields) as field(key) where not (field.key = any(allowed)))
      then raise exception 'Campos inválidos'; end if;
    if fields ? 'status' and fields->>'status' not in ('pendente','andamento','concluida','bloqueada')
      then raise exception 'Situação inválida'; end if;
    if coalesce(fields->>'due', '') <> '' then
      if fields->>'due' !~ '^\d{4}-\d{2}-\d{2}$' then raise exception 'Data inválida'; end if;
      perform (fields->>'due')::date;
    end if;
    items := '[]'::jsonb;
    for entry in select value from jsonb_array_elements(result->kind) loop
      if (entry->>'id')::integer = item_id then
        entry := entry || fields;
        found_item := true;
      end if;
      items := items || jsonb_build_array(entry);
    end loop;
    if not found_item then raise exception 'Registro inexistente'; end if;
    result := jsonb_set(result, array[kind], items);
    description := case when kind = 'tasks' then 'Tarefa ' else 'Quesito ' end || item_id::text || ' atualizado';
  end if;
  items := jsonb_build_array(jsonb_build_object('time', now(), 'text', description)) || coalesce(result->'activity','[]'::jsonb);
  select coalesce(jsonb_agg(value order by ordinal), '[]'::jsonb) into items
    from jsonb_array_elements(items) with ordinality as a(value, ordinal) where ordinal <= 200;
  result := jsonb_set(result, '{activity}', items);
  update public.pericia_cases set state = result, updated_at = now() where user_id = auth.uid();
  return result;
end;
$$;
revoke all on function public.pericia_update(text, integer, jsonb) from public;
grant execute on function public.pericia_update(text, integer, jsonb) to authenticated;
