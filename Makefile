# Makefile — atalhos de desenvolvimento QDI
.PHONY: help install dev down logs test lint format type-check clean migrate ci-integration frontend-init qa-backend openapi-export mvp-gate verify-schema-mvp verify-schema-mvp-strict

PYTHON := python3.12
VENV := .venv
PIP := $(VENV)/bin/pip

help: ## Mostra esta ajuda
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Cria .venv e instala dependências
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -e ".[dev]"
	@echo ""
	@echo "✅ Ambiente Python pronto. Ative com: source $(VENV)/bin/activate"

dev: ## Sobe ambiente de dev (db + api + web)
	docker compose up -d --remove-orphans
	@echo ""
	@echo "✅ Ambiente subindo:"
	@echo "  → API:  http://localhost:60000/docs (mapa host 60000 → container 8000)"
	@echo "  → Web:  http://localhost:60001 (mapa host 60001 → container 3010)"
	@echo "  → DB:   postgres://postgres:postgres@localhost:60322/postgres"
	@echo "  → Mailpit (SMTP OTP): API usa host mailpit:1025 · UI http://127.0.0.1:8025"
	@echo ""
	@echo "Logs:    make logs"
	@echo "Parar:   make down"

down: ## Para o ambiente de dev
	docker compose down

logs: ## Acompanha logs em tempo real
	docker compose logs -f

test: ## Roda todos os testes com cobertura
	PYTHONPATH=. $(VENV)/bin/pytest

test-watch: ## Roda testes em modo watch (precisa pytest-watch)
	PYTHONPATH=. $(VENV)/bin/pytest -f

lint: ## Lint com ruff
	$(VENV)/bin/ruff check src/ tests/ scripts/

format: ## Formata código com black + ruff
	$(VENV)/bin/black src/ tests/ scripts/
	$(VENV)/bin/ruff check --fix src/ tests/ scripts/

type-check: ## Type checking com mypy
	$(VENV)/bin/mypy src/

qa-backend: ## Gate backend: ruff + mypy + pytest (equiv. Seção 5.1 do PLANO_COMPLETO_HANDOFF)
	$(VENV)/bin/ruff check src/ tests/ scripts/
	$(VENV)/bin/mypy src/
	PYTHONPATH=. $(VENV)/bin/pytest

mvp-gate: ## Subconjunto checklist MVP: smoke API + schema 0012 + RLS dois tenants (precisa Postgres)
	PYTHONPATH=. $(VENV)/bin/pytest tests/integration/test_smoke_mvp_fechado_api.py tests/integration/test_mvp_gate_postgres.py -q --no-cov

verify-schema-mvp: ## Verifica 0012/M11 + RLS no Postgres (DATABASE_URL ou QDI_POSTGRES_TEST_URL; default local :60322)
	@export QDI_POSTGRES_TEST_URL="$${QDI_POSTGRES_TEST_URL:-postgresql://postgres:postgres@127.0.0.1:60322/postgres}"; \
	$(VENV)/bin/python scripts/verify_mvp_schema.py

verify-schema-mvp-strict: ## Como verify-schema-mvp + CNAE 0013/0014 (1332 subclasses, extensões pg_trgm/pgcrypto)
	@export QDI_POSTGRES_TEST_URL="$${QDI_POSTGRES_TEST_URL:-postgresql://postgres:postgres@127.0.0.1:60322/postgres}"; \
	QDI_VERIFY_SCHEMA_STRICT_CNAE=1 $(VENV)/bin/python scripts/verify_mvp_schema.py

openapi-export: ## Gera docs/api/openapi.generated.json a partir do schema FastAPI (gitignored)
	PYTHONPATH=. $(VENV)/bin/python scripts/export_openapi_json.py

clean: ## Limpa arquivos gerados
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/ .coverage build/ dist/

migrate: ## Aplica SQL em src/infrastructure/db/migrations na instância docker compose (DB já existente)
	@set -e; for f in $$(ls src/infrastructure/db/migrations/*.sql | sort); do \
	  echo "migrate: $$f"; \
	  docker compose exec -T db psql -U postgres -d postgres -v ON_ERROR_STOP=1 < "$$f"; \
	done
	@echo "✅ Migrações aplicadas."

ci-integration: ## Espelho local do CI: migra Postgres + pytest integration (analise ANALISE §B)
	@if ! command -v psql >/dev/null 2>&1; then echo "Instale postgresql-client (psql)."; exit 1; fi
	@if [ -z "$$POSTGRES_CI_URL" ]; then \
	  echo "Defina POSTGRES_CI_URL, ex.: postgresql://postgres:postgres@127.0.0.1:60322/postgres"; exit 1; \
	fi
	@set -e; for f in $$(ls src/infrastructure/db/migrations/*.sql | sort); do \
	  echo "ci-integration migrate: $$f"; \
	  psql "$$POSTGRES_CI_URL" -v ON_ERROR_STOP=1 -f "$$f"; \
	done
	QDI_POSTGRES_TEST_URL=$$POSTGRES_CI_URL PYTHONPATH=. $(VENV)/bin/pytest tests/integration/

frontend-init: ## Inicializa o frontend Next.js (executar uma vez)
	cd frontend && npx create-next-app@14 . --ts --tailwind --app --eslint --no-src-dir
	cd frontend && npm install @anthropic-ai/sdk lucide-react @radix-ui/react-progress recharts

all: install dev ## Setup completo + sobe ambiente
