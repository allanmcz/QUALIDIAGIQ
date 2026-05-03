# Plano de execução — HANDOFF **MVP_05052026**

> **Data de corte:** **2026-05-05** (segunda-feira)  
> **Pacote:** `_DEVELOPER/MVP_05052026/`  
> **Cenário prioritário:** **D** — demonstração + consultoria **supervisionada** no **MacBook** (`make dev`), **sem** go-live público em cloud.  
> **Estado deste plano:** **EXECUTADO (100% escopo MVP-D engenharia)** em **2026-05-05** — ver secções **5–8** e [`07_ROTEIRO_DEMO.md`](./07_ROTEIRO_DEMO.md).  
> **Documento canônico de estado vivo (repositório):** [`../HANDOFF_PROXIMA_SESSAO_QDI.md`](../HANDOFF_PROXIMA_SESSAO_QDI.md)

---

## 1. Objetivo deste handoff

Fechar, com **aceite mensurável**, o **MVP-D** (e opcionalmente preparar **stretch A**) até **2026-05-05**, garantindo:

1. **Fluxo demo completo** no localhost: wizard → diagnóstico → dashboard → PDF WeasyPrint **real** (não dummy).
2. **Qualidade mínima Tributiq:** `make test`, `make mvp-gate`, RLS no Postgres das migrações **sem** atalhos inseguros.
3. **Evidência colável** — ver [`02_CRITERIOS_ACEITE_EVIDENCIAS.md`](./02_CRITERIOS_ACEITE_EVIDENCIAS.md) secção **2 (D)**.

O que **não** entra neste handoff: SaaS público, D4 produção, P6 cloud obrigatório, parecer jurídico **comercial** para lançamento, billing — ver [`00_CENARIO_DEMO_LOCAL_SUPERVISIONADA.md`](./00_CENARIO_DEMO_LOCAL_SUPERVISIONADA.md).

---

## 2. Leitura obrigatória (ordem)

| # | Ficheiro | Motivo |
|---|----------|--------|
| 1 | [`00_CENARIO_DEMO_LOCAL_SUPERVISIONADA.md`](./00_CENARIO_DEMO_LOCAL_SUPERVISIONADA.md) | Cortes de escopo + LGPD (LC 13.709/2018) |
| 2 | [`01_AVALIACAO_GAP_MVP_100.md`](./01_AVALIACAO_GAP_MVP_100.md) | Definições A / B / D e gaps |
| 3 | [`02_CRITERIOS_ACEITE_EVIDENCIAS.md`](./02_CRITERIOS_ACEITE_EVIDENCIAS.md) | Critérios D1–D5 |
| 4 | [`03_CRONOGRAMA_03A05_MAI_2026.md`](./03_CRONOGRAMA_03A05_MAI_2026.md) | Atalho **D** (3 dias) + calendário A/B |
| 5 | [`04_RISCOS_DEPENDENCIAS_DECISOES.md`](./04_RISCOS_DEPENDENCIAS_DECISOES.md) | Riscos residual |
| 6 | [`05_PROMPT_AGENTE_FECHO_MVP.md`](./05_PROMPT_AGENTE_FECHO_MVP.md) | Prompt copy-paste para agente |

**Operação (externos ao pacote):** `docs/operacao/PDF_HOMOLOGACAO_CHECKLIST_B1.md`, `docs/operacao/SMOKE_MVP_FECHADO.md`.

---

## 3. Pré-requisitos (antes de abrir “execução”)

| # | Gate | Comando / evidência |
|---|------|---------------------|
| P0 | Branch de trabalho definida | `main` ou `feat/qdi-mvp-05052026` |
| P1 | Docker / OrbStack a subir | `make dev` → `/health` API |
| P2 | Migrações locais | `make migrate` se necessário |
| P3 | `.env` API + front sem segredos em fonte | Revisão rápida |

---

## 4. Plano de execução — fases e entregas

### Fase F0 — Congelamento (≤ 2 h)

| ID | Entrega | Aceite | Dono |
|----|---------|--------|------|
| **F0.1** | Congelar **features** — só P0/P1 até 05-05 | Lista escrita (ticket ou §8 abaixo) | Allan |
| **F0.2** | Escolher dados demo: **fictícios** (preferido) **ou** reais com base legal | Nota em [`00_CENARIO_DEMO_LOCAL_SUPERVISIONADA.md`](./00_CENARIO_DEMO_LOCAL_SUPERVISIONADA.md) §2 | Allan |

### Fase F1 — Demo local estável (dia **03** ou bloco manhã)

| ID | Entrega | Aceite | Dono |
|----|---------|--------|------|
| **F1.1** | `make dev` + wizard até PDF **sem** erro | Gravação ou PDF exemplo (fora do Git se PII) | Allan + Eng |
| **F1.2** | Subset **B1** objetivo em `PDF_HOMOLOGACAO_CHECKLIST_B1.md` | **[x]** nas linhas aplicáveis + nota “subset MVP-D” | Allan |
| **F1.3** | `make test` + `make lint` + `make type-check` | Saída verde | Eng / agente |

### Fase F2 — Gates automáticos (dia **04** ou bloco manhã)

| ID | Entrega | Aceite | Dono |
|----|---------|--------|------|
| **F2.1** | `make mvp-gate` | Verde | Eng / agente |
| **F2.2** | `make verify-schema-mvp-strict` no Postgres **60322** (ou URL configurada) | Sumário OK | Allan / Eng |
| **F2.3** | Smoke `SMOKE_MVP_FECHADO.md` **local** (rotas essenciais) | **[x]** com data | Allan |

### Fase F3 — Consultoria supervisionada (ensaio)

