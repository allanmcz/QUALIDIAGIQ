# Registro de decisões de produto — MVP (D1–D5)

Atualizar esta tabela quando houver **sign-off**; valores **Default repo** refletem o código/doc em 2026-05-01.

## D1 — Free / fluxo contínuo vs conta na plataforma (decisão produto **2026-05-02**, Allan)

**Decisão:** O utilizador **pode continuar o diagnóstico sem estar logado** até ao ponto em que o produto exija **gravar o resultado na API**. Para **persistir** o diagnóstico (POST), há **sessão na plataforma** (login/cadastro) como caminho com Bearer, **sem obrigar** cadastro no primeiro ecrã; em paralelo, **OTP no e-mail** + `POST /diagnosticos/self-service` grava sem conta prévia. Na **mesma jornada**, o utilizador pode **opcionalmente** associar-se a um percurso de **contacto com consultor** (follow-up comercial ou especialista) **ou** optar por **concluir sozinho** (relatório self-service, sem promessa de contacto humano), mediante **opt-in explícito** quando houver tratamento de dados para CRM ou contacto ativo.

**Implicações:** (1) UX deve comunicar claramente os dois modos (“continuar”, “falar com consultor”) sem misturar consentimentos. (2) **LGPD / `/privacidade`**: revisão jurídica para distinguir base legal e finalidade entre “execução do diagnóstico” e “contacto comercial/consultoria”. (3) Operação: SLA de consultor aplica-se apenas a leads que **manifestarem** essa opção. (4) **Gravação sem conta na plataforma prévia:** persistência na API via **OTP no e-mail** + `POST /diagnosticos/self-service` (vínculo ao e-mail); **cadastro ou login** depois permite **vincular** esses diagnósticos ao tenant da conta — ver `.cursor/rules/qdi-gravacao-diagnostico-email.mdc`.

**D2 (2026-05-02, corrigido conforme Allan):** CNPJ é **opcional** no wizard e na API; se informado, valida-se DV e persiste-se o vínculo PJ. Ver `.cursor/rules/qdi-cnpj-opcional.mdc`.

---

## Registro de sincronização (2026-05-01)

- **Baseline técnico** alinhado ao gate MVP: LGPD **0012**, smoke automatizado (`tests/integration/test_smoke_mvp_fechado_api.py`), RLS dois tenants (`tests/integration/test_mvp_gate_postgres.py`), CI em `release/**` e tags `v*` / `mvp-*`.
- **D1:** ver secção **D1 — 2026-05-02** acima (**decidido**). **D3 / D4 / D5** seguem conforme tabela.
- **Processo jurídico:** ver `docs/legal/STATUS_JURIDICO_MVP.md` (parecer externo ainda obrigatório para go-live comercial).

| ID | Tema | Status | Decisão registrada | Impacto técnico |
|----|------|--------|-------------------|-----------------|
| **D1** | Free self-service vs conta na plataforma | **Fechado p/ Allan (2026-05-02)** | Diagnóstico **contínuo sem login no início**; **POST** com **sessão na plataforma** ou **OTP + self-service**; utilizador pode **cadastrar-se** ou **seguir sozinho**, com **opt-in** para contacto/CRM quando aplicável. | Wizard/copy + eventual checkbox ou passo dedicado; revisão jurídica textos; POST/auth mantêm contrato actual até refactor explícito. |
| **D2** | CNPJ opcional no diagnóstico | **Fechado p/ Allan (2026-05-02, alinhado código 2026-05)** | **CNPJ opcional**; vazio permitido; se preenchido → 14 dígitos + DV; BD `empresa_cnpj` pode ser `''`. | Schemas API + Zod wizard + copy; regra persistente `.cursor/rules/qdi-cnpj-opcional.mdc`. |
| **D3** | Faturamento / setor fino | **Adiado pós-MVP (2026-05-02)** — *faixa opcional entregue* | Catálogo usa `setor_macro`. **Complemento:** faixa de faturamento bruto anual **opcional** (autodeclaração), slugs + convenção de limites — ver **`docs/operacao/FAIXA_FATURAMENTO_AUTODECLARADA.md`**. Não reabre “setor fino” nem simulações numéricas nesta data. | Migração **0017**, wizard, API, WORM. |
| **D4** | URL canônica dev/stage/prod | **Parcial** | `RUNBOOK_DEPLOY_ROLLBACK.md`, `frontend/.env.production.example`, `NEXT_PUBLIC_SITE_URL` documentados. Falta URL final de produção assinada por Ops. | CORS + secrets ambiente alvo. |
| **D5** | Billing Plus/Pro | **Adiado (2026-05-02)** | Sem gateway no código; reavaliar após tração MVP. | Stripe/outro = roadmap Beta. |
| **D6** | Persistir M12 | Feito | Coluna `checklist_m12_estado` + PATCH dedicado. | — |

**LGPD:** aceite persistido com timestamp servidor — migração **`0012`**, campo `aceite_termos_privacidade_em`.
