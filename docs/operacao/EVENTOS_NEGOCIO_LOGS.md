# Eventos de negócio e correlação (logs)

## Identificador de pedido

- Header **`X-Trace-Id`** (middleware `trace_context`) — propagado para logs estruturados da API.
- Clientes podem enviar valor externo; caso contrário o servidor gera UUID.

## Eventos recomendados (nível `info` / `warning`)

| Área | Evento (chave sugerida) | Quando |
|------|-------------------------|--------|
| Auth | `auth_login_sucesso` / falha | POST `/auth/login` |
| Diagnóstico | `diagnostico_criado`, `diagnostico_finalizado` | POST/PATCH fluxos principais |
| PDF | `pdf_geracao_ok` / `pdf_geracao_falhou` | Geração WeasyPrint |
| Mutação | `diagnostico_mutacao_audit_gravada` | Auditoria pós-mutação (migração 0026) |

Adapters **devem** usar **`structlog`** — ver `.cursorrules` anti-padrão S-06 (`print` em API).

## OpenTelemetry

Guia local: `docs/operacao/OTEL_QUICKSTART_LOCAL.md`. Variáveis: `OTEL_TRACING_ENABLED`, `OTEL_EXPORTER_OTLP_ENDPOINT`, etc. — `README.md` raiz.

## Propagação W3C Trace Context (QDI-H-008)

- O proxy Next (`frontend/app/api-backend/[[...slug]]/route.ts`) repassa **`traceparent`** e **`tracestate`** para a API quando presentes no pedido do browser.
- A API aceita estes cabeçalhos no CORS (`src/presentation/api/main.py`) para permitir correlação ponta-a-ponta com exportadores OTLP.
