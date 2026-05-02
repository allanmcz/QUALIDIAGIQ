# Registro de decisões de produto — MVP (D1–D5)

Atualizar esta tabela quando houver **sign-off**; valores **Default repo** refletem o código/doc em 2026-05-01.

## D1 — Free / fluxo contínuo vs B2B (decisão produto **2026-05-02**, Allan)

**Decisão:** O utilizador **pode continuar o diagnóstico sem estar logado** até ao ponto em que o produto exija **gravar o resultado na API**. Para **persistir** o diagnóstico (POST), mantém-se o modelo **B2B com sessão** (login/cadastro), **sem obrigar** cadastro no primeiro ecrã. Na **mesma jornada**, o utilizador pode **opcionalmente** associar-se a um percurso de **contacto com consultor** (follow-up comercial ou especialista) **ou** optar por **concluir sozinho** (relatório self-service, sem promessa de contacto humano), mediante **opt-in explícito** quando houver tratamento de dados para CRM ou contacto ativo.

**Implicações:** (1) UX deve comunicar claramente os dois modos (“continuar”, “falar com consultor”) sem misturar consentimentos. (2) **LGPD / `/privacidade`**: revisão jurídica para distinguir base legal e finalidade entre “execução do diagnóstico” e “contacto comercial/consultoria”. (3) Operação: SLA de consultor aplica-se apenas a leads que **manifestarem** essa opção.

Esta decisão **não** reabre D2 (CNPJ permanece obrigatório no fluxo declarado no wizard/API salvo mudança futura explícita).

---

## Registro de sincronização (2026-05-01)

- **Baseline técnico** alinhado ao gate MVP: LGPD **0012**, smoke automatizado (`tests/integration/test_smoke_mvp_fechado_api.py`), RLS dois tenants (`tests/integration/test_mvp_gate_postgres.py`), CI em `release/**` e tags `v*` / `mvp-*`.
- **D1:** ver secção **D1 — 2026-05-02** acima (**decidido**). **D3 / D4 / D5** seguem conforme tabela.
- **Processo jurídico:** ver `docs/legal/STATUS_JURIDICO_MVP.md` (parecer externo ainda obrigatório para go-live comercial).

| ID | Tema | Status | Decisão registrada | Impacto técnico |
|----|------|--------|-------------------|-----------------|
| **D1** | Free self-service vs B2B logado | **Fechado p/ Allan (2026-05-02)** | Diagnóstico **contínuo sem login no início**; **POST persiste com sessão B2B**; utilizador pode **cadastrar-se para consultor** ou **seguir sozinho**, com **opt-in** para contacto/CRM quando aplicável. | Wizard/copy + eventual checkbox ou passo dedicado; revisão jurídica textos; POST/auth mantêm contrato actual até refactor explícito. |
| **D2** | CNPJ opcional no Free | Fechado p/ Allan | **CNPJ obrigatório** (14 dígitos) na API e wizard. | Nenhuma mudança até decisão explícita em contrário. |
| **D3** | Faturamento / setor fino | **Adiado pós-MVP (2026-05-02)** | Catálogo usa `setor_macro`; sem mudança de escopo nesta data. | Schema + UI futuros. |
| **D4** | URL canônica dev/stage/prod | **Parcial** | `RUNBOOK_DEPLOY_ROLLBACK.md`, `frontend/.env.production.example`, `NEXT_PUBLIC_SITE_URL` documentados. Falta URL final de produção assinada por Ops. | CORS + secrets ambiente alvo. |
| **D5** | Billing Plus/Pro | **Adiado (2026-05-02)** | Sem gateway no código; reavaliar após tração MVP. | Stripe/outro = roadmap Beta. |
| **D6** | Persistir M12 | Feito | Coluna `checklist_m12_estado` + PATCH dedicado. | — |

**LGPD:** aceite persistido com timestamp servidor — migração **`0012`**, campo `aceite_termos_privacidade_em`.
