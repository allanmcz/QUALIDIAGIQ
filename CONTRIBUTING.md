# Contribuição — QualiDiagIQ

## Requisitos rápidos

- Python 3.12, `make install`, comandos `.cursorrules` (`make lint`, `make format`, `make test`, `make type-check`).
- ADRs novos em [.github/adr/](.github/adr/).

## Catálogo de perguntas (`perguntas_mvp.json`)

Ao alterar o JSON:

1. Rodar **`make test`** (há contrato JSON Schema automático — `tests/unit/infrastructure/test_perguntas_catalog_json_schema.py`).
2. Coordenar **bump** do campo **`versao_catalogo`** dentro do arquivo com código (`versao_catalogo_lida` / manifesto público).

Checklist obrigatório também no modelo de Pull Request ([PULL_REQUEST_TEMPLATE.md](.github/PULL_REQUEST_TEMPLATE.md)).
