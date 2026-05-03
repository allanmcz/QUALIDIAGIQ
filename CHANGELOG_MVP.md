# Changelog — marcos MVP QDI

## 2026-05 — Sprint 11 handoff (segurança / multi-tenant)

- `Settings`: `SecretStr` para JWT; validação de produção (Supabase HTTPS, DB, SMTP).
- Migração `0019`: RLS em `admins`; `tenant_id` em `idempotency_responses` + políticas `authenticated`.
- Middleware de idempotência e backend Postgres escopados por `tenant_id` do JWT.
- Logging estruturado (`structlog`), Sentry opcional (`SENTRY_DSN`), headers de segurança no Next.js (CSP/COOP em produção).
- CI: gate de cobertura mínima 85% em `src/domain`.
- Front: Radix Tooltip na base legal do wizard; `@sentry/browser` opcional via `NEXT_PUBLIC_SENTRY_DSN`.
- Use case `RealizarDiagnostico`: removida leitura de `_DEVELOPER/`; contexto normativo fixo até RAG/BaseNormativaPort (S12).
