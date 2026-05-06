# ADR-010 — Hash de senha Argon2id (substitui passlib/bcrypt como caminho principal)

| Campo | Valor |
|-------|-------|
| **Status** | Aceito |
| **Data** | 2026-05-04 |
| **Decisor** | Allan Marcio |
| **Tags** | segurança, autenticação, LGPD art. 46 |

## Contexto

O projeto documentava risco de **`passlib` 1.7.4** com **bcrypt 5.x** (`verify()` podendo falhar de forma não tratada).  
Simultaneamente, **Argon2id** é o consenso atual (OWASP 2025 / RFC 9106) para armazenamento de senhas em aplicações novas.

## Decisão

1. Adotar **Argon2id** via **`argon2-cffi`** para **novos** hashes (`gerar_hash_senha`).
2. Manter **`bcrypt.checkpw`** apenas para **verificação** de hashes já persistidos (coluna `hash_algoritmo = bcrypt`).
3. Implementar **rehash gradual**: no primeiro login bem-sucedido com bcrypt (ou Argon2 com parâmetros obsoletos), persistir novo hash Argon2id e atualizar `hash_algoritmo`.
4. Nova coluna **`admins.hash_algoritmo`** (`varchar(16)`, default `bcrypt` para linhas legadas).

## Parâmetros Argon2id

- `time_cost=2`, `memory_cost=64 MiB`, `parallelism=2`, `hash_len=32`, `salt_len=16`.

## Alternativas consideradas

| Alternativa | Motivo de não adoção como principal |
|-------------|-------------------------------------|
| Manter só bcrypt + passlib | Manutenção passlib incerta; risco de runtime com bcrypt 5.x. |
| scrypt | Menos padronização em stacks Python corporativas. |

## Consequências

### Positivas

- Caminho de hash estável sem passlib no caminho quente de login.
- Migração sem logout forçado nem reset em massa.

### Negativas

- Dependência dupla temporária (`argon2-cffi` + `bcrypt`) até encerrar janela de migração.
- Strings Argon2id mais longas que bcrypt — coluna `hashed_password` permanece `VARCHAR(255)` (suficiente para PHC padrão).

## Implementação

- Módulo `src/infrastructure/auth/password_hashing.py`
- Migration `0028_admins_hash_algoritmo.sql`
- Rotas `POST /auth/login` e cadastro atualizados (`auth_router.py`)

## Revisão sugerida

Após ~90 dias em produção: relatório de admins ainda com `hash_algoritmo = bcrypt`; política de remoção da dependência `bcrypt` se residual zero.

## Referências

- [RFC 9106 — Argon2](https://datatracker.ietf.org/doc/html/rfc9106)
- [OWASP Password Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)