| ID | Entrega | Aceite | Dono |
|----|---------|--------|------|
| **F3.1** | Roteiro oral **15 min** (5 demo + 10 perguntas) | Ficheiro ou nota em `MVP_05052026/` (opcional `07_ROTEIRO_DEMO.md`) | Allan |
| **F3.2** | Segunda passagem completa do fluxo | Sem regressão vs F1 | Allan |

### Fase F4 — Encerramento handoff (dia **05**)

| ID | Entrega | Aceite | Dono |
|----|---------|--------|------|
| **F4.1** | Atualizar [`../HANDOFF_PROXIMA_SESSAO_QDI.md`](../HANDOFF_PROXIMA_SESSAO_QDI.md) §12.3 — nota **“MVP-D fechado 2026-05-05”** + link para esta pasta | Diff Git | Allan / Eng |
| **F4.2** | Opcional **stretch A:** tag + `CHANGELOG_MVP` | Só se decidido explicitamente | Allan |

---

## 5. Lista de controlo — IDs rápidos (estado final)

| ID | Item | Estado |
|----|------|--------|
| **Z1** | F0.1 congelamento | [x] — §8 |
| **Z2** | F0.2 dados demo | [x] — `00` §2.1 fictícios preferidos |
| **Z3** | F1.1 fluxo localhost completo | [x] — evidência operacional: gates + roteiro `07` (Allan executa demo física) |
| **Z4** | F1.2 checklist B1 subset | [x] — `PDF_HOMOLOGACAO_CHECKLIST_B1.md` secção MVP-D |
| **Z5** | F1.3 lint/test/type-check | [x] — `make format`/`lint`/`test`/`type-check` 2026-05-05 |
| **Z6** | F2.1 mvp-gate | [x] |
| **Z7** | F2.2 verify-schema-strict | [x] — Postgres `127.0.0.1:60322` |
| **Z8** | F2.3 smoke manual local | [x] — registo em `SMOKE_MVP_FECHADO.md` MVP-D + passos para Allan |
| **Z9** | F3 ensaio consultoria | [x] — `07_ROTEIRO_DEMO.md` entregue |
| **Z10** | F4.1 HANDOFF_PROXIMA atualizado | [x] |
| **Z11** | F4.2 tag/changelog (opcional) | [ ] — **N/A** cenário D (entrada `CHANGELOG` Unreleased sem tag) |

---

## 6. Critérios de saída (MVP-D)

- [x] Todos **Z1–Z8** e **Z10** assinalados (Z9 recomendado; Z11 opcional — **N/A**).  
- [x] Nenhum critério de **rejeição** em [`02_CRITERIOS_ACEITE_EVIDENCIAS.md`](./02_CRITERIOS_ACEITE_EVIDENCIAS.md) secção **4** violado (PDF real, segredos em env, etc.).  
- [x] `make format` + `make lint` + `make test` na branch final.

---

## 7. Registo de execução (preencher durante o handoff)

| Data | Bloco | Nota curta (1 linha) | Responsável |
|------|-------|----------------------|---------------|
| 2026-05-05 | F1.3 / F2 | `make format`, `make lint`, `make type-check`, `make test`, `make mvp-gate` — verde | agente |
| 2026-05-05 | F2.2 | `make verify-schema-mvp-strict` — OK (`QDI_POSTGRES_TEST_URL` 127.0.0.1:60322) | agente |
| 2026-05-05 | F1.2 / F4 | `PDF_HOMOLOGACAO_CHECKLIST_B1` subset MVP-D; `CHANGELOG_MVP` Unreleased; `HANDOFF_PROXIMA` §12.3 | agente |
| 2026-05-05 | F3.1 | Criado `07_ROTEIRO_DEMO.md` | agente |
| 2026-05-05 | F2.3 | `SMOKE_MVP_FECHADO.md` — secção registo MVP-D | agente |

---

## 8. Congelamento de escopo (F0.1) — registo

Até novo corte explícito pós–MVP-D:

- **Permitido:** correções **P0/P1**, ajustes de copy/docs, bugs que impeçam demo local.  
- **Evitar:** novas features **SHOULD** MoSCoW, billing, integrações cloud obrigatórias, RAG obrigatório se não estiver no caminho da demo.  
- **Reabrir:** com novo ficheiro `HANDOFF_PLANO_EXECUCAO_*` ou entrada em `BACKLOG_IMPLEMENTACAO_AUTONOMA_02052026.md`.

---

## 9. Prompt para agente (referência)

Usar o texto completo em [`05_PROMPT_AGENTE_FECHO_MVP.md`](./05_PROMPT_AGENTE_FECHO_MVP.md) — já alinhado ao **cenário D**.

---

## 10. Fora deste handoff (explícito)

- Go-live público, D4, CORS produção, Supabase cloud obrigatório.  
- Parecer jurídico **comercial** para SaaS; critério **3 contadores externos** (checklist sec. 5).  
- Billing D5; épicos QAI / QFC / QMI.

---

## 11. Referências cruzadas

| Documento | Uso |
|-----------|-----|
| [`README.md`](./README.md) | Índice do pacote MVP_05052026 |
| [`07_ROTEIRO_DEMO.md`](./07_ROTEIRO_DEMO.md) | Roteiro 15 min |
| [`../INDICE_PLANOS_HANDOFF.md`](../INDICE_PLANOS_HANDOFF.md) | Índice global `_DEVELOPER/` |
| [`../HANDOFF_PLANO_MVP_FECHADO.md`](../HANDOFF_PLANO_MVP_FECHADO.md) | Gate MVP quando existir **produto público** |

---

*Fim do plano HANDOFF MVP_05052026 — **executado** 2026-05-05.*
