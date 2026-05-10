# Changelog — marcos MVP QDI

## 2026-05-10 — Plano DEV_09052026 (S-01 + parcela S-02 DB/DevSecOps)

- Migrações `0005a_ci_playwright_admin.sql` / `0005b_worm_evidencia_audit.sql` (ordem lexical explícita); ADR-013.
- Migrações **0032** (`qdi_cleanup_idempotency`, pg_cron opcional), **0033** (FORCE RLS em tabelas críticas), **0034** (REVOKE DELETE append-only); ADR-014.
- `POST /admin/maintenance/cleanup-idempotency` (JWT admin/avançado, rate-limit 5 min); runbooks pg_cron e segredo vazado; gitleaks + `make install-hooks`.
- CI: Bandit, Semgrep, Trivy (fs); `init.sql` alinhado às migrações até 0034.

## 2026-05-07 — API pública institucional

- `GET /public/institucional` (DPO + retenção referência); `LGPD_*` em settings; teste de shape em `test_openapi_public_endpoints_shapes.py`.

## 2026-05-07 — Jurídico + aprovação produto

- Parecer formal sobre `/termos` e `/privacidade` arquivado em `docs/legal/` (PDF); **aprovação produto** da minuta para publicação registada em `docs/legal/STATUS_JURIDICO_MVP.md`; UI `/termos` e `/privacidade` com estado «aprovada». Ver `docs/CHANGELOG_MVP.md` **[Unreleased]**.

## 2026-05 — Sprint 11 handoff (segurança / multi-tenant)

- `Settings`: `SecretStr` para JWT; validação de produção (Supabase HTTPS, DB, SMTP).
- Migração `0019`: RLS em `admins`; `tenant_id` em `idempotency_responses` + políticas `authenticated`.
- Middleware de idempotência e backend Postgres escopados por `tenant_id` do JWT.
- Logging estruturado (`structlog`), Sentry opcional (`SENTRY_DSN`), headers de segurança no Next.js (CSP/COOP em produção).
- CI: gate de cobertura mínima 85% em `src/domain`.
- Front: Radix Tooltip na base legal do wizard; `@sentry/browser` opcional via `NEXT_PUBLIC_SENTRY_DSN`.
- Use case `RealizarDiagnostico`: removida leitura de `_DEVELOPER/`; contexto normativo fixo até RAG/BaseNormativaPort (S12).
