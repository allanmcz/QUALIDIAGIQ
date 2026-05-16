# Documentação técnica — QualiDiagIQ (pasta desenvolvedor)

Este diretório concentra **planos de execução, handoffs e notas de engenharia**. O mapa canónico dos planos está em **[`INDICE_PLANOS_HANDOFF.md`](./INDICE_PLANOS_HANDOFF.md)**. Documentação de produto e operação versionada para stakeholders: **[`docs/README.md`](../docs/README.md)**.

## Regra de documentação de desenvolvimento

Toda documentação de **processo, planejamento de implementação, handoff técnico, backlog de execução, proposta técnica, análise de arquitetura e roteiro de desenvolvimento** deve ser criada e mantida dentro de `_DEVELOPER/`.

Exceções:

| Tipo de documento | Local correto |
|---|---|
| Documentação pública/produto para stakeholders | `docs/` |
| Documentação operacional versionada para produção | `docs/operacao/` |
| Documentação jurídica/LGPD validável externamente | `docs/legal/` |
| Referências-base de produto já consolidadas | `docs/refs/` |

Quando uma proposta começar como processo ou implementação e depois virar documentação oficial, ela deve ser promovida de `_DEVELOPER/` para `docs/` por decisão explícita.

Críticas, avaliações e pareceres produzidos pelo Codex sobre propostas externas devem ser registrados em subpasta própria dentro de `_DEVELOPER/`, preservando a pasta-fonte original sem alterações, salvo pedido explícito do Allan.

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
| [`BACKLOG_IMPLEMENTACAO_AUTONOMA_02052026.md`](./BACKLOG_IMPLEMENTACAO_AUTONOMA_02052026.md) | Itens de engenharia sem gate de produto. |
| [`docs/operacao/CHECKLIST_CONFIRMACAO_ALLAN_MVP.md`](../docs/operacao/CHECKLIST_CONFIRMACAO_ALLAN_MVP.md) | Confirmações MVP / homologação — versionado em `docs/operacao/`. |
| [`RUNBOOK_SUPABASE_RLS.md`](./RUNBOOK_SUPABASE_RLS.md) | Operação RLS multi-tenant, migrações e checagens. |
| [`RUNBOOK_SMOKE_SUPABASE_OPS.md`](./RUNBOOK_SMOKE_SUPABASE_OPS.md) | Smoke ops Supabase. |
| [`GUIA_TESTE_AMBIENTE_COMPLETO_E_VISAO_CONTADOR.md`](./GUIA_TESTE_AMBIENTE_COMPLETO_E_VISAO_CONTADOR.md) | Guia de teste / visão contador. |
| [`PLANO_ACAO_AVANCADO/`](./PLANO_ACAO_AVANCADO/) | Propostas avançadas para plano de ação, Kanban e gestão de tarefas. |
| [`PLANO_ACAO_V99/`](./PLANO_ACAO_V99/) | Pacote final consolidado para Kanban do Plano de Ação, incluindo ADR, PRD, especificação técnica e prompt Antigravity. |

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

**Arquivamento 2026-05-04 (planos / sessões concluídos):** `HANDOFF_PLANO_EXECUCAO_2026-05-03.md`, `HANDOFF_CICLO_Q_2026-05-02.md`, `HANDOFF_IMPLEMENTACAO_10H_2026-05-01.md`, `HANDOFF_SESSAO_AUTONOMA_2026-05-01.md`, `HANDOFF_SESSAO_CONTINUACAO_2026-05-01.md`, `PERSISTENCIA_PAINEL.md`; duplicados na raiz `HANDOFF_EPICOS_GRANDES_QDI_COMPLETO.md` e `PLANO_EXECUCAO_HANDOFF_02052026.md` removidos (canónico em `_CONCLUIDOS_DEV/`). Índice: [`INDICE_PLANOS_HANDOFF.md`](./INDICE_PLANOS_HANDOFF.md) secção **Arquivado**.

**Comandos essenciais (raiz do repositório):** `make install`, `make dev`, `make lint`, `make format`, `make test`, `make type-check` (`mypy src`), `make down`.
