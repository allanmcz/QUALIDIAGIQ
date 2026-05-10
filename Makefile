# Makefile — atalhos de desenvolvimento QDI
.PHONY: help install install-hooks dev down logs test test-domain lint format type-check clean migrate ci-integration frontend-init qa-backend openapi-export mvp-gate verify-schema-mvp verify-schema-mvp-strict audit-secrets audit-catalogo export-manifesto-pesos-md go-live go-live-45min uv-lock uv-lock-check k6-smoke

PYTHON := python3.12
VENV := .venv
PIP := $(VENV)/bin/pip
# Prefer `uv` no PATH; fallback ao binário instalado no venv (`pip install uv`).
UV := $(shell command -v uv 2>/dev/null || echo $(VENV)/bin/uv)

help: ## Mostra esta ajuda
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Cria .venv e instala dependências
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -e ".[dev]"
	@$(PIP) install uv >/dev/null 2>&1 || true
	@echo ""
	@echo "✅ Ambiente Python pronto. Ative com: source $(VENV)/bin/activate"

install-hooks: ## Configura Git para usar .githooks/ (pre-commit + commit-msg)
	git config core.hooksPath .githooks
	chmod +x .githooks/commit-msg .githooks/pre-commit 2>/dev/null || true
	@command -v gitleaks >/dev/null 2>&1 || echo "⚠️  gitleaks não encontrado — brew install gitleaks (opcional, recomendado)."
	@echo "✅ Hooks Git apontando para .githooks/"

dev: ## Sobe ambiente de dev (db + api + web); --build alinha deps do pyproject na imagem da API
	docker compose up -d --build --remove-orphans
	@bash -ec 'source INICIAR_APP/lib/qdi-env.sh && qdi_cd_root "$(CURDIR)/INICIAR_APP" && if qdi_wait_api_health 25; then echo "✓ API /health OK."; else echo "⚠ API ainda não respondeu — docker compose logs api"; fi'
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

test-domain: ## Cobertura 100% em src/domain (statements + branches; ver _DEVELOPER/PLANO_EXECUCAO_COBERTURA_100.md)
	PYTHONPATH=. $(VENV)/bin/coverage run --branch --source=src/domain -m pytest -o addopts= -p no:cov tests/unit/domain -q
	$(VENV)/bin/coverage report --include='src/domain/*' --fail-under=100 --show-missing

audit-secrets: ## Heurística anti-padrões S-01 (segredos em fonte)
	@bash scripts/audit_secrets.sh

audit-catalogo: ## G1 — invariantes estruturais em perguntas_mvp.json (avisos pilar ABNT)
	PYTHONPATH=. $(VENV)/bin/python scripts/auditoria_catalogo_perguntas_mvp.py

export-manifesto-pesos-md: ## Regenera docs/refs/MANIFESTO_PESOS_EXPORTADO.md a partir do catálogo JSON
	PYTHONPATH=. $(VENV)/bin/python scripts/export_manifesto_pesos_md.py

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

verify-schema-mvp-strict: ## Como verify-schema-mvp + CNAE 0013/0014 + normativa score macro 0015 (modo strict)
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

go-live: ## Executa pré-voo técnico do checklist de go-live (~45min)
	@bash scripts/go_live_45min.sh

go-live-45min: ## Alias para go-live (compatibilidade)
	@bash scripts/go_live_45min.sh

uv-lock: ## Regenera uv.lock a partir do pyproject.toml (resolve deps; commit o ficheiro)
	@test -x "$(UV)" || { echo "❌ uv não encontrado. Rode: make install (instala uv no venv) ou: brew install uv"; exit 1; }
	$(UV) lock

uv-lock-check: ## Falha CI-local se uv.lock estiver desactualizado face ao pyproject
	@test -f uv.lock || { echo "❌ uv.lock ausente — rode: make uv-lock"; exit 1; }
	@test -x "$(UV)" || { echo "❌ uv não encontrado. Rode: make install ou: brew install uv"; exit 1; }
	$(UV) lock --check

k6-smoke: ## Smoke k6 em GET /health (BASE_URL opcional; requer binário k6)
	@command -v k6 >/dev/null 2>&1 || { echo "❌ k6 não encontrado — brew install k6"; exit 1; }
	k6 run loadtest/k6_diagnostico_smoke.js
