# Instruções — diff OpenAPI (`/docs`)

Objetivo do roadmap **R2:** evidenciar que o refactor do `diagnostico_router` não alterou paths/métodos sem documentar.

## Gerar snapshot local

Com API a correr (ex. `http://127.0.0.1:8765`):

```bash
curl -sS "http://127.0.0.1:8765/openapi.json" | jq . > /tmp/qdi-openapi-$(date +%Y%m%d).json
```

Compare com snapshot anterior:

```bash
diff -u docs/operacao/_artefactos/openapi_ref.json /tmp/qdi-openapi-$(date +%Y%m%d).json | head -200
```

## Artefacto de referência

Opcionalmente guardar `docs/operacao/_artefactos/openapi_ref.json` **sem segredos** (apenas contrato). Criar pasta `_artefactos` só se o equipa quiser versionar snapshots.
