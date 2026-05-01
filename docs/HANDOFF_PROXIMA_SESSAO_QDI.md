# Handoff QualiDiagIQ — estado completo e backlog detalhado

> **Propósito:** permitir retomada por Allan, por outro agente ou após pausa longa, **sem depender de memória de chat**.  
> **Local canônico (versionado):** `docs/HANDOFF_PROXIMA_SESSAO_QDI.md`  
> **Última atualização:** 2026-04-30 (handoff regenerado pós-blocos F/G/H/J/K/L parciais)

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
12. [Blocos sugeridos para próximas sessões](#12-blocos-sugeridos-para-próximas-sessões)  
13. [Prompt modelo para agente](#13-prompt-modelo-para-agente)  
14. [Checklist pós-sessão (Allan)](#14-checklist-pós-sessão-allan)  
15. [Documentos de referência obrigatórios](#15-documentos-de-referência-obrigatórios)  

---

## 1. Resumo executivo

O **QualiDiagIQ (QDI)** é o módulo de diagnóstico tributário (Reforma do Consumo: **EC 132/2023**, **LC 214/2025**, **ABNT NBR 17301:2026**) dentro do ecossistema Tributiq.

**Situação atual (macro):**

- **API FastAPI:** diagnóstico (POST/GET/PATCH), motor de score em **7 dimensões**, **GET `/diagnosticos/questionario` público** (sem JWT), catálogo JSON **37** perguntas (`versao_catalogo` **v1-doc-05-full-37**), idempotência persistida (Postgres + fallback), WORM/hash/versão otimista, OTEL opcional.
- **Consultoria / contrato enriquecido:** `ConsultoriaService` com **cronograma em 5 fases**, checklist com **`prioridade`** + **`base_legal`** por ação, bloco **10 controles ABNT NBR 17301**; **`DiagnosticoResponse.cronograma`** no JSON; PDF WeasyPrint com **síntese executiva**, cronograma, checklist com coluna de base legal (ver `src/infrastructure/templates/relatorio_diagnostico.html`).
- **Front-end:** alinhamento **substantivo** ao contrato HTTP: **`getApiUrl()`** (default `http://localhost:60000`), **Bearer + `Idempotency-Key`** no POST (`frontend/lib/api/diagnostico.ts`), **GET questionário sem token** após perfil (`frontend/lib/api/questionario.ts` + `WizardForm`), login usa **`getApiUrl()`**, wizard com **consentimento LGPD** (`aceite_termos_privacidade`, não enviado no corpo do POST). Dashboard detalhe usa **Bearer** no GET e **radar Recharts** quando há `score`.
- **MVP MoSCoW (12 MUST):** ainda **não fechado**; maiores gaps: **M01** (UI por todos os `tipo` de pergunta), **M04** (validação editorial “1 exec + N técnicas” / homologação contábil), **M05** (heatmap + ranking de gaps no produto), **M09** (jornada Free vs B2B e campos lead), **M10** (RLS/prod Supabase), **M11** (PDCA/7 pilares explícitos na UI), **Playwright E2E** além do smoke.

**Próximo marco recomendado:** **Bloco N1** — dashboard consome **`cronograma` + matriz + checklist** tipados da API; **Bloco N2** — wizard com componentes por **`tipo`** (`binaria`, `multipla`, `checklist`, `numerica`, …) coerentes com o domínio.

---

## 2. Stack e comandos operacionais

| Área | Escolha do projeto |
|------|-------------------|
| Backend | Python 3.12+, FastAPI 0.115+, Pydantic v2, Clean Architecture (`src/domain`, `application`, `infrastructure`, `presentation`) |
| DB local | PostgreSQL via Docker; migrações em `src/infrastructure/db/migrations/` + `init.sql` |
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
PLAYWRIGHT_SKIP_WEBSERVER=1 npm run test:e2e   # só se já houver app no PLAYWRIGHT_BASE_URL
```

**URLs típicas (Docker Compose do repo):**

- API: `http://localhost:60000` (host `60000` → container `8000`)  
- Web: `http://localhost:60001`  
- Postgres: `localhost:60322`  
- Playwright dev server local: **`http://127.0.0.1:3333`** (evita colisão com outro app em `:3000`)

**Variáveis relevantes:**

- **`NEXT_PUBLIC_API_URL`** — URL da API no browser (default no código: `http://localhost:60000`). Ver `frontend/.env.example` se existir.  
- `DATABASE_URL`, `JWT_SECRET_KEY`, `SUPABASE_*`, `OTEL_*` — conforme `.env` / Docker.

---

## 3. Mapa do repositório (onde está o quê)

| Caminho | Responsabilidade |
|---------|------------------|
| `src/domain/` | Entidades (`diagnostico`, `questionario`), VOs de score, ports |
| `src/application/` | Use cases, **`ConsultoriaService`** (`cronograma`, checklist ABNT 10, matriz) |
| `src/infrastructure/` | Supabase repo, **WeasyPrint** + templates HTML/CSS, questionário JSON, idempotência |
| `src/presentation/api/` | FastAPI, schemas (**`DiagnosticoResponse.cronograma`**), middleware idempotência |
| `src/infrastructure/db/migrations/` | `0001`…`0007` |
| `frontend/lib/api/` | **`config.ts`**, **`diagnostico.ts`**, **`questionario.ts`** |
| `frontend/components/wizard/` | **`WizardForm.tsx`** |
| `frontend/e2e/` | Smoke Playwright (`smoke.spec.ts`) |
| `frontend/playwright.config.ts` | Porta **3333**, `npm run dev -- -p …` |
| `docs/refs/` | PRD, MoSCoW, questionário v1, metodologia |

---

## 4. O que já está implementado (snapshot técnico)

### 4.1 API HTTP

- **POST `/diagnosticos/`** — Bearer JWT + **`Idempotency-Key`** obrigatória.  
- **GET `/diagnosticos/{id}`**, **PATCH** com **If-Match**, **GET `/diagnosticos/metodologia`**, **GET `/health`**, **POST `/auth/login`**.  
- **GET `/diagnosticos/questionario`** — **público** (query perfil empresa); resposta `versao_catalogo`, `perguntas[]` com `base_legal`, `tipo`, etc.

### 4.2 Resposta de diagnóstico (JSON)

- `score`, `checklist`, `matriz_impacto`, **`cronograma`** (lista `{ fase, foco, referencia_normativa }`), `hash_evidencia`, `versao_otimista`, etc.

### 4.3 Domínio e PDF

- Motor 7 dimensões; tipos de pergunta e condicionais no catálogo JSON.  
- PDF: síntese executiva, dimensões, gaps genéricos, matriz, **cronograma 5 fases**, checklist com **prioridade** e **base legal**, bloco IA opcional.

### 4.4 Front (contrato)

- POST diagnóstico: **Authorization Bearer**, **`Idempotency-Key`** (UUID).  
- GET questionário: **sem** Bearer; query alinhada ao backend.  
- Login: **`getApiUrl()`** para `/auth/login`.  
- Wizard: carrega catálogo após step 2; **LGPD** no formulário (campo não vai no POST).  
- Dashboard `[id]`: GET com Bearer; radar se `score`; fallback mock em erro.

### 4.5 Testes automatizados

- pytest: unit + integração ASGI (inclui **GET questionário sem JWT → 200**), idempotência, WORM (marcador postgres onde aplicável).  
- **`tests/unit/application/test_consultoria_service.py`** — cronograma, ABNT×10, portes.  
- Playwright: **2 testes smoke** (`/wizard`, `/login`) na porta dedicada.

### 4.6 Paridade documental

- Catálogo **37** vs doc **35** em `docs/refs/05_QUESTIONARIO_v1.md` — **auditoria editorial pendente**.

---

## 5. MoSCoW MUST (M01–M12) — status e lacunas

| ID | Feature | Status | Comentário / pendência |
|----|---------|--------|-------------------------|
| **M01** | Wizard adaptativo | **PARCIAL** | Backend + fetch catálogo **OK**. UI: ramo explícito só **`escala_1_5`**; demais tipos caem no mesmo controle — falta paridade com `TipoPergunta` (multipla, checklist, numerica, binaria). |
| **M02** | Motor score 0–100, 6+ dimensões | **OK** (refinar) | 7 dimensões; calibração com cases reais **não feita**. |
| **M03** | Pesos transparentes | **PARCIAL** | `/metodologia`; manifesto único (peso por pergunta exportado / página legal) **aberto**. |
| **M04** | PDF executivo | **PARCIAL** | Há síntese + seções técnicas + cronograma; **não** validado como “1p + Np” nem homologado por contadores. |
| **M05** | Heatmap + radar + ranking gaps | **PARCIAL** | Radar no **detalhe** do diagnóstico; sem heatmap nem ranking explícito de gaps na UI. |
| **M06** | Cronograma 5 fases | **PARCIAL** | API + PDF **OK**; **sem** timeline dedicada no dashboard. |
| **M07** | Recomendações priorizadas | **PARCIAL** | `prioridade` + ordenação; ligação dinâmica com gaps das **respostas** **não**. |
| **M08** | Ancoragem legal por bullet | **PARCIAL** | Checklist/PDF com base legal; matriz departamental **sem** dispositivo por linha. |
| **M09** | Lead magnet self-service | **PARCIAL** | Consentimento LGPD no wizard; jornada Free vs login B2B, campos lead (faturamento, etc.) **em aberto**. |
| **M10** | Multi-tenant Supabase + RLS | **PARCIAL** | RLS em migrações; hardening prod + políticas auxiliares (**ex. idempotency**) **avaliar**. |
| **M11** | Eixos ABNT como espinha | **PARCIAL** | Conteúdo parcial no PDF/catálogo; PDCA/7 pilares **não** mapeados na UI. |
| **M12** | Checklist 10 itens binários | **PARCIAL** | Bloco ABNT 10 no serviço + PDF; **sem** tela dedicada “sim/não” para conferência. |

---

## 6. MoSCoW SHOULD / COULD / WONT — backlog

*(Sem mudança estrutural — ver `docs/refs/02_MOSCOW_FEATURES.md`.)*

- **SHOULD:** LLM com guardrail Lexiq (**não**), RAG wizard (**não**), simulador R$ (**não**), etc.  
- **COULD:** Winthor, white-label, API pública documentada — backlog longo.  
- **WONT:** QAI, QFC, QMI, defesa auto, RestituIQ — **fora do QDI**.

---

## 7. Front-end Next.js — pendências (próximo ciclo)

1. **Tipos de pergunta no wizard** — implementar UX por `tipo` alinhado ao backend (múltipla escolha, checklist, numérica, binária explícita).  
2. **Dashboard detalhe** — tipar e exibir **`cronograma`**; enriquecer checklist com **`prioridade`** (já pode vir no JSON aninhado); matriz e links para PDF quando existir `relatorio_pdf_url`.  
3. **M05 visual** — heatmap simples ou lista “top gaps” derivada de `score_por_dimensao`.  
4. **Playwright** — fluxo **login → wizard → POST** contra API (Docker ou mock), não só smoke de página estática.  
5. **LGPD produto** — URL real de política de privacidade / termos (hoje texto + checkbox).  
6. **CI** — job opcional `npm run test:e2e` com cache Playwright (decisão Allan).

---

## 8. Back-end / infra / dados

- Reconciliar **37 vs 35** perguntas com `05_QUESTIONARIO_v1.md`.  
- Versionamento normativo em DB (`vigencia_*`) — **não** implementado (JSON estático).  
- OTEL produção (OTLP, correlação logs) — **pendente**.  
- OpenAPI: documentar **Idempotency-Key** e exemplos de **`cronograma`**.  
- Anthropic/LangGraph no fluxo principal — **não** obrigatório ao MVP diagnóstico.

---

## 9. Testes, qualidade e observabilidade

| Item | Estado |
|------|--------|
| pytest, cobertura ≥ 80% | **OK** (última rodada verde + `consultoria_service` 100% linhas) |
| mypy `src` | **OK** |
| ruff + black | **OK** |
| Playwright | **Smoke** 2 cenários; **sem** E2E de POST |
| Calibração score (5 segmentos) | **NÃO** |

---

## 10. Conformidade, LGPD e critérios de lançamento

Checklist produto (extrato MoSCoW §8) — majoritariamente **aberto**: 12 MUST fechados, calibração, PDF homologado, manifesto pesos, parecer jurídico, LGPD completa (política publicada).

---

## 11. Decisões de produto pendentes

| # | Tema | Observação |
|---|------|------------|
| D1 | Free self-service vs B2B logado | Unificar narrativa (wizard público vs token para POST). |
| D2 | CNPJ opcional no Free | API hoje exige CNPJ 14 dígitos no schema — alinhar produto. |
| D3 | Faturamento / setor detalhado | Schema API + front. |
| D4 | URL canônica dev/stage/prod | `NEXT_PUBLIC_API_URL` + documentação. |
| D5 | Billing Plus/Pro | Triggers nas perguntas sem cobrança no código. |

---

## 12. Blocos sugeridos para próximas sessões

| ID | Escopo | Pronto quando |
|----|--------|----------------|
| **N1** | Dashboard: `cronograma`, checklist completo (prioridade + base_legal), matriz a partir do JSON real | Paridade com `DiagnosticoResponse` sem mock quando API OK |
| **N2** | Wizard: componentes por `tipo` de pergunta | Catálogo completo respondível sem atalhos inadequados |
| **N3** | Playwright: jornada POST diagnóstico (Docker ou mock MSW) | 1 spec verde que falha se contrato HTTP quebrar |
| **N4** | M04 PDF: revisão páginação + teste snapshot/HTML golden opcional | Critérios “1 exec + N técnicas” definidos e validados |
| **N5** | M05: heatmap ou ranking gaps na UI | Visual derivado de `score_por_dimensao` + texto consultoria |
| **N6** | M10 + docs operação idempotency / RLS | Decisão escrita + migração se necessário |
| **N7** | Protótipo Lexiq / guardrail mínimo | Resposta sem fonte = erro controlado (S02) |

**Histórico de blocos entregues (visão macro):**

- **A–E:** núcleo API, catálogo 37, score, OTEL mínimo, idempotência Postgres.  
- **F/G (parcial):** Bearer, Idempotency-Key, `NEXT_PUBLIC_API_URL`, GET questionário no wizard, LGPD no form.  
- **H/J/K (parcial):** PDF síntese + cronograma + checklist normativo; `ConsultoriaService` enriquecido; ABNT 10 itens.  
- **L (parcial):** smoke Playwright na porta **3333**.

---

## 13. Prompt modelo para agente

```
Branch local: feat/qdi-<nome>.

Leia docs/HANDOFF_PROXIMA_SESSAO_QDI.md (§1, §7, §12 e bloco escolhido).

Escopo: apenas o bloco N<n> acordado — não expandir para QAI/QFC/QMI, Winthor completo ou RAG Lexiq total sem pedido explícito.

Não fazer: git push/rebase sem confirmação do Allan.

Ao terminar: make lint; make format; make test; mypy src; se tocar no front E2E: npm run test:e2e (frontend).
```

---

## 14. Checklist pós-sessão (Allan)

- [ ] Diff revisado  
- [ ] `make test` + `mypy src`  
- [ ] Atualizar este handoff se mudança material em §4–§7 ou MoSCoW  
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

*Fim do handoff. Prioridade imediata sugerida: **§12 N1 + N2** (dashboard completo + wizard por tipo).*
