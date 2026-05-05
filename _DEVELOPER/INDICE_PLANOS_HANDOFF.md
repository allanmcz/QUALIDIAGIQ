# Índice — planos de execução e handoffs (`_DEVELOPER/`)

> **Regra do repositório:** planos de execução, handoffs de sessão e análises pontuais de engenharia vivem nesta pasta (ou em `analises/`). A pasta `docs/` mantém **produto**, **operação** e **conformidade** — ver [`docs/README.md`](../docs/README.md).

## Estado vivo e plano mestre

| Ficheiro | Uso |
|----------|-----|
| [`HANDOFF_PROXIMA_SESSAO_QDI.md`](./HANDOFF_PROXIMA_SESSAO_QDI.md) | Snapshot técnico, MoSCoW MUST, backlog P1–P8, prompts agente |
| [`HANDOFF_PLANO_MVP_FECHADO.md`](./HANDOFF_PLANO_MVP_FECHADO.md) | Gate MVP fechado — fases A–G, critérios §6 |
| [`03_roadmap_sprint_1.md`](./03_roadmap_sprint_1.md) | Plano dia-a-dia Sprint 1 (30 dias) |

## Planos por ciclo / data

Handoffs **executados** ou **sessões encerradas** (2026-05) estão arquivados em [`_CONCLUIDOS_DEV/`](./_CONCLUIDOS_DEV/) — tabela na secção **Arquivado** abaixo. O estado técnico vivo continua em [`HANDOFF_PROXIMA_SESSAO_QDI.md`](./HANDOFF_PROXIMA_SESSAO_QDI.md).

## Arquivado — handoffs e planos encerrados (`_CONCLUIDOS_DEV/`)

| Ficheiro | Nota |
|----------|------|
| [`HANDOFF_PLANO_EXECUCAO_2026-05-03.md`](./_CONCLUIDOS_DEV/HANDOFF_PLANO_EXECUCAO_2026-05-03.md) | Plano HANDOFF engenharia 2026-05-03 (**executado**) |
| [`HANDOFF_CICLO_Q_2026-05-02.md`](./_CONCLUIDOS_DEV/HANDOFF_CICLO_Q_2026-05-02.md) | Ciclo Q (**executado**) |
| [`HANDOFF_IMPLEMENTACAO_10H_2026-05-01.md`](./_CONCLUIDOS_DEV/HANDOFF_IMPLEMENTACAO_10H_2026-05-01.md) | Janela ~10 h (P5–P8) — snapshot de sessão |
| [`HANDOFF_SESSAO_AUTONOMA_2026-05-01.md`](./_CONCLUIDOS_DEV/HANDOFF_SESSAO_AUTONOMA_2026-05-01.md) | Sessão autónoma |
| [`HANDOFF_SESSAO_CONTINUACAO_2026-05-01.md`](./_CONCLUIDOS_DEV/HANDOFF_SESSAO_CONTINUACAO_2026-05-01.md) | Continuação pós-autonomia |
| [`PERSISTENCIA_PAINEL.md`](./_CONCLUIDOS_DEV/PERSISTENCIA_PAINEL.md) | Plano persistência painel — decisões D1–D5; implementação no repo concluída (2026-05-04) |

## Análises e inventários (engenharia)

| Ficheiro | Uso |
|----------|-----|
| [`analises/GAP_ANALYSIS_RLS_P6_2026-05-02.md`](./analises/GAP_ANALYSIS_RLS_P6_2026-05-02.md) | Gap RLS / multi-tenant (P6) |
| [`analises/p3_aschild_inventario.md`](./analises/p3_aschild_inventario.md) | Inventário `Button` + `asChild` |

## Pacote de corte MVP (calendário)

| Pasta | Uso |
|-------|-----|
| [`MVP_05052026/`](./MVP_05052026/README.md) | Pacote **05/05/2026** — **[`HANDOFF_PLANO_EXECUCAO_MVP_05052026.md`](./MVP_05052026/HANDOFF_PLANO_EXECUCAO_MVP_05052026.md)** **executado** (MVP-D) + roteiro [`07_ROTEIRO_DEMO.md`](./MVP_05052026/07_ROTEIRO_DEMO.md) |

## Outros (backlog, kits, runbooks internos)

- [`FALTA_IMPLEMENTAR.md`](./FALTA_IMPLEMENTAR.md) — plano sintético do que falta concluir (executável vs gates)
- [`BACKLOG_IMPLEMENTACAO_AUTONOMA_02052026.md`](./BACKLOG_IMPLEMENTACAO_AUTONOMA_02052026.md)
- [`RUNBOOK_SUPABASE_RLS.md`](./RUNBOOK_SUPABASE_RLS.md)
- Pastas `ORIENTACAO_CURSOR/`, `ANALISE_30042026/`, `_CONCLUIDOS_DEV/` — arquivo e orientação Cursor

---

*Ao criar um novo plano: adicionar uma linha nesta tabela e um link em [`docs/README.md`](../docs/README.md) apenas se stakeholders precisarem de ponte explícita.*
