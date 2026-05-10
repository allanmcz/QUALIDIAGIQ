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
SKIP_OPENAPI_DRIFT="${QDI_GO_LIVE_SKIP_OPENAPI_DRIFT:-0}"
TRACE_ID="${QDI_TRACE_ID:-go-live-45min-$(date +%Y%m%d%H%M%S)}"

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "❌ Dependência ausente: '$1'"
    exit 1
  fi
}

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
SKIP_OPENAPI_DRIFT: $SKIP_OPENAPI_DRIFT (1 = pula git diff do openapi.generated.json)
TRACE_ID: $TRACE_ID
EOF
}

main() {
  require_cmd curl
  require_cmd rg
  require_cmd make

  print_context

  run_step "A1 - Commit de release" git log -1 --oneline
  run_step "A2 - Backend lint" make lint
  run_step "A2 - Backend test" make test

  if [[ "$SKIP_OPENAPI_DRIFT" != "1" ]]; then
    run_step "A2c - OpenAPI versionado sem drift (git diff)" env ROOT_DIR="$ROOT_DIR" bash -c '
      set -euo pipefail
      cd "$ROOT_DIR"
      if [[ -x "$ROOT_DIR/.venv/bin/python" ]]; then PY="$ROOT_DIR/.venv/bin/python"; else PY=python3; fi
      PYTHONPATH="$ROOT_DIR" "$PY" scripts/export_openapi_json.py
      git diff --exit-code docs/api/openapi.generated.json
    '
  else
    log "A2c - OpenAPI drift pulado (QDI_GO_LIVE_SKIP_OPENAPI_DRIFT=1)."
  fi

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
    if [[ -z "${QDI_POSTGRES_TEST_URL:-}" ]]; then
      log "C1 - QDI_POSTGRES_TEST_URL não definido; make usará default local (127.0.0.1:60322)."
    fi
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

  log "C3 - Smoke endpoints públicos (institucional + metodologia)"
  for ep in "/public/institucional" "/diagnosticos/metodologia"; do
    code="$(curl -sS -o /dev/null -w "%{http_code}" -H "X-Trace-Id: $TRACE_ID" "$API_URL$ep")"
    if [[ "$code" != "200" ]]; then
      echo "❌ GET $ep → HTTP $code (esperado 200) em $API_URL"
      exit 1
    fi
  done

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
