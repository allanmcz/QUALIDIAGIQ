# ADR-009 — `JWT_SECRET_KEY` como SecretStr e gate de produção

## Status

Aceito — Sprint 11 hardening.

## Contexto

Segredos em texto plano em memória/logging são vetor de vazamento; produção não pode aceitar URLs ou SMTP de desenvolvimento.

## Decisão

1. Modelar `jwt_secret_key` como `pydantic.SecretStr`.
2. Validadores `after` em `Settings`: mínimo 32 caracteres fora de `development`; em `production` exigir `https` no Supabase, chaves não vazias, `DATABASE_URL` definido e `SMTP_HOST` não local (`localhost`, `mailpit`, etc.).

## Consequências

- Todo uso da chave em `jwt.encode`/`decode` deve chamar `get_secret_value()`.
- Deploy incorreto falha cedo no startup (preferível a runtime silencioso).
