# Checklist go-live — janela ~45 minutos

**Objetivo:** repetir um cutover **previsível** quando não há tempo para improvisar.  
**Stack assumida pelo repo:** FastAPI + Postgres (Supabase ou self-hosted) + Next.js 14.  
**Analogia (ERP):** é o “roteiro de virada de versão” antes de abrir a filial para uso real — mesma ordem que um script de migração + smoke na base.

**Desenvolvimento / evidência MVP (não é este cutover):** gates `make mvp-gate`, `make verify-schema-mvp-strict` e smoke RLS usam **Docker Compose** — `make dev`, Postgres **`127.0.0.1:60322`**, API típica **`http://127.0.0.1:60000`**, `QDI_POSTGRES_TEST_URL` / `DATABASE_URL` conforme `docs/operacao/DEMO_MAC_DEV.md`. Segunda evidência opcional em **Supabase gerido** antes do go-live público (G3).

**Antes de começar:** ter URLs finais de **API** e **site**, credenciais de deploy (CI ou SSH), e **backup** ou snapshot do Postgres se for aplicar DDL.

### Execução assistida (automatiza A + C)

```bash
# modo padrão (sem E2E; com verify-schema strict)
make go-live

# modo completo (inclui E2E e type-check)
QDI_GO_LIVE_RUN_E2E=1 QDI_GO_LIVE_RUN_TYPECHECK=1 make go-live

# API de produção e sem acesso DB local (pula verify-schema)
QDI_API_BASE_URL="https://api.seudominio.com" QDI_GO_LIVE_SKIP_SCHEMA=1 make go-live

# Ambiente sem git ou snapshot só de runtime (pula diff OpenAPI — já coberto no CI)
QDI_GO_LIVE_SKIP_OPENAPI_DRIFT=1 make go-live
```

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
| A2 | **API:** `make test` + `make lint` (+ `make type-check` se política do release) verdes **na mesma base** | Sem surpresas “só no laptop”; inclui integração LGPD (ver abaixo) |
| A3 | **Front:** `npm run build` (+ `npm run test:e2e` se pipeline não cobrir regressão wizard) | Build sem erro |
| A4 | **DDL:** migrações aplicadas **antes** de expor tráfego novo — ordem em `init.sql` / `make migrate` conforme ambiente | Sem migração pendente crítica |
| A5 | **Secrets:** `JWT_SECRET_KEY`, `DATABASE_URL` / Supabase, idempotência Postgres se usada; **sem** `CORS_ALLOWED_ORIGINS=*` com credentials | Conferir `settings` / painel do host |

**PWA (ADR-011):** **B1** = manifest + viewport. **B2** = `public/sw.js` + registo client-side em produção — validar wizard/login após deploy se SW activo.

### Evidência automatizada — LGPD `/privacidade` (CI / pré-release)

Contrato HTTP coberto em `tests/integration/test_privacidade_api.py` (POST/GET/PATCH, filtros, 400/404). Faz parte de `make test` quando o pacote de release inclui esses commits.

```bash
# Foco manual no módulo (atenção: `make test` já é o gate completo com cobertura)
PYTHONPATH=. .venv/bin/pytest tests/integration/test_privacidade_api.py -q
```

**Produção / smoke manual:** após login Bearer, validar `POST /privacidade/solicitacoes` com `Idempotency-Key`, `GET /privacidade/solicitacoes` e `PATCH .../status` conforme `RUNBOOK_DIREITOS_TITULAR_RASCUNHO.md`.

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
| C1 | Schema strict (se Postgres acessível da máquina de ops) | `make verify-schema-mvp-strict` com `QDI_POSTGRES_TEST_URL` / URL de serviço (em dry-run local: Compose **60322**) — ver `RUNBOOK_DEPLOY_ROLLBACK.md` |
| C2 | Health API | `GET /health` → `200`; `X-Trace-Id` presente (`SMOKE_MVP_FECHADO.md` item 1) |
| C3 | Endpoints públicos | `GET /public/institucional` e `GET /diagnosticos/metodologia` → `200` em `QDI_API_BASE_URL` (automático em `scripts/go_live_45min.sh` após C2) |

**Pré-voo A2c (automático):** regeneração `openapi.generated.json` + `git diff --exit-code` — alinhado ao job CI backend; usar `QDI_GO_LIVE_SKIP_OPENAPI_DRIFT=1` só se necessário.

---

## Fase D — Smoke negócio (38–45 min)

Executar **pelo menos** os itens **1–5** de `SMOKE_MVP_FECHADO.md` contra URLs **de produção** (login real ou conta de teste dedicada):

1. Health / trace  
2. Login JWT  
3. Wizard até LGPD  
4. POST diagnóstico `201` com aceite  
5. Lista `GET /diagnosticos/` (opcional: repetir com `?empresa_cnpj=` do diagnóstico criado — smoke da grelha por empresa)

Se falhar em **4 ou 5**: considerar rollback da API ou front conforme `RUNBOOK_DEPLOY_ROLLBACK.md`.

**Opcional (LGPD técnico):** se o release incluir fluxo de solicitações do titular, smoke rápido `POST/GET/PATCH` em `/privacidade/solicitacoes` (Bearer + `Idempotency-Key` no POST) alinhado ao runbook.

### Registo rápido (copiar/colar no PR ou diário)

```text
Data/hora:
Executor:
Commit/tag:
API URL:
Resultado make go-live:
Resultado smoke itens 1-5:
Resultado pytest LGPD (opcional): tests/integration/test_privacidade_api.py OK / N/A
Decisão final: GO / NO-GO / ROLLBACK
```

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
| [ADR-011](../../.github/adr/ADR-011-pwa-next14-qualidiagiq.md) | PWA B1 + B2 (SW); política de cache |
| [RUNBOOK_DIREITOS_TITULAR_RASCUNHO.md](./RUNBOOK_DIREITOS_TITULAR_RASCUNHO.md) | API `/privacidade/solicitacoes` + operações sensíveis |
| `tests/integration/test_privacidade_api.py` | Integração HTTP LGPD (pytest) |

---

**Registo de execução:** data · executor · commit/tag deployada · resultado smoke (OK / rollback).
