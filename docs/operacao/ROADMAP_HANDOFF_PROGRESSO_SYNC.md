# Progresso do roadmap handoff (espelho Git)

Este ficheiro **substitui** no histórico versionado o painel em `_DEVELOPER/DEV_DIAG_04052026/ROADMAP_HANDOFF_REFACTOR_LGPD_PWA.md` (pasta `_DEVELOPER/` ignorada pelo Git).

**Última sincronização:** 2026-05-13 — **Onda 2a** `deps_auth_supabase.py`; **Onda 2b** `deps_repositories_core.py`; **Onda 2c** `deps_infra_services.py` (normativa, score, LLM, CNPJ/CNAE, PDF, e-mail, orquestrador); **Onda 3** `deps_lgpd_painel.py` (LGPD titular, export portável, retificações, vínculo lead, mutações painel/plano); `dependencies.py` = reexports. E2E `wizard-offline-banner.spec.ts`; `make report-rls-public`. Handoff 2026-05-10: [`HANDOFF_SESSAO_2026-05-10_DESCANSO.md`](./HANDOFF_SESSAO_2026-05-10_DESCANSO.md).

## Painel

| Item | Fase | Status | Evidência |
|------|------|--------|-----------|
| Refactor `diagnostico_router` | R1–R4 | Concluído | Routers modularizados; `make test` verde no último refactor |
| Refactor `WizardForm` | W1–W5 | Concluído | ADR-010; `npm run build` + `npm run lint` |
| PLANO janela 23h | HANDOFF | Concluído | ADR-011 B1 · ADR-012 desenho · runbook · templates jurídicos |
| P0-07 LGPD técnico | C.2 | Em produção (técnico) | Migração `0028`; `POST/GET/PATCH` `/privacidade/solicitacoes` · `tests/integration/test_privacidade_api.py` · `make test`. Processo DPO / RIPD art. 18 completo → **ADR-012** + jurídico |
| P0-06 PWA | D | B1 + B2 | Manifest + `sw.js` + registo client-side; validação pós-deploy quando SW activo |
| ADR-012 LGPD/WORM | J | Fechado tecnicamente | ADR aceito; export portável `GET /privacidade/diagnosticos/{id}/export-portabilidade`; anonimização executável; **`POST .../eliminar-diagnostico`** (pré-`finalizado`; `finalizado` → 422 → anonimizar); SLA **15 dias úteis** na página pública; runbook direitos do titular. RIPD/DPO permanecem trilho jurídico-operacional. |
| Retificação WORM | C.3 | Em produção (técnico) | Migração `0035_diagnostico_retificacao_append_only.sql`; `POST/GET /diagnosticos/{id}/retificacao(|es)`; cadeia append-only sem `UPDATE` do diagnóstico original. |
| OpenAPI versionado | A2c | Em CI | `docs/api/openapi.generated.json` versionado; `tests/unit/presentation/test_openapi_generated_contract.py`; CI falha em drift do contrato gerado. |
| Go-live 45min | A2c/C3 | Pronto para execução | `make go-live`; A2c valida drift OpenAPI; C3 smoke `GET /public/institucional` e `GET /diagnosticos/metodologia` após `/health`. |
| Refactor `dependencies.py` (auth + Supabase) | Onda 2 | Concluído | `deps_auth_supabase.py`. |
| Refactor `dependencies.py` (repos core) | Onda 2 | Concluído | `deps_repositories_core.py`; `reset_ci_playwright_diagnostico_singleton()`. |
| Refactor `dependencies.py` (infra / serviços) | Onda 2c | Concluído | `deps_infra_services.py` (normativa, score, questionário, LLM, CNPJ/CNAE, PDF, storage, e-mail, `RealizarDiagnostico`). |
| Refactor `dependencies.py` (LGPD + painel) | Onda 3 | Concluído | `deps_lgpd_painel.py`; `dependencies.py` só reexports + `logger`. |
| Relatório RLS `public` | Ops | Disponível | `make report-rls-public` · `scripts/report_rls_public.py` (requer Postgres alvo). |

## Testes E2E (frontend)

| Comando | Significado |
|---------|-------------|
| `npm run test:e2e` | Suíte mock + **2 skipped**: integrado (`PLAYWRIGHT_INTEGRATED`) · normativa (`PLAYWRIGHT_WIZARD_NORMATIVA`); inclui `e2e/wizard-offline-banner.spec.ts` (banner sem rede no `/wizard`) |
| `npm run test:e2e:integrado` | Exige API real + env documentados em `frontend/README.md` |
| `npm run test:e2e:wizard-normativa` | P8 âncora normativa |

**Evidência local (referência):** `make lint` + `make test` (inclui `test_privacidade_api`) · `npm run lint` + `npm run build` + `npm run test:e2e` conforme política do release.

**Referência Git:** `4d4c02c test(qdi-api): contrato estático OpenAPI e endurecer go-live 45min`.

## OpenAPI versionado

Contrato completo versionado em `docs/api/openapi.generated.json`. Ver também `docs/operacao/OPENAPI_DIFF_INSTRUCOES.md` para regeneração (`make openapi-export`), comparação contra ambiente publicado e análise de diffs sem segredos.

O CI executa verificação de drift (`git diff --exit-code docs/api/openapi.generated.json`) e o teste estático `tests/unit/presentation/test_openapi_generated_contract.py` cobre paths mínimos de LGPD, retificações e endpoints públicos.
