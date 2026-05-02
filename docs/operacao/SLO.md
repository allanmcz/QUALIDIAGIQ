# SLO operacional — QDI (rascunho MVP)

Objetivos preliminares para alinhamento com observabilidade (OpenTelemetry + logs estruturados).

| Indicador | Alvo MVP | Medição |
|-----------|----------|---------|
| Disponibilidade API `/health` | 99,5% mensal | probes + uptime externo |
| Latência p95 `POST /diagnosticos/` | &lt; 8 s (sem PDF) | métricas OTel |
| Taxa de erro 5xx | &lt; 0,5% | Sentry + gateway |

Revisar após primeiros clientes pagantes e dimensionamento do cluster.
