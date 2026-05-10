# Runbook — pg_cron e limpeza `idempotency_responses`

## Verificar se pg_cron está instalado

```sql
SELECT extname FROM pg_extension WHERE extname = 'pg_cron';
SELECT * FROM cron.job WHERE jobname = 'qdi-cleanup-idempotency';
```

Em imagens Docker sem pacote `pg_cron`, a migração **0032** apenas regista `NOTICE` e mantém a função SQL.

## Limpeza manual (SQL)

```sql
SELECT * FROM qdi_cleanup_idempotency();
```

Retorna `deleted_count` e `executed_at`.

## Endpoint HTTP (fallback)

Requer JWT com `perfil_conta` **admin** ou **avançado** e `DATABASE_URL` configurado.

```bash
curl -s -X POST "$API/admin/maintenance/cleanup-idempotency" \
  -H "Authorization: Bearer $TOKEN"
```

Rate-limit: **1 pedido / 5 minutos** por `tenant_id`.

## Ajustar intervalo do job

Com pg_cron disponível: remover job por `jobid` e voltar a agendar `cron.schedule(...)` com nova expressão cron (ex.: horaria).

## Troubleshooting

- **503 no endpoint:** API sem `DATABASE_URL` síncrono → configurar Postgres.
- **Primeiro DELETE grande:** pode demorar; considerar lotes futuros (`LIMIT` em subconsulta) se a tabela crescer para milhões de linhas.
