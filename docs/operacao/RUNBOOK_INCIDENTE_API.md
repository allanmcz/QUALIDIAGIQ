# Runbook — incidente na API QDI

## Sintomas comuns

1. **5xx em massa** — verificar Sentry (`SENTRY_DSN`), logs JSON (`trace_id`).
2. **429 em rotas públicas** — rate limit por IP (`QDI_PUBLIC_RATE_LIMIT_*`).
3. **Falha Postgres** — health do serviço; `DATABASE_URL`; pool esgotado.

## Passos rápidos

1. Isolar versão deployada (tag/imagem Docker).
2. Buscar `trace_id` no request afetado e correlacionar nos logs.
3. Se migração suspeita: conferir `scripts/verify_mvp_schema.py` no ambiente.
4. Rollback da API apenas após snapshot de estado e comunicação ao Allan/time.

Detalhar runbooks específicos (Supabase, Mailpit vs SMTP prod) na wiki interna Tributiq.
