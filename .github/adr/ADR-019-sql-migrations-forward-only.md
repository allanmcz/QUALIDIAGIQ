# ADR-019 — Migrações SQL: forward-only e ordem canónica

Data: 2026-05-11  
Estado: **aceite** (QDI-H-027)

## Contexto

O QDI versiona DDL em `src/infrastructure/db/migrations/*.sql` aplicadas em ordem lexical (`make migrate`, `init.sql` no Docker).

## Decisão

1. **Forward-only:** não editar migrações já aplicadas em ambientes partilhados; correções ⇒ **novo** ficheiro sequencial (ex.: `0041_...sql`).
2. **Idempotência:** preferir `IF NOT EXISTS`, `DROP IF EXISTS` apenas quando seguro para reexecução em dev.
3. **Bootstrap Docker:** `init.sql` deve listar **todas** as migrações até à última, para volumes novos consistentes.

## Consequências

- Rollback de schema = **nova** migração compensatória ou restore a partir de backup (**BACKUP_E_DR.md**).
- CI / dev devem falhar cedo se ordem ou nomes quebrarem o pipeline.

## Referências

- `Makefile` alvo `migrate`
- `docs/operacao/BACKUP_E_DR.md`
