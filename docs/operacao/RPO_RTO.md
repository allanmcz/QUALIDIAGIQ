# RPO / RTO / MTTR — QDI (MVP baseline)

> Metas de continuidade para **go-live público**. Ajustar após primeiro mês de operação real.

| Métrica | Valor MVP | Notas |
|---------|-----------|--------|
| **RPO** (Recovery Point Objective) | ≤ 24 h | Alinhado a backup diário documentado em `docs/operacao/BACKUP_E_DR.md` (Supabase). |
| **RTO** (Recovery Time Objective) | ≤ 4 h | Restore + smoke + comunicação interna. |
| **MTTR alvo** (incidente P1) | ≤ 2 h | Primeira resposta + mitigação inicial. |
| **MTBF mínimo aceitável** (P1) | ≥ 30 dias | Indicador de maturidade — rever trimestralmente. |

## Relação com SLO

- Disponibilidade e erros 5xx: ver `_DEVELOPER/DECISAO_EXTERNA/SLO_OPERACAO_QDI.md`.
- Rollback de aplicação: `docs/operacao/RUNBOOK_ROLLBACK_APLICACAO.md`.

## Ratificação

- **PO:** Allan Marcio — 2026-05-13
- **Ops:** Allan Marcio — 2026-05-13; substituto operacional `PENDENTE_ALLAN`
