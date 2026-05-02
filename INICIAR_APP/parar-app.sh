#!/usr/bin/env bash
#
# QualiDiagIQ — encerra o stack Docker (db + api + web + mailpit).
# Uso: ./INICIAR_APP/parar-app.sh
#
# Equivale a: make down  |  ./INICIAR_APP/iniciar-app.sh stop
# Documentação: INICIAR_APP/README.md

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/qdi-env.sh
source "$SCRIPT_DIR/lib/qdi-env.sh"
qdi_cd_root "$SCRIPT_DIR"

usage() {
  cat <<'EOF'
QualiDiagIQ — INICIAR_APP/parar-app.sh

Encerra containers do Compose neste repositório (API :60000, Web :60001, Postgres :60322).

  (nenhum)          docker compose down
  -v, --volumes     docker compose down --volumes (apaga dados locais do Postgres; irreversível)

  -h, --help        Esta mensagem

Alternativas: make down  ·  ./INICIAR_APP/iniciar-app.sh stop
EOF
}

compose_down() {
  if (($# > 0)); then
    echo "→ docker compose down $*"
    docker compose down "$@"
  else
    echo "→ docker compose down"
    docker compose down
  fi
  echo "✓ Stack QDI encerrado."
}

case "${1:-}" in
  -h|--help)
    usage
    ;;
  "")
    compose_down
    ;;
  -v|--volumes)
    compose_down --volumes
    ;;
  *)
    echo "Argumento desconhecido: $1 (use --help)" >&2
    exit 1
    ;;
esac
