# Contribuição — QualiDiagIQ

## Requisitos rápidos

- Python 3.12, `make install`, comandos `.cursorrules` (`make lint`, `make format`, `make test`, `make type-check`).
- **Bateria de QA em um fluxo:** `make qa-backend` ou `./INICIAR_APP/iniciar-app.sh backend` — ver [INICIAR_APP/README.md](INICIAR_APP/README.md).
- ADRs novos em [.github/adr/](.github/adr/).

## Catálogo de perguntas (`perguntas_mvp.json`)

Ao alterar o JSON:

1. Rodar **`make test`** (há contrato JSON Schema automático — `tests/unit/infrastructure/test_perguntas_catalog_json_schema.py`).
2. Coordenar **bump** do campo **`versao_catalogo`** dentro do arquivo com código (`versao_catalogo_lida` / manifesto público).

Checklist obrigatório também no modelo de Pull Request ([PULL_REQUEST_TEMPLATE.md](.github/PULL_REQUEST_TEMPLATE.md)).
