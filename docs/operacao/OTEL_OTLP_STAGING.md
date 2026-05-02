# OpenTelemetry — export OTLP (M2)

## Ativar

| Variável | Exemplo | Descrição |
|----------|---------|-----------|
| `OTEL_TRACING_ENABLED` | `true` | Liga instrumentação FastAPI + exporter. |
| `OTEL_SERVICE_NAME` | `qualidiagiq-api` | Nome do serviço no collector. |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | `http://otel-collector:4318/v1/traces` | Endpoint **HTTP/protobuf** (sem OTLP gRPC neste MVP). |
| `OTEL_EXPORTER_OTLP_HEADERS` | `authorization=Bearer xxx` | Opcional; vários pares separados por vírgula. |

Se `OTEL_EXPORTER_OTLP_ENDPOINT` estiver vazio, os spans vão para **console** (desenvolvimento).

## Correlação HTTP

- Header `X-Trace-Id` continua sendo gerado/repassado pelo `TraceContextMiddleware`.
- Com OTEL ligado, o span ativo recebe o atributo `qualidiagiq.trace_id_http` após a requisição (facilita cruzar com logs).

## Smoke staging

1. Subir collector OTLP HTTP na mesma rede da API.
2. Definir `OTEL_TRACING_ENABLED=true` e `OTEL_EXPORTER_OTLP_ENDPOINT` apontando para `/v1/traces`.
3. `curl -sS http://127.0.0.1:<porta>/health` e verificar span recebido no backend do collector (Jaeger/Tempo/Datadog conforme o caso).
