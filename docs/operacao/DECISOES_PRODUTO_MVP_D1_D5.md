# Registro de decisões de produto — MVP (D1–D5)

Atualizar esta tabela quando houver **sign-off**; valores **Default repo** refletem o código/doc em 2026-05-01.

## D1 — Free / fluxo contínuo vs conta na plataforma (decisão produto **2026-05-02**, Allan)

**Decisão:** O utilizador **pode continuar o diagnóstico sem estar logado** até ao ponto em que o produto exija **gravar o resultado na API**. Para **persistir** o diagnóstico (POST), há **sessão na plataforma** (login/cadastro) como caminho com Bearer, **sem obrigar** cadastro no primeiro ecrã; em paralelo, **OTP no e-mail** + `POST /diagnosticos/self-service` grava sem conta prévia. Na **mesma jornada**, o utilizador pode **opcionalmente** associar-se a um percurso de **contacto com consultor** (follow-up comercial ou especialista) **ou** optar por **concluir sozinho** (relatório self-service, sem promessa de contacto humano), mediante **opt-in explícito** quando houver tratamento de dados para CRM ou contacto ativo.

**Implicações:** (1) UX deve comunicar claramente os dois modos (“continuar”, “falar com consultor”) sem misturar consentimentos. (2) **LGPD / `/privacidade`:** minuta **aprovada** em parecer externo e pelo controlador (2026-05-07 — ver `docs/legal/STATUS_JURIDICO_MVP.md`); manter bases legais e finalidades alinhadas à operação. (3) Operação: SLA de consultor aplica-se apenas a leads que **manifestarem** essa opção. (4) **Gravação sem conta na plataforma prévia:** persistência na API via **OTP no e-mail** + `POST /diagnosticos/self-service` (vínculo ao e-mail); **cadastro ou login** depois permite **vincular** esses diagnósticos ao tenant da conta — ver `.cursor/rules/qdi-gravacao-diagnostico-email.mdc`.

**D2 (2026-05-02, corrigido conforme Allan; ADR-013 2026-05-10):** No **topo de funil** (self-service / rascunho / OTP **sem** conta na plataforma), CNPJ é **opcional** no wizard e nos POST `IniciarDiagnosticoRequest`. Com **sessão na plataforma** (`POST /diagnosticos/` com JWT) ou **vinculação de rascunho à conta**, CNPJ **obrigatório** (14 dígitos, DV) para histórico por empresa no tenant — ver `.github/adr/ADR-013-cnpj-contextos-lead-vs-painel.md` e `.cursor/rules/qdi-cnpj-opcional.mdc`.

---

## Registro de sincronização (2026-05-01)

- **Baseline técnico** alinhado ao gate MVP: LGPD **0012**, smoke automatizado (`tests/integration/test_smoke_mvp_fechado_api.py`), RLS dois tenants (`tests/integration/test_mvp_gate_postgres.py`), CI em `release/**` e tags `v*` / `mvp-*`.
- **D1:** ver secção **D1 — 2026-05-02** acima (**decidido**). **D3 / D4 / D5** seguem conforme tabela.
- **Processo jurídico:** minuta **`/termos`** e **`/privacidade`** com parecer externo e **aprovação produto** (2026-05-07) — `docs/legal/STATUS_JURIDICO_MVP.md`; canal DPO e versão em URL de produção seguem operacionais.

| ID | Tema | Status | Decisão registrada | Impacto técnico |
|----|------|--------|-------------------|-----------------|
| **D1** | Free self-service vs conta na plataforma | **Fechado p/ Allan (2026-05-02)** | Diagnóstico **contínuo sem login no início**; **POST** com **sessão na plataforma** ou **OTP + self-service**; utilizador pode **cadastrar-se** ou **seguir sozinho**, com **opt-in** para contacto/CRM quando aplicável. | Wizard/copy + eventual checkbox ou passo dedicado; revisão jurídica textos; POST/auth mantêm contrato actual até refactor explícito. |
| **D2** | CNPJ por contexto (lead vs painel) | **Fechado** — ADR-013 | **Lead / OTP:** CNPJ opcional (`''` na BD). **Painel / vincular rascunho:** CNPJ obrigatório (`EmpresaPainelSchema` / `IniciarDiagnosticoPainelRequest`). | API + front (`superRefine` com `admin_token`) + docs ADR-013. |
| **D3** | Faturamento / setor fino | **Adiado pós-MVP (2026-05-02)** — *faixa opcional entregue* | Catálogo usa `setor_macro`. **Complemento:** faixa de faturamento bruto anual **opcional** (autodeclaração), slugs + convenção de limites — ver **`docs/operacao/FAIXA_FATURAMENTO_AUTODECLARADA.md`**. Não reabre “setor fino” nem simulações numéricas nesta data. | Migração **0017**, wizard, API, WORM. |
| **D4** | URL canônica dev/stage/prod | **Parcial** | `RUNBOOK_DEPLOY_ROLLBACK.md`, `frontend/.env.production.example`, `NEXT_PUBLIC_SITE_URL` documentados. Falta URL final de produção assinada por Ops. | CORS + secrets ambiente alvo. |
| **D5** | Billing Plus/Pro | **Adiado (2026-05-02)** | Sem gateway no código; reavaliar após tração MVP. | Stripe/outro = roadmap Beta. |
| **D6** | Persistir M12 | Feito | Coluna `checklist_m12_estado` + PATCH dedicado. | — |

**LGPD:** aceite persistido com timestamp servidor — migração **`0012`**, campo `aceite_termos_privacidade_em`.
