# Handoff QualiDiagIQ — estado completo e backlog detalhado

> **Propósito:** permitir retomada por Allan, por outro agente ou após pausa longa, **sem depender de memória de chat**.  
> **Local canônico (versionado):** `docs/HANDOFF_PROXIMA_SESSAO_QDI.md`  
> **Última atualização:** 2026-04-30  

---

## Índice

1. [Resumo executivo](#1-resumo-executivo)  
2. [Stack e comandos](#2-stack-e-comandos-operacionais)  
3. [Mapa do repositório (onde está o quê)](#3-mapa-do-repositório-onde-está-o-quê)  
4. [O que já está implementado (snapshot técnico)](#4-o-que-já-está-implementado-snapshot-técnico)  
5. [MoSCoW MUST (M01–M12) — status e lacunas](#5-moscow-must-m01m12--status-e-lacunas)  
6. [MoSCoW SHOULD / COULD / WONT — backlog](#6-moscow-should--could--wont--backlog)  
7. [Front-end Next.js — pendências críticas](#7-front-end-nextjs--pendências-críticas)  
8. [Back-end / infra / dados](#8-back-end--infra--dados)  
9. [Testes, qualidade e observabilidade](#9-testes-qualidade-e-observabilidade)  
10. [Conformidade, LGPD e critérios de lançamento](#10-conformidade-lgpd-e-critérios-de-lançamento)  
11. [Decisões de produto pendentes](#11-decisões-de-produto-pendentes)  
12. [Blocos sugeridos para próximas sessões (F em diante)](#12-blocos-sugeridos-para-próximas-sessões-f-em-diante)  
13. [Prompt modelo para agente](#13-prompt-modelo-para-agente)  
14. [Checklist pós-sessão (Allan)](#14-checklist-pós-sessão-allan)  
15. [Documentos de referência obrigatórios](#15-documentos-de-referência-obrigatórios)  

---

## 1. Resumo executivo

O **QualiDiagIQ (QDI)** é o módulo de diagnóstico tributário (Reforma do Consumo: **EC 132/2023**, **LC 214/2025**, **ABNT NBR 17301:2026**) dentro do ecossistema Tributiq.

**Situação atual (macro):**

- O **núcleo de API FastAPI** está avançado: diagnóstico (POST/GET/PATCH), motor de score 7 dimensões, questionário adaptativo via **GET `/diagnosticos/questionario`**, catálogo JSON versionado (**37** perguntas), idempotência **persistente** opcional (Postgres), WORM/hash/versão otimista, OTEL opcional.
- O **front-end** ainda **não está alinhado** ao contrato real da API em pontos críticos: falta **Bearer JWT**, falta **Idempotency-Key** no POST, URLs de API podem divergir do Docker (**porta 60000** vs `localhost:8000`), wizard ainda usa **perguntas mock** em vez do GET adaptativo.
- O **MVP MoSCoW (12 MUST)** **não** está fechado: faltam entregas fortes em **relatório PDF completo (M04)**, **visualizações (M05)**, **cronograma 5 fases (M06)**, **recomendações determinísticas ricas + ancoragem legal por bullet (M07/M08)**, **lead magnet / fluxo Free conforme doc (M09)**, **hardening multi-tenant Supabase/RLS em produção (M10)**, **checklist 10 itens explícito (M12)**, além de **fechar M01 no front**.

**Próximo marco recomendado:** **Bloco F — integração front ↔ API (auth + idempotência + GET questionário)** — desbloqueia demo ponta a ponta sem mentir no contrato HTTP.

---

## 2. Stack e comandos operacionais

| Área | Escolha do projeto |
|------|-------------------|
| Backend | Python 3.12+, FastAPI 0.115+, Pydantic v2, Clean Architecture (`src/domain`, `application`, `infrastructure`, `presentation`) |
| DB local | PostgreSQL (imagem Supabase-compatible) via Docker; migrações em `src/infrastructure/db/migrations/` + `init.sql` |
| Front | Next.js 14 App Router, Tailwind, shadcn/ui |
| PDF | WeasyPrint (Python) |
| Testes | pytest, pytest-asyncio; Playwright citado no PRD — **ainda sem suíte Playwright no repo** |
| Lint / types | ruff, black, mypy strict |

**Comandos úteis:**

```bash
make install      # venv + deps
make dev          # docker compose up -d
make down
make migrate      # aplica todos os *.sql em ordem via `docker compose exec db psql`
make lint
make format
make test
make type-check   # mypy src/
```

**URLs típicas (Docker Compose do repo):**

- API: `http://localhost:60000` (mapeamento `60000:8000` no host)  
- Web: `http://localhost:60001`  
- Postgres: `localhost:60322`  

O login MVP em `frontend/app/login/page.tsx` hoje aponta para `http://127.0.0.1:8000` — **inconsistente** com o compose acima (pendência).

**Variáveis relevantes:**

- `DATABASE_URL` — na API Docker já existe (`postgresql+asyncpg://...@db:5432/postgres`); `sync_database_url` remove `+asyncpg` para SQLAlchemy sync (idempotência).  
- `OTEL_TRACING_ENABLED`, `OTEL_SERVICE_NAME` — tracing console quando habilitado.  
- `JWT_SECRET_KEY`, `SUPABASE_*` — conforme `.env` / ambiente.

---

## 3. Mapa do repositório (onde está o quê)

| Caminho | Responsabilidade |
|---------|------------------|
| `src/domain/` | Entidades puras (`diagnostico`, `questionario`), VOs de score, ports |
| `src/application/` | Casos de uso (`realizar_diagnostico`, `calcular_score`, `gerar_questionario_adaptativo`, …), `ConsultoriaService` |
| `src/infrastructure/` | Supabase repo, PDF WeasyPrint, questionário JSON (`data/perguntas_mvp.json`, `json_banco_loader`, `banco_cache`), idempotência Postgres, settings |
| `src/presentation/api/` | `main.py`, `dependencies.py`, `schemas.py`, routers, middleware idempotência |
| `src/infrastructure/db/migrations/` | `0001`…`0007` (inclui `idempotency_responses`) |
| `init.sql` | Bootstrap + `\i` das migrações no primeiro start do volume DB |
| `frontend/` | App Router, wizard, dashboard, `lib/api`, `lib/schemas` |
| `docs/refs/` | PRD-base, MoSCoW, questionário v1, metodologia |
| `docs/01_arquitetura.md`, `docs/02_dominio_qdi.md` | Arquitetura e domínio |

---

## 4. O que já está implementado (snapshot técnico)

### 4.1 API HTTP

- **POST `/diagnosticos/`** — cria diagnóstico; exige **Bearer JWT** (`sub`, `tenant_id`) e **header `Idempotency-Key`** (middleware).  
- **GET `/diagnosticos/{id}`** — isolamento por tenant via repositório.  
- **PATCH `/diagnosticos/{id}`** — anexa URL de PDF com **If-Match** (versão otimista).  
- **GET `/diagnosticos/metodologia`** — pesos por dimensão (transparência parcial).  
- **GET `/diagnosticos/questionario`** — query params de perfil (`cnpj`, `razao_social`, `porte`, `regime`, `cnae_principal`, `uf`, `setor_macro`) + JWT; resposta com `versao_catalogo`, lista filtrada por `GerarQuestionarioAdaptativoUseCase`.  
- **POST `/auth/login`** — fluxo MVP para token (validar alinhamento com seed de admin).  
- **GET `/health`**

### 4.2 Domínio e motor

- **Score 0–100** com **7 dimensões** (inclui compliance ABNT como valor de enum).  
- **Pesos macro** por dimensão no `CalcularScoreUseCase` (Fiscal, Tecnológica, Compliance ABNT reforçados).  
- **Tipos de pergunta:** ternária (com `nao_se_aplica` excluído da média), binária, escala 1–5, múltipla, checklist, numérica.  
- **Condicionais:** regime, setor permitido/excluído, portes permitidos.  
- **Evidência / WORM:** campos de hash, snapshot de score, trigger de imutabilidade pós-finalização (migrações `0005`/`0006`).

### 4.3 Dados

- Catálogo **`perguntas_mvp.json`**: `versao_catalogo` = **`v1-doc-05-full-37`**, **37** perguntas com UUID estáveis (namespace no JSON).  
- **Nota de paridade:** o doc `docs/refs/05_QUESTIONARIO_v1.md` fala em **35** perguntas no banco total (21+9+5). Os **37** no JSON precisam ser **reconciliados** com o doc (duplicatas, extras ou doc desatualizado) — pendência explícita de auditoria editorial.

### 4.4 Idempotência e observabilidade

- Tabela **`idempotency_responses`** (`0007`); replay compatível com hash da chave + Authorization.  
- Fallback **TTLCache** em memória se não houver engine sync.  
- **OpenTelemetry:** instrumentação FastAPI + export console quando flag ativa (não é pipeline prod completo).

### 4.5 Testes automatizados

- **Unit + integration ASGI** (httpx) para health, metodologia, questionário, POST sem auth, etc.  
- **Integração Postgres** para WORM (`tests/integration/test_worm_postgres.py`, marcador `postgres`).  
- **Testes** para backend idempotência com mocks SQLAlchemy.  
- **Cobertura global** configurada com `fail_under = 80` — última meta atingida com suíte verde.

---

## 5. MoSCoW MUST (M01–M12) — status e lacunas

Legenda: **OK** = atende o espírito da feature no código atual; **PARCIAL**; **NÃO** = não atende ou só no papel.

| ID | Feature | Status | Comentário / pendência |
|----|---------|--------|-------------------------|
| **M01** | Wizard adaptativo (segmento × regime × porte × UF) | **PARCIAL** | Backend: GET + filtro **OK**. Front: ainda **MOCK_QUESTIONS** (3 itens), não chama GET; fluxo não guia 12–15 min nem todos os tipos de pergunta. |
| **M02** | Motor score 0–100, 6+ dimensões | **OK** (refinar) | 7 dimensões; calibração contra cases reais (MoSCoW §8) **não feita**. |
| **M03** | Pesos transparentes + ponderação | **PARCIAL** | `/metodologia` e PRD; falta **manifesto público** único (peso por pergunta exportado / OpenAPI rico / página legal). |
| **M04** | PDF executivo (1p exec + 6p técnicas) | **PARCIAL** | WeasyPrint gera PDF; estrutura **não** validada como 1+6 páginas nem “executivo” vs técnico; revisão contador **pendente**. |
| **M05** | Heatmap + radar + ranking gaps | **NÃO** | `ConsultoriaService` gera checklist/matriz **textuais**; sem visualizações acordadas no front (Recharts instalável mas não fechado). |
| **M06** | Cronograma 5 fases temporais | **NÃO** | Prazos genéricos em checklist; sem modelo explícito curto/médio/longo/36–60m/60–96m na UI/PDF. |
| **M07** | Recomendações priorizadas (determinísticas) | **PARCIAL** | Regras por porte/regime em checklist/matriz; falta **priorização** explícita, scoring de ações, ligação forte com gaps das respostas. |
| **M08** | Ancoragem legal por bullet | **PARCIAL** | Perguntas têm `base_legal` no JSON; checklist/matriz **não** repete citação dispositivo a dispositivo em cada bullet. |
| **M09** | Lead magnet self-service | **PARCIAL** | Wizard público existe; doc pede campos (segmento detalhado, faturamento, CNPJ opcional Free) **não** todos no schema; fluxo **login B2B** misturado ao lead self-service — definir jornada. |
| **M10** | Multi-tenant Supabase + RLS | **PARCIAL** | RLS em migrações para `diagnosticos`; produção Supabase **não** é o único caminho no dev; políticas para **`idempotency_responses`** (não multi-tenant por linha — chave hash global) **avaliar risco**. JWT é fonte de verdade do tenant. |
| **M11** | Eixos ABNT como espinha | **PARCIAL** | Bloco ABNT no JSON; aderência PDCA/7 pilares **não** mapeada explicitamente na UI nem no relatório. |
| **M12** | Checklist final 10 itens binários | **NÃO** | Checklist atual ≠ modelo “10 binários BMS+ABNT” do MoSCoW; contar itens e padronizar. |

---

## 6. MoSCoW SHOULD / COULD / WONT — backlog

### SHOULD (Beta) — S01–S11

Nenhum item SHOULD está **fechado** como produto. Destaques:

- **S01** LLM plano de ação — adapter Ollama existe; guardrails Lexiq **não**.  
- **S02** RAG Lexiq no wizard — **não**.  
- **S03–S06** Simulador, R$, benchmark, ICMS-ST — **fora** do código atual (grandes esforços).  
- **S07–S11** Templates, setorial profundo, microlearning, gating ABNT, cross-sell — **não**.

### COULD (GA) — C01–C10

Winthor, Protheus, white-label, API pública, etc. — **backlog longo**; ver `docs/refs/02_MOSCOW_FEATURES.md`.

### WONT (ecossistema)

Apuração contínua **QAI**, split **QFC**, auditoria motor **QMI**, defesa auto, RestituIQ — **não implementar no QDI** (regra de escopo).

---

## 7. Front-end Next.js — pendências críticas

Estes itens bloqueiam **demo honesta** “wizard → API → relatório”:

1. **Autenticação no POST diagnóstico**  
   - API exige `Authorization: Bearer <jwt>`.  
   - `frontend/lib/api/diagnostico.ts` **não** envia Bearer; envia `X-Tenant-ID` que **não** é usado pelo backend de diagnóstico (JWT é o contrato; ver `.cursor/rules/fastapi-presentation.mdc`).  

2. **Idempotency-Key**  
   - Obrigatório em POST `/diagnosticos/`.  
   - Front **não** envia — receberá **400**.  

3. **Base URL da API**  
   - Hardcode `127.0.0.1:8000` no login vs `NEXT_PUBLIC_API_URL` parcial no diagnóstico vs Docker **60000**.  
   - Padronizar env e documentar no README do front.  

4. **GET `/diagnosticos/questionario`**  
   - Substituir `MOCK_QUESTIONS` por fetch após perfil (step 2) com token; renderizar tipos: ternária, escala, binária, múltipla, checklist, numérica (componentes por tipo).  

5. **Dashboard `/dashboard/diagnosticos/[id]`**  
   - Fetch com header legado `X-Tenant-ID` — alinhar a Bearer + URL correta.  

6. **Playwright / E2E front**  
   - PRD pede Playwright; **não há** testes e2e de browser no repositório (apenas testes Python httpx).  

7. **LGPD / termos**  
   - MoSCoW §8 exige consentimento e políticas — **não** vistos no fluxo UI.  

---

## 8. Back-end / infra / dados

### 8.1 Pendentes técnicos

- **Reconciliação catálogo vs `05_QUESTIONARIO_v1.md`:** 37 vs 35; revisar códigos Q-xxx e condicionais setoriais (varejo/indústria/serviços/agro) e bloco Lucro Real.  
- **Normas vigência:** regras versionadas por `vigencia_inicio`/`vigencia_fim` em DB — **não** implementado; hoje catálogo é JSON estático.  
- **Idempotência:** tabela sem RLS por `tenant_id`; mitigação atual é hash que inclui `Authorization`. Documentar ameaça e se na Supabase haverá separação física por schema/tenant.  
- **OpenTelemetry prod:** exporter OTLP/Jaeger, sampling, correlação com `trace_id` em logs structlog — **pendente**.  
- **API pública / Idempotency-Key no OpenAPI:** garantir documentação Swagger clara para clientes geradores.  
- **Seed admin / tenant:** alinhar UUIDs usados em testes e qualquer mock front legado (`11111111-…`).  

### 8.2 Integrações

- **Anthropic / LangChain / LangGraph:** dependências no projeto; fluxo principal ainda não é “LangGraph obrigatório” para MVP diagnóstico.  
- **Lexiq / RAG:** **não** implementado — respostas IA sem citação devem ser rejeitadas (princípio Tributiq).  

---

## 9. Testes, qualidade e observabilidade

| Item | Estado |
|------|--------|
| pytest + cobertura ≥ 80% global | **OK** (última verificação na entrega A–E) |
| mypy strict em `src/` | **OK** |
| ruff + black | **OK** |
| Teste integração idempotência **com Postgres real** (subir docker, duplicar POST, replay) | **opcional / não obrigatório** na suíte CI |
| Playwright (fluxo login + wizard + POST) | **NÃO** |
| Casos de calibração score (5 segmentos) | **NÃO** (MoSCoW §8) |

---

## 10. Conformidade, LGPD e critérios de lançamento

Extrato de `docs/refs/02_MOSCOW_FEATURES.md` §8 — **checklist de produto**, quase tudo **aberto**:

- [ ] 12 MUST implementados e testados (cobertura ≥ 80% **global** — domain ≥ 85% para código novo de domain, regra interna QDI).  
- [ ] Score calibrado contra **5 cases** de referência.  
- [ ] PDF aprovado por **3 contadores**.  
- [ ] Manifesto de pesos revisado por **advogado tributarista**.  
- [ ] Aderência ABNT **declarada e auditável** na entrega.  
- [ ] LGPD: consentimento + termos + política de privacidade.  

---

## 11. Decisões de produto pendentes

| # | Tema | Observação |
|---|------|------------|
| D1 | Jornada **Free self-service** vs **B2B logado** | Wizard em `/wizard` parece lead; dashboard exige login — unificar narrativa. |
| D2 | CNPJ obrigatório ou opcional no Free | Doc questionário sugere opcional Free / obrigatório Plus. |
| D3 | Campo “faturamento” / “setor detalhado” | No doc §3; no Pydantic atual pode faltar — alinhar schema API + front. |
| D4 | URL canônica da API em dev/staging/prod | Evitar hardcode. |
| D5 | Tier Plus/Pro | Gatilhos “Trigger Plus” no texto das perguntas — sem billing no código observado. |

---

## 12. Blocos sugeridos para próximas sessões (F em diante)

| ID | Escopo | Pronto quando |
|----|--------|----------------|
| **F** | Front: Bearer + Idempotency-Key + `NEXT_PUBLIC_API_URL`; opcional `crypto.randomUUID()` por submit | POST diagnóstico 201 no browser contra API Docker |
| **G** | Front: substituir mock por **GET questionário**; UI por `tipo` | Lista de perguntas = resposta da API para o perfil |
| **H** | PDF M04: estrutura 1 exec + N técnicas; sumário executivo | PDF revisável + teste snapshot ou golden parcial |
| **I** | M05/M06: componentes dashboard (radar, heatmap simples, timeline 5 fases) | Dados derivados do `DiagnosticoResponse` ou novo endpoint |
| **J** | M07/M08: enriquecer `ConsultoriaService` com prioridade + `base_legal` por ação | Contrato JSON estável para front/PDF |
| **K** | M12: checklist 10 itens binários | Contagem e regras testadas |
| **L** | Playwright: smoke crítico | 1 spec verde no CI |
| **M** | S02 protótipo RAG Lexiq (guardrail mínimo) | Resposta sem fonte = erro controlado |

**Blocos históricos A–E:** concluídos (GET questionário, catálogo 37, domínio tipos/pontuação, OTEL mínimo, idempotência Postgres + migração).

---

## 13. Prompt modelo para agente

```
Branch local: feat/qdi-<nome>.

Leia docs/HANDOFF_PROXIMA_SESSAO_QDI.md (índice + bloco escolhido).

Escopo: apenas o bloco <F|M|...> — não expandir para RAG completo, Winthor ou QAI/QFC/QMI.

Não fazer: git push/rebase sem confirmação do Allan; refactors amplos fora do escopo.

Ao terminar: make lint; make format; make test; mypy src; listar arquivos alterados e critérios "pronto quando".
```

---

## 14. Checklist pós-sessão (Allan)

- [ ] Diff revisado  
- [ ] `make test` + `mypy src` locais  
- [ ] Atualizar **§1 e §4–§7** deste handoff se algo mudou materialmente  
- [ ] Commit Conventional em **pt-BR** quando satisfeito  

---

## 15. Documentos de referência obrigatórios

1. `docs/refs/01_PRD_BASE.md`  
2. `docs/refs/02_MOSCOW_FEATURES.md`  
3. `docs/refs/05_QUESTIONARIO_v1.md`  
4. `docs/refs/04_METODOLOGIA.md`  
5. `docs/01_arquitetura.md`  
6. `docs/02_dominio_qdi.md`  

---

*Fim do handoff estendido. Para sessões curtas, priorizar **§7 + bloco F** até o fluxo web bater na API com contrato correto.*
