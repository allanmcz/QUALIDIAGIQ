# Runbook — deploy e rollback (MVP QDI)

**Escopo:** API FastAPI + migrações PostgreSQL / Supabase + Next.js (front).  
**Princípio:** multi-tenant e RLS não são opcionais — ver `_DEVELOPER/RUNBOOK_SUPABASE_RLS.md`.

## Pré-deploy

1. `make test`, `make lint`, `make type-check` verdes na branch de release.
2. Aplicar migrações até **`0015`** (pesos macro por dimensão em `qdi.normativa_score_macro_dimensao`) em ambientes que servem **GET `/diagnosticos/metodologia`** / **`manifesto-pesos`** com `DATABASE_URL`. Incluir **`0019`** (RLS `admins` + `idempotency_responses.tenant_id`) para alinhar multi-tenant no Postgres self-hosted. Incluir **`0020`** se usar **RAG-light** (`qdi_rag.documento_normativo`, extensão **`vector`**) — imagem Postgres deve ser **pgvector** (ex.: `pgvector/pgvector:pg16`), como no `docker-compose.yml` do repositório. Mínimo operacional sem CNAE: **`0012`**; com CNAE referencial: **`0013`/`0014`**. Ordem lexical: `src/infrastructure/db/migrations/*.sql` — ver `init.sql` e `make migrate` em pré-prod ou pipeline equivalente.
3. Variáveis: `JWT_SECRET_KEY`, `SUPABASE_*`, `DATABASE_URL` / `sync_database_url` (idempotência Postgres), `CORS` explícito (sem `*` com credentials). **OpenTelemetry:** guia curto dedicado em [`OTEL_QUICKSTART_LOCAL.md`](./OTEL_QUICKSTART_LOCAL.md); variáveis em `README.md` (raiz) e `src/infrastructure/config/settings.py`.

### Front (Next.js) — URLs canónicas (D4)

| Variável | Uso |
|----------|-----|
| `NEXT_PUBLIC_API_URL` | Base da API no browser (ex.: `https://api.exemplo.com`). |
| `NEXT_PUBLIC_SITE_URL` | Origem do site App Router — usada em `metadataBase` (Open Graph / Twitter). |

Exemplo sem segredos: `frontend/.env.production.example`.

## Deploy (ordem sugerida)

1. **DDL:** migrações SQL (`src/infrastructure/db/migrations/*.sql`) antes do tráfego novo.
2. **API:** imagem/container com WeasyPrint e dependências de sistema documentadas no Dockerfile.
3. **Front:** build `next build`; `NEXT_PUBLIC_API_URL` e **`NEXT_PUBLIC_SITE_URL`** apontando para URLs canónicas (ver tabela acima).

## Rollback

| Camada | Ação |
|--------|------|
| Front | Reverter para artefato/imagem anterior; cache CDN se houver. |
| API | Reverter imagem; manter compatibilidade de schema ou rodar migração reversa **somente** se script existir (preferir forward-fix). |
| DB | Evitar `DROP` em produção; usar feature flags ou correções forward. Backup antes de DDL. |

## Pós-deploy (fumaça)

Executar checklist em `docs/operacao/SMOKE_MVP_FECHADO.md` (mínimo itens 1–5).

### Verificação objetiva de schema (release com Postgres aplicado)

Com cliente `psql` e Python do projeto (`.venv` ou CI):

```bash
export POSTGRES_CI_URL='postgresql://USER:SENHA@HOST:5432/DB'   # ou URL do pool Supabase (service)
export QDI_POSTGRES_TEST_URL="$POSTGRES_CI_URL"
make verify-schema-mvp-strict
```

O alvo **strict** confere núcleo MVP + **CNAE 0013/0014** + **normativa de pesos macro 0015** (ver `scripts/verify_mvp_schema.py`). Falha com código ≠0 se alguma tabela/contagem obrigatória faltar.

Equivalente sem Makefile:

```bash
QDI_VERIFY_SCHEMA_STRICT_CNAE=1 QDI_POSTGRES_TEST_URL="$POSTGRES_CI_URL" python scripts/verify_mvp_schema.py
```

Gate opcional **RAG (0020)** — falha se extensão `vector` ou tabela `qdi_rag.documento_normativo` ausente:

```bash
QDI_VERIFY_SCHEMA_RAG=1 QDI_POSTGRES_TEST_URL="$POSTGRES_CI_URL" python scripts/verify_mvp_schema.py
# ou: python scripts/verify_mvp_schema.py --rag "$POSTGRES_CI_URL"
```

Após migrações, popular embeddings (dev/staging) com `OPENAI_API_KEY` e `DATABASE_URL` síncrono:

```bash
PYTHONPATH=. OPENAI_API_KEY=... DATABASE_URL=postgresql://... python scripts/ingestao_rag_baseline.py
```

## Referências

- `_DEVELOPER/HANDOFF_PLANO_MVP_FECHADO.md` — Fase C (RLS) e Fase G (observabilidade).
- `docs/operacao_rls_idempotency.md` — idempotência e RLS.
- `docs/operacao/CORS_PRODUCAO.md` — variável `CORS_ALLOWED_ORIGINS`.
- `docs/operacao/RLS_TABELAS_CHECKLIST_MVP.md` — índice de tabelas/políticas MVP.
