-- Historai schema: persistence for what-if simulations.
-- Run in the Supabase SQL editor (or `psql`) against your project.

create extension if not exists pgcrypto;

create or replace function public.historai_set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at := now();
  return new;
end;
$$;

create table if not exists public.simulations (
    id uuid primary key default gen_random_uuid(),
    question text not null,
    status text not null check (status in ('pending','running','done','error')),
    turns integer not null default 6 check (turns between 1 and 20),
    actors jsonb not null default '[]'::jsonb,
    result jsonb,
    report jsonb,
    error text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index if not exists simulations_created_at_idx
    on public.simulations (created_at desc);

create index if not exists simulations_status_idx
    on public.simulations (status);

drop trigger if exists simulations_set_updated_at on public.simulations;
create trigger simulations_set_updated_at
    before update on public.simulations
    for each row execute function public.historai_set_updated_at();

-- Lock down the table. Backend uses the service-role key, which bypasses RLS;
-- everyone else is blocked.
alter table public.simulations enable row level security;
