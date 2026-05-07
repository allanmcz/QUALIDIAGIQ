#!/usr/bin/env bash
# Go-live 45min — executor de pré-voo/smoke técnico.
# Não faz deploy; valida gates antes/depois do cutover.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

API_URL="${QDI_API_BASE_URL:-http://127.0.0.1:60000}"
RUN_E2E="${QDI_GO_LIVE_RUN_E2E:-0}"
RUN_TYPECHECK="${QDI_GO_LIVE_RUN_TYPECHECK:-0}"
SKIP_SCHEMA="${QDI_GO_LIVE_SKIP_SCHEMA:-0}"
TRACE_ID="${QDI_TRACE_ID:-go-live-45min-$(date +%Y%m%d%H%M%S)}"

log() {
  printf "\n[%s] %s\n" "$(date +%H:%M:%S)" "$1"
}

run_step() {
  local title="$1"
  shift
  log "$title"
  "$@"
}

print_context() {
  cat <<EOF
Go-live 45min executor
ROOT_DIR: $ROOT_DIR
API_URL: $API_URL
RUN_E2E: $RUN_E2E (1 = roda playwright)
RUN_TYPECHECK: $RUN_TYPECHECK (1 = roda mypy)
SKIP_SCHEMA: $SKIP_SCHEMA (1 = pula verify-schema-mvp-strict)
TRACE_ID: $TRACE_ID
EOF
}

main() {
  print_context

  run_step "A1 - Commit de release" git log -1 --oneline
  run_step "A2 - Backend lint" make lint
  run_step "A2 - Backend test" make test

  if [[ "$RUN_TYPECHECK" == "1" ]]; then
    run_step "A2 - Backend type-check" make type-check
  fi

  run_step "A3 - Front lint/build" bash -lc "cd frontend && npm run lint && npm run build"

  if [[ "$RUN_E2E" == "1" ]]; then
    run_step "A3 - Front E2E" bash -lc "cd frontend && npm run test:e2e"
  else
    log "A3 - Front E2E pulado (defina QDI_GO_LIVE_RUN_E2E=1 para executar)."
  fi

  if [[ "$SKIP_SCHEMA" == "1" ]]; then
    log "C1 - verify-schema-mvp-strict pulado (QDI_GO_LIVE_SKIP_SCHEMA=1)."
  else
    run_step "C1 - Verify schema strict" make verify-schema-mvp-strict
  fi

  log "C2 - Health API com trace id"
  local health_output
  health_output="$(curl -sS -i -H "X-Trace-Id: $TRACE_ID" "$API_URL/health")"
  printf "%s\n" "$health_output" | rg -n "HTTP/|X-Trace-Id|x-trace-id|healthy|ok" || true

  if ! printf "%s\n" "$health_output" | rg -q "HTTP/[0-9.]+\s+200"; then
    echo "❌ /health não retornou HTTP 200 em $API_URL"
    exit 1
  fi

  cat <<'EOF'

✅ Pré-voo técnico concluído.
Próximo passo manual (Fase D):
1) Login JWT em produção
2) Wizard até LGPD
3) POST /diagnosticos (201 + aceite)
4) GET /diagnosticos (lista)

Use docs/operacao/CHECKLIST_GO_LIVE_45MIN.md para marcar execução.
EOF
}

main "$@"
