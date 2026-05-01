# Handoff QualiDiagIQ — estado completo e backlog detalhado

> **Propósito:** permitir retomada por Allan, por outro agente ou após pausa longa, **sem depender de memória de chat**.  
> **Local canônico (versionado):** `docs/HANDOFF_PROXIMA_SESSAO_QDI.md`  
> **Última atualização:** 2026-04-30 (pós-blocos **N1–N7** fechados; lint/test/mypy + Playwright `wizard-post` verdes)

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
12. [Blocos entregues (N1–N7) e próximos (O1–O8)](#12-blocos-entregues-n1n7-e-próximos-o18)  
13. [Prompt modelo para agente](#13-prompt-modelo-para-agente)  
14. [Armadilhas conhecidas (evitar regressão)](#14-armadilhas-conhecidas-evitar-regressão)  
15. [Checklist pós-sessão (Allan)](#15-checklist-pós-sessão-allan)  
16. [Documentos de referência obrigatórios](#16-documentos-de-referência-obrigatórios)  

---

## 1. Resumo executivo

O **QualiDiagIQ (QDI)** é o módulo de diagnóstico tributário (Reforma do Consumo: **EC 132/2023**, **LC 214/2025**, **ABNT NBR 17301:2026**) dentro do ecossistema Tributiq.

**Situação atual (macro) — abril/2026:**

- **API FastAPI:** POST/GET/PATCH diagnóstico, motor em **7 dimensões**, **GET `/diagnosticos/questionario` público**, catálogo JSON **37** perguntas, idempotência (Postgres + fallback), **migração `0008`** com comentários operacionais, WORM/hash/versão otimista, OTEL opcional, **router `/normativa/validar-ancora`** (protótipo guardrail Lexiq) com schemas dedicados.
- **Consultoria + contrato:** `ConsultoriaService` com cronograma 5 fases, checklist **prioridade** + **base legal**, matriz (incl. `base_legal` onde aplicável), resposta JSON com `cronograma`, `matriz_impacto`, etc.
- **Front-end:** wizard com ramos **`escala_1_5`**, **`binaria`**, **`numerica`**, **`multipla_escolha` / `checklist`**, **`ternaria`**; LGPD com link **`/privacidade`**; dashboard detalhe com **cronograma**, **matriz**, checklist, radar + **heatmap** + **Barras de ranking de gaps**, botão PDF; componente **`Badge`** (`frontend/components/ui/badge.tsx`).
- **Testes:** pytest verde (~139 passed, 1 skipped); **`frontend/e2e/wizard-post.spec.ts`** cobre login → wizard → POST mock (Bearer + Idempotency-Key); **`tests/unit/infrastructure/test_pdf_template_m04.py`** valida marcadores HTML M04 no template Jinja.

**MoSCoW MVP (12 MUST):** ainda **não declarado “fechado”** pelo produto; principais lacunas editoriais/arquiteturais: homologação **M04**, manifesto pesos **M03**, **M09**/jornada Free, **M10** hardening produção Supabase, **M11**/UI PDCA explícita, **M12** tela checklist 10× binário dedicada.

**Próximo marco sugerido (§12):** blocos **O1–O3** — polir produto executivo + CI E2E; **O4–O6** — conteúdo normativo/UI ABNT + reconciliação 37×35 perguntas.

---

## 2. Stack e comandos operacionais

| Área | Escolha do projeto |
|------|-------------------|
| Backend | Python 3.12+, FastAPI 0.115+, Pydantic v2, Clean Architecture (`src/domain`, `application`, `infrastructure`, `presentation`) |
| DB local | PostgreSQL via Docker; migrações `src/infrastructure/db/migrations/` (`0001`…`0008`) + `init.sql` |
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

---

## 3. Mapa do repositório (onde está o quê)

| Caminho | Responsabilidade |
|---------|------------------|
| `src/domain/` | Entidades (`diagnostico`, `questionario`), VOs de score, ports |
| `src/application/` | Use cases; **`ConsultoriaService`**; **`services/lexiq_guardrail.py`** (validação pós-resposta âncoras) |
| `src/infrastructure/` | Supabase repo, WeasyPrint + **`templates/relatorio_diagnostico.html`** (marcadores **M04**), questionário JSON, idempotência |
| `src/infrastructure/db/migrations/` | **`0001`…`0008`** (incl. `0008_idempotency_comentarios_operacao.sql`) |
| `src/presentation/api/` | FastAPI, schemas, **`routers/normativa_router.py`**, middleware idempotência |
| `docs/operacao_rls_idempotency.md` | Notas operação RLS + idempotência (N6) |
| `frontend/lib/api/` | `config.ts`, `diagnostico.ts`, `questionario.ts` |
| `frontend/app/privacidade/` | Página política LGPD (link no wizard) |
| `frontend/app/dashboard/diagnosticos/[id]/` | **`DiagnosticoDetalheClient.tsx`** — radar, heatmap, gaps, cronograma, matriz |
| `frontend/components/wizard/` | **`WizardForm.tsx`** — tipos de pergunta |
| `frontend/components/ui/badge.tsx` | Badge (dashboard / detalhe) |
| `frontend/e2e/` | **`smoke.spec.ts`**, **`wizard-post.spec.ts`** |
| `frontend/playwright.config.ts` | Porta **3333** |
| `tests/unit/infrastructure/test_pdf_template_m04.py` | Golden parcial HTML M04 |
| `tests/unit/application/test_lexiq_guardrail.py` | Guardrail âncoras |
| `docs/refs/` | PRD, MoSCoW, questionário v1, metodologia |

---

## 4. O que já está implementado (snapshot técnico)

### 4.1 API HTTP

- **POST `/diagnosticos/`** — Bearer JWT + **`Idempotency-Key`** obrigatória.  
- **GET `/diagnosticos/{id}`**, **PATCH** (If-Match), **GET `/diagnosticos/metodologia`**, **GET `/health`**, **POST `/auth/login`**.  
- **GET `/diagnosticos/questionario`** — público (query perfil empresa).  
- **POST `/normativa/validar-ancora`** (ou prefixo configurado em `main.py`) — protótipo **N7**: corpo texto + flag âncoras normativas (LC/EC/ABNT/NT).

### 4.2 Resposta de diagnóstico (JSON)

- `score`, `checklist`, `matriz_impacto`, **`cronograma`**, `relatorio_pdf_url`, recomendação IA opcional, WORM/metadata.

### 4.3 Domínio e PDF

- Motor 7 dimensões; catálogo com condicionais; PDF com síntese, dimensões, gaps, matriz, cronograma, checklist (**prioridade** + **base legal** onde gerado pelo serviço).  
- Template com comentários Jinja/HTML **`M04_SECAO:*`** para testes de regressão estrutural.

### 4.4 Front (contrato)

- POST: Bearer + Idempotency-Key; GET questionário sem token no wizard após perfil.  
- Dashboard detalhe: tipos alinhados à API (**cronograma**, **matriz_impacto**, checklist com prioridade/base_legal).  
- Visualizações: radar + heatmap por dimensão + ranking de gaps (Recharts).

### 4.5 Testes automatizados

- pytest: unit + integração (incl. normativa/âncoras), idempotência, WORM onde aplicável, **`test_lexiq_guardrail`**, **`test_pdf_template_m04`**.  
- Playwright: smoke (`/wizard`, `/login`) + **`wizard-post`**: mocks de rede + **atenção à ordem de `page.route`** (§14).

### 4.6 Paridade documental

- Catálogo **37** vs doc **35** em `docs/refs/05_QUESTIONARIO_v1.md` — **auditoria editorial ainda pendente**.

---

## 5. MoSCoW MUST (M01–M12) — status e lacunas

| ID | Feature | Status | Comentário / pendência |
|----|---------|--------|-------------------------|
| **M01** | Wizard adaptativo | **PARCIAL → avançado** | Ramos UI por **`ternaria`**, **`binaria`**, **`escala_1_5`**, **`numerica`**, **`multipla_escolha`/`checklist`**. Revisão UX com catálogo real (edge cases opções vazias) e testes visuais. |
| **M02** | Motor score 0–100, 6+ dimensões | **OK** (refinar) | Calibração por segmento **não** feita. |
| **M03** | Pesos transparentes | **PARCIAL** | `/metodologia`; manifesto exportável/legal **aberto**. |
| **M04** | PDF executivo | **PARCIAL** | Estrutura rica + testes M04 parciais; **não** homologado “1 exec + N técnicas”; paginação WeasyPrint em produção. |
| **M05** | Heatmap + radar + ranking gaps | **PARCIAL → melhor** | Radar + heatmap + barras gaps no **detalhe**. Falta decisão produto onde replicar (lista principal, PDF mirror). |
| **M06** | Cronograma 5 fases | **PARCIAL → melhor** | Tabela no dashboard + PDF; timeline visual “premium” opcional (O8). |
| **M07** | Recomendações priorizadas | **PARCIAL** | Prioridade em checklist; ligar deterministicamente a **gaps derivados das respostas** (regras) — backlog. |
| **M08** | Ancoragem legal por bullet | **PARCIAL** | Checklist/PDF; matriz ganhou **base legal** em parte do fluxo — conferir todas as linhas + NTs granularmente. |
| **M09** | Lead magnet self-service | **PARCIAL** | LGPD + `/privacidade`; jornada Free sem login até certo passo vs B2B; campos extras (faturamento) **em aberto**. |
| **M10** | Multi-tenant Supabase + RLS | **PARCIAL** | RLS + doc operação + comentários migração; **hardening prod** + políticas auxiliares (revisão periódica). |
| **M11** | Eixos ABNT como espinha | **PARCIAL** | Conteúdo catálogo/PDF; **UI** com PDCA/7 pilares (mapa navegável ou stepper) **não**. |
| **M12** | Checklist 10 itens binários | **PARCIAL** | Conteúdo serviço + PDF; **tela dedicada** tipo auditoria binária **não**. |

---

## 6. MoSCoW SHOULD / COULD / WONT — backlog

- **SHOULD:** S01 LLM plano personalizado (**não** no núcleo); **S02 RAG Lexiq no wizard — não** (há apenas **endpoint + guardrail** e opcional uso em adapter LLM; não é fluxo wizard completo). S03+ conforme `docs/refs/02_MOSCOW_FEATURES.md`.  
- **COULD:** Winthor, white-label, API pública documentada — backlog longo.  
- **WONT:** QAI, QFC, QMI, defesa auto, RestituIQ — **fora do QDI**.

---

## 7. Front-end Next.js — pendências (próximo ciclo)

1. **`asChild` / Button (Base UI):** warning no dev SSR — revisar uso de `Button` onde `asChild` vaza para `<button>` nativo ou alinhar API do componente.
2. **CI:** job opcional `npm run test:e2e` (cache Playwright) em pipeline — decisão Allan.
3. **Dashboard lista vs detalhe:** consistência visual e deep-link para relatório quando `relatorio_pdf_url` nulo vs disponível (estados vazios).
4. **Acessibilidade:** radios/checkboxes do wizard já em `Label`; rodar axe ou checklist manual nas telas críticas.
5. **`allowedDevOrigins`:** aviso Next em dev (127.0.0.1 vs localhost) — configurar antes de upgrade major conforme doc Next.

---

## 8. Back-end / infra / dados

- Reconciliar **37 vs 35** perguntas com `05_QUESTIONARIO_v1.md`.  
- Versionamento normativo em DB (`vigencia_*`) — **não** implementado (JSON estático).  
- OTEL produção (OTLP, correlação logs) — **pendente**.  
- OpenAPI: documentar **Idempotency-Key**, exemplo **`cronograma`**, endpoint **normativa**.  
- Pipeline LLM LangGraph — **opcional** ao MVP diagnóstico; guardrail Lexiq já reutilizável em adapters.

---

## 9. Testes, qualidade e observabilidade

| Item | Estado |
|------|--------|
| pytest, cobertura ≥ 80% | **OK** (última rodada global verde) |
| mypy `src` | **OK** |
| ruff + black | **OK** (rodar `make format` ao fechar sessão) |
| Playwright | **Smoke** + **`wizard-post`** (mock rede; valida headers POST) |
| Calibração score (segmentos reais) | **NÃO** |

---

## 10. Conformidade, LGPD e critérios de lançamento

Checklist produto (extrato MoSCoW) — manifesto pesos, PDF homologado, parecer jurídico página privacidade “oficial”, 12 MUST assinados pelo negócio: **majoritariamente aberto**.

---

## 11. Decisões de produto pendentes

| # | Tema | Observação |
|---|------|------------|
| D1 | Free self-service vs B2B logado | Narrativa única no marketing + fluxo técnico. |
| D2 | CNPJ opcional no Free | API/schema hoje **exige** CNPJ válido — alinhar. |
| D3 | Faturamento / setor detalhado | Schema API + front. |
| D4 | URL canônica dev/stage/prod | `NEXT_PUBLIC_API_URL` + docs deploy. |
| D5 | Billing Plus/Pro | Triggers perguntas “Plus” sem cobrança no código. |

---

## 12. Blocos entregues (N1–N7) e próximos (O1–O8)

### 12.1 Ciclo **N** (concluído — referência)

| ID | Escopo entregue (resumo) |
|----|--------------------------|
| **N1** | Dashboard detalhe: `cronograma`, matriz, checklist tipados; radar + heatmap + ranking gaps; botão PDF; mock enriquecido. |
| **N2** | Wizard por `tipo` (`escala_1_5`, `binaria`, `numerica`, `multipla`/`checklist`, `ternaria`); LGPD → `/privacidade`. |
| **N3** | Playwright `wizard-post.spec.ts`: login → wizard → POST mock (**Bearer + Idempotency-Key**). **Registrar rota específica `questionario` depois da rota ampla `diagnosticos**`** (§14). |
| **N4** | Marcadores **`M04_SECAO:*`** no template PDF + teste unitário Jinja/HTML. |
| **N5** | Heatmap + barras de gaps no detalhe (M05). |
| **N6** | `docs/operacao_rls_idempotency.md` + migração **`0008`** (comentários operação); `init.sql` atualizado. |
| **N7** | `lexiq_guardrail.py`, adapter LLM (prompt/validação), `normativa_router`, schemas + testes + integração API. |

**Histórico anterior (A–L):** ver commits anteriores; núcleo API, Bearer, catálogo 37, idempotência, PDF consultoria.

### 12.2 Ciclo **O** (sugerido — próximo handoff operacional)

| ID | Escopo | Pronto quando |
|----|--------|---------------|
| **O1** | **M03 + OpenAPI:** endpoint ou página “manifesto de pesos” (export JSON/Markdown) + exemplos Swagger para `cronograma`, idempotência, normativa | Publicável sem consultar código-fonte |
| **O2** | **CI E2E:** GitHub/GitLab job com Playwright (`wizard-post` mínimo), cache browsers, opcional apenas em PR que toca `frontend/` | Pipeline verde reproduzível |
| **O3** | **Button/`asChild`:** eliminar warning React no dev server (dashboard/marketing) | Log limpo nos fluxos wizard + dashboard |
| **O4** | **M12 UI:** tela ou seção expansível “10 controles ABNT” com toggles binários espelhando checklist PDF (somente leitura vs self-check — decidir) | Critérios MoSCoW M12 revisitados pelo produto |
| **O5** | **M11 UI:** mapa **PDCA + 7 pilares** no detalhe ou hub `/metodologia` enriquecido com âncoras catálogo | Linkagem pergunta → pilar opcionalmente |
| **O6** | **Auditoria 37×35:** script ou planilha + ajustes catálogo ou doc refs para paridade oficial | Lista de divergências = 0 ou justificativas registradas |
| **O7** | **S02 evolução:** tooltip ou painel wizard com “consulta normativa” behind feature flag + mesma política guardrail Lexiq | Não obrigatório ao MVP — beta |
| **O8** | **M06 visual:** timeline vertical (CSS ou lib leve) para cronograma 5 fases | UX revisada Allan |

Prioridade sugerida para a **próxima sessão única:** **O3 + O2** (qualidade DX/CI), em seguida **O6** (dívida documental).

---

## 13. Prompt modelo para agente

```
Branch local: feat/qdi-<nome>.

Leia docs/HANDOFF_PROXIMA_SESSAO_QDI.md (§1, §7, §12 — bloco O<n> combinado).

Escopo: apenas o bloco O acordado — não expandir para QAI/QFC/QMI, Winthor completo ou RAG Lexiq wizard completo sem pedido explícito.

Não fazer: git push/rebase sem confirmação do Allan.

Ao terminar: make lint; make format; make test; mypy src; se front E2E: cd frontend && npx playwright test (ou spec alvo).

Playwright: ao mockar APIs, registre rotas **específicas** (ex.: */questionario*) **depois** de rotas amplas (**/diagnosticos**) — ver §14.
```

---

## 14. Armadilhas conhecidas (evitar regressão)

1. **Playwright `page.route`:** interceptores são avaliados **do último registrado para o primeiro**. Um handler **`**/diagnosticos**`** que faz `continue()` para GET **absorve** o request antes do mock **`**/diagnosticos/questionario*`**, gerando **“Failed to fetch”** na UI. Mitigação: registrar `questionario` **por último** ou não usar `continue()` para esse path no handler genérico.  
2. **NEXT vs API porta:** frontend default **`localhost:60000`**; Playwright não sobe API — E2E de contrato deve **mockar** ou usar script que suba compose.  
3. **LGPD:** `aceite_termos_privacidade` **não** vai no corpo POST (strip no client) — não reintroduzir no DTO HTTP de criação.  

---

## 15. Checklist pós-sessão (Allan)

- [ ] Diff revisado  
- [ ] `make test` + `mypy src` (+ Playwright se front)  
- [ ] Atualizar este handoff se mudança material em §4–§7, §12 ou migrations  
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

*Fim do handoff. Prioridade operacional imediata sugerida: **§12.2 → O3 + O2**, depois **O6** (paridade perguntas).*
