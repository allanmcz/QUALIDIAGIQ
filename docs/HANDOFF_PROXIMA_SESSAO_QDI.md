# Handoff QualiDiagIQ — estado completo e backlog detalhado

> **Propósito:** permitir retomada por Allan, por outro agente ou após pausa longa, **sem depender de memória de chat**.  
> **Local canônico (versionado):** `docs/HANDOFF_PROXIMA_SESSAO_QDI.md`  
> **Última atualização:** 2026-04-30 (pós **N1–N7** + incremento **MoSCoW MUST M01–M12** no código; ~141 pytest passed, 1 skipped; Playwright `wizard-post` verde)

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

---

## 1. Resumo executivo

O **QualiDiagIQ (QDI)** é o módulo de diagnóstico tributário (Reforma do Consumo: **EC 132/2023**, **LC 214/2025**, **ABNT NBR 17301:2026**) dentro do ecossistema Tributiq.

**Situação atual (macro) — abril/2026:**

- **API FastAPI:** POST/GET/PATCH diagnóstico, motor em **7 dimensões**, **GET `/diagnosticos/questionario`** e **`GET /diagnosticos/manifesto-pesos`** públicos, **`GET /diagnosticos/metodologia`** alinhada ao motor (pesos macro = `PESOS_MACRO_DIMENSAO_SCORE_GERAL` em `src/domain/value_objects/score.py`). Catálogo **37** perguntas, idempotência, migrações **`0001`…`0009`** (`0009` = `respondente_telefone` + comentários M10), WORM/OTEL, **`/normativa/validar-ancora`**.
- **Consultoria:** `ConsultoriaService` com frente **M07** (“Prioridade por gaps do score”) quando há `ScoreCompleto`; cronograma 5 fases; matriz com **NT CGNFS-e** na linha Jurídico (M08); checklist ABNT 10 itens.
- **Front-end:** wizard (tipos de pergunta + **telefone opcional** M09 + links manifesto/metodologia JSON + **`/abnt-framework`**); dashboard lista com **barra de score** (M05); detalhe com radar, heatmap, ranking, **timeline** cronograma (M06), **autoconferência M12** (checkboxes só no browser, não persistidos).
- **Testes:** pytest ~141 passed / 1 skipped; integração **`test_manifesto_pesos_publico`**; **`test_m07_prioridade_checklist`**; Playwright **`wizard-post`** (ordem de rotas §14).

**MoSCoW MVP (12 MUST):** **avanço grande no código**; **fechamento comercial/jurídico** ainda depende de homologação **M04**, calibração **M02** com dados reais, hardening **M10** em Supabase produção, decisões **M09** (Free vs CNPJ), e auditoria **37×35**.

**Próximo marco sugerido (§12.3):** ciclo **P** — **OpenAPI** + **CI E2E**, **auditoria 37×35**, **fix `asChild`**, homologação PDF, hardening RLS prod.

---

## 2. Stack e comandos operacionais

| Área | Escolha do projeto |
|------|-------------------|
| Backend | Python 3.12+, FastAPI 0.115+, Pydantic v2, Clean Architecture (`src/domain`, `application`, `infrastructure`, `presentation`) |
| DB local | PostgreSQL via Docker; migrações `src/infrastructure/db/migrations/` (**`0001`…`0009`**) + `init.sql` na raiz |
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
- `DATABASE_URL`, `JWT_SECRET_KEY`, `SUPABASE_*`, `OTEL_*` — conforme `.env` / Docker.

**Bases novas / upgrade:** rodar stack com volume limpo ou aplicar **`0009`** manualmente em bases já existentes (coluna `respondente_telefone`).

---

## 3. Mapa do repositório (onde está o quê)

| Caminho | Responsabilidade |
|---------|------------------|
| `src/domain/value_objects/score.py` | **`PESOS_MACRO_DIMENSAO_SCORE_GERAL`**, `pesos_macro_dimensao_para_dict_iso()` — fonte única da agregação do score geral (M02/M03) |
| `src/domain/entities/diagnostico.py` | `Respondente.telefone` opcional (M09) |
| `src/application/services/consultoria_service.py` | M07 frente gaps; matriz M08; checklist ABNT M12 |
| `src/application/use_cases/calcular_score_use_case.py` | Consome pesos macro do domain |
| `src/infrastructure/db/migrations/` | **`0001`…`0009`** (`0009_respondente_telefone_m10.sql`) |
| `src/presentation/api/routers/diagnostico_router.py` | **`/manifesto-pesos`**, `/metodologia`, `/questionario`, CRUD diagnóstico |
| `src/presentation/api/schemas.py` | `ManifestoPesosResponse`, `ManifestoPesoPerguntaSchema`, `nota_calibracao_m02` |
| `init.sql` | Orquestra `\i` das migrações no bootstrap Docker |
| `frontend/app/abnt-framework/page.tsx` | Hub **M11** (PDCA + 7 pilares, texto didático) |
| `frontend/app/privacidade/` | LGPD |
| `frontend/app/dashboard/diagnosticos/[id]/DiagnosticoDetalheClient.tsx` | Radar, heatmap, gaps, cronograma+tabela+t**imeline**, **M12** checkboxes locais |
| `frontend/app/dashboard/page.tsx` | Lista mock + **barra M05** por card |
| `frontend/components/wizard/WizardForm.tsx` | Tipos pergunta, telefone, `aria-live`, links API |
| `frontend/lib/schemas/wizard.ts` | Zod incl. `respondente.telefone` |
| `docs/operacao_rls_idempotency.md` | Operação RLS + idempotência |
| `frontend/e2e/` | `smoke.spec.ts`, `wizard-post.spec.ts` |
| `docs/refs/` | PRD, MoSCoW, questionário v1, metodologia |

