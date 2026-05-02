# Plano de implementação / handoff — MVP QualiDiagIQ fechado

> **Objetivo:** único documento mestre para declarar o **MVP fechado** (técnico + operação + mínimo comercial/jurídico), com fases, artefactos versionados no repo, critérios de aceite e links para runbooks.
>
> **Documentos relacionados:** `docs/HANDOFF_PROXIMA_SESSAO_QDI.md`, `docs/refs/02_MOSCOW_FEATURES.md`, `docs/operacao/CHECKLIST_CONFIRMACAO_ALLAN_MVP.md` (gates produto / Allan), `_DEVELOPER/RUNBOOK_SUPABASE_RLS.md`, `_DEVELOPER/ANALISE_30042026/`.
>
> **Última atualização:** 2026-05-01 — execução técnica das Fases **D.3** (LGPD persistido), **G.1** lean (`X-Trace-Id`), artefactos **§7**, migração **0012**.

---

## Índice

1. [Definição de MVP fechado](#1-definição-de-mvp-fechado)  
2. [Mapa lacunas × MUST / P](#2-mapa-lacunas--must--p)  
3. [Fases A–G (execução)](#3-fases-ag-execução)  
4. [Épicos fora do MVP](#4-épicos-fora-do-mvp)  
5. [Artefactos implementados no repositório (§7)](#5-artefactos-implementados-no-repositório-7)  
6. [Checklist gate final](#6-checklist-gate-final)  
7. [Smoke manual (A.3)](#7-smoke-manual-a3)  
8. [CHANGELOG e release (A.1)](#8-changelog-e-release-a1)  
9. [Prompt próximo agente](#9-prompt-próximo-agente)

---

## 1. Definição de MVP fechado

Para este plano, **MVP fechado** significa:

1. **Funcional:** wizard → POST diagnóstico (com **aceite LGPD** persistido) → lista → detalhe → **M12** com PATCH → PDF quando ambiente configurado — sem regressões nos **12 MUST** MoSCoW acordados.
2. **Operável:** pré-prod ou produção com **RLS** validado (`_DEVELOPER/RUNBOOK_SUPABASE_RLS.md`), segredos só via env, migrações até **0012+** aplicadas.
3. **Auditável (mínimo):** `hash_evidencia`, `versao_otimista`, **sem dummy de PDF** onde o PRD exige WeasyPrint real.
4. **Lançável:** parecer jurídico sobre **`/termos`** e **`/privacidade`**; decisões **D1–D5** registradas (mesmo que “adiado”) — acompanhamento explícito em **`docs/operacao/CHECKLIST_CONFIRMACAO_ALLAN_MVP.md`**.

**Fora do escopo deste fechamento:** versionamento normativo completo no DB (`vigencia_*`), RAG Lexiq integral, Winthor, billing real.

---

## 2. Mapa lacunas × MUST / P

| Lacuna | MUST / P | Tipo |
|--------|----------|------|
| Homologação PDF WeasyPrint | M04, P5 | Negócio + técnico |
| RLS Supabase produção | M10, P6 | Operação |
| Jurídico termos/privacidade | §10 handoff | Compliance |
| Retenção telefone respondente | D.2 / LGPD | Texto MVP + processo interno |
| Aceite LGPD com timestamp | D.3 | **Implementado** — migração 0012 |
| Correlation HTTP trace | G.1 lean | **Implementado** — `X-Trace-Id` |
| Revisão editorial M08 | M08 | Conteúdo |
| Decisões D1/D3/D4/D5 | M09 | Produto |
| Calibração motor coorte real | M02 | Beta |

---

## 3. Fases A–G (execução)

### Fase A — Congelamento técnico

| # | Entrega | Estado | Evidência |
|---|---------|--------|-----------|
| A.1 | Tag/release + changelog MVP | Processo | `docs/CHANGELOG_MVP.md` — preencher linha de release ao tagar |
| A.2 | OpenAPI export | Comando | `make openapi-export` → `docs/api/openapi.generated.json` (gitignored) |
| A.3 | Smoke manual | Checklist | `docs/operacao/SMOKE_MVP_FECHADO.md` |

### Fase B — PDF (P5 / M04)

| # | Entrega | Estado | Evidência |
|---|---------|--------|-----------|
| B.1 | Checklist seções PDF | Template | `docs/operacao/PDF_HOMOLOGACAO_CHECKLIST_B1.md` |
| B.2 | Sign-off contábil | Pendente Allan | Tabela no mesmo doc |
| B.3 | Ambiente prod espelho | Pendente ops | Runbook deploy |
| B.4 | Storage + PATCH PDF | Código existente | Router PATCH relatório |

### Fase C — RLS produção (P6 / M10)

Executar `_DEVELOPER/RUNBOOK_SUPABASE_RLS.md`; evidência de isolamento dois tenants.

### Fase D — Compliance

| # | Entrega | Estado |
|---|---------|--------|
| D.1 | Parecer jurídico termos/privacidade | Pendente externo |
| D.2 | Retenção telefone | Texto MVP em `/privacidade` + processo interno |
| D.3 | Aceite persistido | **Feito** — `aceite_termos_privacidade_em`, WORM inclui coluna |

### Fase E — Produto D1–D3

Registro vivo: `docs/operacao/DECISOES_PRODUTO_MVP_D1_D5.md`.

### Fase F — M08 editorial

Passagem linha a linha matriz/checklist/PDF — backlog conteúdo; catálogo 37×35 já auditado script P4.

### Fase G — Observabilidade

| # | Entrega | Estado |
|---|---------|--------|
| G.1 | Trace HTTP | **Feito** — ver `docs/operacao/OBSERVABILIDADE_TRACE_ID.md` |
| G.2 | Deploy/rollback | **Feito** — `docs/operacao/RUNBOOK_DEPLOY_ROLLBACK.md` |
| OTEL export prod | Opcional | Flag `OTEL_TRACING_ENABLED` |

---

## 4. Épicos fora do MVP

| Épico | Motivo |
|-------|--------|
| Regras `vigencia_inicio/fim` no PostgreSQL | Épico schema + ADR |
| RAG Lexiq wizard completo | SHOULD |
| Billing Stripe | D5 |

---

## 5. Artefactos implementados no repositório (§7)

Implementação alinhada a este plano (2026-05-01):

| Artefacto | Caminho / notas |
|-----------|-----------------|
| Migração LGPD + WORM aceite | `src/infrastructure/db/migrations/0012_aceite_lgpd_e_worm.sql` |
| Bootstrap Docker | `init.sql` inclui **0012** |
| Domínio aceite | `Diagnostico.registrar_aceite_termos_privacidade`, campo `aceite_termos_privacidade_em` |
| Use case | `ComandoRealizarDiagnostico.aceite_termos_privacidade` + `RealizarDiagnostico` |
| API | `IniciarDiagnosticoRequest`, `DiagnosticoResponse`, router POST |
| Repositório | `SupabaseDiagnosticoRepository` serialização ISO da coluna |
| Middleware trace | `src/presentation/api/middleware/trace_context.py`; registro em `main.py`; CORS |
| Front POST | `frontend/lib/api/diagnostico.ts` envia `aceite_termos_privacidade` |
| Privacidade MVP | `frontend/app/privacidade/page.tsx` — telefone respondente |
| Testes | Domínio, API 422 sem aceite, health `X-Trace-Id`, WORM bloqueia UPDATE aceite, E2E pytest + Playwright JSON |
| Changelog MVP | `docs/CHANGELOG_MVP.md` |
| Smoke / PDF / Deploy / Trace / Decisões / Checklist Allan | `docs/operacao/*.md`; índice `docs/operacao/README.md`; checklist Allan `docs/operacao/CHECKLIST_CONFIRMACAO_ALLAN_MVP.md` |
| Status jurídico (processo) | `docs/legal/STATUS_JURIDICO_MVP.md` |
| Gate pytest MVP | `make mvp-gate`; `tests/integration/test_smoke_mvp_fechado_api.py`; `tests/integration/test_mvp_gate_postgres.py` |
| Verificação schema (ops) | `make verify-schema-mvp`; `scripts/verify_mvp_schema.py`; `docs/operacao/SQL_VERIFICACAO_SCHEMA_MVP.sql` |

---

## 6. Checklist gate final

**Checklist produto / confirmações Allan (rastreável no Git):** `docs/operacao/CHECKLIST_CONFIRMACAO_ALLAN_MVP.md` — mapa *Quem decide / Quem executa*, gates P5/P6, jurídico, D3–D5, M02/M03/M08, Beta e princípios não negociáveis.

- [x] `make test`, `make lint`, `make type-check` na branch principal — **CI** em `main`/`master`, `release/**`, tags `v*` e `mvp-*` (`.github/workflows/ci.yml`)  
- [x] **Validação local (2026-05-01):** `make test` (167+), `make lint`, `make format`, `make type-check` — cobertura global **≥80%**  
- [ ] Migrações **`0012`** aplicadas em **pré-prod/prod** (Supabase ou DB alvo) — *operacional* — evidência: **`make verify-schema-mvp`** com `DATABASE_URL` do ambiente ou **`docs/operacao/SQL_VERIFICACAO_SCHEMA_MVP.sql`** (todas as linhas `status = ok`)  
- [x] Smoke — **automatizado:** `make mvp-gate` + pytest em CI (`docs/operacao/SMOKE_MVP_FECHADO.md` §Automatizado); **manual:** login real + wizard + PDF real quando exigido  
- [x] P5 (parcial): marcadores M04 no template cobertos por **`test_pdf_template_m04.py`**; **pendente Allan:** sign-off + PDF gerado em ambiente espelho (`PDF_HOMOLOGACAO_CHECKLIST_B1.md`)  
- [x] P6 (parcial): isolamento **dois tenants** validado em **`tests/integration/test_mvp_gate_postgres.py`**; **pendente ops:** repetir no projeto Supabase real (`_DEVELOPER/RUNBOOK_SUPABASE_RLS.md`)  
- [x] Jurídico (parcial): páginas MVP + processo descritos em **`docs/legal/STATUS_JURIDICO_MVP.md`**; **pendente externo:** parecer formal pré-comercial  
- [x] `DECISOES_PRODUTO_MVP_D1_D5.md` — registro de sincronização 2026-05-01 + baseline D2/D6  
- [x] Atualizar `docs/HANDOFF_PROXIMA_SESSAO_QDI.md` com data + links (`§17 Plano MVP fechado`, migrações **0012**, POST com aceite LGPD)  

---

## 7. Smoke manual (A.3)

Roteiro passo a passo: **`docs/operacao/SMOKE_MVP_FECHADO.md`**.

---

## 8. CHANGELOG e release (A.1)

- Modelo de entradas: **`docs/CHANGELOG_MVP.md`**  
- Ao tagar: copiar bloco Unreleased → data; referenciar commit SHA ou tag git (`git tag -a mvp-2026-05-01 …`) — **sem push automático** sem confirmação do Allan.

---

## 9. Prompt próximo agente

```
Leia docs/HANDOFF_PLANO_MVP_FECHADO.md (§3 Fase B ou C conforme prioridade).

Escopo: apenas P5 homologação PDF OU P6 RLS produção — não expandir QAI/QFC/QMI.

Não fazer git push/rebase sem confirmação.

Ao concluir: evidências em §6 + entrada em docs/CHANGELOG_MVP.md + HANDOFF_PROXIMA §12.3.
```

---

*Donos sugeridos: Allan (produto + PDF + decisões); Eng (API/DB/front); Jurídico (externo); Ops (Supabase/deploy).*
