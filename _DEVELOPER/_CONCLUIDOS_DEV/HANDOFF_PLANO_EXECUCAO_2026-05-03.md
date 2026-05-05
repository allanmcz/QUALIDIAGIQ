# Plano de execução — HANDOFF QualiDiagIQ

> **Data de corte:** 2026-05-03 (sábado)  
> **Estado:** **EXECUTADO (100% escopo engenharia)** em 2026-05-03 — ver secção **8** e [`docs/operacao/GUIA_TESTE_COMPLETO_QDI_2026-05-03.md`](../docs/operacao/GUIA_TESTE_COMPLETO_QDI_2026-05-03.md).  
> **Documento canônico de estado vivo:** [`HANDOFF_PROXIMA_SESSAO_QDI.md`](../HANDOFF_PROXIMA_SESSAO_QDI.md) (raiz do repositório: `_DEVELOPER/HANDOFF_PROXIMA_SESSAO_QDI.md`)  
> **Backlog autónomo:** [`BACKLOG_IMPLEMENTACAO_AUTONOMA_02052026.md`](../BACKLOG_IMPLEMENTACAO_AUTONOMA_02052026.md)  
> **Análise Claude 02/05 arquivada:** [`ANALISE_02052026_CLAUDE/`](./ANALISE_02052026_CLAUDE/)

---

## 1. Objetivo deste plano

Orquestrar **as próximas entregas de engenharia** que:

1. Têm **aceite mensurável** (testes, CI, diff, runbook).
2. **Não dependem** de decisão comercial, jurídica, calibração M02 com dados reais, homologação PDF assinada, smoke Supabase cloud, nem escolha de roadmap Beta (MoSCoW SHOULD).

O que **depende** de Allan/produto/jurídico fica na secção **6 — Fora deste plano**.

---

## 2. Snapshot do que já está fechado (contexto 2026-05-03)

| Tema | Estado |
|------|--------|
| Migrações **0001…0020** | CI + `init.sql` / `make migrate`; imagem **pgvector**. |
| Gate schema | Strict CNAE + modo **RAG** (`verify_mvp_schema.py`). |
| LLM + RAG | LangGraph/Ollama, Anthropic opcional, pgvector + ingestão baseline. |
| Documentação operação | RUNBOOK + **OTEL_QUICKSTART_LOCAL** + **GUIA_TESTE_COMPLETO** 2026-05-03. |
| ADR **006** | Deps IA documentadas com uso em `src/`. |
| UX M05/M06 | Ranking + timeline com **a11y** reforçada (`motion-reduce`, `focus-within`). |
| Catálogo G1 | `catalogo_auditoria.py` + CLI + **`make audit-catalogo`** + passo **CI**. |

---

## 3. Plano de execução — entregas realizadas

| Fase | Entrega | Evidência |
|------|---------|-----------|
| **A.1** | A1 Playwright wizard edge | `wizard-edge-cases.spec.ts` + novo bloco **catálogo multipla inválido**. |
| **A.2** | A4 idempotência | `test_post_diagnostico_chaves_idempotencia_distintas_executa_duas_vezes`. |
| **A.3** | Cobertura pgvector (mocks) | `tests/unit/infrastructure/test_base_normativa_pgvector.py`. |
| **B.1** | G1 auditoria catálogo | `src/infrastructure/questionario/catalogo_auditoria.py` + `scripts/auditoria_catalogo_perguntas_mvp.py` + testes + CI. |
| **B.2** | B2 HANDOFF_PROXIMA | Cabeçalho atualizado (data, guia teste, harmonização). |
| **C.1** | D2 M06 | `DiagnosticoDetalheClient` — `motion-reduce` + `focus-within:ring`. |
| **C.2** | F2 | Adapters LLM já em **structlog** (sem `logging` std nos ficheiros `llm_*.py` auditados). |
| **C.3** | E1 OTEL | `docs/operacao/OTEL_QUICKSTART_LOCAL.md` + link no RUNBOOK. |
| **B1** | README front storage | Tabela `localStorage` / `sessionStorage` no `frontend/README.md`. |
| **A2** | Domain `multipla_total` 0 | Teste em `tests/unit/domain/test_questionario.py`. |
| **Wizard** | Validação máx. seleções | `WizardForm.tsx` — limite `multipla_total` em passo e no payload. |

---

## 4. Lista pós-execução (sem decisão externa)

| ID | Item | Status |
|----|------|--------|
| **A1** | Edge cases wizard | **F** |
| **A2** | Ramos `questionario.py` | **F** (extensão `multipla_total` 0) |
| **A3** | Integração metodologia 0015 | **F** (pré-existente) |
| **A4** | Idempotência | **F** |
| **B1** | README storage | **F** |
| **B2** | HANDOFF_PROXIMA | **F** |
| **B3** | RUNBOOK | **F** |
| **C1** | ADR-006 | **F** |
| **D1** | M05 ranking | **F** |
| **D2** | M06 polimento | **F** |
| **E1** | OTEL | **F** |
| **E2** | CI verify | **F** |
| **F1** | Ollama timeout | **F** |
| **F2** | structlog LLM | **F** |
| **G1** | Auditoria 37 perguntas + invariantes | **F** (baseline estrutural; `--strict` pilar = modo futuro) |

**Extras plano:** Sentry browser já integrado em `AppProviders.tsx`. E2E integrado M12 permanece opcional (ambiente).

---

## 5. Critérios de saída (sessão de fecho)

- [x] `make lint` e `make format`
- [x] `make type-check`
- [x] `make test` e `make test-domain`
- [x] `npm run build` (frontend)
- [x] CI: auditoria catálogo + gates schema existentes

---

## 6. Fora deste plano (dependem de decisão externa)

Homologação PDF, M02 dados reais, M10 prod Supabase, M09 Free/CNPJ, legal M08, SHOULD comercial, billing.

---

## 7. Referências cruzadas

| Documento | Uso |
|-----------|-----|
| [`HANDOFF_PROXIMA_SESSAO_QDI.md`](../HANDOFF_PROXIMA_SESSAO_QDI.md) | Estado completo |
| [`docs/operacao/RUNBOOK_DEPLOY_ROLLBACK.md`](../docs/operacao/RUNBOOK_DEPLOY_ROLLBACK.md) | Release |
| [`docs/refs/05_QUESTIONARIO_v1.md`](../docs/refs/05_QUESTIONARIO_v1.md) | Fonte editorial perguntas |
| [`.github/adr/ADR-006-dependencias-ia-fora-src.md`](../.github/adr/ADR-006-dependencias-ia-fora-src.md) | Deps IA |

---

## 8. Estado de execução (handoff fechado)

| Artefacto | Caminho |
|-----------|---------|
| Guia teste hoje | `docs/operacao/GUIA_TESTE_COMPLETO_QDI_2026-05-03.md` |
| OTEL quick start | `docs/operacao/OTEL_QUICKSTART_LOCAL.md` |
| Auditoria G1 | `make audit-catalogo` · `scripts/auditoria_catalogo_perguntas_mvp.py` · `src/infrastructure/questionario/catalogo_auditoria.py` |
| Testes novos | `test_base_normativa_pgvector.py`, `test_catalogo_auditoria.py`, idempotência, domain `multipla_total` 0 |

---

*Plano HANDOFF 2026-05-03 — ciclo engenharia encerrado.*