---

## 4. O que já está implementado (snapshot técnico)

### 4.1 API HTTP

- **POST `/diagnosticos/`** — Bearer JWT + **`Idempotency-Key`** obrigatória; corpo pode incluir **`respondente.telefone`** (opcional).  
- **GET `/diagnosticos/{id}`**, **PATCH** (If-Match), **GET `/diagnosticos/metodologia`**, **`GET /diagnosticos/manifesto-pesos`**, **GET `/health`**, **POST `/auth/login`**.  
- **GET `/diagnosticos/questionario`** — público (query perfil empresa).  
- **POST `/normativa/validar-ancora`** — protótipo guardrail (N7).

### 4.2 Resposta de diagnóstico (JSON)

- `score`, `checklist` (**incl. frente M07** quando score disponível), `matriz_impacto`, `cronograma`, `relatorio_pdf_url`, WORM/metadata.

### 4.3 Domínio e PDF

- Motor 7 dimensões; PDF com marcadores **M04** (`capa`, `sintese_executiva`, `tecnico_detalhamento_dimensoes`, **`tecnico_gaps_recomendacoes`**, etc.).
- **`nota_calibracao_m02`** exposta no JSON do manifesto (texto roadmap Beta).

### 4.4 Front (contrato)

- Lista dashboard: prévia por score (barra).  
- Detalhe: cronograma em tabela + **linha do tempo**; **M12** espelho local dos 10 itens ABNT.  
- **`/abnt-framework`**: navegação M11.

### 4.5 Testes automatizados

- **`tests/integration/test_api.py`:** `test_manifesto_pesos_publico`, `test_metodologia_endpoint` (chaves **`pesos_macro_dimensao_score_geral`**).  
- **`tests/unit/application/test_consultoria_service.py`:** `test_m07_prioridade_checklist_por_piores_dimensoes`, matriz com CGNFS-e.  
- **`tests/unit/infrastructure/test_pdf_template_m04.py`:** assert **`M04_SECAO: tecnico_gaps_recomendacoes`**.

### 4.6 Paridade documental

- Catálogo **37** vs doc **35** em `docs/refs/05_QUESTIONARIO_v1.md` — **auditoria editorial pendente (P4)**.

---

## 5. MoSCoW MUST (M01–M12) — status e lacunas

| ID | Feature | Status | Comentário / pendência |
|----|---------|--------|-------------------------|
| **M01** | Wizard adaptativo | **Fortemente avançado** | Ramos por tipo; copy + `aria-live` no fetch; revisar UX edge cases (`multipla_total`/`opcoes` vazias). |
| **M02** | Motor score 0–100, 6+ dimensões | **OK no núcleo** | Calibração por coorte real = roadmap (`nota_calibracao_m02` no manifesto). |
| **M03** | Pesos transparentes | **Fortemente avançado** | **`/manifesto-pesos`** + `/metodologia` coerentes com domain; página HTML “humana” opcional (`/metodologia` Next ainda não existe no repo). |
| **M04** | PDF executivo | **PARCIAL técnico** | Homologação contábil “1 exec + N técnicas”, WeasyPrint em produção, revisão páginas. |
| **M05** | Heatmap + radar + ranking gaps | **Avançado** | Completo no detalhe + barra na **lista** (mock); alinhar quando lista vier da API real. |
| **M06** | Cronograma 5 fases | **Avançado** | Tabela + **timeline** no detalhe + PDF; polimento visual se Allan quiser. |
| **M07** | Recomendações priorizadas | **Avançado** | **3 dimensões piores score** geram primeira frente de checklist (regra determinística). |
| **M08** | Ancoragem legal por bullet | **PARCIAL** | Matriz jurídica + NT CGNFS-e; revisão editorial linha-a-linha (todas NTs / dispositivos). |
| **M09** | Lead magnet self-service | **PARCIAL** | Telefone opcional persistido (**`0009`**); jornada Free sem login total, CNPJ opcional, faturamento = decisão produto (§11). |
| **M10** | Multi-tenant Supabase + RLS | **PARCIAL** | RLS + docs + comentários tabela; **políticas e roles produção** + auditoria periódica. |
| **M11** | Eixos ABNT como espinha | **Avançado UI** | **`/abnt-framework`** + links no wizard e detalhe; linkagem pergunta↔pilar no catálogo = opcional. |
| **M12** | Checklist 10 itens binários | **Avançado UI** | Autoconferência no detalhe **não persistida**; PDF/serviço já tinham os 10 itens. |

