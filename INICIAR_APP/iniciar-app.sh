#!/usr/bin/env bash
# QualiDiagIQ — inicialização e bateria de QA local (PLANO_COMPLETO_HANDOFF §5).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT"

export POSTGRES_CI_URL="${POSTGRES_CI_URL:-postgresql://postgres:postgres@127.0.0.1:60322/postgres}"

usage() {
  cat <<'EOF'
Uso: iniciar-app.sh <comando>

  deps          make install + npm ci (frontend)
  backend       make qa-backend (ruff + mypy + pytest)
  integration   migrações SQL + pytest tests/integration/
  frontend      npm ci + lint + playwright + test:e2e
  dev           docker compose up -d
  stop          docker compose down
  full          deps + backend + integration + frontend (ver SKIP_* abaixo)

Variáveis:
  POSTGRES_CI_URL      URL Postgres (default porta compose 60322)
  SKIP_DEPS=1          full: pula deps
  SKIP_INTEGRATION=1   full: pula integration
  SKIP_FRONTEND=1      full: pula frontend

Documentação: INICIAR_APP/README.md
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

cmd="${1:-help}"
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
    docker compose up -d
    echo "→ API http://localhost:60000/docs · Web http://localhost:60001 · DB porta 60322"
    ;;
  stop)
    docker compose down
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
