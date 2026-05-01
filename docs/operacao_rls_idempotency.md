# Operação: RLS multi-tenant e tabela `idempotency_responses` (M10)

## Contexto

- **Diagnósticos** e demais entidades de negócio usam **RLS** no PostgreSQL com `tenant_id` derivado do JWT (ver migrações `0002`/`0003`).
- A tabela **`idempotency_responses`** (`0007`) armazena respostas cacheadas do **POST `/diagnosticos/`** para garantir **idempotência** entre restarts (LC 214/2025 — previsibilidade operacional).

## Decisão (N6)

1. **Não aplicar RLS por `tenant_id` em `idempotency_responses` na forma atual**, porque:
   - A chave primária é **`chave_hash`** (global), não há coluna `tenant_id`.
   - O hash já incorpora o header **`Authorization`** no middleware; requisições de tenants distintos geram hashes distintos mesmo com a mesma `Idempotency-Key` literal.

2. **Risco residual:** qualquer principal com acesso direto ao role do banco que ignore RLS nas outras tabelas ainda enxerga **metadados de cache** (status, timestamps). Mitigação em produção: credenciais restritas, VPC, auditoria.

3. **Evolução opcional:** introduzir `tenant_id UUID` + RLS na tabela de idempotência **somente se** houver requisito explícito de políticas por tenant no storage físico; exigiria migração de chave composta `(tenant_id, chave_hash)` e ajuste do middleware.

## Referências no repositório

- Middleware: `src/presentation/api/middleware/idempotency.py`
- Migração DDL: `src/infrastructure/db/migrations/0007_idempotency_responses.sql`
- Comentários Postgres: `0008_idempotency_comentarios_operacao.sql`
