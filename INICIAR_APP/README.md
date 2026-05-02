# INICIAR_APP — QualiDiagIQ

Scripts para **subir o ambiente Docker** e rodar a **bateria de QA** local (alinhado a `_DEVELOPER/PLANO_COMPLETO_HANDOFF.md`, §5).

## Qual script usar?

| Script | Quando usar |
|--------|----------------|
| **`iniciar.sh`** | Dia a dia com **feedback visual**: sobe o stack, testa `/health`, imprime URLs e fica em **`docker compose logs -f`**. **Ctrl+C = `compose down`** (para tudo). |
| **`iniciar-app.sh`** | **CLI completo**: `dev` / `stop` / `logs` / `status`, pipeline `deps` · `backend` · `integration` · `frontend` · `full`. **Ctrl+C em `logs`** só encerra o tail. |

Texto comum de URLs e dicas fica em **`lib/qdi-env.sh`** (uma única fonte).

```bash
chmod +x INICIAR_APP/iniciar.sh INICIAR_APP/iniciar-app.sh   # uma vez
./INICIAR_APP/iniciar-app.sh help
```

## Portas (host)

| Serviço | URL / porta |
|---------|-------------|
| API (Swagger) | http://127.0.0.1:60000/docs |
| Next.js | http://127.0.0.1:60001 (no container o Next escuta **3010**; mapa `60001:3010`) |
| Postgres | `postgresql://postgres:postgres@127.0.0.1:60322/postgres` |

No Compose, o browser fala com **`/api-backend/*`** no mesmo host (**proxy** no Next → API interna `api:8000`). Detalhes: `frontend/next.config.mjs`, `docker-compose.yml`.

## Comandos — `iniciar-app.sh`

### Docker

| Comando | Ação |
|---------|------|
| *(nenhum)* ou `dev` | `docker compose up -d --remove-orphans` |
| `stop` | `docker compose down` |
| `logs` | `docker compose logs -f` |
| `status` | `docker compose ps` |

### QA / pipeline

| Comando | Ação |
|---------|------|
| `deps` | `make install` + `npm ci` em `frontend/` |
| `backend` | `make qa-backend` |
| `integration` | `make ci-integration` (precisa `psql` + Postgres acessível) |
| `frontend` | `npm ci`, lint, Playwright E2E |
| `full` | Encadeia deps → backend → integration → frontend |

### Variáveis (`full` / integration)

| Variável | Efeito |
|----------|--------|
| `POSTGRES_CI_URL` | URL Postgres (default: compose `:60322`) |
| `SKIP_DEPS=1` | `full` sem instalar deps |
| `SKIP_INTEGRATION=1` | `full` sem integration |
| `SKIP_FRONTEND=1` | `full` sem E2E frontend |

Antes de `integration`: suba o DB (`./INICIAR_APP/iniciar-app.sh dev`) ou aponte `POSTGRES_CI_URL`.

## Pré-requisitos

| Ferramenta | Uso |
|------------|-----|
| Python **3.12** | CI / `make install` |
| Node **20+** | Frontend / Playwright |
| Docker | Stack db + api + web |
| `psql` | Obrigatório para `integration` |

## Makefile

- `make dev` / `make down` / `make logs` — equivalentes diretos ao Compose (os scripts chamam ou complementam isso).

## Testes manuais rápidos

```bash
curl -s http://127.0.0.1:60000/health
curl -s http://127.0.0.1:60000/diagnosticos/metodologia | head -c 200
```

No browser: http://127.0.0.1:60001/metodologia , `/wizard`, `/login`.
