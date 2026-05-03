# OpenTelemetry — arranque rápido (local)

Objetivo: ligar **traços OTLP/HTTP** da API QDI a um **collector** ou **Jaeger/Tempo** sem alterar código (só variáveis de ambiente).

## Variáveis (API)

| Variável | Exemplo | Efeito |
|----------|---------|--------|
| `OTEL_TRACING_ENABLED` | `true` | Ativa instrumentação no lifespan da app (`main.py`). |
| `OTEL_SERVICE_NAME` | `qualidiagiq-api` | Nome do serviço no trace. |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | `http://127.0.0.1:4318` | Base URL do exporter OTLP (**HTTP**, porta típica **4318**). |
| `OTEL_EXPORTER_OTLP_HEADERS` | `api-key=xxx` | Opcional — headers CSV para SaaS (Datadog, Honeycomb, etc.). |

Configuração lida em `src/infrastructure/config/settings.py` (Pydantic).

## Passo a passo mínimo (Mac / Linux)

1. Suba um collector OTLP na porta **4318** (ex.: [OpenTelemetry Collector](https://opentelemetry.io/docs/collector/) ou stack de dev que exponha `/v1/traces`).
2. No `.env` da API (ou `docker-compose`):

   ```bash
   OTEL_TRACING_ENABLED=true
   OTEL_SERVICE_NAME=qualidiagiq-api
   OTEL_EXPORTER_OTLP_ENDPOINT=http://host.docker.internal:4318
   ```

   Se a API corre **dentro do Docker** e o collector no **host**, use `host.docker.internal` (já padrão em muitos compose QDI).

3. Reinicie a API e faça pedidos (`GET /health`, fluxo wizard). Verifique spans no backend do collector/UI.

## Referências

- README raiz do repositório — secção OpenTelemetry.
- `docs/operacao/RUNBOOK_DEPLOY_ROLLBACK.md` — pré-deploy.
