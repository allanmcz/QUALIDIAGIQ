# Documentação técnica — QualiDiagIQ (pasta desenvolvedor)

Este diretório concentra **planos de execução, handoffs e notas de engenharia**. O mapa canónico dos planos está em **[`INDICE_PLANOS_HANDOFF.md`](./INDICE_PLANOS_HANDOFF.md)**. Documentação de produto e operação versionada para stakeholders: **[`docs/README.md`](../docs/README.md)**.

## Onde está o quê

| Área | Caminho |
|------|---------|
| **Activo** (planos, handoff estado vivo, backlog, runbooks internos) | Raiz `_DEVELOPER/` + [`analises/`](./analises/) |
| **Encerrados** (análises datadas, snapshots) | [`_CONCLUIDOS_DEV/`](./_CONCLUIDOS_DEV/) |

### Raiz `_DEVELOPER/` (referência rápida)

| Ficheiro | Conteúdo |
| -------- | -------- |
| [`INDICE_PLANOS_HANDOFF.md`](./INDICE_PLANOS_HANDOFF.md) | **Índice** de planos de execução e handoffs. |
| [`HANDOFF_PROXIMA_SESSAO_QDI.md`](./HANDOFF_PROXIMA_SESSAO_QDI.md) | Estado técnico vivo + backlog P/M. |
| [`PLANO_EXECUCAO_EPICOS_GRANDES_QDI.md`](./PLANO_EXECUCAO_EPICOS_GRANDES_QDI.md) | Roadmap épicos E1–E5 (multi-sprint). |
| [`HANDOFF_PLANO_EXECUCAO_2026-05-03.md`](./HANDOFF_PLANO_EXECUCAO_2026-05-03.md) | Plano HANDOFF + lista técnica sem decisões externas (2026-05-03). |
| [`BACKLOG_IMPLEMENTACAO_AUTONOMA_02052026.md`](./BACKLOG_IMPLEMENTACAO_AUTONOMA_02052026.md) | Itens de engenharia sem gate de produto. |
| [`docs/operacao/CHECKLIST_CONFIRMACAO_ALLAN_MVP.md`](../docs/operacao/CHECKLIST_CONFIRMACAO_ALLAN_MVP.md) | Confirmações MVP / homologação — versionado em `docs/operacao/`. |
| [`RUNBOOK_SUPABASE_RLS.md`](./RUNBOOK_SUPABASE_RLS.md) | Operação RLS multi-tenant, migrações e checagens. |
| [`RUNBOOK_SMOKE_SUPABASE_OPS.md`](./RUNBOOK_SMOKE_SUPABASE_OPS.md) | Smoke ops Supabase. |
| [`GUIA_TESTE_AMBIENTE_COMPLETO_E_VISAO_CONTADOR.md`](./GUIA_TESTE_AMBIENTE_COMPLETO_E_VISAO_CONTADOR.md) | Guia de teste / visão contador. |

### `_CONCLUIDOS_DEV/` (snapshots)

Exemplos (lista não exaustiva): análise developer 02/05/2026, plano handoff 02/05/2026, handoff épicos grandes pós-E1, índice engenharia com planos curto/médio prazo arquivados, análises 3004/0105, etc.

**Arquivamento 2026-05-03 (ciclo entregue / duplicados absorvidos):**

| Item | Nota |
|------|------|
| `ANALISE_02052026_CLAUDE/` | Auditoria + prompt total implementação (Sprint/handoff código). |
| `KIT_DESENVOLVIMENTO_01-05-2026/` | Kit datado de arranque — substituído pelo fluxo `make install` + docs versionados. |
| `REFORMULACAO_MARCA/` | Entrega de marca/tokens aplicada em `frontend/public/brand` (snapshot de trabalho). |
| `HANDOFF_EPICOS_GRANDES_QDI_COMPLETO.md` | Versão final na pasta de concluídos (raiz limpa). |
| `PLANO_EXECUCAO_HANDOFF_02052026.md` | Idem — histórico de execução do handoff 02/05. |

**Comandos essenciais (raiz do repositório):** `make install`, `make dev`, `make lint`, `make format`, `make test`, `make type-check` (`mypy src`), `make down`.
