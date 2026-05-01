# Documentação técnica — QualiDiagIQ (pasta desenvolvedor)

Este diretório concentra notas úteis **fora** do núcleo de produto (`docs/` referências de negócio). Use como ponto de partida antes de grandes mudanças.

| Arquivo | Conteúdo |
| ------- | -------- |
| [ANALISE_PROJETO.md](./ANALISE_PROJETO.md) | Snapshot da stack, camadas, riscos e backlog técnico. |
| [FEATURES_HANDOFF_P1_P8.md](./FEATURES_HANDOFF_P1_P8.md) | O que foram os blocos P1–P8 (OpenAPI, CI, UI, PDF, RLS/M10, dashboard, wizard Lexiq). |
| [RUNBOOK_SUPABASE_RLS.md](./RUNBOOK_SUPABASE_RLS.md) | Operação de RLS multi-tenant, migrações e checagens. |

**Comandos essenciais (raiz do repositório):** `make install`, `make dev`, `make lint`, `make format`, `make test`, `make type-check` (`mypy src`), `make down`.
