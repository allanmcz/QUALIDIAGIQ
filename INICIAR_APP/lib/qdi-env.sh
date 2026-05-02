#!/usr/bin/env bash
# Biblioteca compartilhada dos scripts INICIAR_APP (QualiDiagIQ).
# Carregamento: após definir SCRIPT_DIR do chamador:
#   source "$SCRIPT_DIR/lib/qdi-env.sh"
#   qdi_cd_root "$SCRIPT_DIR"

qdi_cd_root() {
  local d="${1:?diretório INICIAR_APP (dirname do script)}"
  QDI_ROOT="$(cd "$d/.." && pwd)"
  cd "$QDI_ROOT" || return 1
}

# Texto único de URLs / dicas (evita drift entre iniciar.sh e iniciar-app.sh).
qdi_print_service_info() {
  cat <<'EOF'

→ API (Swagger)   http://127.0.0.1:60000/docs
→ Web (Next)      http://127.0.0.1:60001  (Next no container :3010 → host :60001; fetch → /api-backend/*)
→ Postgres        postgresql://postgres:postgres@127.0.0.1:60322/postgres
→ Mailpit (OTP)   http://127.0.0.1:8025  · SMTP API interno: mailpit:1025
→ Health          curl -s http://127.0.0.1:60000/health

ℹ Compose (default): QDI_CI_PLAYWRIGHT_INTEGRATED=1 — login via Postgres; diagnósticos em memória no processo da API.
  Persistência real no projeto Supabase: `.env` na raiz com QDI_CI_PLAYWRIGHT_INTEGRATED=0 e SUPABASE_* (substituição automática no compose).
ℹ Self-service (OTP): tenant default 44444444-4444-4444-8444-444444444444 — override via QDI_SELF_SERVICE_TENANT_ID no `.env`.
ℹ LLM: ANTHROPIC_API_KEY / OPENAI_API_KEY vazias no host são normais em dev (só afetam rotas de IA).
ℹ Next no Compose já usa NEXT_PUBLIC_API_URL=/api-backend. frontend/.env.local importa sobretudo para npm no host (porta 3010).

EOF
}

# Aguarda e testa GET /health. Exit code 0 = OK, 1 = falhou (silencioso no stderr).
qdi_health_probe() {
  local sleep_s="${1:-4}"
  sleep "$sleep_s"
  curl -sf --connect-timeout 3 "http://127.0.0.1:60000/health" >/dev/null
}

# Espera a API responder /health (até N tentativas, intervalo 2s). 0 = OK.
qdi_wait_api_health() {
  local max_attempts="${1:-20}"
  local i=0
  while (( i < max_attempts )); do
    if curl -sf --connect-timeout 3 "http://127.0.0.1:60000/health" >/dev/null; then
      return 0
    fi
    i=$((i + 1))
    sleep 2
  done
  return 1
}
