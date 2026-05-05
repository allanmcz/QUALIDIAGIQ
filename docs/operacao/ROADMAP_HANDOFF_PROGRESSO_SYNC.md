# Progresso do roadmap handoff (espelho Git)

Este ficheiro **substitui** no histórico versionado o painel em `_DEVELOPER/DEV_DIAG_04052026/ROADMAP_HANDOFF_REFACTOR_LGPD_PWA.md` (pasta `_DEVELOPER/` ignorada pelo Git).

**Última sincronização:** 2026-05-05 — handoff PLANO_HANDOFF_JANELA_23H (implementação documental + PWA B1).

## Painel

| Item | Fase | Status | Evidência |
|------|------|--------|-----------|
| Refactor `diagnostico_router` | R1–R4 | Concluído | Routers modularizados; `make test` verde no último refactor |
| Refactor `WizardForm` | W1–W5 | Concluído | ADR-010; `npm run build` + `npm run lint` |
| PLANO janela 23h | HANDOFF | Concluído | ADR-011 B1 · ADR-012 desenho · runbook · templates jurídicos |
| P0-07 LGPD técnico | C.2 | Em preparação | ADR-012 + runbook; **sem** endpoints art. 18 até jurídico |
| P0-06 PWA | D | B1 | Manifest + metadata; **B2 SW** pendente |

## Testes E2E (frontend)

| Comando | Significado |
|---------|-------------|
| `npm run test:e2e` | Suíte mock + **2 skipped**: integrado (`PLAYWRIGHT_INTEGRATED`) · normativa (`PLAYWRIGHT_WIZARD_NORMATIVA`) |
| `npm run test:e2e:integrado` | Exige API real + env documentados em `frontend/README.md` |
| `npm run test:e2e:wizard-normativa` | P8 âncora normativa |

**Evidência local (handoff 2026-05-05):** `make lint` + `make test` verdes · `npm run lint` + `npm run build` + `npm run test:e2e` (23 passados, 2 skipped).

**Referência Git:** este pacote corresponde a **um único** commit em `main` — usar `git log -1 --oneline` após sincronizar.

## OpenAPI (opcional R2)

Ver `docs/operacao/OPENAPI_DIFF_INSTRUCOES.md`.
