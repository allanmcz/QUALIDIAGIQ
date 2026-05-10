# Instruções — diff OpenAPI (`/docs`)

Objetivo do roadmap **R2:** evidenciar que o refactor do `diagnostico_router` não alterou paths/métodos sem documentar.

## Contrato versionado no repositório (preferido)

O ficheiro **`docs/api/openapi.generated.json`** é gerado offline a partir do schema FastAPI (sem servidor HTTP):

Regressão de **paths** críticos (LGPD, retificações, públicos): `tests/unit/presentation/test_openapi_generated_contract.py`.

```bash
make openapi-export
# ou: PYTHONPATH=. python scripts/export_openapi_json.py
```

Após alterar routers ou schemas Pydantic expostos na API, regenere e inclua o diff no PR. O **CI** (`backend` job) falha se o ficheiro commitado divergir da exportação atual (`git diff`).

## Gerar snapshot contra API em execução (opcional)

Com API a correr (ex. `http://127.0.0.1:8765`):

```bash
curl -sS "http://127.0.0.1:8765/openapi.json" | jq . > /tmp/qdi-openapi-$(date +%Y%m%d).json
```

Compare com o artefacto versionado ou com snapshot anterior:

```bash
diff -u docs/api/openapi.generated.json /tmp/qdi-openapi-$(date +%Y%m%d).json | head -200
```

## Artefacto legado `_artefactos`

Opcionalmente guardar `docs/operacao/_artefactos/openapi_ref.json` **sem segredos** (apenas contrato). Criar pasta `_artefactos` só se a equipa quiser snapshots adicionais além de `docs/api/openapi.generated.json`.
