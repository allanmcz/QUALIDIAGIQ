# Documentação QualiDiagIQ — mapa da pasta `docs/`

Esta pasta concentra **documentação de produto, operação e conformidade** versionada no Git. **Planos de execução, handoffs de sessão e análises de ciclo de engenharia** ficam em **`_DEVELOPER/`** (ver `_DEVELOPER/INDICE_PLANOS_HANDOFF.md`).

## Onde está o quê

| Pasta / ficheiro | Conteúdo |
|------------------|----------|
| **`docs/operacao/`** | Runbooks, smoke, OTEL, checklists de pentest/homologação, decisões D1–D5, guias de teste operacional, SQL de verificação de schema. **Sem** planos de sprint ou handoffs de sessão. |
| **`docs/contabilidade/`** | Guias e avaliação contábil auditável (MVP). |
| **`docs/CHANGELOG_MVP.md`** | Registro de entregas orientadas ao MVP fechado. |
| **`docs/refs/`** | PRD-base, MoSCoW, questionário, metodologia (quando presentes no clone — podem exigir `git add -f` conforme política local). |
| **`docs/01_arquitetura.md`**, **`docs/02_dominio_qdi.md`**, **`docs/00_INDICE.md`** | Arquitetura e domínio (workspace; versionação conforme `.gitignore`). |
| **`docs/legal/`** | `STATUS_JURIDICO_MVP.md` e parecer formal em PDF (exceção em `.gitignore`). |
| **`docs/schemas/`** | JSON Schema versionado (ex.: export portabilidade LGPD `qdi-diagnostico-export-v1` — ADR-012 §4). |
| **`docs/api/openapi.generated.json`** | OpenAPI 3 gerado pela app FastAPI (`make openapi-export`) — diff em PR ao alterar rotas ou schemas Pydantic. |
| **`_DEVELOPER/`** | **Planos de execução**, handoff próxima sessão, roadmap sprint, análises P6/`asChild`, notas de desenvolvimento. Índice: `_DEVELOPER/INDICE_PLANOS_HANDOFF.md`. **Pacote MVP 05/05/2026** (inclui cenário **D** — demo local supervisionada, sem go-live público): `_DEVELOPER/MVP_05052026/README.md`. |

## Ligações rápidas

- Estado técnico e backlog: `_DEVELOPER/HANDOFF_PROXIMA_SESSAO_QDI.md`
- Plano mestre gate MVP: `_DEVELOPER/HANDOFF_PLANO_MVP_FECHADO.md`
- Operação (deploy, smoke): [`operacao/README.md`](./operacao/README.md)
- Changelog: [`CHANGELOG_MVP.md`](./CHANGELOG_MVP.md)

---

*Convénio: novos **planos datados** ou **handoffs de agente** → criar ficheiro em `_DEVELOPER/` e referenciar aqui só se for documentação de produto visível a stakeholders.*
