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
- **Dono do SLO (até ratificação formal):** equipa de operações do produto / Allan Marcio como PO técnico.
- **Error budget mensal:** 1 − disponibilidade alvo ⇒ 0,1 % do mês (~43 min) para indisponibilidade não planeadada da API pública; estourar o budget exige revisão de release e priorização de hardening.

## Referências

- `docs/operacao/SLO.md` (se existir conteúdo legado complementar)
- QDI-H-023 / QDI-H-024 — ratificação com Grafana.
