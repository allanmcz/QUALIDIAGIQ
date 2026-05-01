# Notas sobre os arquivos brutos da API

| Arquivo | Origem | Descrição |
|---|---|---|
| `openapi.json` | `https://consumo.tributos.gov.br/servico/calcular-tributos-consumo/api/api-docs` | **Spec OpenAPI 3.1.0 oficial e válida** — usar este como fonte de verdade |
| `swagger-config.json` | `/api/api-docs/swagger-config` | Config consumida pelo Swagger UI |
| `swagger-ui.html` | `/api/swagger-ui/index.html` | Shell HTML do Swagger UI (renderiza `openapi.json`) |
| `swagger-initializer.js` | `/api/swagger-ui/swagger-initializer.js` | Bootstrap JS do Swagger UI |
| `openapi-v3.json` | `https://consumo.tributos.gov.br:18018/.../api-docs` | ⚠️ **Conteúdo HTML — ignorar.** O caminho `:18018` retorna o app Angular (não a spec). Marcado para limpeza no `cleanup_final.sh`. |

> **Observação importante:** o caminho `/v3/api-docs` (padrão Springdoc clássico) **retorna 404 nesta API**. Use sempre `/api/api-docs`.

## Como recarregar a spec a qualquer momento

```bash
curl -sS -o openapi.json \
  "https://consumo.tributos.gov.br/servico/calcular-tributos-consumo/api/api-docs"

# Validação rápida
python3 -c "import json; d=json.load(open('openapi.json')); print('paths:', len(d['paths']))"
```

## Regenerar Pydantic models a partir da spec

```bash
pip install datamodel-code-generator
datamodel-codegen \
  --input openapi.json \
  --input-file-type openapi \
  --output ../clients/python/dto_generated.py \
  --output-model-type pydantic_v2.BaseModel \
  --use-schema-description \
  --target-python-version 3.11
```

## Regenerar client TypeScript a partir da spec

```bash
npm install -g openapi-zod-client
openapi-zod-client openapi.json -o ../clients/typescript/dto-generated.ts
```
