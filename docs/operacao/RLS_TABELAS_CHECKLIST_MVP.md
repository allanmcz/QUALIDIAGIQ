# Checklist RLS — esquema `qdi` e tabelas relacionadas (MVP)

> **Objetivo:** mapa de leitura para políticas **SELECT / INSERT / UPDATE** alinhado às migrações principais (`0003`, `0019`, `0025`, `0026`).  
> **Nota:** políticas exactas estão nos ficheiros SQL em `src/infrastructure/db/migrations/` — este documento é índice humano, não substitui o DDL.

## Núcleo diagnóstico

| Tabela / recurso | Migração de referência | Notas |
|------------------|------------------------|-------|
| `qdi.diagnosticos` | `0002`, `0003`, WORM `0012` | Multi-tenant por `tenant_id`; finalizado imutável conforme regras WORM |
| `qdi.diagnostico_*` (rascunhos, leitura pública, etc.) | `0023`, `0024`, … | Ver migrações `002x` |
| `qdi.checklist_m12_autoconf` / colunas M12 | `0011` | |
| `public.idempotency_responses` | `0007`, `0019` | `tenant_id` NOT NULL; RLS alinhado admin |

## Operação e auditoria

| Tabela | Migração | Notas |
|--------|----------|-------|
| `qdi.diagnostico_mutacao_audit` | `0026` | Append-only auditoria de mutações |

## Verificação automatizada

- `make mvp-gate` / `tests/integration/test_mvp_gate_postgres.py` — isolamento dois tenants.
- `make verify-schema-mvp` / `verify-schema-mvp-strict` — colunas e presença de políticas esperadas no script.

Runbook cloud: `_DEVELOPER/RUNBOOK_SUPABASE_RLS.md`.
