# INICIAR_APP — QualiDiagIQ

Scripts e instruções para **subir ambiente** e rodar a **bateria de testes** descrita no `_DEVELOPER/PLANO_COMPLETO_HANDOFF.md` (Seção 5).

## Pré-requisitos

| Ferramenta | Uso |
|------------|-----|
| Python **3.12** | Alinhado ao CI (`.github/workflows/ci.yml`). |
| Node **20+** | Frontend / Playwright. |
| Docker | `make dev` — DB na porta **60322**, API **60000**, Web **60001** (ver `docker-compose.yml`). |
| `psql` | Cliente PostgreSQL — obrigatório para `integration` / `ci-integration`. |

## URL do compose (host)

| Serviço | URL |
|---------|-----|
| API Swagger | http://localhost:60000/docs |
| Next.js | http://localhost:60001 |
| Postgres | `postgresql://postgres:postgres@127.0.0.1:60322/postgres` |

O frontend usa por padrão `NEXT_PUBLIC_API_URL=http://localhost:60000` — ver `frontend/lib/api/config.ts` e `frontend/.env.example`.

## Script principal

```bash
chmod +x INICIAR_APP/iniciar-app.sh   # uma vez
./INICIAR_APP/iniciar-app.sh help
```

### Comandos

| Comando | O que faz |
|---------|-----------|
| `deps` | `make install` + `npm ci` no `frontend/`. |
| `backend` | `make qa-backend` → ruff + mypy + pytest (toda a suíte Python). |
| `integration` | Aplica migrações SQL na ordem lexical e roda **apenas** `tests/integration/` (`POSTGRES_CI_URL` configurável). |
| `frontend` | `npm ci`, ESLint, instala Chromium do Playwright, `npm run test:e2e`. |
| `dev` | `docker compose up -d`. |
| `stop` | `docker compose down`. |
| `full` | Encadeia `deps` → `backend` → `integration` → `frontend` (use skips abaixo). |

### Variáveis de ambiente (opcional)

| Variável | Efeito |
|----------|--------|
| `POSTGRES_CI_URL` | URL do Postgres para integração (default: mesma do compose na porta 60322). |
| `SKIP_DEPS=1` | No `full`, não roda instalação de deps. |
| `SKIP_INTEGRATION=1` | No `full`, não roda migrações + integration tests. |
| `SKIP_FRONTEND=1` | No `full`, não roda lint/E2E do Next. |

**Antes de `integration`:** suba o banco (`./INICIAR_APP/iniciar-app.sh dev` e aguarde o healthcheck) ou aponte `POSTGRES_CI_URL` para uma instância acessível.

## Equivalência com Makefile

- `make qa-backend` = Seção **5.1** do plano (lint + mypy + test).
- `make ci-integration` = Seção **5.2** (com `POSTGRES_CI_URL` definido).

## Testes manuais (Seção 6 do plano)

Com API e web no ar: `/docs`, `/wizard`, `/login`, fluxo dashboard — checklist em `PLANO_COMPLETO_HANDOFF.md`.
