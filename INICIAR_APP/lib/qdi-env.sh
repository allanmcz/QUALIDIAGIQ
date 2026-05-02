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
→ Health          curl -s http://127.0.0.1:60000/health

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
