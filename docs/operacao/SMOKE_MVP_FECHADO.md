# Smoke test manual — MVP QualiDiagIQ fechado

**Objetivo:** validar o fluxo crítico ponta a ponta antes de declarar MVP fechado (complementa **Fase A.3** do plano).

**Pré-requisitos:** `make dev` (API + DB), front `npm run dev` ou Docker na porta web; JWT válido (login na plataforma).

## Automatizado (CI / pytest)

Com Postgres acessível (`QDI_POSTGRES_TEST_URL` ou Docker na porta padrão):

- `make mvp-gate` — smoke API (`tests/integration/test_smoke_mvp_fechado_api.py`) + schema **0012** + RLS dois tenants (`tests/integration/test_mvp_gate_postgres.py`).
- `tests/integration/test_privacidade_api.py` — contrato HTTP LGPD (incluído em `make test`); execução isolada pode falhar o gate global de cobertura.
- `tests/unit/presentation/test_openapi_generated_contract.py` — paths mínimos no `docs/api/openapi.generated.json` (LGPD + retificações + públicos); incluído em `make test`.
- `make verify-schema-mvp` — só leitura no Postgres alvo (`DATABASE_URL` ou `QDI_POSTGRES_TEST_URL`; default Compose `127.0.0.1:60322`). Em Supabase, equivalente: `docs/operacao/SQL_VERIFICACAO_SCHEMA_MVP.sql`.
- O job **GitHub Actions** já roda o pytest completo após aplicar todas as migrações no Postgres de serviço.

Passos **2** (login Supabase real), **3** (wizard UI) e **8** (PDF real) continuam manuais ou cobertos por **Playwright** / ambiente com WeasyPrint.

**Portas típicas (Compose do repo):**

| Serviço | URL |
|----------|-----|
| API | `http://localhost:60000` |
| Next | `http://localhost:60001` |
| Postgres | `localhost:60322` |

## Registo **MVP-D** (execução handoff 2026-05-05 — engenharia)

| Gate | Evidência |
|------|-----------|
| `make mvp-gate` | Executado com sucesso no repositório (CI/local agente). |
| `make verify-schema-mvp-strict` | OK em `QDI_POSTGRES_TEST_URL` default `127.0.0.1:60322` (quando Postgres disponível). |
| Passos 1–8 abaixo | **Allan:** executar na demo MacBook seguindo [`_DEVELOPER/MVP_05052026/07_ROTEIRO_DEMO.md`](../../_DEVELOPER/MVP_05052026/07_ROTEIRO_DEMO.md); marcar caixas quando concluídos. |

---

## Passos (marcar evidência)

1. [ ] **Health:** `GET /health` → `200`; header **`X-Trace-Id`** presente; repetir com header `X-Trace-Id: smoke-manual` → resposta ecoa o mesmo valor.
2. [ ] **Login:** obter Bearer JWT (`POST /auth/login` ou tela `/login`).
3. [ ] **Wizard:** preencher fluxo até finalizar; checkbox LGPD marcado.
4. [ ] **POST diagnóstico:** corpo contém `aceite_termos_privacidade: true`; resposta **`201`** com `aceite_termos_privacidade_em` preenchido (ISO-8601).
5. [ ] **Lista:** `GET /diagnosticos/` → linha do diagnóstico criado.
6. [ ] **Detalhe:** `GET /diagnosticos/{id}` → score, checklist, hash, versão otimista coerentes.
7. [ ] **M12:** alterar um checkbox na autoconf ABNT → após debounce, **`PATCH .../checklist-m12-autoconf`** com `If-Match` → `200` ou `412` seguido de refetch coerente no browser.
8. [ ] **PDF (se ambiente com WeasyPrint/storage):** URL do relatório preenchida ou fluxo documentado como pendência **P5**.

## Falha conhecida

- **412** repetido no M12: concorrência — refazer GET e reaplicar `If-Match` com versão atual.

## Referência

- Plano mestre: `_DEVELOPER/HANDOFF_PLANO_MVP_FECHADO.md`
