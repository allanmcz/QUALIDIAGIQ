# INICIAR_APP — QualiDiagIQ

Scripts para **subir o ambiente Docker** e rodar a **bateria de QA** local (alinhado a `_DEVELOPER/PLANO_COMPLETO_HANDOFF.md`, §5).

## Qual script usar?

| Script | Quando usar |
|--------|----------------|
| **`iniciar.sh`** | Dia a dia com **feedback visual**: chama **`make dev`** (Compose `up -d --build`, igual ao `iniciar-app.sh dev`), testa `/health`, imprime URLs e fica em **`docker compose logs -f`**. **Ctrl+C = `compose down`** (para tudo). |
| **`iniciar-app.sh`** | **CLI completo**: `dev` / `stop` / `logs` / `status`, pipeline `deps` · `backend` · `integration` · `frontend` · `full`. **Ctrl+C em `logs`** só encerra o tail. |
| **`parar-app.sh`** | **Só parar o Docker**: `docker compose down` na raiz do repo (atalho explícito; mesmo efeito que `make down` ou `iniciar-app.sh stop`). Opção `-v` remove volumes (zera Postgres local). |

Texto comum de URLs e dicas fica em **`lib/qdi-env.sh`** (uma única fonte).

```bash
chmod +x INICIAR_APP/iniciar.sh INICIAR_APP/iniciar-app.sh INICIAR_APP/parar-app.sh   # uma vez
./INICIAR_APP/iniciar-app.sh help
./INICIAR_APP/parar-app.sh          # encerra stack
```

## Portas (host)

| Serviço | URL / porta |
|---------|-------------|
| API (Swagger) | http://127.0.0.1:60000/docs |
| Next.js | http://127.0.0.1:60001 (no container o Next escuta **3010**; mapa `60001:3010`) |
| Postgres | `postgresql://postgres:postgres@127.0.0.1:60322/postgres` |
| Mailpit (OTP dev) | UI http://127.0.0.1:8025 · SMTP interno `mailpit:1025` |

No Compose, o browser fala com **`/api-backend/*`** no mesmo host (**Route Handler** em `frontend/app/api-backend/[[...slug]]/route.ts` → API interna `api:8000` via `API_PROXY_TARGET`). Detalhes: `docker-compose.yml`.

### Variáveis no `.env` da raiz (opcional)

O Docker Compose **lê automaticamente** o arquivo `.env` na raiz do repositório para interpolar `${VAR}` em `docker-compose.yml` (não confundir com `frontend/.env.local`).

| Variável | Efeito típico |
|----------|----------------|
| `DATABASE_URL` | No Compose (default), a API grava **diagnósticos** na tabela `diagnosticos` do **PostgreSQL** (`PostgresDiagnosticoRepository`). Sem DSN e sem Supabase real, use o modo CI em memória só em cenários de teste sem banco. |
| `QDI_CI_PLAYWRIGHT_INTEGRATED` | Default **`1`**: suíte E2E integrada + login em `admins` no Postgres; **com `DATABASE_URL`**, diagnósticos vão para o mesmo Postgres (não ficam só em memória). Use **`0`** + `SUPABASE_*` se quiser persistir diagnósticos via PostgREST **sem** DSN local. |
| `SUPABASE_URL` / `SUPABASE_ANON_KEY` | Sobrescrevem os placeholders do compose quando você usa projeto Supabase (tipicamente com `QDI_CI_PLAYWRIGHT_INTEGRATED=0` e sem depender do Postgres local para diagnósticos). |
| `JWT_SECRET_KEY` | Default de desenvolvimento no compose; defina uma chave forte em ambientes compartilhados. |
| `QDI_SELF_SERVICE_TENANT_ID` | Tenant UUID do fluxo OTP → `/diagnosticos/self-service` (default alinhado ao backend). |

## Comandos — `iniciar-app.sh`

### Docker

| Comando | Ação |
|---------|------|
| *(nenhum)* ou `dev` | `docker compose up -d --build --remove-orphans` (reconstrói imagens quando o contexto de build mudou; evita API com deps antigas do `pyproject.toml`) |
| `stop` | `docker compose down` (atalho dedicado: **`./INICIAR_APP/parar-app.sh`**) |
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

### Docker parado no Mac

`make dev`, `./INICIAR_APP/iniciar-app.sh dev` e `./INICIAR_APP/iniciar.sh` chamam **`qdi_ensure_docker_daemon`** (`lib/qdi-env.sh`): se o motor não estiver ativo, abrem **OrbStack** (se existir) ou **Docker Desktop** e aguardam até **90s** (`QDI_DOCKER_START_TIMEOUT_SEC` para alterar). Na primeira vez após reiniciar o Mac, o arranque do motor pode levar ~30–60s.

## Makefile

- `make dev` — `docker compose up -d --build --remove-orphans` (usado por **`iniciar.sh`** e espelhado por **`iniciar-app.sh dev`**).
- `make down` — igual a `./INICIAR_APP/parar-app.sh` (sem apagar volumes).
- `make logs` — equivalente direto ao Compose.

## Testes manuais rápidos

```bash
curl -s http://127.0.0.1:60000/health
curl -s http://127.0.0.1:60000/diagnosticos/metodologia | head -c 200
```

No browser: http://127.0.0.1:60001/metodologia , `/wizard`, `/login`.
