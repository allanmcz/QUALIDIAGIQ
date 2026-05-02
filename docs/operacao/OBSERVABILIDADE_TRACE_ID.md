# Observabilidade — `X-Trace-Id` e OpenTelemetry (MVP)

## HTTP — correlacionamento imediato

**Middleware:** `src/presentation/api/middleware/trace_context.py`

- Cada resposta inclui header **`X-Trace-Id`** (UUID v4 gerado ou valor repassado pelo cliente em `X-Trace-Id`).
- Estado disponível em **`request.state.trace_id`** para extensão futura (ex.: structlog `bind_contextvars`).
- CORS: header permitido/exposto em `src/presentation/api/main.py`.

**Testes:** `tests/unit/presentation/test_api.py` (`test_healthcheck`, `test_healthcheck_repasse_x_trace_id`).

## OpenTelemetry (opcional)

- Ativação via settings: `OTEL_TRACING_ENABLED` + `otel_service_name` (vide `get_settings`).
- Instrumentação mínima em `create_app()` quando flag verdadeira (`FastAPIInstrumentor`).

## Próximo passo (pós-MVP imediato)

- Propagar `trace_id` para logs estruturados (`structlog`) em routers críticos.
- Exportador OTLP em produção (collector / SaaS APM) — definir na Fase G do plano de MVP.
