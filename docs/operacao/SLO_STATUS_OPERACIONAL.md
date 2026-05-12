# SLO / status operacional — QualiDiagIQ (MVP)

> Valores iniciais; ajustar com métricas reais (Grafana / Supabase observability).

## Disponibilidade API

| SLO | Meta MVP | Medição |
|-----|----------|---------|
| Disponibilidade mensal | 99,0 % | `/health/live` + uptime externo |

## Latência p95 (API)

| Endpoint (exemplo) | Meta MVP |
|----------------------|----------|
| GET `/health/live` | < 100 ms |
| POST `/auth/login` | < 800 ms |

## Erro orçamento

- Incidentes P0: comunicação imediata stakeholders + post-mortem em 5 dias úteis.
