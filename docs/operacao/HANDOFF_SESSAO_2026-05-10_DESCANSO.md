# Handoff completo — sessão 2026-05-10 (descanso)

**Para:** Allan Marcio · **Contexto:** fecho de sessão antes de descanso — tudo o que precisas ao voltar está aqui e nos ficheiros citados.

---

## 1. TL;DR

- **Documentação MVP/dev:** caminho **primário** para gates e RLS = **Docker Compose** (`make dev`, Postgres `127.0.0.1:60322`, API `http://127.0.0.1:60000`). Cloud Supabase = evidência **opcional** pré-go-live público (ver decisões G3).
- **Checklist único para ir marcando:** [`CHECKLIST_IMPLEMENTACAO_MVP_POS_DOCKER_DEV.md`](./CHECKLIST_IMPLEMENTACAO_MVP_POS_DOCKER_DEV.md) — indexado em [`README.md`](./README.md), [`EXECUCAO_DEV_09052026_V2_CHECKLIST_OPS.md`](./EXECUCAO_DEV_09052026_V2_CHECKLIST_OPS.md) e [`DECISOES_PENDENTES_DEV_09052026_V2_RESPOSTA.md`](./DECISOES_PENDENTES_DEV_09052026_V2_RESPOSTA.md).
- **Build/Make:** `mvp-gate` alinha `QDI_POSTGRES_TEST_URL` / `DATABASE_URL` ao default local (`60322`) quando omitidos — ver `Makefile` e `.env.example`.
- **LGPD (decisões DEV_09052026_V2 no código):**
  - **`POST /privacidade/diagnosticos/{id}/eliminar-diagnostico`** — eliminação física só com solicitação tipo `eliminacao` **deferida**; diagnóstico **`finalizado`** → **422** (orienta anonimização).
  - **SLA art. 18:** **15 dias úteis** — constante `LGPD_PRAZO_RESPOSTA_ART18_DIAS_UTEIS` (`src/application/services/privacidade_operacao.py`) + secção `#sla-art-18` em `/privacidade`.
- **Política Git (agentes):** sem `git commit` / `git push` automáticos — `.cursor/rules/qdi-commit-policy.mdc` e `.claude/CLAUDE.md` §10.

---

## 2. Estado do repositório (ao fechar a sessão)

- **HEAD registado na máquina:** `06eaafd` (pode haver commits locais teus depois disto).
- **Working tree:** há **alterações não commitadas** (M / ??) — rever com `git status` e `git diff` quando regressares. **Não há push automático** — conforme política acima.

Comandos úteis ao voltar:

```bash
git status --short
git diff --stat
make lint && make test
cd frontend && npm run lint && npm run build   # se mexeste em front na mesma release
```

---

## 3. Mapa de ficheiros novos / tocados (por tema)

| Tema | Onde |
|------|------|
| Checklist MVP pós-Docker | `docs/operacao/CHECKLIST_IMPLEMENTACAO_MVP_POS_DOCKER_DEV.md` (novo) |
| Formulário decisões | `docs/operacao/DECISOES_PENDENTES_DEV_09052026_V2_RESPOSTA.md` |
| Índice operação | `docs/operacao/README.md` |
| Execução DEV_09052026_V2 | `docs/operacao/EXECUCAO_DEV_09052026_V2_CHECKLIST_OPS.md` |
| Docker primário em vários runbooks | `SMOKE_MVP_FECHADO.md`, `CHECKLIST_GO_LIVE_45MIN.md`, `RUNBOOK_DEPLOY_ROLLBACK.md`, `CHANGELOG_MVP.md`, `RLS_*`, `DECISAO_RLS_*`, `SQL_VERIFICACAO_*`, `GUIA_TESTE_*`, `MVP_CRITERIO_*`, `EVIDENCIA_RLS_*`, `docs/contabilidade/AVALIACAO_*`, etc. |
| Eliminação LGPD + SLA | `src/.../privacidade_router.py`, `schemas.py`, `dependencies.py`, `errors.py`, port + adapter + use case eliminação; testes em `tests/integration/test_privacidade_api.py`, `tests/unit/...` |
| OpenAPI | `docs/api/openapi.generated.json` — regenerar com `make openapi-export` se mudares rotas |
| Front privacidade | `frontend/app/privacidade/page.tsx`, `frontend/lib/legal/lgpdOperacao.ts` |
| Runbook titular | `docs/operacao/RUNBOOK_DIREITOS_TITULAR_RASCUNHO.md` |
| Commit policy | `.cursor/rules/qdi-commit-policy.mdc`, `.claude/CLAUDE.md` |
| Makefile / env exemplo | `Makefile`, `.env.example` |

**Nota:** `_DEVELOPER/` continua **fora do Git** (`.gitignore`). Decisões consolidadas e backlog **DEV_09052026_V2** na tua pasta local — sincroniza mentalmente com os docs em `docs/operacao/` que **estão** versionados.

---

## 4. Sugestão de commits (quando revires o diff)

Podes partir em 2–3 commits Conventional Commits PT-BR, por exemplo:

1. `feat(qdi-api): endpoint LGPD eliminação diagnóstico pré-WORM e SLA art 18`
2. `docs(qdi-docs): handoff checklist MVP Docker e harmonizar operação dev`
3. `chore(qdi-build): defaults mvp-gate e exemplo env gates`

(Ajusta mensagens ao que realmente mantiveres no stage.)

---

## 5. O que continua **contigo** (operacional / jurídico)

Consulta sempre [`CHECKLIST_IMPLEMENTACAO_MVP_POS_DOCKER_DEV.md`](./CHECKLIST_IMPLEMENTACAO_MVP_POS_DOCKER_DEV.md):

- **T1.1** — `make mvp-gate` + `verify-schema-mvp-strict` com Postgres Docker; anexar evidência sem secrets.
- **T1.2** — 5 PDFs reais + sign-off (G1 auto-sign-off Allan).
- **T1.3** — evidência RLS dois tenants (template + checklist Allan); automatizado já cobre paridade em CI/Docker.
- **T1.4** — assinar `MVP_CRITERIO_CORTE_E_DECLARACAO_MUST.md`.
- **T2** — J4, DPO, RIPD v0.1, ADR-012 prazos espelhados, revisão `/privacidade`.
- **T4.1 / M08** — após gates; âncoras Lexiq por bullet (PRD).

---

## 6. Riscos / lacunas técnicas conscientes

- **J2 (anonimização):** **fechado em código** — coluna `diagnosticos.respondente_ip_origem` (migração 0036), captura HTTP nos POST de criação de diagnóstico, export portável com `respondente.ip_origem`, anonimização NULL + log JSON; trigger WORM alinhado.
- **`BACKLOG_TAREFAS_T1_T4.md`** na pasta local `_DEVELOPER/DEV_09052026_V2` pode ainda mencionar “cloud/staging” nos bullets antigos — alinhar à mão ou regenerar a partir deste handoff.
- **Deprecation FastAPI:** `HTTP_422_UNPROCESSABLE_ENTITY` em `/privacidade` substituído por `HTTP_422_UNPROCESSABLE_CONTENT` (mesmo código 422).

---

## 7. Saúde

Sessão longa — hidratação, pausa e descanso conforme a tua regra de 45 min. Ao voltar, começa por `git status` + um `make test` antes de commitar.

---

**Última atualização deste handoff:** 2026-05-10.
