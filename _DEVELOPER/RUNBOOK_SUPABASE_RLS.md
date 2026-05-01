# Runbook — Postgres / Supabase e RLS (QDI)

## Princípios

1. **Multi-tenant primeiro:** toda linha sensível deve carregar `tenant_id` consistente com o JWT emitido pela API/auth.
2. **Defense-in-depth:** a FastAPI sempre filtra `tenant_id` nas queries de repositório, mesmo quando o cliente PostgREST respeita RLS.
3. **Trilha de evidência:** WORM/hash em diagnósticos finalizados (migrações `0005`, `0006` — revisar arquivo SQL antes de ambientes externos).

## Onde ler o que foi aplicado

- Esquema e tabelas: `src/infrastructure/db/migrations/0002_schema_core.sql`
- Políticas RLS: `0003_rls_policies.sql`
- Documentação só com COMMENT (sem mudança de comportamento): `0010_rls_comentarios_documentacao_m10.sql`

## Como aplicar migrações (Docker Compose local)

Na raiz do repo:

```bash
make migrate
```

Conectado ao container `db` usando `docker compose exec` (vide `Makefile`).

## Troubleshooting rápido

| Sintoma provável | O que verificar |
| ---------------- | --------------- |
| 401/403 no front com Supabase direto | Claim `tenant_id` ausente ou role errada (`authenticated`). |
| SELECT retorna dados de outro tenant | Falha gravíssima — política `diagnosticos_tenant_select`; rodar auditoria nos logs do PostgREST. |
| Ordenação estranha na lista B2B | `GET /diagnosticos/` usa `ORDER BY criado_em DESC` no adapter Python. |

## Analogia Delphi/Oracle

Imagine `qdi_jwt_tenant_id()` como uma sessão/contexto antes do `OPEN` da query (`DBMS_APPLICATION_INFO` ou pacote global), só que declarado explicitamente como função SECURITY DEFINER **não** — é `stable` sem elevação, confiável no PostgREST.
