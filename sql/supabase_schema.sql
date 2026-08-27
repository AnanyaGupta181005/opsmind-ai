-- OpsMind AI · Supabase vector store
-- Run once in the Supabase SQL editor.

create extension if not exists vector;

create table if not exists policy_chunks (
  id           uuid primary key default gen_random_uuid(),
  doc_id       uuid not null,
  title        text not null,
  kind         text not null default 'policy',
  chunk_index  int  not null,
  content      text not null,
  embedding    vector(768),
  created_at   timestamptz not null default now()
);

create index if not exists policy_chunks_doc_idx  on policy_chunks (doc_id);
create index if not exists policy_chunks_kind_idx on policy_chunks (kind);

-- cosine ANN index; lists ~ sqrt(rows)
create index if not exists policy_chunks_embedding_idx
  on policy_chunks using ivfflat (embedding vector_cosine_ops) with (lists = 100);

-- retrieval RPC used by app/rag/store.py
create or replace function match_policy_chunks (
  query_embedding vector(768),
  match_count int default 5,
  filter_kind text default null
)
returns table (
  id uuid, doc_id uuid, title text, kind text,
  chunk_index int, content text, similarity float
)
language sql stable as $$
  select c.id, c.doc_id, c.title, c.kind, c.chunk_index, c.content,
         1 - (c.embedding <=> query_embedding) as similarity
  from policy_chunks c
  where filter_kind is null or c.kind = filter_kind
  order by c.embedding <=> query_embedding
  limit match_count;
$$;

alter table policy_chunks enable row level security;

create policy "service role full access" on policy_chunks
  for all using (auth.role() = 'service_role');
