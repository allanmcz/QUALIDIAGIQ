# Contribuição — QualiDiagIQ

## Requisitos rápidos

- Python 3.12, `make install`, comandos `.cursorrules` (`make lint`, `make format`, `make test`, `make type-check`).
- **Bateria de QA em um fluxo:** `make qa-backend` ou `./INICIAR_APP/iniciar-app.sh backend` — ver [INICIAR_APP/README.md](INICIAR_APP/README.md).
- ADRs novos em [.github/adr/](.github/adr/).

## Cursor — MCP Playwright (opcional)

O repositório inclui [`.cursor/mcp.json`](.cursor/mcp.json) com o servidor oficial [**@playwright/mcp**](https://playwright.dev/docs/getting-started-mcp) (Model Context Protocol). No **Cursor**: *Settings → MCP* — confirme que o servidor `playwright` aparece e está activo (pode ser necessário reabrir o workspace).

- Requer **Node.js 18+** (o Cursor executa `npx -y @playwright/mcp@latest` à primeira utilização).
- **Não substitui** a suite E2E (`cd frontend && npm run test:e2e` / `test:e2e:ci`); serve para o agente **navegar e inspeccionar** a UI com o motor Playwright (snapshots de acessibilidade, cliques, etc.).
- URLs típicas em dev (ver `docker-compose.yml`): API `http://127.0.0.1:60000`, Next no compose `http://127.0.0.1:60001`.

## Catálogo de perguntas (`perguntas_mvp.json`)

Ao alterar o JSON:

1. Rodar **`make test`** (há contrato JSON Schema automático — `tests/unit/infrastructure/test_perguntas_catalog_json_schema.py`).
2. Coordenar **bump** do campo **`versao_catalogo`** dentro do arquivo com código (`versao_catalogo_lida` / manifesto público).

Checklist obrigatório também no modelo de Pull Request ([PULL_REQUEST_TEMPLATE.md](.github/PULL_REQUEST_TEMPLATE.md)).
