# Registro de decisões de produto — MVP (D1–D5)

Atualizar esta tabela quando houver **sign-off**; valores **Default repo** refletem o código/doc em 2026-05-01.

## Registro de sincronização (2026-05-01)

- **Baseline técnico** alinhado ao gate MVP: LGPD **0012**, smoke automatizado (`tests/integration/test_smoke_mvp_fechado_api.py`), RLS dois tenants (`tests/integration/test_mvp_gate_postgres.py`), CI em `release/**` e tags `v*` / `mvp-*`.
- **D1 / D3 / D4 / D5** permanecem **pendentes de decisão de produto** (sem mudança de escopo nesta data).
- **Processo jurídico:** ver `docs/legal/STATUS_JURIDICO_MVP.md` (parecer externo ainda obrigatório para go-live comercial).

| ID | Tema | Status | Decisão registrada | Impacto técnico |
|----|------|--------|-------------------|-----------------|
| **D1** | Free self-service vs B2B logado | **Adiado (registro 2026-05-02)** | Baseline mantido: **B2B logado** para POST diagnóstico até decisão datada com stakeholders. | Se Free anônimo: novo fluxo auth + rate limit + revisão LGPD. |
| **D2** | CNPJ opcional no Free | Fechado p/ Allan | **CNPJ obrigatório** (14 dígitos) na API e wizard. | Nenhuma mudança até decisão explícita em contrário. |
| **D3** | Faturamento / setor fino | **Adiado pós-MVP (2026-05-02)** | Catálogo usa `setor_macro`; sem mudança de escopo nesta data. | Schema + UI futuros. |
| **D4** | URL canônica dev/stage/prod | **Parcial** | `RUNBOOK_DEPLOY_ROLLBACK.md`, `frontend/.env.production.example`, `NEXT_PUBLIC_SITE_URL` documentados. Falta URL final de produção assinada por Ops. | CORS + secrets ambiente alvo. |
| **D5** | Billing Plus/Pro | **Adiado (2026-05-02)** | Sem gateway no código; reavaliar após tração MVP. | Stripe/outro = roadmap Beta. |
| **D6** | Persistir M12 | Feito | Coluna `checklist_m12_estado` + PATCH dedicado. | — |

**LGPD:** aceite persistido com timestamp servidor — migração **`0012`**, campo `aceite_termos_privacidade_em`.
