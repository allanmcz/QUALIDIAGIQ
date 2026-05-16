#!/usr/bin/env bash
#
# QualiDiagIQ — CLI único: Docker (dev/stop/logs/status), QA local e pipeline full.
# Documentação: INICIAR_APP/README.md

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/qdi-env.sh
source "$SCRIPT_DIR/lib/qdi-env.sh"
qdi_cd_root "$SCRIPT_DIR"

export POSTGRES_CI_URL="${POSTGRES_CI_URL:-postgresql://postgres:postgres@127.0.0.1:60322/postgres}"

usage() {
  cat <<'EOF'
QualiDiagIQ — INICIAR_APP/iniciar-app.sh

Docker / ambiente
  (omitido)   Equivale a: dev
  dev         docker compose up -d --build --remove-orphans (db + api + web; rebuild se Dockerfile/pyproject mudaram)
  stop        docker compose down (atalho: ./INICIAR_APP/parar-app.sh)
  logs        docker compose logs -f (Ctrl+C só para o tail; containers continuam)
  status      docker compose ps

Qualidade / pipeline
  deps        make install + npm ci (frontend)
  backend     make qa-backend (ruff + mypy + pytest)
  integration Migrações SQL + pytest tests/integration/ (precisa Postgres; psql)
  frontend    npm ci + lint + Playwright E2E
  full        deps → backend → integration → frontend (SKIP_* abaixo)

Ajuda
  help | -h | --help   Esta mensagem

Variáveis
  POSTGRES_CI_URL       Postgres para integration (default compose :60322)
  SKIP_DEPS=1           full: sem deps
  SKIP_INTEGRATION=1    full: sem integration
  SKIP_FRONTEND=1       full: sem frontend

Docs: INICIAR_APP/README.md
EOF
}

run_deps() {
  make install
  (cd frontend && npm ci)
}

run_backend() {
  make qa-backend
}

run_integration() {
  if ! command -v psql >/dev/null 2>&1; then
    echo "Erro: psql não encontrado. Instale postgresql-client." >&2
    exit 1
  fi
  echo "→ POSTGRES_CI_URL=$POSTGRES_CI_URL"
  make ci-integration
}

run_frontend() {
  cd frontend
  npm ci
  npm run lint
  npx playwright install --with-deps chromium
  npm run test:e2e
}

run_dev() {
  qdi_ensure_docker_daemon
  # --build: evita imagem da API “congelada” sem deps novas do pyproject.toml (ex.: langchain-ollama).
  docker compose up -d --build --remove-orphans
  echo "→ Aguardando GET /health na API (porta 60000)…"
  if qdi_wait_api_health 25; then
    echo "✓ API respondeu /health."
  else
    echo "⚠ API ainda não respondeu após as tentativas — veja: docker compose logs api" >&2
  fi
  qdi_print_service_info
}

cmd="${1:-dev}"
case "$cmd" in
  help|-h|--help)
    usage
    ;;
  deps)
    run_deps
    ;;
  backend)
    run_backend
    ;;
  integration)
    run_integration
    ;;
  frontend)
    run_frontend
    ;;
  dev)
    run_dev
    ;;
  stop)
    docker compose down
    ;;
  logs)
    docker compose logs -f
    ;;
  status)
    docker compose ps
    ;;
  full)
    if [[ "${SKIP_DEPS:-0}" != "1" ]]; then
      run_deps
    fi
    run_backend
    if [[ "${SKIP_INTEGRATION:-0}" != "1" ]]; then
      run_integration
    fi
    if [[ "${SKIP_FRONTEND:-0}" != "1" ]]; then
      run_frontend
    fi
    echo "✅ full concluído."
    ;;
  *)
    echo "Comando desconhecido: $cmd" >&2
    usage
    exit 1
    ;;
esac
