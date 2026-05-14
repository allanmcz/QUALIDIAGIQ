#!/usr/bin/env bash
#
# Gate técnico único — pré-voo go-live (handoff 10_PROMPT_CURSOR_IMPLEMENTACAO.md).
#
# Executa (ordem):
#   1. make lint
#   2. make type-check
#   3. npm run test:unit (frontend)
#   4. npx tsc --noEmit (frontend)
#   5. npm run build (frontend)
#   6. make audit-secrets
#   7. make mvp-gate — apenas se Postgres de teste responder (ou se forçado)
#
# Não apaga dados, não faz commit, não altera branches.
#
# Variáveis:
#   QDI_POSTGRES_TEST_URL — DSN Postgres (default postgresql://postgres:postgres@127.0.0.1:60322/postgres)
#   QDI_GO_LIVE_TECNICO_SKIP_MVP_GATE=1 — não tenta RLS/mvp-gate (só imprime lembrete)
#   QDI_GO_LIVE_TECNICO_REQUIRE_POSTGRES=1 — falha (exit 1) se Postgres indisponível ou mvp-gate falhar
#
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

POSTGRES_URL="${QDI_POSTGRES_TEST_URL:-postgresql://postgres:postgres@127.0.0.1:60322/postgres}"
SKIP_MVP="${QDI_GO_LIVE_TECNICO_SKIP_MVP_GATE:-0}"
REQUIRE_PG="${QDI_GO_LIVE_TECNICO_REQUIRE_POSTGRES:-0}"

log() {
  printf "\n[%s] %s\n" "$(date +%H:%M:%S)" "$1"
}

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "❌ Comando ausente: $1"
    exit 1
  fi
}

postgres_tcp_reachable() {
  # Usa Python do venv se existir (mesmo interpretador dos testes).
  local py="${ROOT_DIR}/.venv/bin/python"
  if [[ ! -x "$py" ]]; then
    py="$(command -v python3.12 || command -v python3 || true)"
  fi
  if [[ -z "$py" || ! -x "$py" ]]; then
    return 2
  fi
  QDI_PG_CHECK_URL="$POSTGRES_URL" "$py" <<'PY'
import os
import socket
from urllib.parse import urlparse

raw = os.environ.get("QDI_PG_CHECK_URL", "")
if not raw.strip():
    raise SystemExit(2)
u = urlparse(raw)
host = u.hostname or "127.0.0.1"
port = u.port or 5432
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(2)
try:
    s.connect((host, port))
except OSError:
    raise SystemExit(1)
finally:
    s.close()
raise SystemExit(0)
PY
}

print_postgres_instructions() {
  cat <<EOF

────────────────────────────────────────────────────────────────────
Postgres de integração não respondeu em ${POSTGRES_URL}
Para validar RLS / gate MVP localmente:
  1. make dev   # ou suba o serviço na porta mapeada (ex.: 60322)
  2. make migrate   # aplica src/infrastructure/db/migrations/*.sql
  3. export QDI_POSTGRES_TEST_URL="${POSTGRES_URL}"
  4. make mvp-gate

CI: definir POSTGRES_CI_URL / QDI_POSTGRES_TEST_URL e job que aplica migrações antes de pytest.
────────────────────────────────────────────────────────────────────
EOF
}

main() {
  require_cmd make

  log "T1 — Backend lint (ruff)"
  make lint

  log "T2 — Backend type-check (mypy)"
  make type-check

  log "T3 — Frontend testes unitários (vitest)"
  (cd frontend && npm run test:unit)

  log "T4 — Frontend TypeScript (tsc --noEmit)"
  (cd frontend && npx tsc --noEmit)

  log "T5 — Frontend build (next build)"
  (cd frontend && npm run build)

  log "T6 — Auditoria heurística de segredos (scripts/audit_secrets.sh)"
  make audit-secrets

  if [[ "$SKIP_MVP" == "1" ]]; then
    log "T7 — mvp-gate omitido (QDI_GO_LIVE_TECNICO_SKIP_MVP_GATE=1)"
    echo ""
    echo "✅ Gate técnico (sem mvp-gate) concluído."
    exit 0
  fi

  log "T7 — RLS / gate MVP (make mvp-gate) — deteção de Postgres"
  if postgres_tcp_reachable; then
    export QDI_POSTGRES_TEST_URL="$POSTGRES_URL"
    make mvp-gate
  else
    print_postgres_instructions
    if [[ "$REQUIRE_PG" == "1" ]]; then
      echo "❌ QDI_GO_LIVE_TECNICO_REQUIRE_POSTGRES=1 — Postgres obrigatório indisponível."
      exit 1
    fi
    echo "⚠️  Postgres indisponível — gate técnico principal concluído sem mvp-gate (exit 0)."
  fi

  echo ""
  echo "✅ Gate técnico go-live concluído (lint + mypy + front + audit-secrets + mvp-gate quando aplicável)."
}

main "$@"
