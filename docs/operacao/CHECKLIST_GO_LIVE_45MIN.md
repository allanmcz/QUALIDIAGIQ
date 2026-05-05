# Checklist go-live — janela ~45 minutos

**Objetivo:** repetir um cutover **previsível** quando não há tempo para improvisar.  
**Stack assumida pelo repo:** FastAPI + Postgres (Supabase ou self-hosted) + Next.js 14.  
**Analogia (ERP):** é o “roteiro de virada de versão” antes de abrir a filial para uso real — mesma ordem que um script de migração + smoke na base.

**Antes de começar:** ter URLs finais de **API** e **site**, credenciais de deploy (CI ou SSH), e **backup** ou snapshot do Postgres se for aplicar DDL.

---

## Onde isto corre na tua infra (1 min — preencher uma vez)

| Camada | Onde está em produção | Comando / painel |
|--------|----------------------|------------------|
| Postgres | _ex.: Supabase project X / RDS / VM_ | |
| API | _ex.: container / systemd / PaaS_ | |
| Front | _ex.: Vercel / Docker / static behind CDN_ | |
| DNS / TLS | _domínios canónicos_ | |

Variáveis críticas do front: ver `RUNBOOK_DEPLOY_ROLLBACK.md` (tabela `NEXT_PUBLIC_*`). CORS: `CORS_PRODUCAO.md`.

---

## Fase A — Pré-voo (0–12 min)

| # | Tarefa | Critério |
|---|--------|----------|
| A1 | Branch/release alinhada ao commit que vai a produção | `git log -1` = artefacto que vai ser deployado |
| A2 | **API:** `make test` + `make lint` (+ `make type-check` se política do release) verdes **na mesma base** | Sem surpresas “só no laptop” |
| A3 | **Front:** `npm run build` (+ `npm run test:e2e` se pipeline não cobrir regressão wizard) | Build sem erro |
| A4 | **DDL:** migrações aplicadas **antes** de expor tráfego novo — ordem em `init.sql` / `make migrate` conforme ambiente | Sem migração pendente crítica |
| A5 | **Secrets:** `JWT_SECRET_KEY`, `DATABASE_URL` / Supabase, idempotência Postgres se usada; **sem** `CORS_ALLOWED_ORIGINS=*` com credentials | Conferir `settings` / painel do host |

**PWA:** ADR-011 **B1** (manifest + viewport) — sem service worker; risco de cache SW **não** aplica neste release.

---

## Fase B — Deploy (12–28 min)

Ordem recomendada (igual ao runbook):

| # | Ordem | Accção |
|---|-------|--------|
| B1 | 1º | **Base:** migrações até ao nível acordado para o release (ver notas em `RUNBOOK_DEPLOY_ROLLBACK.md` § pré-deploy) |
| B2 | 2º | **API:** publicar imagem/container com WeasyPrint conforme Dockerfile do repo |
| B3 | 3º | **Front:** `next build` + deploy com `NEXT_PUBLIC_API_URL` e `NEXT_PUBLIC_SITE_URL` **canónicos** |

Se algo falhar: **parar** antes de misturar versão nova de API com schema antigo (ou o contrário).

---

## Fase C — Verificação objectiva (28–38 min)

| # | Tarefa | Critério |
|---|--------|----------|
| C1 | Schema strict (se Postgres acessível da máquina de ops) | `make verify-schema-mvp-strict` com `QDI_POSTGRES_TEST_URL` / URL de serviço — ver `RUNBOOK_DEPLOY_ROLLBACK.md` |
| C2 | Health API | `GET /health` → `200`; `X-Trace-Id` presente (`SMOKE_MVP_FECHADO.md` item 1) |

---

## Fase D — Smoke negócio (38–45 min)

Executar **pelo menos** os itens **1–5** de `SMOKE_MVP_FECHADO.md` contra URLs **de produção** (login real ou conta de teste dedicada):

1. Health / trace  
2. Login JWT  
3. Wizard até LGPD  
4. POST diagnóstico `201` com aceite  
5. Lista `GET /diagnosticos/`

Se falhar em **4 ou 5**: considerar rollback da API ou front conforme `RUNBOOK_DEPLOY_ROLLBACK.md`.

---

## Rollback express (se precisar nos 45 min)

| Camada | Accção mínima |
|--------|----------------|
| Front | Voltar ao deployment/imagem anterior |
| API | Idem; **não** fazer `DROP` em BD |
| BD | Preferir **forward-fix**; backup antes de qualquer DDL em produção |

---

## Referências rápidas

| Documento | Uso |
|-----------|-----|
| [RUNBOOK_DEPLOY_ROLLBACK.md](./RUNBOOK_DEPLOY_ROLLBACK.md) | Ordem deploy, variáveis, verify-schema |
| [SMOKE_MVP_FECHADO.md](./SMOKE_MVP_FECHADO.md) | Itens 1–8 + `make mvp-gate` |
| [CORS_PRODUCAO.md](./CORS_PRODUCAO.md) | Lista explícita de origens |
| [RLS_TABELAS_CHECKLIST_MVP.md](./RLS_TABELAS_CHECKLIST_MVP.md) | Conferência políticas |
| [ADR-011](../../.github/adr/ADR-011-pwa-next14-qualidiagiq.md) | PWA B1 sem SW |

---

**Registo de execução:** data · executor · commit/tag deployada · resultado smoke (OK / rollback).
