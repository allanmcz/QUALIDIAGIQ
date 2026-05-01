# Runbook — Postgres síncrono e idempotência (CI / Ops)

Este arquivo **é versionado** (pasta `_DEVELOPER/` e `docs/` podem estar no `.gitignore` localmente).

## Variável `DATABASE_URL` (sync SQLAlchemy)

- `IdempotencyMiddleware` quando habilitado com URL síncrono usa **SQLAlchemy** + Postgres.
- Produção/HML: garantir mesmo valor que o Postgres acessível pelo processo FastAPI (**não** use `asyncpg` aqui — engine é síncrono).
- Se vazio em dev: apenas cache TTL em memória continua válido para testes de unidade isolados.

## URL usada pelo teste WORM integration

`tests/integration/test_worm_postgres.py` lê **`QDI_POSTGRES_TEST_URL`**, default  
`postgresql://postgres:postgres@127.0.0.1:60322/postgres` (porta Compose QDI típica).

GitHub Actions: ver workflow `ci.yml` — serviço `postgres` + mesma URL em `5432`.

## Comando local rápido (espelhar CI backend)

Ver alvo **`make ci-integration`** no `Makefile` (exportar `POSTGRES_CI_URL`).
