# Makefile — atalhos de desenvolvimento QDI
.PHONY: help install dev down logs test lint format type-check clean migrate frontend-init

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
	docker compose up -d
	@echo ""
	@echo "✅ Ambiente subindo:"
	@echo "  → API:  http://localhost:8000/docs"
	@echo "  → Web:  http://localhost:3000"
	@echo "  → DB:   postgres://postgres:postgres@localhost:54322/postgres"
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
	$(VENV)/bin/ruff check src/ tests/

format: ## Formata código com black + ruff
	$(VENV)/bin/black src/ tests/
	$(VENV)/bin/ruff check --fix src/ tests/

type-check: ## Type checking com mypy
	$(VENV)/bin/mypy src/

clean: ## Limpa arquivos gerados
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/ .coverage build/ dist/

migrate: ## Roda migrações Supabase (placeholder)
	@echo "TODO: configurar supabase migration up quando supabase-cli estiver instalado"

frontend-init: ## Inicializa o frontend Next.js (executar uma vez)
	cd frontend && npx create-next-app@14 . --ts --tailwind --app --eslint --no-src-dir
	cd frontend && npm install @anthropic-ai/sdk lucide-react @radix-ui/react-progress recharts

all: install dev ## Setup completo + sobe ambiente
