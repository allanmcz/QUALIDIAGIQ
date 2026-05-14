# Gate técnico único — go-live QDI

> Implementação alinhada a `_DEVELOPER/ANALISE_13052026_CODEX/10_PROMPT_CURSOR_IMPLEMENTACAO.md` (Etapa 2).

## Comando

Na raiz do repositório:

```bash
make go-live-tecnico
```

Equivalente:

```bash
bash scripts/go_live_tecnico.sh
```

## O que valida

| Passo | Descrição |
|-------|-----------|
| T1 | `make lint` — ruff em `src/`, `tests/`, `scripts/` |
| T2 | `make type-check` — mypy strict em `src/` |
| T3 | `cd frontend && npm run test:unit` |
| T4 | `cd frontend && npx tsc --noEmit` |
| T5 | `cd frontend && npm run build` |
| T6 | `make audit-secrets` — heurística S-01 (`scripts/audit_secrets.sh`) |
| T7 | `make mvp-gate` — smoke API + schema + **RLS dois tenants**, **só** se o TCP ao Postgres de teste responder |

## Postgres e RLS

- URL por defeito: `postgresql://postgres:postgres@127.0.0.1:60322/postgres` (mapa típico `make dev`).
- Personalizar: `export QDI_POSTGRES_TEST_URL=...` antes de `make go-live-tecnico`.
- Se a porta **não** estiver a escutar, o script **imprime** instruções (`make dev`, `make migrate`, `make mvp-gate`) e termina com **exit 0** (não bloqueia máquinas sem Docker).
- Para **falhar** explicitamente sem Postgres (ex.: CI que esqueceu o serviço): `QDI_GO_LIVE_TECNICO_REQUIRE_POSTGRES=1 make go-live-tecnico`.
- Para **omitir** o passo MVP mesmo com Postgres: `QDI_GO_LIVE_TECNICO_SKIP_MVP_GATE=1 make go-live-tecnico`.

## Relação com `make go-live`

- `make go-live` / `scripts/go_live_45min.sh` — pré-voo alargado (OpenAPI drift, health, endpoints públicos, opcional E2E).
- `make go-live-tecnico` — foco em **qualidade de código** e **gate MVP/RLS** quando o ambiente permite.

## Segurança

O script **não** executa `git commit`, `git push`, `git rebase`, nem comandos destrutivos sobre dados.
