# ADR-008 — Rodadas bcrypt no login administrativo

## Status

Aceito — Sprint 11 hardening.

## Contexto

Hashes de senha administrativa devem resistir a brute-force offline sem degradar UX de login.

## Decisão

Usar `CryptContext` do Passlib com `bcrypt__rounds=12` no fluxo de autenticação da API (`auth_router`).

## Consequências

- Custo de CPU por login aumenta vs. rounds menores; aceitável para volume administrativo baixo.
- Manter `bcrypt<5` até migração coordenada do ecossistema Passlib.
