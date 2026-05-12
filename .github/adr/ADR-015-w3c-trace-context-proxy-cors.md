# ADR-015 — Propagação W3C Trace Context (traceparent / tracestate)

Data: 2026-05-11  
Estado: **aceite**

## Contexto

Correlação entre browser, BFF Next.js e API FastAPI deve alinhar-se ao padrão **W3C Trace Context** (cabeçalhos `traceparent`, `tracestate`) para encaixar em exportadores **OpenTelemetry** e dashboards (Grafana, etc.).

## Decisão

1. O **proxy** `frontend/app/api-backend/[[...slug]]/route.ts` **repassa** `traceparent` e `tracestate` do pedido recebido para o backend, quando existirem.
2. A API inclui estes cabeçalhos na lista **CORS** (`allow_headers`) em `src/presentation/api/main.py`, mantendo lista explícita (anti-padrão S-05).

## Consequências

- Clientes sem estes cabeçalhos continuam a usar `X-Trace-Id` gerado no middleware.
- Instrumentação OTLP na API permanece conforme `docs/operacao/OTEL_QUICKSTART_LOCAL.md`.

## Referências

- [W3C Trace Context](https://www.w3.org/TR/trace-context/)
- `docs/operacao/EVENTOS_NEGOCIO_LOGS.md`
