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

# Garante daemon Docker antes de `docker compose` (macOS: OrbStack ou Docker Desktop).
# Timeout: QDI_DOCKER_START_TIMEOUT_SEC (default 90).
qdi_ensure_docker_daemon() {
  if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
    return 0
  fi

  if ! command -v docker >/dev/null 2>&1; then
    echo "Erro: CLI 'docker' não encontrada. Instale Docker Desktop ou OrbStack." >&2
    return 1
  fi

  echo "→ Docker não está a correr; a iniciar o motor local…" >&2

  case "$(uname -s)" in
    Darwin)
      if [[ -d "/Applications/OrbStack.app" ]]; then
        open -a OrbStack >/dev/null 2>&1 || true
      elif [[ -d "/Applications/Docker.app" ]]; then
        open -a Docker >/dev/null 2>&1 || true
      else
        echo "Erro: instale OrbStack ou Docker Desktop em /Applications." >&2
        return 1
      fi
      ;;
    Linux)
      if command -v systemctl >/dev/null 2>&1; then
        systemctl --user start docker-desktop 2>/dev/null \
          || systemctl start docker 2>/dev/null \
          || sudo systemctl start docker 2>/dev/null \
          || true
      fi
      ;;
    *)
      echo "Erro: inicie o Docker manualmente neste sistema (uname: $(uname -s))." >&2
      return 1
      ;;
  esac

  local max_wait="${QDI_DOCKER_START_TIMEOUT_SEC:-90}"
  local i=0
  while (( i < max_wait )); do
    if docker info >/dev/null 2>&1; then
      echo "✓ Docker pronto ($(docker info -f '{{.OperatingSystem}}' 2>/dev/null || echo motor ativo))." >&2
      return 0
    fi
    if (( i == 0 || i % 15 == 0 )); then
      echo "  … à espera do Docker (${i}s / ${max_wait}s)" >&2
    fi
    sleep 1
    i=$((i + 1))
  done

  echo "Erro: Docker não ficou disponível em ${max_wait}s." >&2
  echo "  Abra OrbStack ou Docker Desktop (ícone estável) e execute de novo." >&2
  return 1
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