---

## 6. MoSCoW SHOULD / COULD / WONT — backlog

- **SHOULD:** S01 LLM plano (**não** núcleo); **S02** RAG wizard completo (**não**); existe endpoint **validar-ancora** + guardrail.  
- **COULD:** Winthor, white-label, API pública documentada.  
- **WONT:** QAI, QFC, QMI, defesa auto, RestituIQ.

---

## 7. Front-end Next.js — pendências (próximo ciclo)

1. **`asChild` / Button (Base UI):** warning SSR no dev — **P3**.  
2. **CI E2E:** job Playwright + cache — **P2**.  
3. **Lista dashboard real:** hoje **mock**; substituir por GET API + estados vazios/erro + barra M05 com dados reais.  
4. **Página Next `/metodologia`:** consumir JSON da API e renderizar manifesto “legível” (complemento ao JSON bruto).  
5. **Acessibilidade:** axe / checklist manual.  
6. **`allowedDevOrigins`:** Next config antes de upgrade major.

---

## 8. Back-end / infra / dados

- **P4:** Reconciliar **37×35** com `05_QUESTIONARIO_v1.md`.  
- **P5 + M04:** Homologação PDF + paginação/impressão.  
- **P6:** OTEL prod; OpenAPI exemplos (**Idempotency-Key**, `cronograma`, `manifesto-pesos`, normativa).  
- Versionamento normativo DB (`vigencia_*`) — não implementado.  
- **Bases antigas:** garantir migração **`0009`** aplicada (coluna telefone).

---

## 9. Testes, qualidade e observabilidade

| Item | Estado |
|------|--------|
| pytest, cobertura ≥ 80% | **OK** (~141 passed, 1 skipped na última rodada registrada) |
| mypy `src` | **OK** |
| ruff + black | Rodar **`make format`** ao fechar sessão |
| Playwright | Smoke + **`wizard-post`** |
| Calibração score (campo real) | **NÃO** |

---

## 10. Conformidade, LGPD e critérios de lançamento

Parecer jurídico em **privacidade** “oficial”, homologação **M04**, assinatura negocial dos **12 MUST**, política de retenção do **`respondente_telefone`**: **abertos**.

---

## 11. Decisões de produto pendentes

| # | Tema | Observação |
|---|------|------------|
| D1 | Free self-service vs B2B logado | Narrativa + fluxo (wizard já menciona lead B2B). |
| D2 | CNPJ opcional no Free | API ainda **exige** CNPJ 14 dígitos. |
| D3 | Faturamento / setor detalhado | Schema + UI. |
| D4 | URL canônica dev/stage/prod | Deploy docs. |
| D5 | Billing Plus/Pro | Triggers comerciais sem cobrança no código. |
| **D6** | **Persistir estado M12** (checkboxes) | Hoje só cliente; decisão se vira PATCH ou evidência auditoria. |

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
| **M03** | **`GET /diagnosticos/manifesto-pesos`**; **`/metodologia`** alinhada ao motor. |
| **M04** | Marcador **`tecnico_gaps_recomendacoes`** no template. |
| **M05** | Barra score na **lista** dashboard (mock). |
| **M06** | **Timeline** vertical no detalhe (além da tabela). |
| **M07** | Frente checklist **top 3 dimensões** mais fracas. |
| **M08** | **NT CGNFS-e** na matriz Jurídico. |
| **M09** | **`respondente.telefone`** + migração **0009** + campo wizard. |
| **M10** | Comentários SQL em **0009** (auditoria tabela/coluna). |
| **M11** | **`/abnt-framework`** + links. |
| **M12** | Checkboxes locais 10 controles no detalhe. |

### 12.3 Ciclo **P** (próximo handoff operacional)

| ID | Escopo | Pronto quando |
|----|--------|---------------|
| **P1** | **OpenAPI/Swagger:** exemplos `manifesto-pesos`, metodologia, POST diagnóstico (Idempotency), normativa | Documentação exportável |
| **P2** | **CI E2E** Playwright (`wizard-post` mínimo) | Job verde em PR |
| **P3** | Corrigir warning **`asChild`** no `Button` | Log dev limpo nas rotas principais |
| **P4** | **Auditoria 37×35** + ajuste catálogo ou doc | Divergências zeradas ou ADR |
| **P5** | **M04** homologação + PDF produção (WeasyPrint) | Checklist contábil Allan |
| **P6** | **M10** hardening Supabase prod (RLS, roles, revisão) | Runbook + teste de fumaça tenant |
| **P7** | Dashboard lista **real** (GET diagnósticos) + empty states | Sem mock hardcoded |
| **P8** | **S02** leve: feature flag consulta normativa no wizard (reuso `validar-ancora`) | Opcional / Beta |

**Prioridade sugerida:** **P2 + P3** (DX), em seguida **P4** (dívida documental), **P5/P6** conforme prazo de go-live.

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

*Fim do handoff. Prioridade sugerida: **§12.3 → P2 + P3**, depois **P4**.*
