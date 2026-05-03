# Handoff QualiDiagIQ — estado completo e backlog detalhado

> **Propósito:** permitir retomada por Allan, por outro agente ou após pausa longa, **sem depender de memória de chat**.  
> **Local canônico (versionado):** `docs/HANDOFF_PROXIMA_SESSAO_QDI.md`  
> **Última atualização:** 2026-05-02 — inclui **`0019`** (RLS `admins` + `idempotency_responses.tenant_id`), **`0020`** (RAG-light: extensão **`vector`**, schema **`qdi_rag`**, `scripts/ingestao_rag_baseline.py`, adapters **`BaseNormativaPort`** / Anthropic opcional), gate **`make test-domain`** (cobertura só `src/domain` ≥85%), integração **`test_metodologia_postgres_normativa_0015`**. Migrações **`0001`…`0020`** em **`init.sql`** / **`make migrate`**; Postgres local/CI com imagem **pgvector**. Verificação ops: **`scripts/verify_mvp_schema.py --rag`** ou **`QDI_VERIFY_SCHEMA_RAG=1`**. Ver **`CHANGELOG_MVP.md`** e **`docs/HANDOFF_CICLO_Q_2026-05-02.md`**.

---

## Índice

1. [Resumo executivo](#1-resumo-executivo)  
2. [Stack e comandos](#2-stack-e-comandos-operacionais)  
3. [Mapa do repositório (onde está o quê)](#3-mapa-do-repositório-onde-está-o-quê)  
4. [O que já está implementado (snapshot técnico)](#4-o-que-já-está-implementado-snapshot-técnico)  
5. [MoSCoW MUST (M01–M12) — status e lacunas](#5-moscow-must-m01m12--status-e-lacunas)  
6. [MoSCoW SHOULD / COULD / WONT — backlog](#6-moscow-should--could--wont--backlog)  
7. [Front-end Next.js — pendências (próximo ciclo)](#7-front-end-nextjs--pendências-próximo-ciclo)  
8. [Back-end / infra / dados](#8-back-end--infra--dados)  
9. [Testes, qualidade e observabilidade](#9-testes-qualidade-e-observabilidade)  
10. [Conformidade, LGPD e critérios de lançamento](#10-conformidade-lgpd-e-critérios-de-lançamento)  
11. [Decisões de produto pendentes](#11-decisões-de-produto-pendentes)  
12. [Blocos entregues (N, M) e próximos (P1–P8)](#12-blocos-entregues-n-m-e-próximos-p1p8)  
13. [Prompt modelo para agente](#13-prompt-modelo-para-agente)  
14. [Armadilhas conhecidas (evitar regressão)](#14-armadilhas-conhecidas-evitar-regressão)  
15. [Checklist pós-sessão (Allan)](#15-checklist-pós-sessão-allan)  
16. [Documentos de referência obrigatórios](#16-documentos-de-referência-obrigatórios)  
17. [Plano MVP fechado e operação](#17-plano-mvp-fechado-e-operação)  

---

## 1. Resumo executivo

O **QualiDiagIQ (QDI)** é o módulo de diagnóstico tributário (Reforma do Consumo: **EC 132/2023**, **LC 214/2025**, **ABNT NBR 17301:2026**) dentro do ecossistema Tributiq.

**Situação atual (macro) — maio/2026:**

- **API FastAPI:** POST/GET/PATCH diagnóstico, motor em **7 dimensões**, **GET `/diagnosticos/questionario`** e **`GET /diagnosticos/manifesto-pesos`** públicos, **`GET /diagnosticos/metodologia`** com **`pesos_macro_dimensao_score_geral`** resolvido via **`NormativaScoreMacroRepository`** — com **`DATABASE_URL`** + migração **`0015`** lê **`qdi.normativa_score_macro_dimensao`** (vigência); sem DB usa constantes em **`src/domain/value_objects/score.py`**. **RAG-light (opcional):** com **`DATABASE_URL`** síncrono + **`OPENAI_API_KEY`**, **`RealizarDiagnostico`** enriquece prompt e guardrail LLM via **`BaseNormativaPort`** (**pgvector** / migração **`0020`**); senão **stub** + regex Lexiq. **`QDI_LLM_BACKEND=anthropic`** com **`ANTHROPIC_API_KEY`** usa **`AnthropicLlmAdapter`**. Catálogo **37** perguntas, idempotência escopada por tenant (**`0019`**), migrações **`0001`…`0020`** (incl. **`0012`** LGPD/WORM; **`0013`/`0014`** CNAE; **`0015`** pesos macro; **`0016`–`0018`** PDF/locale/dev; **`0019`** RLS admins/idempotency; **`0020`** RAG), **`0011`** M12, **header `X-Trace-Id`**, WORM/OTEL, **`/normativa/validar-ancora`**, **`GET /referencia/cnae/subclasses`** (JWT + `DATABASE_URL`).
- **Consultoria:** `ConsultoriaService` com frente **M07** (“Prioridade por gaps do score”) quando há `ScoreCompleto`; cronograma 5 fases; matriz com **NT CGNFS-e** na linha Jurídico (M08); checklist ABNT 10 itens.
- **Front-end:** identidade **QualiDiagIQ / Tributiq** (`public/brand`, componentes marca); cartões sociais **1200×630** (`opengraph-image` / `twitter-image`); wizard (tipos + telefone M09 + **datalist CNAE** passo 2 + links API); **`/abnt-framework`**, **`/metodologia`**, **`/termos`**, **`/privacidade`**; dashboard **M05**; detalhe radar/heatmap/**timeline** **M06**; **M12** PATCH + **If-Match**.
- **Testes:** pytest (ver **`make test`**); integração **`test_manifesto_pesos_publico`**; **`test_m07_prioridade_checklist`**; WORM inclui UPDATE **`checklist_m12_estado`** pós-finalizado; Playwright **`wizard-post`** + smoke — ordem de rotas §14.

**MoSCoW MVP (12 MUST):** **avanço grande no código**; **fechamento comercial/jurídico** ainda depende de homologação **M04**, calibração **M02** com dados reais, hardening **M10** em Supabase produção, decisões **M09** (Free vs CNPJ), e auditoria **37×35**.

**Próximo marco sugerido (§12.3):** **P1–P4** fechados; **P7** lista já usa API real no app (**§7**); foco go-live: **P5** homologação manual PDF Allan + **P6** RLS prod conforme runbook.

---

## 2. Stack e comandos operacionais

| Área | Escolha do projeto |
|------|-------------------|
| Backend | Python 3.12+, FastAPI 0.115+, Pydantic v2, Clean Architecture (`src/domain`, `application`, `infrastructure`, `presentation`) |
| DB local | PostgreSQL via Docker (**imagem pgvector** para **`0020`**); migrações `src/infrastructure/db/migrations/` (**`0001`…`0020`**) + `init.sql` na raiz |
| Front | Next.js 14 App Router, Tailwind, shadcn/ui, Recharts |
| PDF | WeasyPrint (Python) + Jinja2 (`src/infrastructure/adapters/pdf_generator_weasyprint.py`) |
| Testes | pytest, pytest-asyncio; Playwright (`frontend/e2e/`) |
| Lint / types | ruff, black, mypy strict |

**Comandos úteis:**

```bash
make install      # venv + deps
make dev          # docker compose up -d
make down
make migrate      # aplica *.sql via docker compose exec db psql
make lint
make format
make test         # pytest + cobertura (fail_under 80)
make type-check   # mypy src/
```

**Front / E2E:**

```bash
cd frontend && npm install
cd frontend && npm run test:e2e          # sobe Next na porta PLAYWRIGHT_PORT (default 3333)
cd frontend && npx playwright test e2e/wizard-post.spec.ts   # apenas contrato wizard→POST
PLAYWRIGHT_SKIP_WEBSERVER=1 npm run test:e2e   # só se já houver app no PLAYWRIGHT_BASE_URL
```

**URLs típicas (Docker Compose do repo):**

- API: `http://localhost:60000` (host `60000` → container `8000`)  
- Web: `http://localhost:60001`  
- Postgres: `localhost:60322`  
- Playwright dev server local: **`http://127.0.0.1:3333`**

**Variáveis relevantes:**

- **`NEXT_PUBLIC_API_URL`** — URL da API no browser (default no código: `http://localhost:60000`). Ver `frontend/.env.example`.
- `DATABASE_URL`, `JWT_SECRET_KEY`, `SUPABASE_*`, `OTEL_*`, **`OPENAI_API_KEY`** / **`ANTHROPIC_API_KEY`** / **`QDI_LLM_BACKEND`** / **`QDI_RAG_SIMILARITY_THRESHOLD`** — conforme `.env` / Docker e `settings.py`.

**Bases novas / upgrade:** rodar stack com volume limpo ou aplicar **`0009`** manualmente em bases já existentes (coluna `respondente_telefone`).

---

## 3. Mapa do repositório (onde está o quê)

| Caminho | Responsabilidade |
|---------|------------------|
| `src/domain/value_objects/score.py` | **`PESOS_MACRO_DIMENSAO_SCORE_GERAL`** (fallback sem DB), `pesos_macro_dimensao_para_dict_iso()` — agregação do score geral; com **`DATABASE_URL`** + **0015** a HTTP usa Postgres via `NormativaScoreMacroRepository` |
| `src/domain/entities/diagnostico.py` | `Respondente.telefone` opcional (M09) |
| `src/application/services/consultoria_service.py` | M07 frente gaps; matriz M08; checklist ABNT M12 |
| `src/application/use_cases/calcular_score_use_case.py` | Consome pesos macro do domain |
| `src/infrastructure/db/migrations/` | **`0001`…`0020`** (`0012` LGPD + WORM; `0011` M12; `0013`/`0014` CNAE; **`0015`** normativa pesos macro; **`0019`** RLS admins/idempotency; **`0020`** RAG `qdi_rag.documento_normativo` + extensão `vector`) |
| `src/application/ports/base_normativa_port.py` | Contrato RAG-light (chunks normativos) |
| `scripts/ingestao_rag_baseline.py` | Ingestão embeddings → **`qdi_rag`** (fonte default `scripts/normativos_baseline/`) |
| `docs/HANDOFF_PLANO_MVP_FECHADO.md` | Plano mestre gate MVP fechado |
| `docs/operacao/SMOKE_MVP_FECHADO.md` | Smoke manual A.3 |
| `docs/CHANGELOG_MVP.md` | Registro de entregas MVP |
| `src/presentation/api/routers/diagnostico_router.py` | **`/manifesto-pesos`**, `/metodologia`, `/questionario`, CRUD diagnóstico |
| `src/presentation/api/schemas.py` | `ManifestoPesosResponse`, `ManifestoPesoPerguntaSchema`, `nota_calibracao_m02` |
| `init.sql` | Orquestra `\i` das migrações no bootstrap Docker |
| `frontend/app/abnt-framework/page.tsx` | Hub **M11** (PDCA + 7 pilares, texto didático) |
| `frontend/app/metodologia/page.tsx` | Painel **M03** (GET metodologia + manifesto-pesos no browser) |
| `frontend/app/termos/page.tsx` | Termos de uso MVP |
| `frontend/app/privacidade/` | LGPD MVP |
| `frontend/lib/api/metodologia_public.ts` | Clientes HTTP públicos M03 |
| `frontend/app/dashboard/diagnosticos/[id]/DiagnosticoDetalheClient.tsx` | Radar, heatmap, gaps, cronograma+tabela+t**imeline**, **M12** + PATCH servidor |
| `frontend/app/dashboard/page.tsx` | Lista **GET `/diagnosticos/`** quando logado + **barra M05**; E2E usa mock |
| `frontend/components/wizard/WizardForm.tsx` | Tipos pergunta, telefone, `aria-live`, links API + **`/metodologia`** |
| `frontend/lib/schemas/wizard.ts` | Zod incl. `respondente.telefone` |
| `docs/operacao_rls_idempotency.md` | Operação RLS + idempotência |
| `frontend/e2e/` | `smoke.spec.ts`, `wizard-post.spec.ts`, `dashboard-list.spec.ts`, `wizard-normativa.spec.ts` (flag) |
| `docs/refs/` | PRD, MoSCoW, questionário v1, metodologia |

---

## 4. O que já está implementado (snapshot técnico)

### 4.1 API HTTP

- **POST `/diagnosticos/`** — Bearer JWT + **`Idempotency-Key`** obrigatória; corpo com **`aceite_termos_privacidade: true`** (LGPD) e opcional **`respondente.telefone`**.  
- **GET `/diagnosticos/{id}`**, **PATCH `/{id}`** (relatório PDF, If-Match), **PATCH `/{id}/checklist-m12-autoconf`** (M12, If-Match), **GET `/diagnosticos/metodologia`**, **`GET /diagnosticos/manifesto-pesos`**, **GET `/health`**, **POST `/auth/login`**.  
- **GET `/diagnosticos/questionario`** — público (query perfil empresa).  
- **POST `/normativa/validar-ancora`** — protótipo guardrail (N7).

### 4.2 Resposta de diagnóstico (JSON)

- `score`, `checklist` (**incl. frente M07** quando score disponível), `matriz_impacto`, `cronograma`, `relatorio_pdf_url`, **`checklist_m12_autoconf`** (10 booleanos quando persistido), **`aceite_termos_privacidade_em`** (instante UTC do POST), WORM/metadata (`hash_evidencia`, `versao_otimista`).

### 4.3 Domínio e PDF

- Motor 7 dimensões; PDF com marcadores **M04** (`capa`, `sintese_executiva`, `tecnico_detalhamento_dimensoes`, **`tecnico_gaps_recomendacoes`**, etc.); paleta **Tributiq** + logo NB1 em `assets/`; síntese executiva com `page-break-inside: avoid`; disclaimer reforçado (EC 132/2023, LC 214/2025, ABNT NBR 17301:2026).
- **`nota_calibracao_m02`** exposta no JSON do manifesto (texto roadmap Beta).
- Fallback WeasyPrint indisponível: **`structlog`** (`weasyprint_indisponivel_pdf_mock`), sem `print`.

### 4.4 Front (contrato)

- Lista dashboard: prévia por score (barra) via **`fetchDiagnosticosResumo`** quando há sessão.  
- Detalhe: cronograma em tabela + **linha do tempo**; **M12** espelho dos 10 itens ABNT com **sync ao backend** (debounce).  
- **`/abnt-framework`**: navegação M11; **`/metodologia`**, **`/termos`**, **`/privacidade`**: páginas públicas MVP.

### 4.5 Testes automatizados

- **`tests/integration/test_api.py`:** `test_manifesto_pesos_publico`, `test_metodologia_endpoint` (chaves **`pesos_macro_dimensao_score_geral`**).  
- **`tests/unit/application/test_consultoria_service.py`:** `test_m07_prioridade_checklist_por_piores_dimensoes`, matriz com CGNFS-e.  
- **`tests/unit/infrastructure/test_pdf_template_m04.py`:** assert **`M04_SECAO: tecnico_gaps_recomendacoes`**.

### 4.6 Paridade documental

- Script **`scripts/auditoria_questionario_vs_catalogo.py`** + relatório `docs/operacao/auditoria_catalogo_vs_pr_v1_2026-05-01.md` — **37 códigos** alinhados ao catálogo JSON (`P4` fechado em §12.3). Revisão editorial **37×35** no doc legado `docs/refs/05_QUESTIONARIO_v1.md` pode seguir como refinamento de texto, não bloqueio de código.

### 4.7 CNAE 2.3 (referência global)

- Migrações **`0013_cnae_referencia.sql`** (DDL, RLS, view `qdi.v_cnae_completo`, RPC `fn_importar_cnae_subclasses`) e **`0014_cnae_seed_dados.sql`** (seed IBGE/CONCLA — 1332 subclasses). UUID do log com **`gen_random_uuid()`** (sem `uuid-ossp`, alinhado a `0001_extensions.sql`).
- **API/UI de lookup** no wizard — **GET `/referencia/cnae/subclasses`** + datalist no passo 2 (sessão + `DATABASE_URL`); dados continuam disponíveis via SQL/RPC administrativas.

---

## 5. MoSCoW MUST (M01–M12) — status e lacunas

| ID | Feature | Status | Comentário / pendência |
|----|---------|--------|-------------------------|
| **M01** | Wizard adaptativo | **Fortemente avançado** | Ramos por tipo; copy + `aria-live` no fetch; revisar UX edge cases (`multipla_total`/`opcoes` vazias). |
| **M02** | Motor score 0–100, 6+ dimensões | **OK no núcleo** | Calibração por coorte real = roadmap (`nota_calibracao_m02` no manifesto). |
| **M03** | Pesos transparentes | **Avançado** | API **`/manifesto-pesos`** + **`/metodologia`**; Next **`/metodologia`** (painel) + links home/wizard/rodapé. |
| **M04** | PDF executivo | **PARCIAL técnico** | Homologação contábil “1 exec + N técnicas”, WeasyPrint em produção, revisão páginas. |
| **M05** | Heatmap + radar + ranking gaps | **Avançado** | Completo no detalhe + barra na **lista** com dados do **GET `/diagnosticos/`** (logado); E2E da lista continua mockada no CI. |
| **M06** | Cronograma 5 fases | **Avançado** | Tabela + **timeline** no detalhe + PDF; polimento visual se Allan quiser. |
| **M07** | Recomendações priorizadas | **Avançado** | **3 dimensões piores score** geram primeira frente de checklist (regra determinística). |
| **M08** | Ancoragem legal por bullet | **PARCIAL** | Matriz jurídica + NT CGNFS-e; revisão editorial linha-a-linha (todas NTs / dispositivos). |
| **M09** | Lead magnet self-service | **PARCIAL** | Telefone opcional (**`0009`**); **CNPJ obrigatório** na API (decisão **D2**); jornada Free anónima / D1 = decisão produto (§11). |
| **M10** | Multi-tenant Supabase + RLS | **PARCIAL** | RLS + docs + comentários tabela; **políticas e roles produção** + auditoria periódica. |
| **M11** | Eixos ABNT como espinha | **Avançado UI** | **`/abnt-framework`** + links no wizard e detalhe; linkagem pergunta↔pilar no catálogo = opcional. |
| **M12** | Checklist 10 itens binários | **OK MVP** | **`checklist_m12_estado`** no PostgreSQL; **PATCH** dedicado + UI com debounce; WORM granular permite após finalizado. |

---

## 6. MoSCoW SHOULD / COULD / WONT — backlog

- **SHOULD:** S01 LLM plano (**não** núcleo); **S02** RAG wizard completo (**não**); existe endpoint **validar-ancora** + guardrail.  
- **COULD:** Winthor, white-label, API pública documentada.  
- **WONT:** QAI, QFC, QMI, defesa auto, RestituIQ.

---

## 7. Front-end Next.js — pendências (próximo ciclo)

1. **P3 `asChild`:** tipagem `SlotProps` no `Button` + build strict — **feito** (2026-05-01).  
2. **P2 E2E:** Playwright com `CI=true` — **feito** (8 passed + 1 suite P8 em skip quando sem flag).  
3. **Lista dashboard (P7):** **`frontend/app/dashboard/page.tsx`** já chama **`fetchDiagnosticosResumo`** (`GET /diagnosticos/`) com estados carregando / vazio / erro; **não** há mock hardcoded na página. O E2E **`dashboard-list.spec.ts`** continua com **`page.route`** mockando a API porque o job **`frontend-e2e`** não sobe o backend — isso é **intencional** para CI. Teste “sem mock” só faz sentido em job integrado ou local com API + login.  
4. **P8 wizard normativa:** flag **`NEXT_PUBLIC_WIZARD_NORMATIVA`**; painel passo 3 com **`data-testid="wizard-p8-normativa"`**. Local/CI opcional: **`npm run test:e2e:wizard-normativa`** (define **`PLAYWRIGHT_WIZARD_NORMATIVA=1`** + env no `webServer`).  
5. **Página Next `/metodologia`:** — **feito** (`frontend/app/metodologia/page.tsx`) — consome **`GET /diagnosticos/metodologia`** + **`GET /diagnosticos/manifesto-pesos`**; estado de erro se API offline; wizard linka **Metodologia (painel)**.  
6. **Acessibilidade:** axe / checklist manual — incremental: rodapé em `<nav aria-label="Links institucionais">`; CTAs da home como `<Link>` (não botão inerte).  
7. **`allowedDevOrigins`:** `next.config.mjs` inclui host/porta e URLs `http://…` para E2E; em **Next 14.2.35** o aviso “Blocked cross-origin… `/_next/*`” ainda pode aparecer no log do `next dev` durante Playwright (**ruído dev-only**, builds `next build` OK).
8. **Marca + SEO social:** `frontend/public/brand/`; **`NEXT_PUBLIC_SITE_URL`** para `metadataBase`; rotas **`/opengraph-image`** e **`/twitter-image`** (1200×630 via `next/og`). Exemplo produção: **`frontend/.env.production.example`**.

---

## 8. Back-end / infra / dados

- **P4:** Script + relatório `docs/operacao/auditoria_catalogo_vs_pr_v1_2026-05-01.md` (37 códigos alinhados ao PRD).  
- **P5 + M04:** Homologação PDF + paginação/impressão; ajustes técnicos Ciclo Q registados em `PDF_HOMOLOGACAO_CHECKLIST_B1.md`.  
- **P6:** OTEL prod; OpenAPI **P1 feito**; RLS prod pendente — **gap analysis:** `docs/operacao/GAP_ANALYSIS_RLS_P6_2026-05-02.md` (G2 fechado: **`make verify-schema-mvp-strict`** + SQL MVP).  
- **CNAE:** migrações **`0013`/`0014`** + `init.sql`; ambientes já criados: rodar **`make migrate`**.  
- Versionamento normativo DB (`vigencia_*`) nas regras de score — não implementado (CNAE já tem vigência nas tabelas de referência).  
- **Bases antigas:** garantir migrações até **`0012`** mínimo; para CNAE, até **`0014`**.

---

## 9. Testes, qualidade e observabilidade

| Item | Estado |
|------|--------|
| pytest, cobertura ≥ 80% | **OK** (`make test`; script auditoria fora do pytest) |
| mypy `src` | **OK** |
| ruff + black | Rodar **`make format`** ao fechar sessão |
| Playwright | Smoke (landing, **`/metodologia`**, **`/termos`**, **`/privacidade`**, wizard, login) + **`wizard-post`** + **`wizard-edge-cases`** (multipla/opções vazias/voltar passo) + **`dashboard-list`**; opcional **`test:e2e:wizard-normativa`** (P8 com flag). Passo 2 do wizard exige selects (**porte**, **regime**, **setor_macro**, **UF**) nos E2E. |
| Calibração score (campo real) | **NÃO** |

**OpenAPI JSON (export local):** não depende de servidor HTTP — usar **`make openapi-export`** (escreve `docs/api/openapi.generated.json`, ignorado no git). Útil para diff antes de PR que mexa em routers/schemas. Integração adicional: `tests/integration/test_openapi_public_endpoints_shapes.py` valida shapes dos endpoints públicos P1.

**CI `frontend-e2e`:** `npm ci`, `npm run lint`, **`npm run build`** (tipagem Next), Playwright Chromium e `CI=true npm run test:e2e`; **não** sobe o backend Python — os testes E2E mockam a API via `page.route`. Backend continua em job separado `backend`.

---

## 10. Conformidade, LGPD e critérios de lançamento

Parecer jurídico em **privacidade** e **termos de uso** “oficiais” (hoje MVP em **`/privacidade`** e **`/termos`**), homologação **M04**, assinatura negocial dos **12 MUST**, política de retenção do **`respondente_telefone`**: **abertos**.

---

## 11. Decisões de produto pendentes

| # | Tema | Observação |
|---|------|------------|
| D1 | Free self-service vs B2B logado | Narrativa + fluxo (wizard já menciona lead B2B). |
| D2 | CNPJ opcional no Free | API ainda **exige** CNPJ 14 dígitos. |
| D3 | Faturamento / setor detalhado | Schema + UI. |
| D4 | URL canônica dev/stage/prod | Deploy docs. |
| D5 | Billing Plus/Pro | Triggers comerciais sem cobrança no código. |
| **D6** | **Persistir estado M12** (checkboxes) | **Feito** — coluna **`checklist_m12_estado`**, contrato **`checklist_m12_autoconf`** + **If-Match** (não altera hash de evidência do score). |
| **D7** | **Aceite LGPD com timestamp servidor** | **Feito** — **`0012`**, campo **`aceite_termos_privacidade_em`**, WORM bloqueia alteração pós-finalizado. |

---

## 12. Blocos entregues (N, M) e próximos (P1–P8)

### 12.1 Ciclo **N** (concluído — referência)

| ID | Escopo entregue (resumo) |
|----|--------------------------|
| **N1** | Dashboard detalhe: cronograma, matriz, checklist; radar + heatmap + ranking; PDF. |
| **N2** | Wizard por `tipo`; LGPD → `/privacidade`. |
| **N3** | Playwright `wizard-post`; ordem de `page.route` (§14). |
| **N4** | Marcadores **M04** no HTML PDF + teste Jinja. |
| **N5** | Heatmap + barras gaps no detalhe. |
| **N6** | `docs/operacao_rls_idempotency.md` + migração **0008**. |
| **N7** | `lexiq_guardrail`, `/normativa/validar-ancora`, testes. |

### 12.2 Ciclo **M** (MoSCoW MUST — incremento código abril/2026)

| ID | Entrega resumida |
|----|------------------|
| **M01** | Copy passos + `aria-live` carregamento catálogo. |
| **M02** | `nota_calibracao_m02` no manifesto; pesos macro centralizados no **domain**. |
| **M03** | **`GET /diagnosticos/manifesto-pesos`**; **`GET /diagnosticos/metodologia`**; Next **`/metodologia`** (painel) + links na home/rodapé. |
| **M04** | Marcador **`tecnico_gaps_recomendacoes`** no template. |
| **M05** | Barra score na **lista** dashboard (dados do **GET /diagnosticos/** quando logado). |
| **M06** | **Timeline** vertical no detalhe (além da tabela). |
| **M07** | Frente checklist **top 3 dimensões** mais fracas. |
| **M08** | **NT CGNFS-e** na matriz Jurídico. |
| **M09** | **`respondente.telefone`** + migração **0009** + campo wizard. |
| **M10** | Comentários SQL em **0009** (auditoria tabela/coluna). |
| **M11** | **`/abnt-framework`** + links. |
| **M12** | Persistência M12: migração **0011**, PATCH API, debounce no detalhe. |

### 12.3 Ciclo **P** (próximo handoff operacional)

| ID | Escopo | Pronto quando |
|----|--------|---------------|
| **P1** | **OpenAPI/Swagger:** exemplos `manifesto-pesos`, metodologia, POST diagnóstico (Idempotency), normativa | **Feito** — `MetodologiaResponse`, campos `ManifestoPesoPerguntaSchema`, summaries GET/POST, normativa; `make type-check` |
| **P2** | **CI E2E** Playwright (`wizard-post` mínimo) | **Verde** — `CI=true npm run test:e2e` (**8** passed + 1 suite P8 skip); `frontend/.env.example` documenta `PLAYWRIGHT_*` |
| **P3** | Corrigir warning **`asChild`** no `Button` | **Feito** — tipagem `SlotProps` em `button.tsx` + build Next sem erro |
| **P4** | **Auditoria 37×35** + ajuste catálogo ou doc | **Feito** — `scripts/auditoria_questionario_vs_catalogo.py` + `docs/operacao/auditoria_catalogo_vs_pr_v1_2026-05-01.md` (37=37) |
| **P5** | **M04** homologação + PDF produção (WeasyPrint) | Checklist contábil Allan |
| **P6** | **M10** hardening Supabase prod (RLS, roles, revisão) | Runbook + teste de fumaça tenant |
| **P7** | Dashboard lista **GET real** no browser + empty states | **Feito** no app; E2E lista **mock** no CI (sem backend) — ver **§7** |
| **P8** | Feature flag painel normativa no wizard (`validar-ancora`) | **Feito** código + E2E opcional verde (`test:e2e:wizard-normativa`) |

**Prioridade sugerida:** **P5 + P6** (go-live); **P7** e **P8** código/E2E fechados — ver **§7**. Ver `docs/HANDOFF_IMPLEMENTACAO_10H_2026-05-01.md` (plano 10h).

**Ciclo Q (2026-05-02):** plano em `docs/HANDOFF_CICLO_Q_2026-05-02.md` — entregues sincronização deste handoff, PDF técnico B1, gap P6, CNAE **0013/0014**, deploy **D4** (`RUNBOOK_DEPLOY_ROLLBACK.md` + `.env.production.example`).

---

## 13. Prompt modelo para agente

```
Branch local: feat/qdi-<nome>.

Leia docs/HANDOFF_PROXIMA_SESSAO_QDI.md (§1, §7, §12.3 — bloco P<n> acordado).

Escopo: apenas o bloco P combinado — não expandir QAI/QFC/QMI sem pedido explícito.

Não fazer: git push/rebase sem confirmação do Allan.

Ao terminar: make lint; make format; make test; mypy src; se front: npx playwright test quando relevante.

Playwright: rotas específicas (*questionario*) depois de rotas amplas (*diagnosticos**) — §14.
```

---

## 14. Armadilhas conhecidas (evitar regressão)

1. **Playwright `page.route`:** ordem **último registrado = avaliado primeiro**; handler amplo `**/diagnosticos**` com `continue()` em GET pode impedir mock de **`questionario`** → “Failed to fetch”.  
2. **Rotas FastAPI estáticas:** **`/manifesto-pesos`** e **`/metodologia`** devem permanecer **antes** de **`/{diagnostico_id}`** (UUID).  
3. **Migração 0009:** ambientes criados antes dela precisam do `ALTER` aplicado; senão upsert pode falhar se PostgREST exigir coluna.  
4. **LGPD:** `aceite_termos_privacidade` **fora** do POST de criação (strip no client).  

---

## 15. Checklist pós-sessão (Allan)

- [ ] Diff revisado  
- [ ] `make test` + `mypy src` (+ Playwright se front)  
- [ ] Atualizar este handoff após mudanças em §4–§8, §12 ou novas migrations  
- [ ] Commit Conventional em **pt-BR** quando satisfeito  

---

## 16. Documentos de referência obrigatórios

1. `docs/refs/01_PRD_BASE.md`  
2. `docs/refs/02_MOSCOW_FEATURES.md`  
3. `docs/refs/05_QUESTIONARIO_v1.md`  
4. `docs/refs/04_METODOLOGIA.md`  
5. `docs/01_arquitetura.md`  
6. `docs/02_dominio_qdi.md`  

---

## 17. Plano MVP fechado e operação

- **Plano mestre (gate comercial/técnico):** `docs/HANDOFF_PLANO_MVP_FECHADO.md`  
- **Smoke manual:** `docs/operacao/SMOKE_MVP_FECHADO.md`  
- **Smoke + gate Postgres (CI/local):** `make mvp-gate`; testes `test_smoke_mvp_fechado_api.py`, `test_mvp_gate_postgres.py`  
- **Verificação schema pós-migrate (ops):** `make verify-schema-mvp` ou `docs/operacao/SQL_VERIFICACAO_SCHEMA_MVP.sql`  
- **PDF homologação (P5):** `docs/operacao/PDF_HOMOLOGACAO_CHECKLIST_B1.md`  
- **Deploy / rollback:** `docs/operacao/RUNBOOK_DEPLOY_ROLLBACK.md`  
- **Trace HTTP / OTEL:** `docs/operacao/OBSERVABILIDADE_TRACE_ID.md`  
- **Decisões D1–D5:** `docs/operacao/DECISOES_PRODUTO_MVP_D1_D5.md`  
- **Status jurídico (processo vs parecer):** `docs/legal/STATUS_JURIDICO_MVP.md`  
- **Changelog MVP:** `docs/CHANGELOG_MVP.md`  

---

*Fim do handoff. Próximo: **§12.3 P5–P8** — detalhe em `docs/HANDOFF_IMPLEMENTACAO_10H_2026-05-01.md`.*
