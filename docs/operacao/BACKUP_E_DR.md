# Backup e disaster recovery (DR) — QualiDiagIQ

> QDI-H-025 — visão DR + RTO/RPO; detalhe operacional de backup em `docs/operacao/BACKUP_RECUPERACAO.md`.

## Objetivos

| Métrica | Alvo MVP (orientador) | Dono (até ratificação) |
|---------|------------------------|-------------------------|
| **RPO** | ≤ 24 h | Operações / fornecedor cloud |
| **RTO** | ≤ 4 h | Operações |

## Procedimento resumido (DR)

1. **Detetar** incidente (indisponibilidade API, corrupção de dados, região cloud fora).
2. **Isolar** escrita (feature flag / manutenção) conforme `docs/operacao/RUNBOOK_DEPLOY_ROLLBACK.md`.
3. **Restaurar** Postgres a partir do último backup consistente (PITR Supabase ou snapshot Docker em dev).
4. **Validar** `/health/ready`, smoke `make go-live` em staging (QDI-H-033).
5. **Comunicar** stakeholders e registar post-mortem.

## Teste de restauro

- **Frequência mínima:** semestral em ambiente não produtivo.
- **Evidência:** ticket interno com data e resultado.

## Referência cruzada

- `docs/operacao/BACKUP_RECUPERACAO.md` — escopo técnico Postgres / artefactos.
